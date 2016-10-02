# -*- coding: utf-8 -*-
'''
Created on 20.3.2012

@author: marko
'''
import os
import shutil
from datetime import datetime

try:
    from xml.etree.cElementTree import ElementTree, Element, SubElement
except ImportError:
    from xml.etree.ElementTree import ElementTree, Element, SubElement

from items import PVideoNotResolved, PFolder, PUserCategory
from Plugins.Extensions.archivCZSK.engine.tools.util import toString, toUnicode
try:
    from Plugins.Extensions.archivCZSK import log
except ImportError:
    class simple_log:
        @staticmethod
        def log(text):
            print text
        @staticmethod
        def debug(text):
            print text
        @staticmethod
        def error(text):
            print text
    log = simple_log


class BaseXML(object):

    def __init__(self, path):
        self.path = os.path.splitext(path)[1] == '.xml'  and path or path + '.xml'
        self.xml_tree = None
        self.xml_root_element = None
        self.parsed = self.parse_file()

    def parse_file(self):
        if not os.path.exists(self.path):
            return False
        try:
            self.xml_tree = ElementTree()
            self.xml_tree.parse(self.path)
            self.xml_root_element = self.xml_tree.getroot()
        except Exception as e:
            log.error("%s invalid xml file - %s, creating backup..."%(str(self), str(e)))
            shutil.copy2(self.path, self.path + ".bak")
            return False
        return True

    def indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for e in elem:
                self.indent(e, level + 1)
                if not e.tail or not e.tail.strip():
                    e.tail = i + "  "
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def write_file(self):
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))
        self.indent(self.xml_root_element)
        self.xml_tree = ElementTree(self.xml_root_element).write(self.path, encoding='utf-8')


class Item2XML(BaseXML):

    def __init__(self, path):
        BaseXML.__init__(self, path)
        if not self.parsed:
            self.__create_root()

    def __str__(self):
        return "[%s - %s]" % (self.__class__.__name__, toString('/'.join(self.path.split('/')[-2:])))

    def __len__(self):
        items = self.xml_root_element.find('items')
        return items.findall('item') and len([item_el for item_el in items.findall('item')]) or 0

    def __create_root(self):
        self.xml_root_element = Element('root')
        SubElement(self.xml_root_element, 'items')

    def create_item(self, xml_item):
        log.debug("{0} create item - {1}".format(self, toString(xml_item)))
        item = self._get_item_cls(xml_item)()
        item.id = xml_item.attrib.get('id')
        item.addon_id = xml_item.attrib.get('addon_id')
        item.ctime = xml_item.attrib.get('ctime')
        item.name = xml_item.findtext('name')
        item.params = {}
        params = xml_item.find('params')
        for key, value in params.items():
            item.params[key] = value
        return self._update_item(item, xml_item)

    def _update_item(self, item, xml_item):
        return item

    def add_item(self, item):
        xml_item = self.create_xml_item(item)
        if xml_item:
            xml_item = self._update_xml_item(xml_item, item)

    def update_item(self, item):
        if item.id:
            self.remove_item(item)
        self.add_item(item)

    def create_xml_item(self, item):
        log.debug("{0} create xml item - {1}".format(self, toString(item)))
        if item.id:
            log.debug('{0} create xml item - {1} already exists, skipping'.format(self, toString(item)))
            return
        item_id = item.get_id()
        if self.find_item_by_id(item_id):
            log.debug('{0} create xml item - {1} already exists, skipping'.format(self, toString(item)))
            return
        addon_id = item.addon_id
        xml_item = SubElement(self.xml_root_element.find('items'), 'item')
        xml_item.set('id', toUnicode(item_id))
        xml_item.set('ctime', str(datetime.now()))
        if addon_id:
            xml_item.set('addon_id', toUnicode(addon_id))
        name = SubElement(xml_item, 'name')
        name.text = toUnicode(item.name)
        params = SubElement(xml_item, 'params')
        for key, value in item.params.iteritems():
            params.set(toUnicode(key), toUnicode(value))
        item.id = item_id
        return xml_item

    def _update_xml_item(self, xml_item, item):
        return xml_item

    def get_item(self, item_id):
        xml_item = self.find_item_by_id(item_id)
        if xml_item:
            item = self.create_item(xml_item)
            item = self._update_item(item, xml_item)
            return item

    def get_items(self):
        item_list = []
        items = self.xml_root_element.find('items')
        items = items.findall('item') or []
        for xml_item in items:
            item = self.create_item(xml_item)
            item = self._update_item(item, xml_item)
            item_list.append(item)
        return item_list

    def remove_item(self, item):
        xml_items = self.xml_root_element.find('items')
        xml_item = self.find_item_by_id(item.id)
        if xml_item is None:
            log.debug('{0} remove_item - {1} not found'.format(self, toString(item)))
        else:
            xml_items.remove(xml_item)
            log.debug('{0} remove_item - {1} successfully removed'.format(self, toString(item)))
        item.id = None

    def find_item_by_id(self, item_id):
        allcases = self.xml_root_element.findall(".//item")
        for c in allcases:
            if c.attrib.get('id') == item_id:
                return c


class Favorite2XML(Item2XML):

    def _get_item_cls(self, xml_item):
        if xml_item.attrib.get('type') == 'video':
            return PVideoNotResolved
        else:
            return PFolder

    def _update_xml_item(self, xml_item, item):
        if isinstance(item, PVideoNotResolved):
            xml_item.set('type', 'video')
        return xml_item

class Category2XML(Item2XML):
    def _get_item_cls(self, xml_item):
        return PUserCategory

    def _update_xml_item(self, xml_item, item):
        if item.image:
            image_el = SubElement(xml_item, 'image')
            image_el.text = item.image
        addons_el = SubElement(xml_item, 'addons')
        for addon_id in item:
            addon_id_el = SubElement(addons_el, 'addon_id')
            addon_id_el.text = addon_id
        return xml_item

    def _update_item(self, item, xml_item):
        item.image = xml_item.findtext('image')
        addons_el = xml_item.find('.//addons')
        addons = addons_el.findall('addon_id') or []
        item.addons = [addon_id_el.text for addon_id_el in addons]
        return item


class CategoriesIO(object):

    def __init__(self, path):
        self._category_io = Category2XML(path)

    def __len__(self):
        return len(self._category_io)

    def get_categories(self):
        return self._category_io.get_items()

    def add_category(self, category):
        return self._category_io.add_item(category)

    def get_category(self, category_id):
        return self._category_io.get_item(category_id)

    def remove_category(self, category):
        return self._category_io.remove_item(category)

    def update_category(self, category):
        self._category_io.update_item(category)

    def save(self):
        self._category_io.write_file()


class FavoritesIO(object):
    def __init__(self, path):
        self._favorite_io = Favorite2XML(path)

    def __len__(self):
        return len(self._favorite_io)

    def get_favorite(self, favorite_id):
        return self._favorite_io.get_item(favorite_id)

    def get_favorites(self):
        return self._favorite_io.get_items()

    def add_favorite(self, favorite):
        return self._favorite_io.add_item(favorite)

    def remove_favorite(self, favorite):
        return self._favorite_io.remove_item(favorite)

    def save(self):
        return self._favorite_io.write_file()
