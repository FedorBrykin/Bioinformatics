"""Пункт 2"""
import sys
from collections import Counter
TS = {("A","G"),("G","A"),("C","T"),("T","C")}
path = sys.argv[1] if len(sys.argv) > 1 else "student_05.vcf"
recs = [l.rstrip("\n").split("\t") for l in open(path) if not l.startswith("#")]
chroms = Counter(r[0] for r in recs)
ts = sum((r[3], r[4]) in TS for r in recs)
tv = len(recs) - ts
out = [
    f"Файл: {path}",
    f"Число записей: {len(recs)}",
    f"Хромосома 21: {chroms['21']}",
    f"Хромосома 22: {chroms['22']}",
    f"Транзиции: {ts}",
    f"Трансверсии: {tv}",
    f"Ts/Tv: {ts/tv:.2f}",
    "Замены REF>ALT: " + ", ".join(f"{a}>{b}: {n}" for (a,b),n in sorted(Counter((r[3],r[4]) for r in recs).items())),
]
print("\n".join(out))
open("vcf_stats.txt", "w").write("\n".join(out) + "\n")
