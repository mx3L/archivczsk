# -*- coding: UTF-8 -*-
'''
Created on 28.4.2012

@author: marko
'''

import os

from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap, NumberActionMap
from Tools.LoadPixmap import LoadPixmap

from base import  BaseArchivCZSKMenuListScreen
from common import PanelListEntryHD

PanelListEntry = PanelListEntryHD    

def showContextMenu(session, name, img, context_items, cb):
    session.openWithCallback(cb, ContextMenuScreen, name, img, context_items)

class ContextMenuScreen(BaseArchivCZSKMenuListScreen):  
        def __init__(self, session, name, img, context_items):
            BaseArchivCZSKMenuListScreen.__init__(self, session)
            self.context_items = context_items
            self["img"] = Pixmap()
            self["name"] = Label(name.encode('utf-8', 'ignore'))
            
            self["actions"] = NumberActionMap(["archivCZSKActions"],
                {
                "ok": self.ok,
                "cancel": self.cancel,
                "up": self.up,
                "down": self.down,
                }, -2)
            
            img_ext = os.path.splitext(img)[1]
            if not img_ext in ['.png', 'jpg']:
                self.img = None
            else:   
                self.img = LoadPixmap(cached=True, path=img)
            
            self.onShown.append(self.__onShown)

        def __onShown(self):
            self.setTitle('Menu')
            
            self["img"].instance.setPixmap(self.img)
                
        def updateMenuList(self):
            #self.menu_list[:]
            list = []
            for idx, menu_item in enumerate(self.context_items):
                list.append(PanelListEntry(menu_item.name, idx))
                            
            self["menu"].setList(list)      
                     
         
        def ok(self):
            if not self.working:
                self.close(self['menu'].getSelectedIndex())
                
        def cancel(self):
            self.close(None)
                
    
