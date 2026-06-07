# Домашнее задание 3

---

## Структура репозитория

```
├── README.md
├── scripts/
│   ├── check_mapping.sh               # Bash-скрипт разбора flagstat и алгоритм OK/not OK
│   ├── pipeline.py                    # Пайплайн на Prefect
│   ├── hello_world.py                 # Hello world на Prefect
│   └── hello_world.log                # Логирование Hello world
├── results/
│   ├── flagstat.txt                   # Результат samtools flagstat
│   ├── pipeline_run.log               # Лог пайплайна
│   └── fastqc/
│       └── QC-report_SRR2584863.html  # QC-отчёт FastQC
└── dag_visualization.png              # Визуализация DAG из Prefect UI
```

---

## 1. Входные данные
   - **Ссылка на загруженные прочтения из NCBI SRA:** https://www.ncbi.nlm.nih.gov/sra/SRR2584863

---

## 3. Результаты картирования (samtools flagstat)

Файл `results/flagstat.txt`:

```
3131060 + 0 in total (QC-passed reads + QC-failed reads)
2939902 + 0 mapped (93.89% : N/A)
2796752 + 0 properly paired (90.03% : N/A)
...
```

**Вывод:** 93.89% ридов успешно картировано → **OK** (порог >90% пройден).

---

## 4. Bash-скрипт разбора flagstat

Файл `scripts/check_mapping.sh` — скрипт разбора результатов `samtools flagstat`.  
Извлекает процент картированных ридов и выводит оценку качества OK / not OK.

```bash
chmod +x scripts/check_mapping.sh
./scripts/check_mapping.sh results/flagstat.txt
```

Пример вывода:
```
Результаты картирования
Файл: results/flagstat.txt
% картированных ридов: 93.89%

Оценка: OK
```

---

## 6. Установка и развёртывание Prefect

### Требования
- Python 3.9+
- Linux / WSL2 (Ubuntu)

### Установка

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установить Prefect
pip install prefect

# Проверить установку
prefect version
```

### Запуск с Prefect Cloud

```bash
# Создание prefect-cloud и вход в аккаунт
curl -LsSf https://astral.sh/uv/install.sh | sh # Install `uv`.
uvx prefect-cloud login # Installs `prefect-cloud` into a temporary virtual env.
```

### Запуск с локальным сервером

```bash
# Запустить локальный сервер
prefect server start

# Веб-интерфейс доступен по адресу:
# http://localhost:4200
```

---

## 14. Отличия DAG от блок-схемы алгоритма

DAG отличается от блок-схемы тем, что показывает реальные зависимости между
задачами и их статус выполнения, но не содержит условных переходов (if/else)
в явном виде — ветвление происходит в коде Python, а не в графе.
