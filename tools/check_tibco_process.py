"""Check the generated BusinessWorks process before opening it in Studio."""

from pathlib import Path
from lxml import etree

path = Path(__file__).resolve().parents[1] / 'ProgettoATM/Processes/progettoatm/ATMCompleto.bwp'
root = etree.parse(str(path)).getroot()
xsd = 'http://www.w3.org/2001/XMLSchema'
schemas = [node for node in root.iter() if node.tag == f'{{{xsd}}}schema']
assert schemas, 'No inline schemas'
for schema in schemas:
    namespace = schema.get('targetNamespace', '')
    if 'activityerror' in namespace or 'errorlinkhandler' in namespace:
        # These inline schemas reference other namespaces and need BW's resolver.
        continue
    try:
        etree.XMLSchema(etree.ElementTree(schema))
    except etree.XMLSchemaParseError as exc:
        raise AssertionError(f"Invalid schema {schema.get('targetNamespace')}: {exc}") from exc

variables = [node for node in root.iter()
             if isinstance(node.tag, str) and node.tag.endswith('}variable')]
assert all(node.get('element', '').split(':')[0] in node.nsmap
           for node in variables if ':' in node.get('element', ''))
bindings = [node for node in root.iter()
            if isinstance(node.tag, str) and node.tag.endswith('}inputBinding')]
for binding in bindings:
    etree.fromstring(binding.get('expression').encode())

print(f'OK: {len(schemas)} inline schemas, {len(variables)} variables, '
      f'{len(bindings)} input bindings')
