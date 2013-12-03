# -*- coding: UTF-8 -*-
'''
Created on 28.4.2012

@author: marko
'''

from enigma import (loadPNG, RT_HALIGN_RIGHT, RT_VALIGN_TOP, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, 
                    RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListboxPythonMultiContent, gFont)

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Tools.Directories import fileExists
from Tools.LoadPixmap import LoadPixmap


from base import  BaseArchivCZSKScreen
def showContextMenu(session, name, img, items, globalItems, cb):
    session.openWithCallback(cb, ContextMenuScreen, name, img, items, globalItems)
    

class ContextMenuList(MenuList):
    def __init__(self):
        MenuList.__init__(self, [], False, eListboxPythonMultiContent)
        self.l.setItemHeight(24)
        self.l.setFont(0, gFont("Regular", 18))


def ContextEntry(name, idx, png='', separator=False):
    res = [(name, idx)]
    if separator:
        res.append(MultiContentEntryText(pos=(5, 12), size=(490, 1), font=0, flags=RT_VALIGN_CENTER, text=name, backcolor=0xffffff))
    elif fileExists(png):
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 0), size=(24, 24), png=loadPNG(png)))
        res.append(MultiContentEntryText(pos=(40, 0), size=(455, 24), font=0, flags=RT_VALIGN_CENTER, text=name))
    else:
        res.append(MultiContentEntryText(pos=(5, 0), size=(490, 24), font=0, flags=RT_VALIGN_CENTER, text=name))
    return res 


class ContextMenuScreen(BaseArchivCZSKScreen):  
    def __init__(self, session, name, img, items=None, globalItems=None):
        BaseArchivCZSKScreen.__init__(self, session)
        self.ctxItems = items or []
        self.globalCtxItems = globalItems or []
        name = name.encode('utf-8', 'ignore')
        img = img.endswith(('.jpg', '.png')) and img
        img = img and LoadPixmap(cached=True, path=img)
        self.img = img or None
        self.itemListDisabled = not (items and len(items) > 0)
        self.globalListDisabled = not (globalItems and len(globalItems) > 0)
        self.useSeparator = not (self.itemListDisabled or self.globalListDisabled)
        self["item_pixmap"] = Pixmap()
        self["item_label"] = Label(name)
        self['list'] = ContextMenuList()
        self["actions"] = ActionMap(["archivCZSKActions"],
            {"ok": self.ok,
             "cancel": self.cancel,
              "up": self.up,
              "down": self.down,
            }, -2)
        self.onLayoutFinish.append(self.checkList)
        self.onLayoutFinish.append(self.updateMenuList)
        self.onShown.append(self.__onShown)

    def __onShown(self):
        self["item_pixmap"].instance.setPixmap(self.img)
        
    def checkList(self):
        if self.itemListDisabled and self.globalListDisabled:
            self['list'].selectionEnabled(False)
                
    def updateMenuList(self):
        list = []
        idx = 0
        for item in self.ctxItems:
            png = item.thumb or ""
            name = item.name
            name = isinstance(name,unicode) and name.encode('utf-8') or name
            list.append(ContextEntry(name, idx, png))
            idx+=1
        if self.useSeparator:
            list.append(ContextEntry("",idx, None, True))
        for item in self.globalCtxItems:
            png = item[1] or ""
            name = item[0]
            name = isinstance(name, unicode) and name.encode('utf-8') or name
            list.append(ContextEntry(name, idx, png))
            idx+=1
        self["list"].setList(list)

    def up(self):
        if self.globalListDisabled and self.itemListDisabled:
            return
        listIdx = self["list"].getSelectedIndex()
        if listIdx == (len(self.ctxItems)+1) and self.useSeparator:
            self["list"].moveToIndex(len(self.ctxItems) - 1)
        else:
            self["list"].up()
            
    def down(self):
        if self.globalListDisabled and self.itemListDisabled:
            return
        listIdx = self["list"].getSelectedIndex()
        if listIdx == (len(self.ctxItems)-1) and self.useSeparator:
            self["list"].moveToIndex(len(self.ctxItems) + 1)
        else:
            self["list"].down()
            
    def ok(self):
        if not self.globalListDisabled or not self.itemListDisabled:
            idx = self["list"].getCurrent()[0][1]
            self.close(idx)
        else:
            self.close(None)
    
    def cancel(self):
        self.close(None)
