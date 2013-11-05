# -*- coding: UTF-8 -*-
'''
Created on 28.2.2012

@author: marko
'''
import copy, os

from enigma import eTimer, eLabel
from skin import parseFont
from Screens.MessageBox import MessageBox
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config
from Components.Pixmap import Pixmap, PixmapConditional
from Tools.LoadPixmap import LoadPixmap


from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK import settings
from Plugins.Extensions.archivCZSK.engine.items import PItem, PFolder, PPlaylist, PExit, PVideo, PContextMenuItem, PSearch, \
                                                        PSearchItem, PDownload, PVideoAddon, Stream, RtmpStream
from Plugins.Extensions.archivCZSK.engine.tools.task import Task
from Plugins.Extensions.archivCZSK.engine.contentprovider import StreamContentProvider, VideoAddonContentProvider
from Plugins.Extensions.archivCZSK.engine.player.player import Player, StreamPlayer


import info
import context


from webpixmap import WebPixmap
from common import MyConditionalLabel, ButtonLabel, PanelList, PanelListEntryHD, LoadingScreen , TipBar, CutLabel
from download import DownloadManagerMessages, DownloadList
from menu import ArchiveCZSKConfigScreen
from base import  BaseArchivCZSKMenuListScreen
from exception import AddonExceptionHandler, DownloadExceptionHandler, PlayExceptionHandler

PanelListEntry = PanelListEntryHD

KEY_MENU_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_menu.png'))
KEY_INFO_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_info.png'))
KEY_5_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'key_5.png'))
PATH_IMG = LoadPixmap(cached=True, path=os.path.join(settings.IMAGE_PATH, 'next.png'))
        
class ItemHandler():
    """ Handles item interaction """
    def __init__(self, session, content_screen):
        self.content_screen = content_screen
        self.session = session
        
        #actual item
        self.item = None
        
    def open_item(self, item):
        """opens item"""
        pass
    
    def menu_item(self, item):
        """opens context menu of item"""
        pass
    
    def info_item(self, item):
        """opens info about item"""
        pass
    
    
    
     
class VideoAddonItemHandler(ItemHandler):
    def __init__(self, session, content_screen):
        ItemHandler.__init__(self, session, content_screen)
       
    def open_item(self, item):
        self.item = item
        if isinstance(item, PVideoAddon):
            
            def open_item_success_cb(result):
                list_items, command, args = result
                list_items.insert(0, PExit())
                self.content_screen.resolveCommand(command, args)
                self.content_screen.stopLoading()
                self.open_video_addon(item.addon, list_items)
            
            @AddonExceptionHandler(self.session)  
            def open_item_error_cb(failure):
                self.open_video_addon_cb(item.addon.provider)
                self.content_screen.stopLoading()
                self.content_screen.workingFinished()
                failure.raiseException()
                
            @AddonExceptionHandler(self.session)
            def get_content(addon):
                try:
                    content_provider = addon.provider
                    content_provider.start()
                    content_provider.get_content(self.session, {}, open_item_success_cb, open_item_error_cb)
                except Exception:
                    content_provider.stop()
                    self.content_screen.stopLoading()
                    self.content_screen.workingFinished()
                    raise
                
            self.content_screen.workingStarted()
            self.content_screen.startLoading()
            get_content(item.addon)
        else:
            self.content_screen.stopLoading()
            self.content_screen.workingFinished()
            log.debug("cannot open unknown item %s" , item.__class__.__name__)
            
            
    def open_video_addon(self, addon, list_items):
        self.session.openWithCallback(self.open_video_addon_cb, ContentScreen, addon, list_items)
        
    def open_video_addon_cb(self, content_provider):
        if isinstance(content_provider, VideoAddonContentProvider):
            content_provider.stop()
        self.content_screen.workingFinished()
        
    def resolve_command(self):
        pass
    
    def info_item(self, item):
        pass
    
    def menu_item(self, item):
        self.item = item
        addon = item.addon
        #item.add_context_menu_item(_("Update"), action=item.addon.update)
        item.add_context_menu_item(_("Settings"), action=addon.open_settings, params={'session':self.session})
        item.add_context_menu_item(_("Changelog"), action=addon.open_changelog, params={'session':self.session})
        item.add_context_menu_item(_("Downloads"), action=addon.open_downloads, params={'session':self.session, 'cb':self.content_screen.workingFinished})
        item.add_context_menu_item(_("Shortcuts"), action=addon.open_shortcuts, params={'session':self.session, 'cb':self.content_screen.workingFinished})
        context.showContextMenu(self.session, item.name, item.thumb, item.context, self.menu_item_cb)
        
    def menu_item_cb(self, idx):
        if idx is not None:
            self.item.context[idx].execute()
        
        
            
            
class ContentItemHandler(ItemHandler):
    items = (PExit, PFolder, PVideo)
    commands = ("open_item", "download_item", "play_item", "play_and_download_item", "")
    
    def __init__(self, session, content_screen, content_provider, player):
        ItemHandler.__init__(self, session, content_screen)
        
        self.content_provider = content_provider
        self.content_screen = content_screen
        self.session = session
        self.player = player
    
    
    def is_exit(self, item): 
        return isinstance(item, PExit)   
    
    def is_folder(self, item):
        return isinstance(item, PFolder)
    
    def is_search(self, item):
        return isinstance(item, PSearchItem)
    
    def is_video(self, item):
        return isinstance(item, PVideo)
    
    def is_playlist(self, item):
        return isinstance(item, PPlaylist)
    
    def is_context(self, item):
        return isinstance(item, PContextMenuItem)
    
 
    def open_item(self, item, mode=''):
        self.item = item
        
        if self.is_exit(item):
            self.exit_item()
                
        elif self.is_folder(item):
            self.folder_item(item)
            
        elif self.is_video(item) or self.is_playlist(item):
            self.play_item(item, mode)
            
        elif self.is_context(item):
            self.run_item(item)
            
        else:
            log.debug("cannot open unknown item %s" , item.__class__.__name__)
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            
            
    def folder_item(self, item):
        def open_item_success_cb(result):
            list_items, screen_command, args = result
            list_items.insert(0, PExit())
                
            if screen_command is not None:
                self.content_screen.resolveCommand(screen_command, args)
            else:
                if not self.content_screen.refreshing:
                    self.content_screen.save()
                else:
                    self.content_screen.refreshing = False
                
                if self.is_search(item):
                    parent_content = self.content_screen.getParent()
                    if parent_content:
                        parent_content['refresh'] = True 
                    
                content = {'parent_it':item, 'lst_items':list_items, 'refresh':False}
                self.content_screen.load(content)
                self.content_screen.stopLoading()
                self.content_screen.showList()
                self.content_screen.workingFinished()
            
        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()
                 
        self.content_screen.workingStarted()
        self.content_screen.startLoading()
        self.content_screen.hideList() 
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)
        
            
            
    def exit_item(self):
        parent_content = self.content_screen.popParent()
        if parent_content is not None:
            self.content_screen.load(parent_content)
        else:
            self.content_provider.save_shortcuts()
            self.content_screen.close(self.content_provider)
        

    def play_item(self, item, mode='play'):
        
        @PlayExceptionHandler(self.session)
        def play(mode):
            if mode == 'play_and_download':
                self.player.playAndDownload()
            elif mode == 'play_and_download_gst':
                self.player.playAndDownload(True)
            else:
                self.player.play()

        self.content_screen.workingStarted()
        seekable = self.content_provider.is_seekable()
        pausable = self.content_provider.is_pausable()
        self.player.setMediaItem(item, seekable=seekable, pausable=pausable)
        self.player.setContentProvider(self.content_provider)
        play(mode)
        
    def show_playlist(self, item):
        self.content_screen.save()
        list_items = [PExit()]
        list_items.extend(item.playlist[:])
        content = {'parent_it':item, 'lst_items':list_items, 'refresh':False}
        self.content_screen.load(content)
        #self.content_screen.stopLoading()
        #self.content_screen.showList()
        #self.content_screen.workingFinished()
        
   
    def info_item(self, item, mode="archive"):
        if mode == "archive":
            if not self.is_exit(item):
                info.showItemInfo(self.session, item)
            
        elif mode == "csfd":
            if not self.is_exit(item):
                name = item.name.replace('.', ' ').replace('-', ' ')
                info.showCSFDInfo(self.session, name)
            
    def menu_item(self, item):
        self.item = item
        
        if self.is_folder(item):
            item.add_context_menu_item(_("Open"), action=self.folder_item, params={'item':item})
            item.add_context_menu_item(_("Add Shortcut"), action=self.ask_add_shortcut, params={'item':item})
            
        elif self.is_playlist(item):
            item.add_context_menu_item(_("Play"), action=self.play_item, params={'item':item})
            item.add_context_menu_item(_("Show playlist"), action=self.show_playlist, params={'item':item})
            
        elif self.is_video(item):
            item.add_context_menu_item(_("Play"), action=self.play_item, params={'item':item})
            item.add_context_menu_item(_("Play and Download"), action=self.play_item, params={'item':item, 'mode':'play_and_download'})
            if config.plugins.archivCZSK.videoPlayer.servicemp4.getValue() and not item.url.startswith('rtmp'):   
                item.add_context_menu_item(_("Play and Download (GStreamer)"), action=self.play_item, params={'item':item, 'mode':'play_and_download_gst'})
            if item.url.startswith('http'):
                item.add_context_menu_item(_("Download (wget)"), action=self.download_item, params={'item':item, 'mode':'wget'})
                item.add_context_menu_item(_("Download (Twisted)"), action=self.download_item, params={'item':item, 'mode':'twisted'})
            elif item.url.startswith('rtmp'):
                item.add_context_menu_item(_("Download (rtmpdump)"), action=self.download_item, params={'item':item, 'mode':'rtmpdump'})
    
        context.showContextMenu(self.session, item.name, item.thumb, item.context, self.menu_item_cb)
        
        
    def run_item(self, item):
        """executes context menu items"""
        if item.can_execute():
            return item.execute()
        
        def run_item_success_cb(result):
            list_items, screen_command, args = result
            self.content_screen.resolveCommand(screen_command, args)
            
        @AddonExceptionHandler(self.session)
        def run_item_error_cb(failure):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()
                 
        self.content_screen.workingStarted()
        self.content_screen.startLoading()
        self.content_screen.hideList() 
        self.content_provider.get_content(self.session, item.get_params(), run_item_success_cb, run_item_error_cb)
        
    
    def download_item(self, item, mode=""):
        @DownloadExceptionHandler(self.session)
        def start_download():
            self.content_provider.download(item, startCB=startCB, finishCB=finishCB, mode=mode)
            
        startCB = DownloadManagerMessages.startDownloadCB
        finishCB = DownloadManagerMessages.finishDownloadCB
        start_download()
        
    
    def menu_item_cb(self, idx=None):
        if idx is not None:
            self.open_item(self.item.context[idx])
        
    def ask_add_shortcut(self, item):
        self.item = item
        self.session.openWithCallback(self.add_shortcut_cb, MessageBox,
                                      text=_("Do you want to add") + " " + item.name.encode('utf-8', 'ignore') + " " + _("shortcut?"),
                                      type=MessageBox.TYPE_YESNO)
        
    def add_shortcut_cb(self, cb=None):
        if cb is not None:
            self.content_provider.create_shortcut(self.item)


 
class StreamContentItemHandler(ContentItemHandler):
    def __init__(self, session, content_screen, content_provider, player):
        ContentItemHandler.__init__(self, session, content_screen, content_provider, player)


    def folder_item(self, item):
        self.content_screen.workingStarted()
        self.content_screen.save()
        
        list_items = self.content_provider.get_content(item)
        if not isinstance(list_items[0], PExit):
            list_items.insert(0, PExit())
        
        content = {'parent_it':item, 'lst_items':list_items, 'refresh':False}
        self.content_screen.load(content)
        self.content_screen.workingFinished()
        
    def exit_item(self):
        parent_content = self.content_screen.popParent()
        if parent_content is not None:
            self.content_screen.load(parent_content)
        else:
            #self.content_provider.save_streams()
            self.content_screen.close(None)
                
    def info_item(self, item):
        pass
            
    def menu_item(self, item):
        self.item = item
        if self.is_folder(item):
            item.add_context_menu_item(_("Open"), action=self.folder_item, params={'item':item})
            
        elif self.is_playlist(item):
            item.add_context_menu_item(_("Play"), action=self.play_item, params={'item':item})
            item.add_context_menu_item(_("Show playlist"), action=self.show_playlist, params={'item':item})
            
        elif self.is_video(item):
            item.add_context_menu_item(_("Play"), action=self.play_item, params={'item':item})
            item.add_context_menu_item(_("Play and Download"), action=self.play_item, params={'item':item, 'mode':'play_and_download'})
            if item.url.startswith('http'):
                item.add_context_menu_item(_("Download (wget)"), action=self.download_item, params={'item':item, 'mode':'wget'})
                item.add_context_menu_item(_("Download (Twisted)"), action=self.download_item, params={'item':item, 'mode':'twisted'})
            elif item.url.startswith('rtmp'):
                item.add_context_menu_item(_("Download (rtmpdump)"), action=self.download_item, params={'item':item, 'mode':'rtmpdump'})
            item.add_context_menu_item(_("Remove"), action=self.ask_remove_stream, params={'item':item})
        context.showContextMenu(self.session, item.name, item.thumb, item.context, self.menu_item_cb)    
        
    def ask_remove_stream(self, item):
        self.content_screen.showInfo(_('Not implemented yet'))
        #self.item = item
        #message = _("Do you want to remove") + item.name.encode('utf-8') + _("stream?")
        #self.session.openWithCallback(self.remove_stream, MessageBox, message, type=MessageBox.TYPE_YESNO)
        
    def remove_stream(self, callback=None):
        if callback is not None:
            self.content_provider.remove_stream(self.item)
            self.content_screen.refreshList()
            
        
            
class BaseContentScreen(BaseArchivCZSKMenuListScreen):
    """Base Content Screen"""
    def __init__(self, session, item_handler, lst_items):
        BaseArchivCZSKMenuListScreen.__init__(self, session)
        self.item_handler = item_handler
        self.loadingScreen = session.instantiateDialog(LoadingScreen)
        
        self.lst_items = lst_items
        self.refresh = False
        self.refreshing = False
        self.parent_it = PFolder()
        self.parent_it.params = {}
        self.parent_it.name = '/'

        self.enabled_path = True
        self.max_path_width = 0
        
        self.path = []
        self.stack = []
        self.old_stack_len=0
        self["status_label"] = Label("")
        self["path_pixmap"] = Pixmap()
        self["path_label"] = CutLabel(" / ")
        #self.onLayoutFinish.append(self.setPixelsPerLetterRatio)
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
        #self["key_red"].changeLabel(ButtonLabel.TYPE_DISABLED)
        #self["key_green"].changeLabel(ButtonLabel.TYPE_DISABLED)
        #self["key_yellow"].changeLabel(ButtonLabel.TYPE_DISABLED)
        #self["key_blue"].changeLabel(ButtonLabel.TYPE_DISABLED)
        
    def stopLoading(self):
        self.loadingScreen.stop()
        self["status_label"].setText("")
        #self["key_red"].changeLabel(ButtonLabel.TYPE_NORMAL)
        #self["key_green"].changeLabel(ButtonLabel.TYPE_NORMAL)
        #self["key_yellow"].changeLabel(ButtonLabel.TYPE_NORMAL)
        #self["key_blue"].changeLabel(ButtonLabel.TYPE_NORMAL)
        #o0-n0 ->save o0-n1 -> load o0-n1 -> updatePath -->append,  -> o0-n0 


    def setPathPixmap(self):
        self["path_pixmap"].instance.setPixmap(PATH_IMG)

    def updatePath(self):
        current_stack_len = len(self.stack)
        parent_name = self.parent_it.name
        if current_stack_len <= self.old_stack_len:
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
            menu_list.append(PanelListEntry(it.name, idx, it.thumb))
        self["menu"].setList(menu_list)
        self["menu"].moveToIndex(index)
        
    def refreshList(self):
        log.debug("refreshing screen of %s item" , self.parent_it.name)
        self.refreshing = True
        self.item_handler.open_item(self.parent_it)
            
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
            if self.enabled_path:
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
            self.item_handler.open_item(self.getSelectedItem())
            
    def menu(self):
        if not self.working and len(self.lst_items) > 0:
            self.item_handler.menu_item(self.getSelectedItem())
            
    def info(self, mode):
        if not self.working and len(self.lst_items) > 0:
            self.item_handler.info_item(self.getSelectedItem(), mode)
            
            
class VideoAddonsContentScreen(BaseContentScreen, DownloadList, TipBar):
    
    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current addon"))
       
    def __init__(self, session, tv_video_addon, video_addon):
        item_handler = VideoAddonItemHandler(session, self)
        BaseContentScreen.__init__(self, session, item_handler, tv_video_addon)
        
        self.tv_video_addon = tv_video_addon
        self.video_addon = video_addon
        
        self.updateGUITimer = eTimer()
        self.updateGUITimer.callback.append(self.updateAddonGUI)
        
        #include DownloadList
        DownloadList.__init__(self)
        
        #include TipList
        TipBar.__init__(self, [self.CONTEXT_TIP], startOnShown=True)
        self.onUpdateGUI.append(self.changeAddon)
        self.onClose.append(self.__onClose)
        
        log.debug('initializing')
        
        self["image"] = Pixmap()
        self["title"] = Label("")
        self["author"] = Label("")
        self["version"] = Label("")
        self["about"] = Label("")
        
        self["key_red"] = Label(_("TV archives"))
        self["key_green"] = Label(_("Video archives"))
        self["key_yellow"] = Label(_("Live streams"))
        self["key_blue"] = Label(_("Settings"))
        
        self["actions"] = NumberActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
                "up": self.up,
                "down": self.down,
                "blue": self.openSettings,
                "red": self.showTVVideoAddons,
                "green": self.showVideoAddons,
                "yellow": self.showStreams,
                "menu" : self.menu
            }, -2)
        # after layout show update item "GUI" - edit: shamann
        self.onLayoutFinish.append(self.updateAddonGUI)

    def __onClose(self):
        self.updateGUITimer.stop()
        self.updateGUITimer = None
        
    def openSettings(self):
        if not self.working:
            self.session.open(ArchiveCZSKConfigScreen)

    def showTVVideoAddons(self):
        if not self.working:
            #self["key_red"].changeLabel(ButtonLabel.TYPE_PRESSED)
            #self["key_green"].changeLabel(ButtonLabel.TYPE_NORMAL)
            self.lst_items = self.tv_video_addon
            self.updateMenuList()
    
    def showVideoAddons(self):
        if not self.working:
            #self["key_red"].changeLabel(ButtonLabel.TYPE_NORMAL)
            #self["key_green"].changeLabel(ButtonLabel.TYPE_PRESSED)
            self.lst_items = self.video_addon
            self.updateMenuList()

    def showStreams(self):
        if not self.working:
            self.workingStarted()
            stream_content_provider = StreamContentProvider(config.plugins.archivCZSK.downloadsPath.getValue(), settings.STREAM_PATH)
            lst_items = stream_content_provider.get_content(None)
            if not isinstance(lst_items[0], PExit):
                lst_items.insert(0, PExit())
            self.session.openWithCallback(self.workingFinished, StreamContentScreen, stream_content_provider, lst_items)
    
    
    def changeAddon(self):
        if self.execing:
            self.updateGUITimer.start(100, True)
        
    
    def updateAddonGUI(self):
        it = self.getSelectedItem()
        if it is not None:
            self["image"].instance.setPixmap(it.image)
            self["title"].setText(it.name.encode('utf-8', 'ignore'))
            self["author"].setText(_("Author: ") + it.author.encode('utf-8', 'ignore'))
            self["version"].setText(_("Version: ") + it.version.encode('utf-8', 'ignore'))
            self["about"].setText(it.description.encode('utf-8'))
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
        player = Player(session, self.workingFinished, config.plugins.archivCZSK.videoPlayer.useVideoController.getValue())
        item_handler = ContentItemHandler(session, self, addon.provider, player)
        BaseContentScreen.__init__(self, session, item_handler, lst_items)

        
        #include DownloadList
        DownloadList.__init__(self)
        
        #include TipList
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
        self["actions"] = NumberActionMap(["archivCZSKActions"],
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
            self.item_handler.open_item(it_sc)
            
    def openAddonDownloads(self):
        if not self.working:
            self.workingStarted()
            self.addon.open_downloads(self.session, self.workingFinished)
            
    def openAddonSettings(self):
        if not self.working:
            self.addon.open_settings(self.session)
        
    def openInfo(self):
        self.info('archive')
               
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
            self.updateGUITimer.start(100,True)
      
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
            self.item_handler.open_item(PExit())
            
            
class StreamContentScreen(BaseContentScreen, DownloadList, TipBar):
    CONTEXT_TIP = (KEY_MENU_IMG, _("show menu of current item"))
    LIVE_PIXMAP = None   
    
    def __init__(self, session, content_provider, lst_items):
        player = StreamPlayer(session, self.workingFinished, config.plugins.archivCZSK.videoPlayer.useVideoController.getValue())
        item_handler = StreamContentItemHandler(session, self, content_provider, player)
        BaseContentScreen.__init__(self, session, item_handler, lst_items)

        self.content_provider = content_provider
        
        #include DownloadList
        DownloadList.__init__(self)
        
        #include TipList
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

        
        self["actions"] = NumberActionMap(["archivCZSKActions"],
            {
                "ok": self.ok,
                "up": self.up,
                "down": self.down,
                "cancel": self.cancel,
                "green" : self.openDownloads,
                "menu": self.menu
            }, -2)
        
        
        self["StreamAction"] = NumberActionMap(["StreamActions"],
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
        if isinstance(it, (PFolder, PPlaylist)):
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
            self.item_handler.ask_remove_stream(self.getSelectedItem())
            
    
    def cancel(self):
        self.item_handler.open_item(PExit())
    
    def __onClose(self):
        self.session.nav.playService(self.oldService)
