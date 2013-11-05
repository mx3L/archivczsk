# -*- coding: utf-8 -*-
'''
Created on 20.3.2012

@author: marko
'''
import os
import items
import logging
from  xml.etree.cElementTree import ElementTree, Element, SubElement

from Components.config import config
log = logging.getLogger(__name__)

class mainXML(object):
    
    def __init__(self, path):
        self.path = os.path.join(path, 'shortcuts.xml')
        self.xmlTree = None
        self.xmlRootElement = None
        self.fileExist = self.openArchiveFile()
            
     
    def createXMLArchive(self):
        pass
     
    def openArchiveFile(self):
        try:
            self.xmlTree = ElementTree()
            self.xmlTree.parse(self.path)
            self.xmlRootElement = self.xmlTree.getroot()
        except:
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
                
    def writeFile(self):    
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))
        self.xmlTree = ElementTree(self.xmlRootElement).write(self.path, encoding='utf-8')
    
class ShortcutXML(mainXML):
    def __init__(self, path):
        mainXML.__init__(self, path)
        if not self.fileExist:
            self.createXMLArchive()

    def createXMLArchive(self):
        self.xmlRootElement = Element('root')
        SubElement(self.xmlRootElement, 'shortcuts')

    def createShortcut(self, shortcut_it):
        log.debug("creating shortcut %s" % shortcut_it.name)
        shortcuts = self.xmlRootElement.find('shortcuts')
        id_sc = shortcut_it.get_id()
        if self.findShortcutById(id_sc) is not None:
            log.debug('shortcut %s already exist' % shortcut_it.name)
            return False
        else:
            shortcut = Element('shortcut')
            shortcut.set('id', str(id_sc))
            name = SubElement(shortcut, 'name')
            name.text = shortcut_it.name
            params = SubElement(shortcut, 'params')
            for key, value in shortcut_it.params.iteritems():
                params.set(str(key), str(value))
            shortcuts.append(shortcut)
        return True

    def getShortcuts(self):
        shortcut_lst = []
        parentEl = self.xmlRootElement
        shortcuts = parentEl.find('shortcuts')
        for shortcut in shortcuts.findall('shortcut'):
            it = items.PFolder()
            it.name = shortcut.findtext('name')
            it.params = {}
            params = shortcut.find('params')
            for key, value in params.items():
                it.params[key] = value
            shortcut_lst.append(it)
        return shortcut_lst	
            
        
    def removeShortcut(self, shortcut_id):
        shortcuts = self.xmlRootElement.find('shortcuts')
        shortcut = self.findShortcutById(shortcut_id)
        if shortcut is None:
            log.debug('cannot find shortcut by %s id' % shortcut_id)
            return
        shortcuts.remove(shortcut)  

    def findShortcutById(self, id_shortcut):
        allcases = self.xmlRootElement.findall(".//shortcut")
        for c in allcases:
            print c.get('id')
            if c.get('id') == id_shortcut:
                return c
  

