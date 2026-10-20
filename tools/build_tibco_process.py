"""Derive the BW 6.8 ATM process from the process saved by Business Studio.

The original Process.bwp remains untouched. Run this only to recreate ATMCompleto.bwp.
"""

from copy import deepcopy
from pathlib import Path
import sys
from uuid import uuid4
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ProgettoATM/Processes/progettoatm/Process.bwp'
TARGET = ROOT / 'ProgettoATM/Processes/progettoatm/ATMCompleto.bwp'
MODULE = ROOT / 'ProgettoATM/META-INF/module.bwm'

BPWS = 'http://docs.oasis-open.org/wsbpel/2.0/process/executable'
TIBEX = 'http://www.tibco.com/bpel/2007/extensions'
XSD = 'http://www.w3.org/2001/XMLSchema'
BWEXT = 'http://tns.tibco.com/bw/model/core/bwext'
ACTIVITY = 'http://tns.tibco.com/bw/model/activityconfig'
JDBC = 'http://ns.tibco.com/bw/palette/jdbc'
FILE_MODEL = 'http://ns.tibco.com/bw/palette/file'
FILE_DATA = 'http://www.tibco.com/namespaces/tnt/plugins/file'
LOG_DATA = 'http://www.tibco.com/pe/WriteToLogActivitySchema'
XSL = 'http://www.w3.org/1999/XSL/Transform'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
NOTATION = 'http://www.eclipse.org/gmf/runtime/1.0.2/notation'
SCA_BPEL = 'http://docs.oasis-open.org/ns/opencsa/sca-bpel/200801'
LANG = 'urn:oasis:names:tc:wsbpel:2.0:sublang:xpath2.0'


def q(ns, name):
    return f'{{{ns}}}{name}' if ns else name


def child(parent, ns, local, **attrs):
    return etree.SubElement(parent, q(ns, local), **{k: str(v) for k, v in attrs.items()})


def activity_node(wrapper):
    return wrapper[0]


def set_edges(node, targets=(), sources=()):
    for old in list(node):
        if old.tag in (q(BPWS, 'targets'), q(BPWS, 'sources')):
            node.remove(old)
    pos = 0
    if targets:
        box = etree.Element(q(BPWS, 'targets'))
        for name in targets:
            child(box, BPWS, 'target', linkName=name)
        node.insert(pos, box)
        pos += 1
    if sources:
        box = etree.Element(q(BPWS, 'sources'))
        for name, expression, error_var in sources:
            source = child(box, BPWS, 'source', linkName=name)
            if error_var:
                source.set(q(TIBEX, 'faultDetailsVar'), error_var)
                source.set(q(TIBEX, 'faultNameVar'), 'FaultName')
            if expression is not None:
                design = child(source, TIBEX, 'DesignExpression')
                child(design, TIBEX, 'expression', expression=expression,
                      expressionLanguage=LANG)
                condition = child(source, BPWS, 'transitionCondition',
                                  expressionLanguage=LANG)
                condition.text = etree.CDATA(expression)
        node.insert(pos, box)


def binding(node, params, template_name, root_ns, root_element, values):
    old = node.find(q(TIBEX, 'inputBindings'))
    if old is not None:
        node.remove(old)
    bindings = etree.Element(q(TIBEX, 'inputBindings'))
    item = child(bindings, TIBEX, 'inputBinding')
    style = etree.Element(q(XSL, 'stylesheet'),
                          nsmap={'xsl': XSL, 'tns': root_ns, 'xs': XSD})
    style.set('version', '2.0')
    for name in params:
        child(style, XSL, 'param', name=name)
    template = child(style, XSL, 'template', name=template_name, match='/')
    data = child(template, root_ns, root_element)
    for field, expression in values:
        field_element = etree.SubElement(data, field)
        child(field_element, XSL, 'value-of', select=expression)
    item.set('expression', etree.tostring(style, encoding='unicode'))
    item.set('expressionLanguage', 'urn:oasis:names:tc:wsbpel:2.0:sublang:xslt1.0')
    config = node.find(q(TIBEX, 'config'))
    node.insert(node.index(config), bindings)


def add_var(variables, name, element):
    child(variables, BPWS, 'variable', name=name, element=element,
          **{q(SCA_BPEL, 'internal'): 'true'})


def add_query_schema(types, namespace, parameter_fields, output_fields):
    schema = etree.SubElement(types, q(XSD, 'schema'),
                              nsmap={None: XSD, 'tns': namespace + '+input'},
                              targetNamespace=namespace + '+input')
    element = child(schema, XSD, 'element', name='jdbcQueryActivityInput')
    sequence = child(child(element, XSD, 'complexType'), XSD, 'sequence')
    for name, datatype in parameter_fields:
        child(sequence, XSD, 'element', name=name, type=datatype, minOccurs='1',
              maxOccurs='1', nillable='true')
    for name, datatype in [('ServerTimeZone', 'string'), ('timeout', 'long'), ('maxRows', 'long')]:
        child(sequence, XSD, 'element', name=name, type=datatype, minOccurs='0', maxOccurs='1')

    output = etree.SubElement(types, q(XSD, 'schema'),
                              nsmap={None: XSD, 'tns': namespace + '+output'},
                              targetNamespace=namespace + '+output')
    result = child(output, XSD, 'element', name='resultSet')
    records = child(child(result, XSD, 'complexType'), XSD, 'sequence')
    record = child(records, XSD, 'element', name='Record', minOccurs='0', maxOccurs='unbounded')
    fields = child(child(record, XSD, 'complexType'), XSD, 'sequence')
    for name, datatype in output_fields:
        child(fields, XSD, 'element', name=name, type=datatype, minOccurs='0',
              maxOccurs='1', nillable='false')


def query_config(node, statement, parameters, columns):
    value = node.find('.//value')
    value.set('sqlStatement', statement)
    value.set('maxRows', '1')
    value.set('timeout', '30')
    for old in list(value):
        value.remove(old)
    for name, jdbc_type, label in parameters:
        child(value, None, 'PreparedParameters', ParameterName=name,
              DataType=str(jdbc_type), DataTypeDisplayValue=label)
    for index, (name, jdbc_type, label) in enumerate(columns, 1):
        child(value, None, 'columnMetadata', columnIndex=str(index), columnName=name,
              dataType=str(jdbc_type), typeName=label, status='OptionalElement')


def make_cancel(template, name, id_namespace, reason, link_in, link_out):
    wrapper = deepcopy(template)
    node = activity_node(wrapper)
    node.set('name', name)
    node.set(q(TIBEX, 'xpdlId'), id_namespace)
    node.set('inputVariable', name + '-input')
    node.set('outputVariable', name)
    set_edges(node, [link_in], [(link_out, None, None)])
    binding(node, ['FilePoller'], name + '-input',
            f'http://www.tibco.com/namespaces/tnt/plugins/jdbc+{id_namespace}+input',
            'jdbcQueryActivityInput',
            [('p_id', "substring-before($FilePoller/fileInfo/fileName, '.xml')"),
             ('p_motivo', "'" + reason + "'")])
    query_config(node,
                 'SELECT public.annulla_prenotazione(CAST(? AS UUID), ?) AS esito',
                 [('p_id', 12, 'VARCHAR'), ('p_motivo', 12, 'VARCHAR')],
                 [('esito', 12, 'VARCHAR')])
    return wrapper


def make_rename(template, name, link_in, folder):
    wrapper = etree.Element(q(BPWS, 'extensionActivity'))
    node = child(wrapper, TIBEX, 'activityExtension', name=name,
                 inputVariable=name + '-input',
                 outputVariable=name,
                 **{q(TIBEX, 'xpdlId'): str(uuid4())})
    set_edges(node, [link_in])
    binding_root = child(node, TIBEX, 'inputBindings')
    item = child(binding_root, TIBEX, 'inputBinding')
    style = etree.Element(q(XSL, 'stylesheet'), nsmap={'xsl': XSL, 'tns': FILE_DATA})
    style.set('version', '2.0')
    child(style, XSL, 'param', name='FilePoller')
    template_xsl = child(style, XSL, 'template', name=name + '-input', match='/')
    data = child(template_xsl, FILE_DATA, 'RenameActivityInputClass')
    for key, expression in [
        ('fromFileName', '$FilePoller/fileInfo/fullName'),
        ('toFileName', f"concat('C:/Users/utente/Desktop/Progetto ATM/{folder}/', $FilePoller/fileInfo/fileName)")
    ]:
        field = etree.SubElement(data, key)
        child(field, XSL, 'value-of', select=expression)
    item.set('expression', etree.tostring(style, encoding='unicode'))
    item.set('expressionLanguage', 'urn:oasis:names:tc:wsbpel:2.0:sublang:xslt1.0')
    config = child(node, TIBEX, 'config')
    bw = etree.SubElement(config, q(BWEXT, 'BWActivity'),
                          nsmap={'activityconfig': ACTIVITY, 'file': FILE_MODEL},
                          activityTypeID='bw.file.rename')
    activity_config = child(bw, None, 'activityConfig')
    props = child(activity_config, None, 'properties', name='config')
    props.set(q(XSI, 'type'), 'activityconfig:EMFProperty')
    child(props, None, 'type', href=FILE_MODEL + '#//RenameFile')
    # A completed request can be replayed with the same UUID. PostgreSQL
    # returns GIA_ELABORATA; replacing its archived XML avoids a rename fault.
    value = child(props, None, 'value', overwrite='true' if name == 'SpostaProcessed' else 'false',
                  createDestinationDirectories='false')
    value.set(q(XSI, 'type'), 'file:RenameFile')
    # QName values of xsi:type must have their prefixes declared locally.
    return wrapper


def main():
    if TARGET.exists() and '--force' not in sys.argv:
        raise SystemExit(f'{TARGET.name} already exists; the generator will not overwrite it')
    parser = etree.XMLParser(remove_blank_text=False)
    source_tree = etree.parse(str(SOURCE), parser)
    source_root = source_tree.getroot()
    types = source_root.find(q(TIBEX, 'Types'))
    variables = source_root.find(q(BPWS, 'variables'))
    flow = source_root.find('.//' + q(BPWS, 'flow'))
    links = flow.find(q(BPWS, 'links'))
    originals = [deepcopy(x) for x in flow.findall(q(BPWS, 'extensionActivity'))]
    if len(originals) != 7:
        raise SystemExit('The source process has changed: expected seven original activities')

    for old in list(links):
        links.remove(old)
    for old in flow.findall(q(BPWS, 'extensionActivity')):
        flow.remove(old)

    graph = [
        ('FileToParse', 0, 1, 'SUCCESSWITHCONDITION',
         "matches($FilePoller/fileInfo/fileName, '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\\.xml$')"),
        ('FileToNomeKO', 0, 12, 'SUCCESSWITHNOCONDITION', '##otherwise##'),
        ('ParseToConcludi', 1, 2, 'SUCCESS', None),
        ('ParseToAnnullaXml', 1, 8, 'ERROR', '##error##'),
        ('ConcludiToOK', 2, 4, 'SUCCESSWITHCONDITION',
         "$ConcludiPrelievo/Record[1]/esito = 'OK' or $ConcludiPrelievo/Record[1]/esito = 'GIA_ELABORATA'"),
        ('ConcludiToRifiuto', 2, 3, 'SUCCESSWITHCONDITION',
         "$ConcludiPrelievo/Record[1]/esito = 'CLIENTE_NON_VALIDO' or $ConcludiPrelievo/Record[1]/esito = 'SALDO_INSUFFICIENTE' or $ConcludiPrelievo/Record[1]/esito = 'RIFIUTATA' or $ConcludiPrelievo/Record[1]/esito = 'NON_PRENOTATA'"),
        ('ConcludiToConflitto', 2, 5, 'SUCCESSWITHNOCONDITION', '##otherwise##'),
        ('ConcludiToErrore', 2, 6, 'ERROR', '##error##'),
        ('OKToProcessed', 4, 9, 'SUCCESS', None),
        ('RifiutoToAnnulla', 3, 7, 'SUCCESS', None),
        ('AnnullaToError', 7, 10, 'SUCCESS', None),
        ('AnnullaXmlToError', 8, 11, 'SUCCESS', None),
    ]
    for name, _, _, kind, _ in graph:
        link = child(links, BPWS, 'link', name=name)
        link.set(q(TIBEX, 'linkType'), kind)

    incoming = {i: [] for i in range(13)}
    outgoing = {i: [] for i in range(13)}
    for name, start, end, _, expression in graph:
        incoming[end].append(name)
        outgoing[start].append((name, expression,
                                '_error_ParseXml' if name == 'ParseToAnnullaXml' else
                                '_error_ConcludiPrelievo' if name == 'ConcludiToErrore' else None))

    # Reuse the original starter, parser, JDBC Query and four Logs, retaining their stable IDs.
    base = originals[:]
    starter = activity_node(base[0])
    set_edges(starter, sources=outgoing[0])
    parser_node = activity_node(base[1])
    set_edges(parser_node, incoming[1], outgoing[1])
    query = activity_node(base[2])
    query.set('name', 'ConcludiPrelievo')
    query.set('inputVariable', 'ConcludiPrelievo-input')
    query.set('outputVariable', 'ConcludiPrelievo')
    set_edges(query, incoming[2], outgoing[2])
    binding(query, ['FilePoller', 'ParseXml'], 'ConcludiPrelievo-input',
            source_root.nsmap['ns4'], 'jdbcQueryActivityInput', [
                ('p_id', "substring-before($FilePoller/fileInfo/fileName, '.xml')"),
                ('p_nome', '$ParseXml/Cliente/Nome'),
                ('p_cognome', '$ParseXml/Cliente/Cognome'),
                ('p_pin', '$ParseXml/Cliente/PIN'),
                ('p_importo', 'xs:long(round($ParseXml/DettagliPrelievo/Importo * 100))'),
            ])
    query_config(query,
                 'SELECT esito, saldo_centesimi FROM public.concludi_prelievo(CAST(? AS UUID), ?, ?, ?, CAST(? AS BIGINT))',
                 [('p_id', 12, 'VARCHAR'), ('p_nome', 12, 'VARCHAR'),
                  ('p_cognome', 12, 'VARCHAR'), ('p_pin', 12, 'VARCHAR'),
                  ('p_importo', -5, 'BIGINT')],
                 [('esito', 12, 'VARCHAR'), ('saldo_centesimi', -5, 'BIGINT')])
    for old, new in [('LeggiClienti-input', 'ConcludiPrelievo-input'),
                     ('LeggiClienti', 'ConcludiPrelievo'),
                     ('_error_LeggiClienti', '_error_ConcludiPrelievo')]:
        variable = next(v for v in variables if v.get('name') == old)
        variable.set('name', new)

    for index, name, message in [
        (3, 'PrelievoRifiutato', 'Prelievo rifiutato dal database'),
        (4, 'PrelievoOK', 'Prelievo eseguito o gia elaborato'),
        (5, 'ConflittoID', 'ID o dati non coerenti: controllare manualmente'),
        (6, 'ErroreDatabase', 'Errore database: richiesta rimasta in input'),
    ]:
        node = activity_node(base[index])
        previous = node.get('inputVariable')
        node.set('name', name)
        node.set('inputVariable', name + '-input')
        variable = next(v for v in variables if v.get('name') == previous)
        variable.set('name', name + '-input')
        set_edges(node, incoming[index], outgoing[index])
        binding(node, [], name + '-input', LOG_DATA, 'ActivityInput',
                [('message', "'" + message + "'")])

    # Change only the metadata schemas belonging to the reused JDBC activity.
    original_input_schema = next(s for s in types if s.get('targetNamespace') == source_root.nsmap['ns4'])
    original_output_schema = next(s for s in types if s.get('targetNamespace') == source_root.nsmap['ns5'])
    for schema in (original_input_schema, original_output_schema):
        types.remove(schema)
    add_query_schema(types, source_root.nsmap['ns4'][:-6],
                     [('p_id', 'string'), ('p_nome', 'string'), ('p_cognome', 'string'),
                      ('p_pin', 'string'), ('p_importo', 'long')],
                     [('esito', 'string'), ('saldo_centesimi', 'integer')])

    cancel_ids = [str(uuid4()), str(uuid4())]
    extras = [
        make_cancel(base[2], 'AnnullaRifiutato', cancel_ids[0],
                    'Richiesta rifiutata da TIBCO', incoming[7][0], outgoing[7][0][0]),
        make_cancel(base[2], 'AnnullaXmlNonValido', cancel_ids[1],
                    'XML non valido', incoming[8][0], outgoing[8][0][0]),
        make_rename(base[2], 'SpostaProcessed', incoming[9][0], 'processed'),
        make_rename(base[2], 'SpostaRifiutato', incoming[10][0], 'error'),
        make_rename(base[2], 'SpostaXmlNonValido', incoming[11][0], 'error'),
        make_rename(base[2], 'SpostaNomeNonValido', incoming[12][0], 'error'),
    ]
    for index, wrapper in enumerate(extras, 7):
        node = activity_node(wrapper)
        name = node.get('name')
        add_var(variables, name + '-input',
                f'ns{8 + 2 * (index - 7)}:jdbcQueryActivityInput' if index < 9
                else 'ns0:RenameActivityInputClass')
        if index >= 9:
            add_var(variables, name, 'ns0:RenameActivityOutput')
        if index < 9:
            add_var(variables, name, f'ns{9 + 2 * (index - 7)}:resultSet')
            uri = f'http://www.tibco.com/namespaces/tnt/plugins/jdbc+{cancel_ids[index - 7]}'
            add_query_schema(types, uri, [('p_id', 'string'), ('p_motivo', 'string')],
                             [('esito', 'string')])

    for wrapper in base + extras:
        flow.append(wrapper)

    # Keep the native Business Studio notation model and create visible shapes/links.
    diagram = source_root.find(q(NOTATION, 'Diagram'))
    old_shapes = [x for x in diagram.iter('children')
                  if x.get('type', '').startswith('4002')]
    shape_parent = old_shapes[0].getparent()
    shape_templates = [deepcopy(x) for x in old_shapes]
    for item in old_shapes:
        shape_parent.remove(item)
    positions = [
        (20, 245), (170, 245), (350, 245), (550, 380), (550, 110),
        (550, 495), (550, 600), (730, 380), (350, 725),
        (730, 110), (920, 380), (550, 725), (170, 855),
    ]
    for index, (x, y) in enumerate(positions):
        shape = deepcopy(shape_templates[index] if index < 7 else
                         shape_templates[2] if index in (7, 8) else shape_templates[3])
        if index in (7, 8):
            shape.set('type', '4002 bw.jdbc.JDBCQuery')
        elif index >= 9:
            shape.set('type', '4002 bw.file.rename')
        shape.find('element').set(
            'href', f'//0/@process/@activity/@activity/@activities.{index}')
        bounds = shape.find('layoutConstraint')
        bounds.set('x', str(x))
        bounds.set('y', str(y))
        shape_parent.append(shape)
    old_edges = diagram.findall('edges')
    edge_normal, edge_error = deepcopy(old_edges[0]), deepcopy(old_edges[-1])
    for edge in old_edges:
        diagram.remove(edge)
    path_prefix = '//@children.0/@children.4/@children.0/@children.0/@children.0/@children.0/@children.0/@children.0/'
    for index, (_, start, end, kind, _) in enumerate(graph):
        edge = deepcopy(edge_error if kind == 'ERROR' else edge_normal)
        edge.set('source', path_prefix + f'@children.{start}')
        edge.set('target', path_prefix + f'@children.{end}')
        edge.find('element').set(
            'href', f'//0/@process/@activity/@activity/@links/@children.{index}')
        diagram.append(edge)
    for bounds in diagram.iter('layoutConstraint'):
        width = int(bounds.get('width', '0'))
        height = int(bounds.get('height', '0'))
        if width >= 500:
            bounds.set('width', '1200')
        if height >= 380:
            bounds.set('height', '950')

    # Preserve Business Studio's original scoped namespaces. Reparenting the
    # whole process makes lxml drop default namespaces used by inline XSD types.
    source_root.set('name', 'progettoatm.ATMCompleto')
    data = etree.tostring(source_tree, encoding='UTF-8', xml_declaration=True,
                          pretty_print=True)
    declarations = []
    for index, id_value in enumerate(cancel_ids):
        uri = f'http://www.tibco.com/namespaces/tnt/plugins/jdbc+{id_value}'
        declarations.extend((f'xmlns:ns{8 + 2 * index}="{uri}+input"',
                             f'xmlns:ns{9 + 2 * index}="{uri}+output"'))
    data = data.replace(b'<bpws:process ',
                        ('<bpws:process ' + ' '.join(declarations) + ' ').encode(), 1)
    etree.fromstring(data)
    TARGET.write_bytes(data)

    module = etree.parse(str(MODULE), parser)
    component = module.find('.//{http://xsd.tns.tibco.com/amf/models/sca/implementationtype/BW}BWComponentImplementation')
    if component is None:
        component = next(x for x in module.iter()
                         if x.get('processName') in ('progettoatm.Process', 'progettoatm.ATMCompleto'))
    if component.get('processName') not in ('progettoatm.Process', 'progettoatm.ATMCompleto'):
        raise SystemExit('module.bwm does not point at the original process; not changing it')
    component.set('processName', 'progettoatm.ATMCompleto')
    MODULE.write_bytes(etree.tostring(module, encoding='UTF-8', xml_declaration=True,
                                      pretty_print=True))
    print('Created', TARGET.relative_to(ROOT))
    print('Updated module component to progettoatm.ATMCompleto')


if __name__ == '__main__':
    main()
