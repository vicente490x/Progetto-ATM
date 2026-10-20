"""Verify that characters reserved by XML survive generation and parsing."""

import subprocess
from pathlib import Path

from lxml import etree


root = Path(__file__).resolve().parents[1]
sample = 'A&B<>"\''
code = (
    "const {buildXml}=require('./lib/atm');"
    "process.stdout.write(buildXml({nome:'A&B<>\"\\\'',cognome:'Rossi',"
    "pin:'12345',amountCents:100}));"
)
result = subprocess.run(['node', '-e', code], cwd=root, capture_output=True, check=True)
document = etree.fromstring(result.stdout)
actual = document.findtext('./Cliente/Nome')
assert actual == sample, (actual, sample)
print('OK: &, <, >, virgolette e apostrofo conservati dopo parsing XML')
