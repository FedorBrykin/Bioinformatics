#!/bin/bash

FLAGSTAT_FILE=$1

if [ ! -f "$FLAGSTAT_FILE" ]; then
    echo "Файл не найден: $FLAGSTAT_FILE"
    exit 1
fi

MAPPED_PCT=$(grep "^[0-9]* + [0-9]* mapped (" "$FLAGSTAT_FILE" \
    | grep -v "primary" \
    | grep -oP '\(\K[0-9]+\.[0-9]+(?=%)')

echo ""
echo "Результаты картирования"
echo "Файл: $FLAGSTAT_FILE"
echo "% картированных ридов: ${MAPPED_PCT}%"
echo ""

THRESHOLD=90

RESULT=$(awk -v pct="$MAPPED_PCT" -v thr="$THRESHOLD" \
    'BEGIN { if (pct+0 > thr+0) print "OK"; else print "not OK" }')

if [ "$RESULT" = "OK" ]; then
    echo "Оценка: OK"
else
    echo "Оценка: not OK"
fi
