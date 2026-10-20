"""Apply the successful-replay setting to the existing generated BW file."""

from pathlib import Path


path = Path(__file__).resolve().parents[1] / 'ProgettoATM/Processes/progettoatm/ATMCompleto.bwp'
content = path.read_bytes()
activity = b'<tibex:activityExtension name="SpostaProcessed"'
start = content.index(activity)
end = content.index(b'</tibex:activityExtension>', start)
before = b'<value overwrite="false" createDestinationDirectories="false"'
after = b'<value overwrite="true" createDestinationDirectories="false"'
segment = content[start:end]
if after in segment:
    print('SpostaProcessed already accepts replay')
elif segment.count(before) == 1:
    path.write_bytes(content[:start] + segment.replace(before, after) + content[end:])
    print('SpostaProcessed now accepts replay')
else:
    raise SystemExit('Expected exactly one Rename File configuration in SpostaProcessed')
