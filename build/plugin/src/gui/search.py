'''
Created on 2.3.2013

@author: marko
'''
import os

from Screens import Screen
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import ChannelSelectionBase
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.EventInfo import EventInfo


from Plugins.Extensions.archivCZSK import _, settings
from Plugins.Extensions.archivCZSK.client import seeker
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, PanelList, PanelListEntryHD, PanelListEntry2
from Plugins.Extensions.archivCZSK.gui.base import BaseArchivCZSKMenuListScreen

    
class SearchClient(BaseArchivCZSKMenuListScreen):
    WIDTH_HD = 400
    WIDTH_SD = 200
    def __init__(self, session, currService):
        BaseArchivCZSKMenuListScreen.__init__(self, session)
        self.session = session
        self.currService = currService
        self.searchList = seeker.getCapabilities()
        event = EventInfo(session.nav, EventInfo.NOW).getEvent()
        self.searchExp = event and event.getEventName() or ''
        self["infolist"] = PanelList([], 30)
        self['search'] = Label(self.searchExp)
        
        self["actions"] = NumberActionMap(["archivCZSKActions"],
                {
                "ok": self.ok,
                "cancel": self.cancel,
                "up": self.up,
                "down": self.down,
                "yellow": self.keyYellow,
                "red": self.keyRed,
                "blue": self.keyBlue,
                }, -2)
        
        self.onShown.append(self.updateTitle)
        self.onLayoutFinish.append(self.disableSelection)
        self.onLayoutFinish.append(self.initInfoList)
        
    def updateTitle(self):
        self.title = _("ArchivCZSK Search")
        
    def disableSelection(self):
        self["infolist"].selectionEnabled(False)
        
    def initInfoList(self):
        blueB = os.path.join(settings.IMAGE_PATH, 'buttons/blue.png')
        redB = os.path.join(settings.IMAGE_PATH, 'buttons/red.png')
        yellowB = os.path.join(settings.IMAGE_PATH, 'buttons/yellow.png')
        infolist = []
        infolist.append(PanelListEntry2(_("change search expression"), self.WIDTH_HD, yellowB))
        infolist.append(PanelListEntry2(_("remove diacritic"), self.WIDTH_HD, redB))
        infolist.append(PanelListEntry2(_("choose from EPG"), self.WIDTH_HD, blueB))
        self['infolist'].l.setList(infolist)
        
    def updateMenuList(self):
        list = []
        for idx, menu_item in enumerate(self.searchList):
            list.append(PanelListEntryHD(menu_item[0], idx))
        self["menu"].setList(list) 
        
    def ok(self):
        if not self.working:
            self.working = True
            idx = self['menu'].getSelectedIndex()
            self.search(self.searchList[idx][1], self.searchList[idx][2])
                
    def cancel(self):
        seeker.searchClose()
        self.close(None)
    
    def keyBlue(self):
        self.chooseFromEpg()
        
    def keyYellow(self):
        self.changeSearchExp()
        
    def keyRed(self):
        self.removeDiacritics()
        
        
    def removeDiacritics(self):
        try:
            import unicodedata
        except ImportError:
            showInfoMessage(self.session, _("Cannot remove diacritics, missing unicodedata.so"))
        else:
            self.searchExp = ''.join((c for c in unicodedata.normalize('NFD', unicode(self.searchExp, 'utf-8', 'ignore')) 
                                      if unicodedata.category(c) != 'Mn')).encode('utf-8')
            self["search"].setText(self.searchExp)
    
        
    def changeSearchExp(self):
        self.session.openWithCallback(self.changeSearchExpCB, VirtualKeyBoard, _("Set your search expression"), text = self.searchExp)
        
    def changeSearchExpCB(self, word=None):
        if word is not None and len(word) > 0:
            self.searchExp = word
            self['search'].setText(self.searchExp)
            
    def chooseFromEpg(self):
        self.session.openWithCallback(self.changeSearchExpCB, SimpleEPGSelection, self.currService)
            
    def goEntry(self, entry):
        if entry is not None:
            self.search(entry[1], entry[2])
            
    def search(self, addon, mode):
        seeker.search(self.session, self.searchExp, addon, mode, cb=self.searchCB)
        
    def searchCB(self):
        self.working = False

        
class SimpleEPGSelection(EPGSelection):
    def __init__(self, session, ref):
        EPGSelection.__init__(self, session, ref)
        self.skinName = "EPGSelection"
        self.key_green_choice = EPGSelection.EMPTY
        self.key_red_choice = EPGSelection.EMPTY
        self.skinName = "EPGSelection"
        
    def infoKeyPressed(self):
        self.search()

    def eventSelected(self):
        self.search()
        
    def search(self):
        cur = self["list"].getCurrent()
        event = cur[0]
        if event is not None:
            self.close(event.getEventName())
            
    def closeScreen(self):
        self.close(None)
        


class SimpleChannelSelectionEPG:
    def __init__(self):
        self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
            {
            "showEPGList": self.showEPGList,
            })
        self.epg_bouquet = None

    def showEPGList(self):
        ref = self.getCurrentSelection()
        if ref:
            self.epg_bouquet = self.servicelist.getRoot()
            self.savedService = ref
            self.session.openWitchCallback(self.showEPGListCB, SimpleEPGSelection, ref)
            
    def showEPGListCB(self, searchExp=None):
        self.close(True, searchExp)
        


# TODO
class SimpleChannelSelection(ChannelSelectionBase, SimpleChannelSelectionEPG):
    def __init__(self, session):
        ChannelSelectionBase.__init__(self, session)
        SimpleChannelSelectionEPG.__init__(self)
        
        self["actions"] = ActionMap(["OkCancelActions", "TvRadioActions"],
                {
                 "cancel": self.cancel,
                 "ok": self.channelSelected,
                 "keyRadio": self.doRadioButton,
                 "keyTV": self.doTVButton,
                })
