# -*- coding: UTF-8 -*-

# system imports
from urllib2 import HTTPError, URLError
import traceback

# enigma2 imports
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config
from Components import Label
from enigma import getDesktop
from Components.Sources.List import List

# plugin imports
from common import PanelList
from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import log


class BaseArchivCZSKScreen(Screen):
    """Base Screen for archivCZSK screens"""
    
    def __init__(self, session, initScreen=True):
        self.HD = False
        
        #setting SD/HD skin
        if getDesktop(0).size().width() >= 1280:
            self.HD = True

        if initScreen:    
            Screen.__init__(self, session)
        
class BaseArchivCZSKMenuListScreen(BaseArchivCZSKScreen):
    """Base Screen for screens with menu list"""
    def __init__(self, session, panelList=None):
        BaseArchivCZSKScreen.__init__(self, session)
        
        pl = PanelList
        if panelList is not None:
            pl = panelList
        
        # timeout for dialogs
        self.timeout = 5
        
        # currently selected item in PanelList
        self.selected_it = None   
        
        # item list holding loaded items
        self.lst_items = []
        
        # item list holding items corresponding to indexes of items in MenuList
        self.menu_list = []
        
        # working flag, set to true when we are doing time demanding task
        self.working = False
        
        # gui menu list
        self["menu"] = pl([])
        self["menu"].onSelectionChanged.append(self.updateGUI)
        
        #called by workingStarted
        self.onStartWork = [self.startWorking]
        
        #called by workingFinished
        self.onStopWork = [self.stopWorking]

        self.onUpdateGUI = []

        # we update list when the layout of the screen is finished
        self.onLayoutFinish.append(self.updateMenuList)

    def stopWorking(self):
        log.debug("stop working")
        self.working = False

    def startWorking(self):
        log.debug("start working")
        self.working = True

    def workingFinished(self, callback=None):
        for f in self.onStopWork:
            f()

    def workingStarted(self):
        for f in self.onStartWork:
            f()

    def updateGUI(self):
        for f in self.onUpdateGUI:
            f()

    def hideList(self):
        log.debug('hiding list')
        self["menu"].hide()

    def showList(self):
        log.debug('showing list')
        self["menu"].show()  


    def getSelectedItem(self):
        if len(self.lst_items) > 0:
            idx = self["menu"].getSelectedIndex()
            self.selected_it = self.lst_items[idx]
            return self.selected_it
        self.selected_it = None
        return None

    def updateMenuList(self, idx):
        pass

    def ok(self):
        pass

    def cancel(self):
        if not self.working:
            self.close()

    def up(self):
        if not self.working:
            self["menu"].up()

    def down(self):
        if not self.working:
            self["menu"].down()

    def right(self):
        if not self.working:
            self["menu"].right()

    def left(self):
        if not self.working:
            self["menu"].left()

class BaseArchivCZSKListSourceScreen(BaseArchivCZSKScreen):
    """Base Screen for screens with menu list"""
    def __init__(self, session):
        BaseArchivCZSKScreen.__init__(self, session)
        # timeout for dialogs
        self.timeout = 5
        # currently selected item in PanelList
        self.selected_it = None
        # item list holding loaded items
        self.lst_items = []
        # item list holding items corresponding to indexes of items in MenuList
        self.menu_list = []
        # working flag, set to true when we are doing time demanding task
        self.working = False
        # gui menu list
        self["menu"] = List([])
        self["menu"].onSelectionChanged.append(self.updateGUI)
        #called by workingStarted
        self.onStartWork = [self.startWorking]
        #called by workingFinished
        self.onStopWork = [self.stopWorking]
        self.onUpdateGUI = []
        # we update list when the layout of the screen is finished
        self.onLayoutFinish.append(self.__getListBoxRenderer)
        self.onLayoutFinish.append(self.updateMenuList)

    def __getListBoxRenderer(self):
        from Components.Sources.Source import Source
        from Components.Renderer.Listbox import Listbox
        for r in self.renderer:
            if isinstance(r, Listbox):
                s = r
                while not isinstance(s,Source):
                    s = s.source
                if s == self['menu']:
                    self.__listboxRenderer = r
                    break

    def stopWorking(self):
        log.debug("<%s> stopWorking" %(self.__class__.__name__))
        self.working = False

    def startWorking(self):
        log.debug("<%s> startWorking" %(self.__class__.__name__))
        self.working = True

    def workingFinished(self, callback=None):
        log.debug("<%s>: workingFinished"%(self.__class__.__name__))
        for f in self.onStopWork:
            f()

    def workingStarted(self):
        log.debug("<%s>: workingStarted"%(self.__class__.__name__))
        for f in self.onStartWork:
            f()

    def updateGUI(self):
        for f in self.onUpdateGUI:
            f()

    def hideList(self):
        log.debug("<%s>: hideList"%(self.__class__.__name__))
        self.__listboxRenderer.hide()

    def showList(self):
        log.debug("<%s>: showList"%(self.__class__.__name__))
        self.__listboxRenderer.show() 

    def getSelectedItem(self):
        if len(self.lst_items) > 0:
            idx = self["menu"].index
            if idx is None:
                self.selected_it = None
            else:
                self.selected_it = self.lst_items[idx]
        else:
            self.selected_it = None
        return self.selected_it

    def getSelectedIndex(self):
        return self["menu"].index

    def updateMenuList(self, idx=0):
        pass

    def ok(self):
        pass

    def cancel(self):
        if not self.working:
            self.close()

    def up(self):
        if not self.working:
            self["menu"].selectPrevious()

    def down(self):
        if not self.working:
            self["menu"].selectNext()

    def right(self):
        if not self.working:
            self.__listboxRenderer.move(self.__listboxRenderer.instance.pageDown)

    def left(self):
        if not self.working:
            self.__listboxRenderer.instance.move(self.__listboxRenderer.instance.pageUp)

    ### Messages ###

    def showError(self, error, timeout=5):
        if isinstance(error, unicode):
            error = error.encode('utf-8', 'ignore')
        self.session.openWithCallback(self.workingFinished, MessageBox, error, type=MessageBox.TYPE_ERROR, timeout=timeout)

    def showWarning(self, warning, timeout=5):
        if isinstance(warning, unicode):
            warning = warning.encode('utf-8', 'ignore')
        self.session.openWithCallback(self.workingFinished, MessageBox, warning, type=MessageBox.TYPE_WARNING, timeout=timeout)

    def showInfo(self, info, timeout=5):
        if isinstance(info, unicode):
            info = info.encode('utf-8', 'ignore')
        self.session.openWithCallback(self.workingFinished, MessageBox, info, type=MessageBox.TYPE_INFO, timeout=timeout)
