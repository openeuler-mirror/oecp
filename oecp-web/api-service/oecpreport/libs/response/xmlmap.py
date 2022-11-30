#!/usr/bin/python3
import os
import threading

try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et


class XmlParse:
    """
    通过传递不同的code来加载xml中响应消息
    """

    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not hasattr(cls, "__instance"):
                cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        self.xml = None

    def _load_xml(self, xml_path):
        """
        加载xml文件的内容
        :param xml_path: xml文件的路径
        :param tag: 默认解析的节点
        """
        if not xml_path:
            self.xml = None
            raise FileNotFoundError("The XML file does not exist")
        xml_path = os.path.join(os.path.dirname(__file__), xml_path)
        try:
            self.xml = et.parse(xml_path)
        except Exception as e:
            pass

    def clear_xml(self):
        self.xml = None

    @property
    def root(self):
        return self.xml.getroot()

    def _todict(self, tag):
        msg = {}
        for child in tag.findall("*"):
            msg[child.tag] = child.text
        return msg

    def content(self, label):
        if not self.xml:
            self._load_xml("mapping.xml")
        tag = self.root.find("./code/[@label='%s']" % label)
        if tag is None:
            return tag

        return self._todict(tag)


xml = XmlParse()
