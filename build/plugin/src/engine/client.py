
#### module for addon creators #####
import os
import twisted.internet.defer as defer
from Plugins.Extensions.archivCZSK import log

from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Components.config import config

from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK.gui.captcha import Captcha
from Plugins.Extensions.archivCZSK.resources.libraries import simplejson as json
from Plugins.Extensions.archivCZSK.engine.contentprovider import VideoAddonContentProvider
from Plugins.Extensions.archivCZSK.engine.tools import util
from Plugins.Extensions.archivCZSK.engine.tools.task import callFromThread, Task
from Plugins.Extensions.archivCZSK.engine.exceptions.addon import AddonInfoError, AddonWarningError, AddonError, AddonThreadException
from Plugins.Extensions.archivCZSK.engine.items import PFolder, PVideo, PPlaylist, PNotSupportedVideo, PSearch, PSearchItem, PContextMenuItem, Stream


GItem_lst = VideoAddonContentProvider.get_shared_itemlist()

def abortTask(func):
    def wrapped_func(*args, **kwargs):
        task = Task.getInstance()
        if task and task._aborted:
            raise AddonThreadException()
        func(*args, **kwargs)
    return wrapped_func
        

def getVersion():
    return "1.0"

def decode_string(string):
    if isinstance(string, unicode):
        return _(string)
    elif isinstance(string, str):
        string = unicode(string, 'utf-8', 'ignore')
        return _(string)


@callFromThread
def getTextInput(session, text):
    def getTextInputCB(word):
        log.debug("textinput: %s", word)
        if word is None:
            d.callback('')
        else:
            d.callback(word)
    d = defer.Deferred()
    session.openWithCallback(getTextInputCB, VirtualKeyBoard, title=text)
    return d

def getSearch(session):
    return getTextInput(session, _("Please set your search expression"))

@callFromThread
def getCaptcha(session, image):
    def getCaptchaCB(word):
        if word is None:
            d.callback('')
        else:
            d.callback(word)
    d = defer.Deferred()
    Captcha(session, image, getCaptchaCB)
    return d

@callFromThread
def openSettings(session, addon):
    def getSettingsCB(word):
        d.callback(word)
    d = defer.Deferred()
    addon.open_settings(session, addon, getSettingsCB)
    return d

def showInfo(info, timeout=5):
    raise AddonInfoError(info)

def showError(error, timeout=5):
    raise AddonError(error)

def showWarning(warning, timeout=5):
    raise AddonWarningError(warning)
    
    
@callFromThread        
def getYesNoInput(session, text):
    def getYesNoInputCB(callback=None):
        if callback:
            d.callback(True)
        else:
            d.callback(False)
    d = defer.Deferred()
    session.openWithCallback(getYesNoInputCB, MessageBox, text=text, type=MessageBox.TYPE_YESNO)
    return d



def set_command(name, **kwargs):
    """set command for active content screen
    first argument is always name of the command, next arguments are arguments for command
    
    possible commands for content screen are: refreshafter - refreshes content screen when again loaded
                                              refreshnow- refreshes content screen immediately"""
    GItem_lst[1] = name
    for arg in kwargs:
        GItem_lst[2][arg] = kwargs[arg]
        
        
def refresh_screen():
    set_command('refreshnow')
    
    
def create_directory_it(name, params={}, image=None, infoLabels={}, menuItems={}, search_folder=False, search_item=False):
    if search_item: it = PSearchItem()
    elif search_folder: it = PSearch()
    else: it = PFolder()
    
    if isinstance(name, str): it.name = unicode(name, 'utf-8', 'ignore')
    else: it.name = name
    
    it.params = params
    it.image = image
    
    infolabel_uni = {}
    for key, value in infoLabels.iteritems():
        if isinstance(value, str):  
            infolabel_uni[key] = unicode(value, 'utf-8', 'ignore')
        elif isinstance(value, unicode):
            infolabel_uni[key] = value
        else:
            infolabel_uni[key] = unicode(str(value), 'utf-8', 'ignore')

    for key, value in menuItems.iteritems():
        item_name = decode_string(key)
        thumb = None
        if isinstance(value, dict):
            params = value
            thumb = None
        if isinstance(value, list):
            thumb = value[0]
            params = value[1]
        it.add_context_menu_item(item_name, thumb=thumb, params=params)
                
    it.info = infolabel_uni 
    return it
    

def create_video_it(name, url, subs=None, image=None, infoLabels={}, menuItems={}, filename=None, live=False, stream=None, settings=None):
    it = PVideo()
    
    if isinstance(name, str): it.name = unicode(name, 'utf-8', 'ignore')
    else: it.name = name 
    
    it.url = url
    
    it.subs = None 
    if subs is not None and subs != '':
        it.subs = subs
    
    it.image = image
    
    infolabel_uni = {}
    for key, value in infoLabels.iteritems():
        if isinstance(value, str):
            infolabel_uni[key] = unicode(value, 'utf-8', 'ignore')
        else:
            infolabel_uni[key] = value      
    if not 'Title' in infolabel_uni:
        infolabel_uni["Title"] = it.name
    it.info = infolabel_uni
    
    for key, value in menuItems.iteritems():
        item_name = decode_string(key) 
        thumb = None
        if isinstance(value, dict):
            params = value
            thumb = None
        if isinstance(value, list):
            thumb = value[0]
            params = value[1]
        
        it.add_context_menu_item(item_name, thumb=thumb, params=params)
        
    if filename is not None:
        if isinstance(filename, unicode):
            it.filename = filename
        else:
            it.filename = unicode(filename, 'utf-8')
    
    it.live = live    
        
    if stream is not None and isinstance(Stream):
        it.add_stream(stream)
        
    if settings is not None:
        if not isinstance(settings, dict):
            log.info("Cannot load settings %s class, it has to be dict class" , settings.__class__.__name__)
        else:
            if 'user-agent' not in settings:
                settings['user-agent'] = ""
            if 'extra-headers' not in settings:
                settings['extra-headers'] = {}
            log.debug("Settings: %s", settings)
            it.settings = settings
            
    return it

@abortTask
def add_dir(name, params={}, image=None, infoLabels={}, menuItems={}, search_folder=False, search_item=False):
    """adds directory item to content screen
    
        @param name : name of the directory
        @param params: dictationary of parameters for next resolving
        @param image: image to show in directories info
        @param infoLabels: dictationary of informations{'title':title,'plot':plot,'rating':rating,''}"
        @param menuItems: dictationary with menu items
    
    """
    it = create_directory_it(name=name,
                             params=params,
                             image=image,
                             infoLabels=infoLabels,
                             menuItems=menuItems,
                             search_folder=search_folder,
                             search_item=search_item)
    GItem_lst[0].append(it)

@abortTask
def add_video(name, url, subs=None, image=None, infoLabels={}, menuItems={}, filename=None, live=False, stream=None, settings=None):
    
    """
    adds video item to content screen
        @param url: play url 
        @param subs: subtitles url
        @param image: image of video item
        @param infoLabels: dictationary of informations{'title':title,'plot':plot,'rating':rating,''}"
        @param filename: set this filename when downloading
        @param live: is video live stream
        @param settings: dictationary of player/download settings{"user-agent",:"","extra-headers":{}}
    """
    
    video_it = create_video_it(name=name,
                               url=url,
                               subs=subs,
                               image=image,
                               infoLabels=infoLabels,
                               menuItems=menuItems,
                               filename=filename,
                               live=live,
                               stream=stream,
                               settings=settings)
    
    if not isinstance(url,basestring):
        log.info('add_video - ignoring %s, invalid url', repr(video_it))
    else:
        GItem_lst[0].append(video_it)

@abortTask    
def add_playlist(name, media_list=[]):
    playlist = PPlaylist()
    playlist.name = name
    for media in media_list:
        playlist.add(media)
    GItem_lst[0].append(playlist)
    
    
    
    
        


