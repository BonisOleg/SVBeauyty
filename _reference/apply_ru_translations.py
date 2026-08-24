#!/usr/bin/env python3
"""Наповнює locale/ru/LC_MESSAGES/django.po значеннями з ru_translations.py.

Українська .po лишається порожньою — це мова оригіналу.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ru_translations import PLURALS, TRANSLATIONS  # noqa: E402

PO_PATH = Path(__file__).resolve().parent.parent / "locale" / "ru" / "LC_MESSAGES" / "django.po"

PLURAL_HEADER = (
    "Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : "
    "n%10>=2 && n%10<=4 && (n%100<12 || n%100>14) ? 1 : 2);\\n"
)


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\\\", "\\")


def main() -> int:
    lines = PO_PATH.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    index = 0
    filled = missing = 0
    missing_ids: list[str] = []

    while index < len(lines):
        line = lines[index]

        if line.startswith('msgid "') and not line.startswith("msgid_plural"):
            msgid = unescape(line[7:-1])
            next_line = lines[index + 1] if index + 1 < len(lines) else ""

            if next_line.startswith('msgid_plural "'):
                forms = PLURALS.get(msgid)
                out.append(line)
                out.append(next_line)
                index += 2
                while index < len(lines) and lines[index].startswith("msgstr["):
                    slot = int(lines[index][7])
                    value = forms[slot] if forms and slot < len(forms) else ""
                    out.append(f'msgstr[{slot}] "{escape(value)}"')
                    index += 1
                if forms:
                    filled += 1
                else:
                    missing += 1
                    missing_ids.append(msgid)
                continue

            translation = TRANSLATIONS.get(msgid, "")
            out.append(line)
            if msgid:
                if translation:
                    filled += 1
                else:
                    missing += 1
                    missing_ids.append(msgid)
            index += 1
            if index < len(lines) and lines[index].startswith('msgstr "'):
                out.append(f'msgstr "{escape(translation)}"' if msgid else lines[index])
                index += 1
            continue

        if line.startswith('"Plural-Forms:'):
            out.append(f'"{PLURAL_HEADER}"')
            index += 1
            continue

        out.append(line)
        index += 1

    PO_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Перекладено: {filled}, без перекладу: {missing}")
    for msgid in missing_ids:
        print("  MISSING:", msgid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
