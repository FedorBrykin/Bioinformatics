import subprocess
import re
from pathlib import Path
from prefect import flow, task

# ── Пути ──────────────────────────────────────────────────────────────────────
BASE      = Path.home() / "ecoli_pipeline"
REF       = BASE / "reference" / "ecoli_ref.fa"
R1        = BASE / "data"    / "SRR2584863_1.fastq.gz"
R2        = BASE / "data"    / "SRR2584863_2.fastq.gz"
RESULTS   = BASE / "results"
FASTQC_DIR = RESULTS / "fastqc"

# ── Tasks ─────────────────────────────────────────────────────────────────────

@task(name="FastQC")
def run_fastqc():
    FASTQC_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["fastqc", str(R1), str(R2), "-o", str(FASTQC_DIR)],
        check=True
    )
    qc_out = FASTQC_DIR / "QC-report_SRR2584863.html"
    (FASTQC_DIR / "SRR2584863_1_fastqc.html").rename(qc_out)
    print(f"QC-отчёт сохранён: {qc_out}")
    return str(qc_out)


@task(name="BWA MEM — картирование")
def run_bwa():
    sam = RESULTS / "sample.sam"
    log = RESULTS / "bwa.log"
    with open(sam, "w") as out, open(log, "w") as err:
        subprocess.run(
            ["bwa", "mem", str(REF), str(R1), str(R2)],
            stdout=out, stderr=err, check=True
        )
    print(f"SAM файл создан: {sam}")
    return str(sam)


@task(name="samtools view — SAM→BAM")
def run_samtools_view(sam_path: str):
    bam = RESULTS / "sample.bam"
    with open(bam, "wb") as out:
        subprocess.run(
            ["samtools", "view", "-bS", sam_path],
            stdout=out, check=True
        )
    print(f"BAM файл создан: {bam}")
    return str(bam)


@task(name="samtools flagstat — оценка")
def run_flagstat(bam_path: str):
    flagstat = RESULTS / "flagstat.txt"
    with open(flagstat, "w") as out:
        subprocess.run(
            ["samtools", "flagstat", bam_path],
            stdout=out, check=True
        )
    print(f"Flagstat сохранён: {flagstat}")
    return flagstat.read_text()


@task(name="Оценка % картирования")
def check_mapping_quality(flagstat_text: str):
    match = re.search(r"\((\d+\.\d+)%", flagstat_text)
    if not match:
        raise ValueError("Не удалось извлечь % картирования из flagstat")
    pct = float(match.group(1))
    print(f"% картированных ридов: {pct}%")
    if pct > 90:
        print("Оценка: OK")
        return True
    else:
        print("Оценка: not OK")
        return False


@task(name="samtools sort")
def run_samtools_sort(bam_path: str):
    sorted_bam = RESULTS / "sample.sorted.bam"
    subprocess.run(
        ["samtools", "sort", bam_path, "-o", str(sorted_bam)],
        check=True
    )
    subprocess.run(["samtools", "index", str(sorted_bam)], check=True)
    print(f"Отсортированный BAM: {sorted_bam}")
    return str(sorted_bam)


@task(name="FreeBayes — коллинг вариантов")
def run_freebayes(sorted_bam: str):
    vcf = RESULTS / "sample.vcf"
    with open(vcf, "w") as out:
        subprocess.run(
            ["freebayes", "-f", str(REF), sorted_bam],
            stdout=out, check=True
        )
    print(f"VCF файл создан: {vcf}")
    return str(vcf)


# ── Flow ──────────────────────────────────────────────────────────────────────

@flow(name="Пайплайн оценки качества картирования E. coli")
def ecoli_pipeline():
    # 1. FastQC
    run_fastqc()

    # 2. Картирование
    sam = run_bwa()

    # 3. SAM → BAM
    bam = run_samtools_view(sam)

    # 4. Flagstat
    flagstat_text = run_flagstat(bam)

    # 5. Проверка качества
    is_ok = check_mapping_quality(flagstat_text)

    if is_ok:
        # 6. Сортировка
        sorted_bam = run_samtools_sort(bam)
        # 7. Коллинг вариантов
        run_freebayes(sorted_bam)
        print("Finished")
    else:
        print("Пайплайн остановлен: качество картирования недостаточное")


if __name__ == "__main__":
    ecoli_pipeline()
