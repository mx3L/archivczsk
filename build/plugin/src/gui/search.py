'''
Created on 2.3.2013

@author: marko
'''

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.EventInfo import EventInfo
from Components.Sources.StaticText import StaticText
from Screens.ChannelSelection import ChannelSelectionBase
from Screens.EpgSelection import EPGSelection
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Plugins.Extensions.archivCZSK.client import seeker
from Plugins.Extensions.archivCZSK.gui.base import BaseArchivCZSKListSourceScreen
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, toString


class ArchivCZSKSearchClientScreen(BaseArchivCZSKListSourceScreen):
    def __init__(self, session, currService):
        BaseArchivCZSKListSourceScreen.__init__(self, session)
        self.session = session
        self.currService = currService
        self.searchList = seeker.getCapabilities()
        event = EventInfo(session.nav, EventInfo.NOW).getEvent()
        self.searchExp = event and event.getEventName() or ''
        self['red_label'] = StaticText(_("change search expression"))
        self['green_label'] = StaticText(_("remove diacritic"))
        self['blue_label'] = StaticText(_("choose from EPG"))
        self['search'] = Label(self.searchExp)
        
        self["actions"] = ActionMap(["archivCZSKActions"],
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
        
    def updateTitle(self):
        self.title = _("ArchivCZSK Search")
        
    def updateMenuList(self, index=0):
        self["menu"].list = [(toString(item[0]), ) for item in self.searchList]
        self["menu"].index = index
    
    def ok(self):
        if not self.working:
            self.working = True
            self.search(self.searchList[self["menu"].index][1], self.searchList[self["menu"].index][2])
                
    def cancel(self):
        seeker.searchClose()
        self.close(None)

    def keyRed(self):
        self.changeSearchExp()

    def keyGreen(self):
        self.removeDiacritics()
    
    def keyBlue(self):
        self.chooseFromEpg()

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
