# GUI items
import os

from Plugins.Extensions.archivCZSK import settings, _
PNG_PATH = settings.IMAGE_PATH

class PContextMenuItem(object):
    def __init__(self, name, thumb, action=None, params={}):
        self.name = name
        self.thumb = thumb
        self.__action = action
        self.__kwargs = params
        
    def __eq__(self, other):
        if isinstance(other, PContextMenuItem):
            return self.name == other.name and self.__action == other.__action
        return NotImplemented
    
    def get_params(self):
        return self.__kwargs
    
    def can_execute(self):
        return self.__action != None
      
    def execute(self):
        if self.can_execute():
            self.__action(**self.__kwargs)
        

class PItem(object):
    def __init__(self):
        self.name = u''
        # parameters for addon scripts
        self.params = {}
        # info dict with supported item info (Title,Image,Rating,Genre,Plot)
        self.info = {}
        # list with PContextMenuItems for context item menu
        self.context = []
        
        self.thumb = u''
        self.image = None
        
    def __repr__(self):
        out = "<%s label=%r" % (self.__class__.__name__, self.name)
        out += " params=%r" % self.params
        out += " info=%r" % self.info
        if self.thumb:
            out += " thumb=" + self.thumb
        out += '>'
        return out.encode('utf-8','ignore')
        
    def add_context_menu_item(self, name, thumb=None, action=None, params={}):
        item = PContextMenuItem(name, thumb, action, params)
        if item not in self.context:
            self.context.append(item)
            
    def remove_context_menu_item(self, name, thumb=None, action=None, params={}):
        item = PContextMenuItem(name, thumb, action, params)
        if item in self.context:
            self.context.remove(item)
            
    def clear_context_menu(self):
        del self.context[:]
        
    def get_id(self):
        return str(len(self.name)) + str(len(self.params))
        
        
class PVideoAddon(PItem):
    def __init__(self, video_addon):
        PItem.__init__(self)
        self.addon = video_addon
        self.id = video_addon.get_info('id')
        self.name = video_addon.get_info('name')
        self.author = video_addon.get_info('author')
        self.description = video_addon.get_info('description')
        self.version = video_addon.get_info('version')
        self.image = video_addon.get_info('image')
        
        
class PFolder(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.root = False
        self.thumb = PNG_PATH + '/folder.png'
        
        
class PVideo(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.url = ""
        self.thumb = PNG_PATH + '/movie.png'
        self.live = False 
        self.filename = None
        self.subs = None 
        self.picon = None
        #stream object, can be stream/rtmp stream
        self.stream = None
        #download object, provides additional info for downloading
        self.settings = {"user-agent":"", "extra-headers":{}}
        
    def get_protocol(self):
        return self.url[:self.url.find('://')].upper()
    
    def add_stream(self, stream):
        self.stream = stream
               
class PNotSupportedVideo(PVideo):
    def __init__(self):
        PVideo.__init__(self)
        self.thumb = PNG_PATH + '/movie_warning.png'
        
class PPlaylist(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.playlist = []
        self.thumb = PNG_PATH + '/playlist.png'
        
    def clear(self):
        del self.playlist[:]
    
    def add(self, media):
        self.playlist.append(media)
        
class PDownload(PVideo):
    def __init__(self, path):
        PVideo.__init__(self)
        self.path = path
        self.size = os.path.getsize(path)
        # for now we assume that all downloads succesfully finished
        self.state = 'success_finished'
        self.textState = _('succesfully finished')
        self.start_time = None
        self.finish_time = os.path.getmtime(path)
        
        
class PExit(PFolder):
    def __init__(self):
        PFolder.__init__(self)
        self.thumb = PNG_PATH + '/up.png'
        self.name = u'..'

class PSearch(PFolder):
    def __init__(self):
        PFolder.__init__(self)
        self.thumb = PNG_PATH + '/search.png'
        
class PSearchItem(PFolder):
    def __init__(self):
        PFolder.__init__(self)
        self.thumb = PNG_PATH + '/search.png'

class Stream():
    """Additional parameters for streams"""
    def __init__(self, url):
        self.url = url
        self.live = True
        self.playerBuffer = 8000
        self.playDelay = 7


class RtmpStream(Stream):
    """Parameters for RTMP Stream"""
    def __init__(self, url, app, playpath, pageUrl, swfUrl, advanced):
        Stream.__init__(self, url)
        self.app = app
        self.playpath = playpath
        self.pageUrl = pageUrl
        self.swfUrl = swfUrl
        self.buffer = 20000
        self.advanced = advanced
        self.timeout = 60
        
    def getUrl(self):
        """ 
        Creates url for librtmp from parameters according to
        http://rtmpdump.mplayerhq.hu/librtmp.3.html
        """
        # Standard rtmp url format:  
        # rtmp[t][e|s]://hostname[:port][/app[/playpath]]
        
        urlPart = self.url.split('://')[1].split('/')
        # librtmp need app/playpath to be set else wont play
        # then we can override them by app=value playpath=value
        
        # plain url without app and playpath
        if len(urlPart) == 1:
            if self.app != "" and self.playpath != "":
                # set whatever we override it later
                self.url += '/someapp/'
            # url is broken
            else:
                print '[archivCZSK] RtmpStream %s is missing app or playpath' % self.url
                
        # url without playpath
        elif len(urlPart) == 2:
            if self.playpath != "":
                self.url += '/'
            else:
                # url is broken
                print '[archivCZSK] RtmpStream %s is missing playpath' % self.url
        
        url = []
        url.append("%s" % self.url)
        if self.live: url.append("live=1")
        else: url.append("live=0")
        if self.app != "":url.append("app=%s" % self.app)
        if self.swfUrl != "":url.append("swfUrl=%s" % self.swfUrl)
        if self.pageUrl != "":url.append("pageUrl=%s" % self.pageUrl)
        if self.playpath != "":url.append("playpath=%s" % self.playpath)
        url.append("buffer=%d" % self.buffer)
        url.append("timeout=%d" % self.timeout)
        url.append(self.advanced)
        return ' '.join(url)
    
    def getRtmpgwUrl(self):
        """ 
        Creates url for rtmpgw/rtmpdump from parameters according to
        http://rtmpdump.mplayerhq.hu/librtmp.3.html
        """
        url = []
        if self.live: url.append("--live")
        url.append("--rtmp '%s'" % self.url)
        if self.app != "":url.append("--app '%s'" % self.app)
        if self.swfUrl != "":url.append("--swfUrl '%s'" % self.swfUrl)
        if self.pageUrl != "":url.append("--pageUrl '%s'" % self.pageUrl)
        if self.playpath != "":url.append("--playpath '%s'" % self.playpath)
        url.append("--buffer %d" % self.buffer)
        url.append("--timeout %d" % self.timeout)
        url.append(self.advanced)
        return ' '.join(url)
