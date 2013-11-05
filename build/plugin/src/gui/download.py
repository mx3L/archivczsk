# -*- coding: UTF-8 -*-
'''
Created on 28.4.2012

@author: marko
'''
import time
import os

from enigma import eTimer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ScrollLabel import ScrollLabel
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Button import Button
from Components.Label import Label, MultiColorLabel

from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK.gsession import GlobalSession
from Plugins.Extensions.archivCZSK.engine.downloader import DownloadManager
from Plugins.Extensions.archivCZSK.engine.tools import util

from base import  BaseArchivCZSKScreen, BaseArchivCZSKMenuListScreen
from common import PanelListEntryHD, PanelListDownload, PanelListDownloadEntry, PanelListDownloadListEntry, MultiLabelWidget

PanelListEntry = PanelListEntryHD


def openDownloads(session, name, content_provider, cb):
    session.openWithCallback(cb, DownloadsScreen, name, content_provider)
    
def openAddonDownloads(session, addon, cb):
    openDownloads(session, addon.name, addon.provider, cb)


class DownloadManagerMessages(object):
    session = None

    @staticmethod
    def finishDownloadCB(download):
        session = GlobalSession.getSession()
        def updateDownloadList(callback=None):
            if DownloadListScreen.instance is not None:
                DownloadListScreen.instance.refreshList()
        if download.downloaded:
            session.openWithCallback(updateDownloadList, MessageBox, _("ArchivyCZSK - Download:") + ' ' + \
                                      download.name.encode('utf-8', 'ignore') + ' ' + _("successfully finished."), \
                                      type=MessageBox.TYPE_INFO, timeout=0)
        else:
            session.openWithCallback(updateDownloadList, MessageBox, _("ArchivyCZSK - Download:") + ' ' + \
                                      download.name.encode('utf-8', 'ignore') + ' ' + _("finished with errors."), \
                                      type=MessageBox.TYPE_ERROR, timeout=0)  
    @staticmethod
    def startDownloadCB(download):
        session = GlobalSession.getSession()
        session.open(MessageBox, _("ArchivCZSK - Download:") + ' ' + \
                     download.name.encode('utf-8', 'ignore') + ' ' + _("started."), \
                     type=MessageBox.TYPE_INFO, timeout=5)
        
    @staticmethod
    def askOverrideDownloadCB(download):
        session = GlobalSession.getSession()
        def overrideDownload(callback=None):
            if callback:
                download.remove()
                DownloadManager.getInstance().addDownload(download)
            else:
                pass
        if download is not None:
            session.openWithCallback(DownloadManagerMessages.saveDownload, MessageBox, _("The file")\
                                      + download.name.encode('utf-8', 'ignore') + "already exist. Do you want to override?" , \
                                       type=MessageBox.TYPE_YESNO)  


class DownloadStatusScreen(BaseArchivCZSKScreen):
    
    def __init__(self, session, download):
        BaseArchivCZSKScreen.__init__(self, session)
        self.title = _("Download progress")
                    
        self["filename"] = Label("")
        self["size_label"] = Label(_("Size:"))
        self["size"] = Label("")
        self["path_label"] = Label(_("Path:"))
        self["path"] = Label("")
        self["start_label"] = Label(_("Start time:"))
        self["start"] = Label("")
        self["finish_label"] = Label(_("Finish time:"))
        self["finish"] = Label("")
        self["state_label"] = Label(_("State:"))
        self["state"] = MultiColorLabel("")
        self["speed_label"] = Label(_("Speed:"))
        self["speed"] = Label("0 KB/s")
        self["status"] = Label("")
        
        self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
        {
            "ok": self.cancel,
            "back": self.cancel,
        }, -1)
        
        self._download = download
        
        self._download.onOutputCB.append(self.outputCallback)
        self._download.onFinishCB.append(self.updateState)
        self._download.onFinishCB.append(self.updateFinishTime)
        self._download.onFinishCB.append(self.stopTimer)
        
        self.timer = eTimer()
        self.timer_running = False
        self.timer_interval = 3000
        self.timer.callback.append(self.updateStatus)
        
        self.onShown.append(self.updateStaticInfo)
        self.onShown.append(self.updateState)
        self.onShown.append(self.updateFinishTime)
        self.onShown.append(self.startTimer)
        
        self.onLayoutFinish.append(self.startRun) # dont start before gui is finished
        self.onLayoutFinish.append(self.updateGUI)
        
        
        
        self.onClose.append(self.__onClose)
        
    def updateGUI(self):
        MultiLabelWidget(self['size_label'], self['size'])
        MultiLabelWidget(self['path_label'], self['path'])
        MultiLabelWidget(self['speed_label'], self['speed'])
        MultiLabelWidget(self['start_label'], self['start'])
        MultiLabelWidget(self['finish_label'], self['finish'])
        MultiLabelWidget(self['state_label'], self['state'])
        
        
    def startTimer(self):
        self.timer.start(self.timer_interval)
        self.timer_running = True
        
    def stopTimer(self, cb=None):
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False 
        
        
    def updateStaticInfo(self):
        download = self._download
        filename = download.filename
        start_time = time.strftime("%b %d %Y %H:%M:%S", time.localtime(download.start_time))
        path = os.path.split(download.local)[0]
        
        self["filename"].setText(filename.encode('utf-8', 'ignore'))
        self["path"].setText(path.encode('utf-8', 'ignore'))
        self["start"].setText(start_time)
        
        
    def updateState(self, cb=None):
        download = self._download
        if download.state == 'success_finished':
            self["state"].setText(download.textState)
            self["state"].setForegroundColorNum(0)
        elif download.state == 'error_finished':
            self["state"].setText(download.textState)
            self["state"].setForegroundColorNum(1)
        elif download.state == 'downloading':
            self["state"].setText(download.textState)
            self["state"].setForegroundColorNum(2)
        else:
            self["state"].setText(download.textState)
            self["state"].setForegroundColorNum(1)
            
    def updateFinishTime(self, cb=None):
        download = self._download
        finish_time = _("not finished")
        if download.finish_time is not None:
            finish_time = time.strftime("%b %d %Y %H:%M:%S", time.localtime(download.finish_time))
        self["finish"].setText(finish_time)
            
    def updateStatus(self):
        download = self._download
        status = download.status
        
        status.update(self.timer_interval / 1000)
        
        speed = status.speed
        speedKB = util.BtoKB(speed)
        
        if speedKB <= 1000 and speedKB > 0:
            self['speed'].setText(("%d KB/s" % speedKB))
        elif speedKB > 1000:
            self['speed'].setText(("%.2f MB/s" % util.BtoMB(speed)))
        else:
            self['speed'].setText(("%d KB/s" % 0))
        
        
        currentLength = status.currentLength
        totalLength = status.totalLength
        
        size = "%s (%2.f MB %s)" % (_("unknown"), util.BtoMB(currentLength), _("downloaded"))
        if totalLength > 0:
            size = "%2.f MB (%2.f MB %s)" % (util.BtoMB(totalLength), util.BtoMB(currentLength), _("downloaded"))
        self["size"].setText(size)
        
        if not download.running:
            self.stopTimer()
        
        
    def outputCallback(self, output):
        self["status"].setText(output)

    def startRun(self):
        #self["status"].setText(_("Execution Progress:") + "\n\n")
        self._download.showOutput = True

    def cancel(self):
        self.close()
        
    def __onClose(self):
        self._download.showOutput = False
        self._download.onOutputCB.remove(self.outputCallback)
        self._download.onFinishCB.remove(self.updateState)
        self._download.onFinishCB.remove(self.updateFinishTime)
        self._download.onFinishCB.remove(self.stopTimer)
        
        self.stopTimer()
        del self.timer


class DownloadList:
    def __init__(self):
        self["DownloadListActions"] = HelpableActionMap(self, "DownloadActions",
            {
                "showDownloadListView": (self.showDownloadListScreen, _("show download list")),
            })

    def showDownloadListScreen(self):
        self.workingStarted()
        self.session.openWithCallback(self.workingFinished, DownloadListScreen)

class DownloadListScreen(BaseArchivCZSKMenuListScreen):
    instance = None       
    def __init__(self, session):
        BaseArchivCZSKMenuListScreen.__init__(self, session)
        DownloadListScreen.instance = self
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Play"))
        self["key_yellow"] = Button(_("Remove"))
        self["key_blue"] = Button("")
        
        from Plugins.Extensions.archivCZSK.engine.player.player import Player
        self.player = Player(session, self.workingFinished)
        
        self.lst_items = []
        self.title = "ArchivyCZSK" +" - "+ _("Recent downloads")
        self.onClose.append(self.__onClose)

        self["actions"] = NumberActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
                "red": self.askCancelDownload,
                "green": self.askPlayDownload,
                "yellow": self.askRemoveDownload,
                "up": self.up,
                "down": self.down,
            }, -2)
        
        self.lst_items = DownloadManager.getInstance().download_lst
        self.onShown.append(self.setWindowTitle)
        
    def __onClose(self):
        DownloadListScreen.instance = None

    def setWindowTitle(self):
        self.setTitle(self.title)
        
    def refreshList(self):
        self.lst_items = DownloadManager.getInstance().download_lst
        self.updateMenuList() 
        
        
    def askCancelDownload(self):
        if len(self.lst_items) > 0:
            download = self.getSelectedItem()
            self.session.openWithCallback(self.cancelDownload, MessageBox, _('Do you want to cancel') + ' '\
                                           + download.name.encode('utf-8', 'ignore') + ' ?', type=MessageBox.TYPE_YESNO)    
    
    def cancelDownload(self, callback=None):
        if callback:
            download = self.getSelectedItem()
            DownloadManager.getInstance().cancelDownload(download)
            self.refreshList()
            
    def askRemoveDownload(self):
        if len(self.lst_items) > 0:
            download = self.getSelectedItem()
            self.session.openWithCallback(self.removeDownload, MessageBox, _('Do you want to remove') + ' '\
                                           + download.name.encode('utf-8', 'ígnore') + _('from disk') + ' ?', type=MessageBox.TYPE_YESNO)    
    
    def removeDownload(self, callback=None):
        if callback:
            download = self.getSelectedItem()
            DownloadManager.getInstance().removeDownload(download)
            self.refreshList()
            
    def askPlayDownload(self):
        if len(self.lst_items) > 0:
            self.workingStarted()
            download = self.getSelectedItem()
            if download.downloaded or not download.running:
                self.playDownload(True)
            else:
                message = '%s %s %s' % (_("The file"), download.name.encode('utf-8', 'ígnore'), _('is not downloaded yet. Do you want to play it anyway?'))
                self.session.openWithCallback(self.playDownload, MessageBox, message, type=MessageBox.TYPE_YESNO)
    
            
    def playDownload(self, callback=None):
        if callback:
            download = self.getSelectedItem()
            self.player.playDownload(download)
        else:
            self.workingFinished()

    def updateMenuList(self):
        menu_list = []
        for idx, x in enumerate(self.lst_items):
            menu_list.append(PanelListDownloadEntry(x.name, x)) 
        self["menu"].setList(menu_list)      

    def ok(self):
        if  len(self.lst_items) > 0:
            download = self.getSelectedItem()
            self.session.openWithCallback(self.workingFinished, DownloadStatusScreen, download)
        

class DownloadsScreen(BaseArchivCZSKMenuListScreen, DownloadList):
    instance = None        
    def __init__(self, session, name, content_provider):
        BaseArchivCZSKMenuListScreen.__init__(self, session, panelList=PanelListDownload)
        DownloadList.__init__(self)
        self.name = name
        self.content_provider = content_provider        
        from Plugins.Extensions.archivCZSK.engine.player.player import Player
        self.player = Player(session, self.workingFinished)
        self.sort_options = [{'id':'az', 'name':_('Sort alphabetically')},
                             {'id':'date', 'name':_('Sort by date')},
                             {'id':'size', 'name':_('Sort by size')},
                             {'id':'state', 'name':_('Sort by state')}]
        self.sort_current = self.sort_options[0]
        self.sort_next = self.sort_options[1]
        self.lst_items = self.content_provider.get_downloads()
        
        self["key_red"] = Button(_("Remove"))
        self["key_green"] = Button("")
        self["key_yellow"] = Button(self.sort_next['name'])
        self["key_blue"] = Button("")
        self.title = self.name.encode('utf-8', 'ignore') + ' - ' + (_("Downloads"))

        self["actions"] = NumberActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
                "red": self.askRemoveDownload,
                "yellow": self.toggleSort,
                "up": self.up,
                "down": self.down,
            }, -2)
        
        self.onLayoutFinish.append(self.sortList)
        self.onShown.append(self.setWindowTitle)    

    def setWindowTitle(self):
        self.setTitle(self.title)
    
    def refreshList(self, sort=False):
        if not sort:
            self.lst_items = self.content_provider.get_downloads()
        self.updateMenuList()
        
    def askRemoveDownload(self):
        if len(self.lst_items) > 0:
            download = self.getSelectedItem()
            self.session.openWithCallback(self.removeDownload, MessageBox, _('Do you want to remove') \
                                          + ' ' + download.name.encode('utf-8', 'ignore') + ' ?', type=MessageBox.TYPE_YESNO)    
    
    def removeDownload(self, callback=None):
        if callback:
            self.content_provider.remove_download(self.getSelectedItem())
            self.refreshList()
            
    def toggleSort(self):
        next_idx = self.sort_options.index(self.sort_next)
        self.sort_current = self.sort_next
        
        if  next_idx == len(self.sort_options) - 1:
            self.sort_next = self.sort_options[0]
        else:
            self.sort_next = self.sort_options[next_idx + 1]

        self["key_yellow"].setText(self.sort_next['name'])
        
        self.sortList()        
        
    def sortList(self):
        if self.sort_current['id'] == 'az':
            self.lst_items.sort(key=lambda d:d.name)
        elif self.sort_current['id'] == 'size':
            self.lst_items.sort(key=lambda d:d.size)
        elif self.sort_current['id'] == 'state':
            self.lst_items.sort(key=lambda d:d.state)
        elif self.sort_current['id'] == 'date':
            self.lst_items.sort(key=lambda d:d.finish_time)
        self.refreshList(True)
        

    def updateMenuList(self):
        menu_list = []
        for idx, x in enumerate(self.lst_items):
            menu_list.append(PanelListDownloadListEntry(x)) 
        self["menu"].setList(menu_list)        

    def ok(self):
        if not self.working and len(self.lst_items) > 0:
            it = self.getSelectedItem()
            download = DownloadManager.getInstance().findDownloadByIT(it)
            if download is not None and download.running:
                self.player.playDownload(download)
            else:
                self.player.setMediaItem(it)
                self.player.play()
            
