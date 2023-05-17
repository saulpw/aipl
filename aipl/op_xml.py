from typing import List
from . import defop


@defop('xml-find', 0, 1)
def op_xml_find(aipl, xml:str, *args) -> List['XmlElement']:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(xml, 'xml')
    for entry in soup.findAll('entry'):
        yield entry


@defop('xml-text', 0, 0.5)
def op_xml_text(aipl, xmlnode:'XmlElement', *args) -> dict:
    ret = {}
    for arg in args:
        ret[arg] = xmlnode.find(arg)
    return ret


@defop('xml-prop', 0, 0)
def op_parse_xml_title(aipl, tag:'XmlElement', propname) -> str:
    return tag.get(propname)
