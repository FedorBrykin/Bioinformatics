#!/usr/bin/env python3
"""
ДЗ №4.

Запуск:
    pip install requests pandas openpyxl
    python annotate.py student_05.vcf

Результаты:
    vep_raw.json          - ответ Ensembl VEP REST
    vep_all_consequences.tsv - все пары: вариант x транскрипт
    clinvar_raw.json      - ответ ClinVar
    gnomad_raw.json       - ответ gnomAD
    annotation_settings.json - параметры запросов
    annotated_variants.tsv / .xlsx - итоговая таблица
"""
import json, sys, time
import requests
import pandas as pd

VCF = sys.argv[1] if len(sys.argv) > 1 else "student_05.vcf"
GNOMAD_DATASET = "gnomad_r4"          
HEAD = {"Content-Type": "application/json", "Accept": "application/json"}

def read_vcf(path):
    out = []
    for l in open(path):
        if l.startswith("#"):
            continue
        c, pos, vid, ref, alt = l.rstrip("\n").split("\t")[:5]
        out.append(dict(chrom=c, pos=int(pos), id=vid, ref=ref, alt=alt,
                        key=f"{c}-{pos}-{ref}-{alt}"))
    return out

VEP_URL = "https://rest.ensembl.org/vep/human/region"
VEP_PARAMS = {          
    "canonical": 1, "mane": 1, "hgvs": 1, "protein": 1, "symbol": 1,
    "variant_class": 1, "biotype": 1, "numbers": 1, "domains": 0,
    "check_existing": 1, "af": 1, "af_1kg": 1, "af_gnomadg": 1, "af_gnomade": 1,
    "appris": 1, "tsl": 1, "uniprot": 0, "pick": 0,   
}

def run_vep(variants):
    res = []
    for i in range(0, len(variants), 50):
        chunk = variants[i:i+50]
        body = {"variants": [f"{v['chrom']} {v['pos']} {v['id']} {v['ref']} {v['alt']} . . ." for v in chunk]}
        r = requests.post(VEP_URL, headers=HEAD, params=VEP_PARAMS, data=json.dumps(body), timeout=120)
        r.raise_for_status()
        res += r.json()
        time.sleep(1)
    return res

def tx_priority(t):
    return (
        0 if t.get("mane_select") else 1,
        0 if t.get("mane_plus_clinical") else 1,
        0 if t.get("canonical") == 1 else 1,
        0 if t.get("biotype") == "protein_coding" else 1,
    )

def pick_transcript(vep_entry):
    most = vep_entry.get("most_severe_consequence")
    tcs = vep_entry.get("transcript_consequences", [])
    if not tcs:
        return most, None
    cand = [t for t in tcs if most in t.get("consequence_terms", [])] or tcs
    return most, sorted(cand, key=tx_priority)[0]

GQL = "https://gnomad.broadinstitute.org/api"
Q = """query($id:String!,$ds:DatasetId!){
  variant(variantId:$id, dataset:$ds){
    variantId rsids
    exome{ac an af}
    genome{ac an af}
  }}"""

def run_gnomad(variants):
    out = {}
    for v in variants:
        try:
            r = requests.post(GQL, json={"query": Q, "variables": {"id": v["key"], "ds": GNOMAD_DATASET}},
                              timeout=60)
            out[v["key"]] = r.json()
        except Exception as e:
            out[v["key"]] = {"error": str(e)}
        time.sleep(1.5)      
    return out

def gnomad_af(resp):
    try:
        d = resp["data"]["variant"]
    except Exception:
        return None, None, None
    if not d:
        return None, None, None
    e, g = d.get("exome"), d.get("genome")
    ac = sum(x["ac"] for x in (e, g) if x)
    an = sum(x["an"] for x in (e, g) if x)
    return (ac / an if an else None,
            e["af"] if e else None,
            g["af"] if g else None)

EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def clinvar_lookup(rsid, chrom, pos):
    num = rsid[2:] if rsid.startswith("rs") else None
    terms = ([f"{num}[RS]"] if num else []) + [f"{chrom}[CHR] AND {pos}[CHRPOS38]"]
    for term in terms:
        r = requests.get(EU + "esearch.fcgi", params={"db": "clinvar", "term": term, "retmode": "json"}, timeout=60)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        time.sleep(0.4)
        if ids:
            s = requests.get(EU + "esummary.fcgi", params={"db": "clinvar", "id": ",".join(ids), "retmode": "json"},
                             timeout=60).json()
            time.sleep(0.4)
            return {"term": term, "ids": ids, "summary": s}
    return {"term": terms, "ids": [], "summary": None}

def parse_clinvar(cv):
    if not cv["ids"]:
        return "нет", "", "", ""
    res = cv["summary"]["result"]
    items = []
    for i in cv["ids"]:
        d = res.get(i, {})
        g = d.get("germline_classification") or d.get("clinical_significance") or {}
        items.append((d.get("accession", i), g.get("description", ""), g.get("review_status", ""), d.get("title", "")))
    return ("есть", "; ".join(x[1] for x in items), "; ".join(x[2] for x in items), "; ".join(x[0] for x in items))

def main():
    variants = read_vcf(VCF)
    assert len(variants) == 50, f"ожидалось 50 вариантов, найдено {len(variants)}"

    print("VEP ..."); vep = run_vep(variants)
    json.dump(vep, open("vep_raw.json", "w"), indent=1)

    vep_by_pos = {}
    for e in vep:
        f = e["input"].split()
        vep_by_pos[(f[0], int(f[1]), f[3], f[4])] = e

    print("gnomAD ..."); gn = run_gnomad(variants)
    json.dump(gn, open("gnomad_raw.json", "w"), indent=1)

    print("ClinVar ..."); cvs = {}
    for v in variants:
        try:
            cvs[v["key"]] = clinvar_lookup(v["id"], v["chrom"], v["pos"])
        except Exception as e:
            cvs[v["key"]] = {"ids": [], "summary": None, "error": str(e)}
    json.dump(cvs, open("clinvar_raw.json", "w"), indent=1)

    rows, all_rows = [], []
    for v in variants:
        e = vep_by_pos.get((v["chrom"], v["pos"], v["ref"], v["alt"]), {})
        most, t = pick_transcript(e)
        for tc in e.get("transcript_consequences", []):
            all_rows.append(dict(variant=v["key"], gene=tc.get("gene_symbol"), transcript=tc.get("transcript_id"),
                                 mane_select=tc.get("mane_select"), canonical=tc.get("canonical"),
                                 biotype=tc.get("biotype"), consequence=",".join(tc.get("consequence_terms", [])),
                                 impact=tc.get("impact"), hgvsc=tc.get("hgvsc"), hgvsp=tc.get("hgvsp"),
                                 amino_acids=tc.get("amino_acids"), sift=tc.get("sift_prediction"),
                                 polyphen=tc.get("polyphen_prediction")))
        n_tx = len(e.get("transcript_consequences", []))
        if t:
            rule = ("MANE Select" if t.get("mane_select") else
                    "MANE Plus Clinical" if t.get("mane_plus_clinical") else
                    "canonical" if t.get("canonical") == 1 else
                    "protein_coding (нет MANE/canonical)" if t.get("biotype") == "protein_coding" else
                    "первый из оставшихся")
        else:
            rule = "транскриптов нет (межгенный/регуляторный)"
        af, af_e, af_g = gnomad_af(gn[v["key"]])
        present, sig, status, acc = parse_clinvar(cvs[v["key"]])
        rows.append({
            "variant": f"{v['chrom']}:{v['pos']} {v['ref']}>{v['alt']}",
            "input_id": v["id"],
            "gene": t.get("gene_symbol") if t else "",
            "most_severe_consequence_VEP": most,
            "impact": t.get("impact") if t else "",
            "selected_transcript": t.get("transcript_id") if t else "",
            "transcript_selection_rule": rule,
            "n_transcripts_VEP": n_tx,
            "HGVSc": t.get("hgvsc") if t else "",
            "HGVSp": t.get("hgvsp") if t else "",
            "rsID": v["id"],
            "gnomAD_AF_total": af, "gnomAD_AF_exomes": af_e, "gnomAD_AF_genomes": af_g,
            "ClinVar_record": present,
            "ClinVar_interpretation": sig,
            "ClinVar_review_status": status,
            "ClinVar_accession": acc,
        })

    pd.DataFrame(all_rows).to_csv("vep_all_consequences.tsv", sep="\t", index=False)
    df = pd.DataFrame(rows)
    assert len(df) == 50
    df.to_csv("annotated_variants.tsv", sep="\t", index=False)
    df.to_excel("annotated_variants.xlsx", index=False)

    json.dump({"VEP_endpoint": VEP_URL, "VEP_params": VEP_PARAMS, "assembly": "GRCh38",
               "transcript_rule": tx_priority.__doc__,
               "gnomAD": {"endpoint": GQL, "dataset": GNOMAD_DATASET},
               "ClinVar": {"endpoint": EU, "db": "clinvar", "search": "rsID[RS], иначе chr+CHRPOS38"},
               "date": time.strftime("%Y-%m-%d")}, open("annotation_settings.json", "w"), indent=1, ensure_ascii=False)
    print(df[["variant", "gene", "most_severe_consequence_VEP", "gnomAD_AF_total", "ClinVar_record"]].to_string())

if __name__ == "__main__":
    main()
