# ДЗ №4.

## Структура ветки
| Файл | Что из себя представляет |
|---|---|
| `student_05.vcf` | исходный VCF |
| `vcf_stats.py`, `vcf_stats.txt` | статистика VCF |
| `annotate.py` | скрипт аннотации (VEP REST + ClinVar + gnomAD) |
| `vep_raw.json`, `vep_all_consequences.tsv` | экспорт VEP |
| `clinvar_raw.json` | результат ClinVar |
| `gnomad_raw.json` | результат gnomAD |
| `annotation_settings.json` | настройки аннотации |
| `annotated_variants_final.xlsx` | итоговая таблица |
| `report.md` | отчёт |

## Как воспроизвести
```
pip install requests pandas openpyxl
python vcf_stats.py student_05.vcf
python annotate.py student_05.vcf
```

