# GUI items
import os
from Plugins.Extensions.archivCZSK import log

try:
    from Plugins.Extensions.archivCZSK import settings, _
    PNG_PATH = settings.IMAGE_PATH
except ImportError:
    PNG_PATH = '/tmp/png/'

class PContextMenuItem(object):
    def __init__(self, name, thumb, enabled, action=None, params=None):
        self.name = name
        self.thumb = thumb
        self.enabled = enabled
        self.__action = action
        self.__kwargs = params

    def __eq__(self, other):
        if isinstance(other, PContextMenuItem):
            return self.name == other.name and self.__action == other.__action
        return NotImplemented

    def get_params(self):
        return self.__kwargs

    def can_execute(self):
        return self.__action is not None and self.enabled

    def execute(self):
        if self.can_execute():
            self.__action(**self.__kwargs)


class PItem(object):
    def __init__(self):
        self.id = None
        self.name = u''
        # parameters for addon scripts
        self.params = {}
        # info dict with supported item info (Title,Image,Rating,Genre,Plot)
        self.info = {}
        # list with PContextMenuItems for context item menu
        self.context = []
        self.enabled = True
        self.thumb = u''
        self.image = None
        self.addon_id = None

    def __str__(self):
        out = "<%s - %s>"%(self.__class__.__name__,self.name)
        return out.encode('utf-8','ignore')

    def __repr__(self):
        out = "<%s label=%r" % (self.__class__.__name__, self.name)
        out += " params=%r" % self.params
        out += " info=%r" % self.info
        if self.thumb:
            out += " thumb=" + self.thumb
        out += '>'
        return out.encode('utf-8', 'ignore')

    def add_context_menu_item(self, name, thumb=None, action=None, params=None, enabled=True):
        item = PContextMenuItem(name, thumb, enabled, action, params)
        if item not in self.context:
            self.context.append(item)

    def remove_context_menu_item(self, name, thumb=None, action=None, params=None, enabled=True):
        item = PContextMenuItem(name, thumb, enabled, action, params)
        if item in self.context:
            self.context.remove(item)

    def clear_context_menu(self):
        del self.context[:]

    def get_id(self):
        return str(len(self.name)) + str(len(self.params))


class PVideoAddon(PItem):

#     def __get_addon(self):
#         from Plugins.Extensions.archivCZSK import addon
#         return addon[self.addon_id]
#
#     addon = property(__get_addon)

    def __init__(self, addon):
        PItem.__init__(self)
        self.addon = addon
        self.addon_id = self.addon.get_info('id')
        self.name = self.addon.get_info('name')
        self.author = self.addon.get_info('author')
        self.description = self.addon.get_info('description')
        self.version = self.addon.get_info('version')
        self.image = self.addon.get_info('image')
        self.order = 99999
        try:
            tmporder = self.addon.get_setting('auto_addon_order')
            if tmporder and tmporder.strip():
                self.order = int(tmporder)
        except:
            log.logError("Invalid value setting 'auto_addon_order' for addon (%s)."%self.addon_id)
            pass

    def get_id(self):
        return self.addon_id

# addon which belongs to category
class PCategoryVideoAddon(PVideoAddon):
    def __init__(self, addon):
        PVideoAddon.__init__(self, addon)
        # self.category_id = category_id


class PFolder(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.root = False
        self.thumb = PNG_PATH + '/folder.png'
        self.dataItem = None

class PVideo(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.url = ""
        self.thumb = PNG_PATH + '/movie.png'
        self.live = False
        self.filename = None
        self.subs = None
        self.picon = None
        self.quality = None
        # stream object, can be stream/rtmp stream
        self.stream = None
        # download object, provides additional info for downloading
        self.settings = {"user-agent":"", "extra-headers":{}}

    def get_protocol(self):
        return self.url[:self.url.find('://')].upper()

    def add_stream(self, stream):
        self.stream = stream

class PVideoResolved(PVideo):
    def __init__(self):
        PVideo.__init__(self)
        self.thumb  = PNG_PATH + '/play2.png'
        self.dataItem = None

class PVideoNotResolved(PVideo):
    def __init__(self):
        PVideo.__init__(self)
        self.thumb = PNG_PATH + '/movie.png'
        self.dataItem = None

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

class PRoot(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.name = u''

class PExit(PItem):
    def __init__(self):
        PItem.__init__(self)
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

class PCategory(PItem):
    def __init__(self):
        PItem.__init__(self)
        self.addons = []
        self.thumb = PNG_PATH + '/category.png'
        self.image = PNG_PATH + '/category_custom.png'

    def __len__(self):
        return len(self.addons)

    def __iter__(self):
        return (addon for addon in self.addons)

    def remove_addon(self, paddon):
        addon_id = paddon.addon_id
        if addon_id in self.addons:
            self.addons.remove(addon_id)

    def add_addon(self, paddon):
        addon_id = paddon.addon_id
        if not addon_id in self.addons:
            self.addons.append(addon_id)

    def get_paddons(self):
        return [PVideoAddonFavorite(addon_id) for addon_id in self.addons]

    def get_id(self):
        # category name is unique id
        return ''.join([str(ord(i)) for i in self.name])

class PUserCategory(PCategory):
    pass


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
