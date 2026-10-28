#!/usr/bin/env python3
"""Генератор календаря полнолуний и CEL-политики.

Алгоритм: средняя фазовая модель.
  - опорное новолуние: 2000-01-06 18:14 UTC
  - синодический месяц: 29.530588853 сут
  - полнолуние = новолуние + SYN/2
  - epoch_day = floor(unix_seconds / 86400)
(разница не более ±12 ч от пика)

Скрипт:
  1) печатает таблицу дат + epoch_days,
  2) перезаписывает список epoch-days в deploy/k8s/policies/20-policy-fullmoon.yaml
     между маркерами # BEGIN_FULLMOON_DAYS / # END_FULLMOON_DAYS,
  3) обновляет deploy/k8s/policies/fullmoon-calendar.md.
"""
from datetime import datetime, timedelta, timezone
import re
import sys
from pathlib import Path

REF_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
SYN = 29.530588853
HERE = Path(__file__).resolve().parent.parent / "policies"
POLICY = HERE / "20-policy-fullmoon.yaml"
CALENDAR = HERE / "fullmoon-calendar.md"

START = datetime(2026, 10, 1, tzinfo=timezone.utc)
END = datetime(2028, 1, 1, tzinfo=timezone.utc)

def fullmoons():
    n, out = 0, []
    while True:
        n += 1
        t = REF_NEW_MOON + timedelta(days=n * SYN + SYN / 2)
        if t > END:
            break
        if t >= START:
            out.append(t)
    return out

def main():
    rows = fullmoons()
    days = [int(t.timestamp() // 86400) for t in rows]
    print(f"{'дата (UTC)':<12} {'время':<9} epoch_days")
    for t, d in zip(rows, days):
        print(f"{t:%Y-%m-%d}  {t:%H:%M}   {d}")
    lst = ", ".join(map(str, days))

    text = POLICY.read_text()
    marker_begin, marker_end = "# BEGIN_FULLMOON_DAYS", "# END_FULLMOON_DAYS"
    if marker_begin not in text:
        sys.exit(f"markers not found in {POLICY}: добавь {marker_begin}/{marker_end}")
    lst = ", ".join(map(str, days))
    nearest = rows[0]
    repl = (
        f"{marker_begin}\n"
        f"  - expression: >-\n"
        f"      int(time.now()) / 86400\n"
        f"        in [{lst}]\n"
        f"    message: \"Редактирование workload'ов разрешено только в сутки полнолуния.\"\n"
        f"  {marker_end}"
    )
    text = re.sub(rf"{re.escape(marker_begin)}.*?{re.escape(marker_end)}", repl, text, flags=re.S)
    POLICY.write_text(text)
    print(f"[OK] {POLICY.name}: {len(days)} дат")

    if CALENDAR.exists():
        lines = ["# Календарь полнолуний (сгенерирован scripts/gen_fullmoon.py)", "",
                 "# Дата (UTC)   Время (UTC)   epoch_days"]
        lines += [f"{t:%Y-%m-%d}   {t:%H:%M}   {d}" for t, d in zip(rows, days)]
        CALENDAR.write_text("\n".join(lines) + "\n")
        print(f"[OK] {CALENDAR.name}")

if __name__ == "__main__":
    main()
