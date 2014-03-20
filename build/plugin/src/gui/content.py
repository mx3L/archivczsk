import copy, os

from enigma import eTimer, eLabel
from skin import parseFont
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Pixmap import Pixmap, PixmapConditional
from Tools.LoadPixmap import LoadPixmap

from menu import ArchiveCZSKConfigScreen
from base import  BaseArchivCZSKMenuListScreen
from webpixmap import WebPixmap
from download import DownloadList
from common import MyConditionalLabel, ButtonLabel, PanelList, PanelListEntryHD, PanelColorListEntry2, LoadingScreen , TipBar, CutLabel

from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK import settings
from Plugins.Extensions.archivCZSK.engine.items import (PItem, PFolder, PRoot, PPlaylist, PExit,
                                                        PVideo, PContextMenuItem, PSearch, PSearchItem,
                                                        PDownload, PVideoAddon, Stream, RtmpStream)
from Plugins.Extensions.archivCZSK.engine.contentprovider import StreamContentProvider, VideoAddonContentProvider, ArchivCZSKContentProvider
from Plugins.Extensions.archivCZSK.engine.handlers import ArchivCZSKContentHandler, VideoAddonContentHandler, VideoAddonManagementScreenContentHandler, StreamContentHandler
from Plugins.Extensions.archivCZSK.engine.tools.task import Task

PanelListEntry = PanelListEntryHD

KEY_MENU_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_menu.png'))
KEY_INFO_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_info.png'))
KEY_5_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_5.png'))
PATH_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'next.png'))


class BaseContentScreen(BaseArchivCZSKMenuListScreen):

    def __init__(self, session, contentHandler, lst_items):
        BaseArchivCZSKMenuListScreen.__init__(self, session)
        self.contentHandler = contentHandler
        self.loadingScreen = session.instantiateDialog(LoadingScreen)

        self.lst_items = lst_items
        # screen context items
        self.ctx_items = []
        self.refresh = False
        self.refreshing = False
        self.parent_it = PRoot()
        self.enabled_path = True
        self.max_path_width = 0

        self.path = []
        self.stack = []
        self.old_stack_len = 0
        self["status_label"] = Label("")
        self["path_pixmap"] = Pixmap()
        self["path_label"] = CutLabel(" / ")
        if not self.enabled_path:
            self["path_label"].hide()
        else:
            self.onLayoutFinish.append(self.setPathPixmap)
        self.onClose.append(self.__onClose)

    def __onClose(self):
        self.session.deleteDialog(self.loadingScreen)

    def startLoading(self):
        self.loadingScreen.start()
        self["status_label"].setText(_("Loading"))

    def stopLoading(self):
        self.loadingScreen.stop()
        self["status_label"].setText("")

    def setPathPixmap(self):
        self["path_pixmap"].instance.setPixmap(PATH_IMG)

    def updatePath(self):
        current_stack_len = len(self.stack)
        parent_name = self.parent_it.name
        if current_stack_len <= self.old_stack_len:
            if len(self.path) > 0:
                self.path.pop()
        elif current_stack_len > self.old_stack_len:
            self.path.append(parent_name)
        if len(self.path) == 0:
            path_text = ' / '
        else:
            path_text = ' / ' + ' / '.join(self.path)
        self["path_label"].setText(path_text.encode('utf-8', 'ignore'))


    def updateMenuList(self, index=0):
        menu_list = []
        for idx, it in enumerate(self.lst_items):
            entry = self._createMenuListEntry(it, idx)
            menu_list.append(entry)
        self["menu"].setList(menu_list)
        self["menu"].moveToIndex(index)

    def _createMenuListEntry(self, item, idx):
        return PanelListEntry(item.name, idx, item.thumb)

    def refreshList(self):
        log.debug("refreshing screen of %s item" , self.parent_it.name)
        self.refreshing = True
        self.contentHandler.open_item(self.parent_it)

    def load(self, params):
        """
        Loads content of screen from params

        params = {'lst_items': list of GUI items which
                               will be loaded in menulist,

                  'parent_it': parent item from which
                               was this content retrieved,

                  'refresh'  : if we want to refresh menulist
                               from parent item,

                  'index'    : position which will
                               be selected in menulist after load
        }
        """

        self.refresh = False
        self.input = None
        self.lst_items = params['lst_items']
        self.parent_it = params['parent_it']
        if params['refresh']:
            self.refreshList()
        else:
            log.debug("loading screen of %s item" , repr(self.parent_it))
            index = 'index' in params and params['index'] or 0
            if self.enabled_path and not self.refreshing:
                self.updatePath()
            self.updateMenuList(index)

    def save(self):
        """saves current screen to stack"""
        log.debug("saving current screen to stack")

        self.old_stack_len = len(self.stack)
        self.stack.append({'lst_items':self.lst_items,
                            'parent_it':copy.copy(self.parent_it),
                           'refresh':self.refresh,
                           'index':self["menu"].getSelectedIndex()})

    def getSelectedIndex(self):
        return self["menu"].getSelectedIndex()

    def getParent(self):
        if len(self.stack) > 0:
            return self.stack[-1]
        return None

    def popParent(self):
        if len(self.stack) > 0:
            return self.stack.pop()
        return None


    def resolveCommand(self, command, arg):
        print arg
        log.debug("resolving %s command " , str(command))

        if command is None:
            pass
        elif command == 'refreshnow':
            self.refreshList()
        else:
            log.debug("unknown command %s" , command)


    def ok(self):
        if not self.working and len(self.lst_items) > 0:
            self.contentHandler.open_item(self.getSelectedItem())

    def menu(self):
        if not self.working and len(self.lst_items) > 0:
            self.contentHandler.menu_item(self.getSelectedItem(), self.ctx_items)

    def info(self, mode):
        if not self.working and len(self.lst_items) > 0:
            self.contentHandler.info_item(self.getSelectedItem(), mode)


class VideoAddonsManagementScreen(BaseContentScreen, TipBar):
    def __init__(self, session, provider):
        contentHandler = VideoAddonManagementScreenContentHandler(session, self, provider)
        addonItems = provider.get_content({'category_addons':'all_addons', 'filter_enabled':False})
        BaseContentScreen.__init__(self, session, contentHandler, addonItems)
        TipBar.__init__(self, [], startOnShown = False)
        if self.HD:
            self.setSkin('ArchivCZSKContentScreen_HD')
        else:
            self.setSkin('ArchivCZSKContentScreen_SD')
        self.updateGUITimer = eTimer()
        self.updateGUITimer.callback.append(self.updateAddonGUI)
        self.onUpdateGUI.append(self.changeAddon)
        self.onClose.append(self.__onClose)
        self["image"] = Pixmap()
        self["title"] = Label("")
        self["author"] = Label("")
        self["version"] = Label("")
        self["about"] = Label("")
        self["key_red"] = Label("")
        self["key_green"] = Label("")
        self["key_yellow"] = Label("")
        self["key_blue"] = Label("")
        self["actions"] = ActionMap(["archivCZSKActions"],
             {
                    "ok": self.menu,
                    "cancel": self.close,
                    "up": self.up,
                    "down": self.down,
                    "menu" : self.menu
             }, -2)
        self.onLayoutFinish.append(self.updateAddonGUI)

    def changeAddon(self):
        if self.execing:
            self.updateGUITimer.start(100, True)

    def _createMenuListEntry(self, item, idx):
        addon = item.addon
        name = item.name
        width = self["menu"].instance.size().width() -5
        if addon.get_info('broken'):
            return PanelColorListEntry2(name, _('broken'), 0xffffff, 0xff0000, width)
        elif not addon.get_setting('enabled'):
            return PanelColorListEntry2(name, _('disabled'), 0xffffff, 0xffff00, width)
        else:
            return PanelColorListEntry2(name, _('enabled'), 0xffffff, 0x00ff00, width)

    def updateAddonGUI(self):
        item = self.getSelectedItem()
        if item is not None:
            self["title"].setText(item.name.encode('utf-8', 'ignore'))
            image = None
            try:
                image = LoadPixmap(cached = True, path = item.image)
            except Exception:
                pass
            try:
                self["image"].instance.setPixmap(image)
                self["author"].setText(_("Author: ") + item.author.encode('utf-8', 'ignore'))
                self["version"].setText(_("Version: ") + item.version.encode('utf-8', 'ignore'))
                self["about"].setText(item.description.encode('utf-8', 'ignore'))
            except Exception:
                self["image"].instance.setPixmap(None)
                self["author"].setText("")
                self["version"].setText("")
                self["about"].setText("")
        else:
            self["image"].instance.setPixmap(None)
            self["title"].setText("")
            self["author"].setText("")
            self["version"].setText("")
            self["about"].setText("")

    def __onClose(self):
        self.updateGUITimer.stop()
        self.updateGUITimer = None



class ArchivCZSKContentScreen(BaseContentScreen, DownloadList, TipBar):

    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current addon"))

    def __init__(self, session, archivCZSK):
        provider = ArchivCZSKContentProvider(archivCZSK, os.path.join(settings.PLUGIN_PATH, 'categories'))
        provider.start()
        contentHandler = ArchivCZSKContentHandler(session, self, provider)
        defaultCategory = config.plugins.archivCZSK.defaultCategory.value
        categoryItem = categoryAddons = None
        if defaultCategory != 'categories':
            categoryItem = provider.get_content({'category':defaultCategory})
            categoryAddons = provider.get_content({'category_addons':defaultCategory})
            categoryAddons is not None and categoryAddons.insert(0, PExit())
        categoryItems = provider.get_content()
        BaseContentScreen.__init__(self, session, contentHandler, categoryItems)
        if categoryItem is not None  and categoryAddons is not None:
            self.save()
            self.load({'lst_items':categoryAddons,
                            'parent_it':categoryItem,
                            'refresh':False})
        self.ctx_items.append((_("Add Category"), None, self.addCategory))
        self.provider = provider
        self.updateGUITimer = eTimer()
        self.updateGUITimer.callback.append(self.updateAddonGUI)

        # include DownloadList
        DownloadList.__init__(self)

        # include TipList
        TipBar.__init__(self, [self.CONTEXT_TIP], startOnShown=True)
        self.onUpdateGUI.append(self.changeAddon)
        self.onClose.append(self.__onClose)

        self["image"] = Pixmap()
        self["title"] = Label("")
        self["author"] = Label("")
        self["version"] = Label("")
        self["about"] = Label("")

        self["key_red"] = Label("")
        self["key_green"] = Label(_("Manager"))
        self["key_yellow"] = Label(_("Live streams"))
        self["key_blue"] = Label(_("Settings"))

        self["actions"] = ActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
                "up": self.up,
                "down": self.down,
                "blue": self.openSettings,
                "green": self.openAddonManagement,
                "yellow": self.showStreams,
                "menu" : self.menu
            }, -2)
        # after layout show update item "GUI" - edit: shamann
        self.onLayoutFinish.append(self.updateAddonGUI)

    def __onClose(self):
        self.provider.stop()
        self.updateGUITimer.stop()
        self.updateGUITimer = None

    def _createMenuListEntry(self, item, idx):
        name = item.name
        thumb = item.thumb
        try:
            addon = item.addon
        except AttributeError:
            return PanelListEntry(name,idx, thumb)
        if addon.get_info('broken'):
            return PanelListEntry(name,idx, thumb, 0xff0000)
        else:
            return PanelListEntry(name,idx, thumb)


    def openSettings(self):
        if not self.working:
            self.provider.pause()
            self.session.openWithCallback(self.openSettingsCB, ArchiveCZSKConfigScreen)

    def openSettingsCB(self, cb=None):
        self.provider.resume()

    def openAddonManagement(self):
        self.session.openWithCallback(self.openAddonManagementCB, VideoAddonsManagementScreen, self.provider)

    def openAddonManagementCB(self, cb=None):
        self.workingStarted()
        self.refreshList()
        self.workingFinished()

    def showStreams(self):
        if not self.working:
            self.workingStarted()
            stream_content_provider = StreamContentProvider(config.plugins.archivCZSK.downloadsPath.getValue(), settings.STREAM_PATH)
            lst_items = stream_content_provider.get_content(None)
            if not isinstance(lst_items[0], PExit):
                lst_items.insert(0, PExit())
            self.session.openWithCallback(self.workingFinished, StreamContentScreen, stream_content_provider, lst_items)

    def addCategory(self):
        self.session.openWithCallback(self.addCategoryCB, InputBox, _("Set category name"))

    def addCategoryCB(self, title):
        if title:
            self.workingStarted()
            self.provider.add_category(title)
            if isinstance(self.parent_it, PRoot):
                self.refreshList()
            else:
                self.getParent()["refresh"] = True
            self.workingFinished()


    def changeAddon(self):
        if self.execing:
            self.updateGUITimer.start(100, True)

    def updateAddonGUI(self):
        item = self.getSelectedItem()
        if item is not None:
            image = None
            self["title"].setText(item.name.encode('utf-8', 'ignore'))
            try:
                image = LoadPixmap(cached=True, path = item.image)
            except Exception:
                pass
            self["image"].instance.setPixmap(image)
            try:
                self["author"].setText(_("Author: ") + item.author.encode('utf-8', 'ignore'))
                self["version"].setText(_("Version: ") + item.version.encode('utf-8', 'ignore'))
                self["about"].setText(item.description.encode('utf-8', 'ignore'))
            except:
                self["author"].setText("")
                self["version"].setText("")
                self["about"].setText("")
        else:
            self["image"].instance.setPixmap(None)
            self["title"].setText("")
            self["author"].setText("")
            self["version"].setText("")
            self["about"].setText("")


    def toggleCancelLoading(self):
        if Task.getInstance() is not None and not Task.getInstance().isCancelling():
            self["status_label"].setText(_("Canceling..."))
            Task.getInstance().setCancel()

        elif Task.getInstance() is not None and Task.getInstance().isCancelling():
            self["status_label"].setText(_("Loading..."))
            Task.getInstance().setResume()
        else:
            log.debug("Task is not running")


    def cancel(self):
        if self.working:
            self.toggleCancelLoading()
        elif not self.working:
            self.session.openWithCallback(self.closePlugin, MessageBox, _('Do you want to exit ArchivCZSK?'), type=MessageBox.TYPE_YESNO)

    def closePlugin(self, callback=None):
        if callback:
            self.close()


class ContentScreen(BaseContentScreen, DownloadList, TipBar):

    CSFD_TIP = (KEY_5_IMG, _("show info in CSFD"))
    INFO_TIP = (KEY_INFO_IMG, _("show additional info"))
    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current item"))

    def __init__(self, session, addon, lst_items):
        self.addon = addon
        contentHandler = VideoAddonContentHandler(session, self, addon.provider)
        BaseContentScreen.__init__(self, session, contentHandler, lst_items)

        # include DownloadList
        DownloadList.__init__(self)

        # include TipList
        TipBar.__init__(self, [self.CSFD_TIP, self.CONTEXT_TIP, self.INFO_TIP], startOnShown=True)
        self.updateGUITimer = eTimer()
        self.updateGUITimer.callback.append(self.updateImage)
        enabledImage = False

        if enabledImage and self.HD:
            self.onUpdateGUI.append(self.changeImage)
            self.setSkin("ContentScreen_HD_IMG")
            self["image"] = WebPixmap()

        self["key_red"] = Label("")
        self["key_green"] = Label(_("Downloads"))
        self["key_yellow"] = Label(_("Shortcuts"))
        self["key_blue"] = Label(_("Settings"))
        self["actions"] = ActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "up": self.up,
                "down": self.down,
                "cancel": self.cancel,
                "green" : self.openAddonDownloads,
                "blue": self.openAddonSettings,
                "yellow": self.openAddonShortcuts,
                "info": self.openInfo,
                "menu": self.menu,
                "csfd": self.openCSFD
            }, -2)

        self.onLayoutFinish.append(self.updateGUI)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        addon_name = self.addon.name.encode('utf-8')
        self.setTitle(addon_name)

    def openAddonShortcuts(self):
        if not self.working:
            self.addon.open_shortcuts(self.session, self.openAddonShortcutsCB)

    def openAddonShortcutsCB(self, it_sc):
        if it_sc is not None:
            self.contentHandler.open_item(it_sc)

    def openAddonDownloads(self):
        if not self.working:
            self.workingStarted()
            self.addon.open_downloads(self.session, self.workingFinished)

    def openAddonSettings(self):
        if not self.working:
            self.addon.open_settings(self.session)

    def openInfo(self):
        self.info('item')

    def openCSFD(self):
        self.info('csfd')


    def toggleCancelLoading(self):
        if Task.getInstance() is not None and not Task.getInstance().isCancelling():
            self["status_label"].setText("Canceling...")
            Task.getInstance().setCancel()

        elif Task.getInstance() is not None and Task.getInstance().isCancelling():
            self["status_label"].setText("Loading...")
            Task.getInstance().setResume()
        else:
            log.debug("Task is not running")

    def changeImage(self):
        if self.execing:
            self['image'].load(None)
            self.updateGUITimer.start(100, True)

    def updateImage(self):
        it = self.getSelectedItem()
        img = it and it.image
        self['image'].load(img)

    def exitItem(self):
        if len(self.stack) == 0:
            self.exitContentScreen()
        else:
            self.load(self.stack.pop())

    def cancel(self):
        if self.working:
            self.toggleCancelLoading()
        else:
            self.contentHandler.exit_item()


class StreamContentScreen(BaseContentScreen, DownloadList, TipBar):
    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current item"))
    LIVE_PIXMAP = None

    def __init__(self, session, content_provider, lst_items):
        contentHandler = StreamContentHandler(session, self, content_provider)
        BaseContentScreen.__init__(self, session, contentHandler, lst_items)
        self.content_provider = content_provider
        # include DownloadList
        DownloadList.__init__(self)

        # include TipList
        TipBar.__init__(self, [self.CONTEXT_TIP], startOnShown=True)

        self["key_red"] = Label(_("Remove"))
        self["key_green"] = Label(_("Downloads"))
        self["key_yellow"] = Label("")
        self["key_blue"] = Label("")

        self['archive_label'] = Label(_("Stream player"))
        self['streaminfo_label'] = MyConditionalLabel(_("STREAM INFO"), self.isStream)
        self['streaminfo'] = MyConditionalLabel("", self.isStream)
        self['protocol_label'] = MyConditionalLabel(_("PROTOCOL:"), self.isStream)
        self['protocol'] = MyConditionalLabel("", self.isStream)
        self['playdelay_label'] = MyConditionalLabel(_("PLAY DELAY:"), self.isStream)
        self['playdelay'] = MyConditionalLabel("", self.isStream)
        self['livestream_pixmap'] = PixmapConditional()
        self['rtmpbuffer_label'] = MyConditionalLabel(_("RTMP BUFFER:"), self.isRtmpStream)
        self['rtmpbuffer'] = MyConditionalLabel("", self.isRtmpStream)
        self['playerbuffer_label'] = MyConditionalLabel(_("PLAYER BUFFER:"), self.isGstreamerPlayerSelected)
        self['playerbuffer'] = MyConditionalLabel("", self.isGstreamerPlayerSelected)


        self["actions"] = ActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "up": self.up,
                "down": self.down,
                "cancel": self.cancel,
                "green" : self.openDownloads,
                "menu": self.menu
            }, -2)


        self["StreamAction"] = ActionMap(["StreamActions"],
            {
                "incBuffer": self.increaseRtmpBuffer,
                "decBuffer": self.decreaseRtmpBuffer,
                "incPlayDelay" : self.increasePlayDelay,
                "decPlayDelay" : self.decreasePlayDelay,
                "red" : self.removeStream,
                "refresh":self.refreshList
            }, -3)

        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()

        self.onUpdateGUI.append(self.updateStreamInfo)
        self.onLayoutFinish.append(self.updateGUI)
        self.onClose.append(self.__onClose)

    def openDownloads(self):
        import download
        if not self.working:
            self.workingStarted()
            download.openDownloads(self.session, "Streamy", self.content_provider, self.workingFinished)

    def isStream(self):
        it = self.getSelectedItem()
        return isinstance(it, PVideo)

    def isRtmpStream(self):
        it = self.getSelectedItem()
        return isinstance(it, PVideo) and it.url.startswith('rtmp')

    def isGstreamerPlayerSelected(self):
        it = self.getSelectedItem()
        return isinstance(it, PVideo) and config.plugins.archivCZSK.videoPlayer.detectedType.getValue() == 'gstreamer'

    def updateStreamInfo(self):
        it = self.getSelectedItem()
        if isinstance(it, (PFolder, PPlaylist, PExit)):
            pass
        else:
            stream = it.stream
            if self.isStream():
                self['protocol'].setText(it.get_protocol())
                self['playdelay'].setText(str(stream.playDelay))
                self['livestream_pixmap'].instance.setPixmap(self.LIVE_PIXMAP)
            if self.isRtmpStream():
                self['rtmpbuffer'].setText(str(stream.buffer))
            if self.isGstreamerPlayerSelected():
                self['playerbuffer'].setText(str(stream.playerBuffer))

        self['streaminfo_label'].update()
        self['streaminfo'].update()
        self['protocol_label'].update()
        self['protocol'].update()
        self['playdelay_label'].update()
        self['playdelay'].update()
        self['livestream_pixmap'].update()
        self['rtmpbuffer_label'].update()
        self['rtmpbuffer'].update()
        self['playerbuffer_label'].update()
        self['playerbuffer'].update()


    def increaseRtmpBuffer(self):
        if not self.working:
            stream = self.selected_it.stream
            if stream is not None and isinstance(stream, RtmpStream):
                stream.rtmpBuffer += 1000
                self['rtmpbuffer'].setText(str(stream.rtmpBuffer))

    def decreaseRtmpBuffer(self):
        if not self.working:
            stream = self.selected_it.stream
            if stream is not None and isinstance(stream, RtmpStream):
                if stream.rtmpBuffer > 1000:
                    stream.rtmpBuffer -= 1000
                    self['rtmpbuffer'].setText(str(stream.rtmpBuffer))

    def increasePlayDelay(self):
        if not self.working:
            stream = self.selected_it.stream
            if stream is not None and isinstance(stream, Stream):
                stream.playDelay += 1
                self['playdelay'].setText(str(stream.playDelay))

    def decreasePlayDelay(self):
        if not self.working:
            stream = self.selected_it.stream
            if stream is not None and isinstance(stream, Stream):
                if stream.playDelay > 3:
                    stream.playDelay -= 1
                    self['playdelay'].setText(str(stream.playDelay))

    def removeStream(self):
        if not self.working:
            self.contentHandler.ask_remove_stream(self.getSelectedItem())

    def cancel(self):
        self.contentHandler.exit_item()

    def __onClose(self):
        self.session.nav.playService(self.oldService)
