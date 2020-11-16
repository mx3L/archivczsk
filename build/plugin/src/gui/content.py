import copy
import os
import datetime
import traceback
import shutil

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap, PixmapConditional
from Components.Sources.StaticText import StaticText
from Components.config import config
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Tools.LoadPixmap import LoadPixmap

from poster import PosterProcessing, PosterPixmapHandler

from Plugins.Extensions.archivCZSK import _, log, settings
from Plugins.Extensions.archivCZSK.compat import eConnectCallback
from Plugins.Extensions.archivCZSK.gui.icon import IconD
from Plugins.Extensions.archivCZSK.engine.contentprovider import \
    VideoAddonContentProvider, ArchivCZSKContentProvider
from Plugins.Extensions.archivCZSK.engine.handlers import \
    ArchivCZSKContentHandler, VideoAddonContentHandler, \
    VideoAddonManagementScreenContentHandler
from Plugins.Extensions.archivCZSK.engine.items import PItem, PFolder, PRoot, \
    PPlaylist, PExit, PVideo, PContextMenuItem, PSearch, PSearchItem, PDownload, \
    PVideoAddon, Stream, RtmpStream, PVideoNotResolved
from Plugins.Extensions.archivCZSK.engine.tools.task import Task
from Plugins.Extensions.archivCZSK.engine.tools.util import toString, download_web_file, download_to_file_async
from base import BaseArchivCZSKListSourceScreen
from common import MyConditionalLabel,  PanelColorListEntry2, \
    LoadingScreen, TipBar, CutLabel
from download import DownloadList
from enigma import eTimer, eLabel, ePicLoad
from menu import ArchivCZSKConfigScreen
from skin import parseFont
from Components.AVSwitch import AVSwitch
import urlparse


KEY_MENU_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_menu.png'))
KEY_INFO_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_info.png'))
KEY_5_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_5.png'))


class BaseContentScreen(BaseArchivCZSKListSourceScreen):

    def __init__(self, session, contentHandler, lst_items):
        BaseArchivCZSKListSourceScreen.__init__(self, session)
        self.contentHandler = contentHandler
        self.loadingScreen = session.instantiateDialog(LoadingScreen)
        self.lst_items = lst_items
        # screen context items
        self.ctx_items = []
        self.refresh = False
        self.refreshing = False
        self.parent_it = PRoot()
        self.enabled_path = True

        self.stack = []
        self.old_stack_len = 0
        self["status_label"] = Label("")
        self["path_label"] = CutLabel(" / ")
        if not self.enabled_path:
            self["path_label"].hide()
        self.onClose.append(self.__onClose)

    def __onClose(self):
        self.session.deleteDialog(self.loadingScreen)

    def startLoading(self):
        self.loadingScreen.start()
        self["status_label"].setText(_("Loading"))

    def stopLoading(self):
        self.loadingScreen.stop()
        self["status_label"].setText("")

    def updatePath(self):
        path_list = []
        path_list_tmp = [params['parent_it'].name for params in self.stack] + [self.parent_it.name]
        # squash two or more successive equal entries into one and show it:
        # [name1, next, next , name] -> [name1, next(2), name2]
        pidx = idx = 0
        while (idx < len(path_list_tmp)):
            path = path_list_tmp[idx]
            path_list.append(path)
            cnt = 0
            while ((idx + 1) < len(path_list_tmp) and path == path_list_tmp[idx+1]):
                idx += 1
                cnt += 1
            if cnt > 0:
                path_list[pidx] = "%s (%d)"%(path, cnt + 1)
            idx += 1
            pidx += 1
        path_text = ' / '.join(path_list)
        self["path_label"].setText(toString(path_text))


    def refreshList(self, restoreLastPosition=True):
        log.debug("refreshing screen of %s item" , self.parent_it.name)
        self.refreshing = True
        if restoreLastPosition:
            self.contentHandler.open_item(self.parent_it, position=self.getSelectedIndex())
        else:
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
            self.updatePath()
            self.updateMenuList(index = params.get('index', 0))

    def save(self):
        """saves current screen to stack"""
        log.debug("saving current screen to stack")
        self.stack.append({'lst_items':self.lst_items,
                            'parent_it':copy.copy(self.parent_it),
                           'refresh':self.refresh,
                           'index':self["menu"].index})

    def getParent(self):
        if len(self.stack) > 0:
            return self.stack[-1]
        return None

    def popParent(self):
        if len(self.stack) > 0:
            return self.stack.pop()
        return None


    def resolveCommand(self, command, arg):
        if command is not None:
            if command == 'refreshnow':
                self.refreshList()
            elif command == 'refreshnow_resetpos':
                self.refreshList(restoreLastPosition=False)
            elif command == 'updatelist':
                self.refreshing = True
            else:
                log.debug("unknown command %s" , command)


    def ok(self):
        
        if not self.working and len(self.lst_items) > 0:
            itm = self.getSelectedItem()
            try:
                log.logDebug("Opening item '%s'..."%itm)
            except:
                log.logError("Something failed.\n%s"%traceback.format_exc())
                pass
            self.contentHandler.open_item(itm)

    def menu(self):
        if not self.working and len(self.lst_items) > 0:
            self.contentHandler.menu_item(self.getSelectedItem(), self.ctx_items)

    def info(self, mode):
        if not self.working and len(self.lst_items) > 0:
            self.contentHandler.info_item(self.getSelectedItem(), mode)


class ArchivCZSKVideoAddonsManagementScreen(BaseContentScreen, TipBar):
    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current addon"))

    def __init__(self, session, provider):

        contentHandler = VideoAddonManagementScreenContentHandler(session, self, provider)
        addonItems = provider.get_content(
            {'category_addons':'all_addons', 
            'filter_enabled':False, 
            'filter_supported': False})
        BaseContentScreen.__init__(self, session, contentHandler, addonItems)
        TipBar.__init__(self, [self.CONTEXT_TIP], startOnShown=False)
        self.skinName = "ArchivCZSKContentScreen"
        self["menu"].style = "management"
        self.updateGUITimer = eTimer()
        self.updateGUITimer_conn = eConnectCallback(self.updateGUITimer.timeout, self.updateAddonGUI)
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

    def updateMenuList(self, index=0):
        itemList = []
        itemColor = 0xffffff
        addonState = _("enabled")
        for item in self.lst_items:
            addon = item.addon
            if addon.get_info('broken'):
                itemColor = 0xff0000
                addonState = _("broken")
            elif not addon.get_setting('enabled'):
                if addon.supported:
                    itemColor = 0xffff00
                else:
                    itemColor = 0xf5f500
                addonState = _("disabled")
            else:
                if addon.supported:
                    itemColor = 0x00ff00
                else:
                    itemColor = 0x00f500
                addonState = _("enabled")
            itemList.append((toString(item.name), addonState, itemColor))
        self["menu"].list = itemList
        self["menu"].index = index

    def updateAddonGUI(self):
        try:
            image = None
            title = author = version = description = ""
            item = self.getSelectedItem()
            if item is not None:
                title = item.name and toString(item.name) or ""
                imagePath = item.image and toString(item.image) or ""
                if imagePath:
                    try:
                        image = LoadPixmap(path=imagePath, cached=False)
                    except Exception as e:
                        print '[ArchivCZSKContent] error when loading image', e
                try:  # addon
                    author = item.author and toString(item.author) or ""
                    version = item.version and toString(item.version) or ""
                    description = item.description and toString(item.description) or ""
                except AttributeError:  # category
                    pass
            self["title"].setText(title.strip())
            if author:
                self["author"].setText(_("Author: ") + author.strip())
            else:
                self["author"].setText("")
            if version:
                self["version"].setText(_("Version: ") + version.strip())
            else:
                self["version"].setText("")
            self["about"].setText(description.strip())
            self["image"].instance.setPixmap(image)
        except:
            log.logError("updateAddonGUI failed.\n%s"%traceback.format_exc())
            pass

    def __onClose(self):
        self.updateGUITimer.stop()
        del self.updateGUITimer_conn
        del self.updateGUITimer



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
            # dont add PExit() if default category is user created cat.
            gotParrent = True
            try:
                gotParrent = self.getParent() is not None
            except:
                pass
            if gotParrent and (defaultCategory=='all_addons' or defaultCategory=='tv_addons' or defaultCategory=='video_addons'):
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
        self.updateGUITimer_conn = eConnectCallback(self.updateGUITimer.timeout, self.updateAddonGUI)

        # include DownloadList
        DownloadList.__init__(self)

        # include TipList
        TipBar.__init__(self, [self.CONTEXT_TIP], startOnShown=True)
        self.onUpdateGUI.append(self.changeAddon)
        self.onClose.append(self.__onClose)

        from Plugins.Extensions.archivCZSK.version import version
        self.setTitle("ArchivCZSK ("+toString(version)+")")
        self["image"] = Pixmap()
        self["title"] = Label("")
        self["author"] = Label("")
        self["version"] = Label("")
        self["about"] = Label("")

        self["key_red"] = Label(_("Manager"))
        self["key_green"] = Label(_("Support us"))
        self["key_yellow"] = Label("")
        self["key_blue"] = Label(_("Settings"))

        self["actions"] = ActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
                "up": self.up,
                "down": self.down,
                "blue": self.openSettings,
                "green": self.showIconD,
                "red": self.openAddonManagement,
                "menu" : self.menu
            }, -2)
        # after layout show update item "GUI" - edit: shamann
        self.onLayoutFinish.append(self.updateAddonGUI)

    def __onClose(self):
        self.provider.stop()
        self.updateGUITimer.stop()
        del self.updateGUITimer_conn
        del self.updateGUITimer

    def updateMenuList(self, index=0):
        try:
            if index is None:
                index = 0
            itemList = []
            itemColor = 0xffffff
            for item in self.lst_items:
                if getattr(item, "addon", False) and item.addon.get_info('broken'):
                    itemColor = 0xff0000
                else:
                    itemColor = 0xffffff
                itemList.append((toString(item.name), itemColor))
            self["menu"].list = itemList
            self["menu"].index = index
        except:
            log.info("update menu failed."+traceback.format_exc())
            pass

    def openSettings(self):
        if not self.working:
            self.provider.pause()
            self.session.openWithCallback(self.openSettingsCB, ArchivCZSKConfigScreen)

    def openSettingsCB(self, cb=None):
        self.provider.resume()

    def openAddonManagement(self):
        self.session.openWithCallback(self.openAddonManagementCB, ArchivCZSKVideoAddonsManagementScreen, self.provider)

    def openAddonManagementCB(self, cb=None):
        self.workingStarted()
        self.refreshList()
        self.workingFinished()

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
        try:
            image = None
            title = author = version = description = ""
            item = self.getSelectedItem()
            if item is not None:
                title = item.name and toString(item.name) or ""
                imagePath = item.image and toString(item.image) or ""
                if imagePath:
                    try:
                        image = LoadPixmap(path=imagePath, cached=False)
                    except Exception as e:
                        print '[ArchivCZSKContent] error when loading image', e
                try:  # addon
                    author = item.author and toString(item.author) or ""
                    version = item.version and toString(item.version) or ""
                    description = item.description and toString(item.description) or ""
                except AttributeError:  # category
                    pass
            self["title"].setText(title.strip())
            if author:
                self["author"].setText(_("Author: ") + author.strip())
            else:
                self["author"].setText("")
            if version:
                self["version"].setText(_("Version: ") + version.strip())
            else:
                self["version"].setText("")
            self["about"].setText(description.strip())
            self["image"].instance.setPixmap(image)
        except:
            log.logError("updateAddonGUI failed.\n%s"%traceback.format_exc())
            pass

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
            if config.plugins.archivCZSK.confirmExit.value:
                self.session.openWithCallback(self.closePlugin, MessageBox, _('Do you want to exit ArchivCZSK?'), type=MessageBox.TYPE_YESNO)
            else:
                self.closePlugin(True)

    def closePlugin(self, callback=None):
        if callback:
            self.close()

    def showIconD(self):
        self.session.open(IconD)


class ArchivCZSKAddonContentScreen(BaseContentScreen, DownloadList, TipBar):

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

        self["key_red"] = Label(_("Changelog"))
        self["key_green"] = Label(_("Downloads"))
        self["key_yellow"] = Label(_("Shortcuts"))
        self["key_blue"] = Label(_("Settings"))
        self["actions"] = ActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "up": self.up,
                "down": self.down,
                "cancel": self.cancel,
                "red" : self.openChangelog,
                "green" : self.openAddonDownloads,
                "blue": self.openAddonSettings,
                "yellow": self.openAddonShortcuts,
                "info": self.openInfo,
                "menu": self.menu,
                "csfd": self.openCSFD
            }, -2)

        #self.onUpdateGUI.append(self.updateFullTitle)
        self.onLayoutFinish.append(self.setWindowTitle)

    def openChangelog(self):
        if not self.working:
            import info
            info.showChangelog(self.session, self.addon.name, self.addon.changelog)

    def setWindowTitle(self):
        self.setTitle(toString(self.addon.name))

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

    def updateMenuList(self, index=0):
        self["menu"].list = [(LoadPixmap(toString(item.thumb)), toString(item.name)) for item in self.lst_items]
        self["menu"].index = index

    def cancel(self):
        if self.working:
            self.toggleCancelLoading()
        else:
            self.contentHandler.exit_item()

class ArchivCZSKAddonContentScreenAdvanced(BaseContentScreen, DownloadList, TipBar):

    CSFD_TIP = (KEY_5_IMG, _("show info in CSFD"))
    INFO_TIP = (KEY_INFO_IMG, _("show additional info"))
    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current item"))

    def __init__(self, session, addon, lst_items):
        self.addon = addon
        contentHandler = VideoAddonContentHandler(session, self, addon.provider)
        BaseContentScreen.__init__(self, session, contentHandler, lst_items)

        # include DownloadList
        DownloadList.__init__(self)

        self.updateGUITimer = eTimer()
        self.updateGUITimer_conn = eConnectCallback(self.updateGUITimer.timeout, self.updateAddonGUI)
        self.onUpdateGUI.append(self.changeAddon)
        self.onClose.append(self.__onClose)
        
        #settigns
        self.showImageEnabled = config.plugins.archivCZSK.downloadPoster.getValue()
        self.maxSavedImages = int(config.plugins.archivCZSK.posterImageMax.getValue())
        self.imagePosterDir = os.path.join(config.plugins.archivCZSK.posterPath.getValue(),'archivczsk_poster')
        self.noImage = os.path.join(settings.PLUGIN_PATH, 'gui','icon', 'no_movie_image.png')

        # include TipList
        TipBar.__init__(self, [self.CSFD_TIP, self.CONTEXT_TIP, self.INFO_TIP], startOnShown=True)

        self["key_red"] = Label(_("Changelog"))
        self["key_green"] = Label(_("Downloads"))
        self["key_yellow"] = Label(_("Shortcuts"))
        self["key_blue"] = Label(_("Settings"))
        self["movie_poster_image"] = Pixmap()
        poster_processing = PosterProcessing(self.maxSavedImages,
                                             self.imagePosterDir)
        self.poster = PosterPixmapHandler(self["movie_poster_image"], 
                                          poster_processing,
                                          self.noImage)
        self["movie_rating"] = Label("")
        self["movie_duration"] = Label("")
        self["movie_plot"] = Label("")
        
        self["actions"] = ActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "up": self.up,
                "down": self.down,
                "cancel": self.cancel,
                "red" : self.openChangelog,
                "green" : self.openAddonDownloads,
                "blue": self.openAddonSettings,
                "yellow": self.openAddonShortcuts,
                "info": self.openInfo,
                "menu": self.menu,
                "csfd": self.openCSFD
            }, -2)
        #self.onUpdateGUI.append(self.updateFullTitle)
        self.onLayoutFinish.append(self.setWindowTitle)

    def __onClose(self):
        self.updateGUITimer.stop()
        del self.updateGUITimer_conn
        del self.updateGUITimer
        del self.poster


    def updateAddonGUI(self):
        try:
            item = self.getSelectedItem()
            idur = ""
            irat = ""
            iplot = ""

            if isinstance(item, PVideoNotResolved) or isinstance(item, PFolder):
                if self.showImageEnabled:
                    if not isinstance(item, (PSearch, PSearchItem)):
                        self.poster.set_image(item.image)
                try:
                    if 'rating' in item.info:
                        if float(item.info['rating']) > 0:
                            irat = str(item.info['rating'])
                except:
                    log.logError("Rating parse failed..\n%s"%traceback.format_exc())
                try:
                    if 'duration' in item.info:
                        durSec = float(item.info['duration'])
                        if durSec > 0:
                            hours = int(durSec/60/60)
                            minutes = int((durSec - hours*60*60)/60)
                            if len(str(minutes)) == 1:
                                if hours > 0:
                                    idur = str(hours)+'h'+'0'+str(minutes)+'min'
                                else:
                                    idur = '0'+str(minutes)+'min'
                            else:
                                if hours > 0:
                                    idur = str(hours)+'h'+str(minutes)+'min'
                                else:
                                    idur = str(minutes)+'min'
                except:
                    log.logError("Duration parse failed..\n%s"%traceback.format_exc())
                try:
                    if 'plot' in item.info:
                        iplot = toString(item.info['plot'])[0:800]
                except:
                    log.logError("Plot parse failed..\n%s"%traceback.format_exc())

            self["movie_duration"].setText(idur)
            self["movie_rating"].setText(irat)
            self["movie_plot"].setText(iplot)
            
        except:
            log.logError("updateAddonGUI fail...\n%s"%traceback.format_exc())

    def changeAddon(self):
        # musi to ist cez timer pretoze enigma vola onUpdate 3x upne zbytocne
        # ak by nebolo cez timer tak by sa cakalo na kazde dobehnutie 3x
        self.updateGUITimer.start(100, True)

    def openChangelog(self):
        if not self.working:
            import info
            info.showChangelog(self.session, self.addon.name, self.addon.changelog)

    def setWindowTitle(self):
        self.setTitle(toString(self.addon.name))

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

    def updateImage(self):
        it = self.getSelectedItem()
        img = it and it.image
        self['image'].load(img)

    def updateMenuList(self, index=0):
        self["menu"].list = [(LoadPixmap(toString(item.thumb)), toString(item.name)) for item in self.lst_items]
        self["menu"].index = index

    def cancel(self):
        if self.working:
            self.toggleCancelLoading()
        else:
            self.contentHandler.exit_item()
