from typing import List
from . import defop

def _xml(s):
    if not isinstance(s, str):
        return s

#    from bs4 import BeautifulSoup
#    return BeautifulSoup(xml, 'xml')

    from lxml import etree
    root = etree.fromstring(s.encode())
    for elem in root.getiterator():
        # Skip comments and processing instructions,
        # because they do not have names
        if not (
            isinstance(elem, etree._Comment)
            or isinstance(elem, etree._ProcessingInstruction)
        ):
            # Remove a namespace URI in the element's name
            elem.tag = etree.QName(elem).localname

    # Remove unused namespace declarations
    etree.cleanup_namespaces(root)

    return root

@defop('xml-xpath', 0, 1)
def op_xml_xpath(aipl, v:str, *args) -> List['XmlElement']:
    xml = _xml(v)
    for arg in args:
        for entry in xml.xpath(arg):
            yield entry

@defop('xml-xpaths', 0, 0.5)
def op_xml_xpaths(aipl, v:str, **kwargs) -> List['XmlElement']:
    xml = _xml(v)
    ret = {}
    for varname, xpath in kwargs.items():
        ret[varname] = xml.xpath(xpath)[0]
    return ret
