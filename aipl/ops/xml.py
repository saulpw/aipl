from typing import List
from aipl import defop

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


class XMLStringableElement:
    def __init__(self, e):
        self._element = e
    def __getattr__(self, k):
        return getattr(self._element, k)
    def __str__(self):
        return getattr(self._element, 'text', '') or ''

def StringifiableObject(s):
    'create pass-through wrapper to stringify with s.text if available'
    if not hasattr(s, 'text'):
        return s
    return XMLStringableElement(s)


@defop('xml-xpath', 0, 1)
def op_xml_xpath(aipl, v:str, *args) -> List['XmlElement']:
    "Return a vector of XMLElements from parsing entries in value."
    xml = _xml(v)
    for arg in args:
        for entry in xml.xpath(arg):
            yield StringifiableObject(entry)


@defop('xml-xpaths', 0, 0.5)
def op_xml_xpaths(aipl, v:str, **kwargs) -> List['XmlElement']:
    "Return a vector of XMLElements from parsing entries in value; kwargs become column_name=xpath."
    xml = _xml(v)
    ret = {}
    for varname, xpath in kwargs.items():
        ret[varname] = StringifiableObject(xml.xpath(xpath)[0])
    return ret
