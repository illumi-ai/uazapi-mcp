"""Extrai do CHANGELOG.md a seção de uma versão, para virar as notas da release.

Uso: python3 scripts/notas_release.py 0.1.0
"""
import pathlib
import re
import sys

versao = sys.argv[1].lstrip("v")
texto = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
m = re.search(
    rf"^## \[{re.escape(versao)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)",
    texto, re.M | re.S,
)
if not m:
    sys.exit(f"CHANGELOG.md não tem a seção [{versao}]")
print(m.group(1).strip())
