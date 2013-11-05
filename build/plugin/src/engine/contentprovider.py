'''
Created on 3.10.2012

@author: marko
'''
import os
import socket
from twisted.internet import defer
from xml.etree.cElementTree import ElementTree

from Components.config import config

from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import version as aczsk
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.settings import VIDEO_EXTENSIONS, SUBTITLES_EXTENSIONS
from Plugins.Extensions.archivCZSK.engine.exceptions.addon import AddonError
import xmlshortcuts
from tools import task, util
from downloader import DownloadManager
from items import PVideo, PFolder, PPlaylist, PDownload, Stream, RtmpStream


class SysPath(list):
    """to append sys path only to addon which belongs to""" 
    def __init__(self, addons):
        self.addons = addons
    def append(self, val):
        for addon in self.addons:
            if val.find(addon.id) != -1:
                addon.loader.add_path(val)
    
class AddonSys():
    "sys for addons"
    def __init__(self):
        self.addons = []
        self.path = SysPath(self.addons)
    
    def __setitem__(self, key, val):
        if key == 'path':
            print 'you cannot replace AddonSysPath'
        else:
            dict.__setitem__(self, key, val)
        
    def add_addon(self, addon):
        self.addons.append(addon)
        
    def remove_addon(self, addon):
        self.addons.remove(addon)
        
    def clear_addons(self):
        del self.addons[:]

        
class ContentProvider(object):
    """ Provides item content which can be shown in GUI
       All item content which can be created is in items module
    """
    
    def __init__(self):
        self._capabilities = []
        self.on_start = []
        self.on_stop = []
        
    def is_seekable(self):
        return True
    
    def is_pausable(self):
        return True
    
    def get_capabilities(self):
        return self._capabilities
    
    def get_content(self, params={}):
        """get content with help of params
          @return: should return list of items created in items module"""
        pass
    
    def start(self):
        for f in self.on_start:
            f()
        
    def stop(self):
        for f in self.on_stop:
            f()
          
        
class Favorites(object):
    def __init__(self, shortcuts_path):
        self.shortcuts = xmlshortcuts.ShortcutXML(shortcuts_path)
        
    def create_shortcut(self, item):
        return self.shortcuts.createShortcut(item)

    def remove_shortcut(self, id_shortcut):
        return self.shortcuts.removeShortcut(id_shortcut)
    
    def get_shortcuts(self):
        return self.shortcuts.getShortcuts()
    
    def save_shortcuts(self):
        self.shortcuts.writeFile()
        
        
class Downloads(object):
    def __init__(self, downloads_path):
        self.downloads_path = downloads_path
        
    def get_downloads(self):
        video_lst = []
        if not os.path.isdir(self.downloads_path):
            util.make_path(self.downloads_path)
            
        downloads = os.listdir(self.downloads_path)
        for download in downloads:
            download_path = os.path.join(self.downloads_path, download)
            
            if os.path.isdir(download_path):
                continue
            
            if os.path.splitext(download_path)[1] in VIDEO_EXTENSIONS:
                filename = os.path.basename(os.path.splitext(download_path)[0])
                url = download_path
                subs = None
                if filename in [os.path.splitext(x)[0] for x in downloads if os.path.splitext(x)[1] in SUBTITLES_EXTENSIONS]:
                    subs = filename + ".srt"
                     
                it = PDownload(download_path)
                it.name = filename
                it.url = url
                it.subs = subs
                
                downloadManager = DownloadManager.getInstance()
                download = downloadManager.findDownloadByIT(it)
                
                if download is not None:
                    it.finish_time = download.finish_time
                    it.start_time = download.start_time
                    it.state = download.state
                    it.textState = download.textState
                video_lst.append(it)
                
        return video_lst
    
    
    def download(self, item, startCB, finishCB, playDownload=False, mode=""):
        """Downloads item PVideo itemem calls startCB when download starts
           and finishCB when download finishes
        """
        quiet = False
        headers = item.settings['extra-headers']
        log.debug("Download headers %s", headers)
        downloadManager = DownloadManager.getInstance()
        d = downloadManager.createDownload(name=item.name, url=item.url, stream=item.stream, filename=item.filename,
                                           live=item.live, destination=self.downloads_path,
                                           startCB=startCB, finishCB=finishCB, quiet=quiet,
                                           playDownload=playDownload, headers=headers, mode=mode)
        if item.subs is not None and item.subs != '':
            log.debug('subtitles link: %s' , item.subs)
            subs_file_path = os.path.splitext(d.local)[0] + '.srt'
            util.download_to_file(item.subs, subs_file_path)
        downloadManager.addDownload(d) 
    
    def remove_download(self, item):
        if item is not None and isinstance(item, PDownload):
            log.debug('removing item %s from disk' % item.name)
            os.remove(item.path.encode('utf-8'))
        else:
            log.info('cannot remove item %s from disk, not PDownload instance', str(item))
            

class VideoAddonContentProvider(ContentProvider, Downloads, Favorites):

    __resolving_provider = None    
    __gui_item_list = [[], None, {}] #[0] for items, [1] for command to GUI [2] arguments for command
    __addon_sys = AddonSys()
    
    @classmethod
    def get_shared_itemlist(cls):
        return cls.__gui_item_list
    
    @classmethod
    def get_resolving_provider(cls):
        return cls.__resolving_provider
    
    @classmethod
    def get_resolving_addon(cls):
        return cls.__resolving_provider.addon

    def __init__(self, video_addon, downloads_path, shortcuts_path):
        ContentProvider.__init__(self)
        Downloads.__init__(self,downloads_path)
        Favorites.__init__(self,shortcuts_path)
        self.video_addon = video_addon
        self._dependencies = []
        self.on_start.append(self.__set_resolving_provider)
        self.on_stop.append(self.__unset_resolving_provider)
        
    def __set_resolving_provider(self):
        VideoAddonContentProvider.__resolving_provider = self
        VideoAddonContentProvider.__addon_sys.add_addon(self.video_addon)
        self.video_addon.include()
        self.resolve_dependencies()
        self.include_dependencies()
        
    def __unset_resolving_provider(self):
        VideoAddonContentProvider.__resolving_provider = None
        VideoAddonContentProvider.__addon_sys.clear_addons()
        self.video_addon.deinclude()
        self.release_dependencies()
        
    def __clear_list(self):
        del VideoAddonContentProvider.__gui_item_list[0][:]
        VideoAddonContentProvider.__gui_item_list[1] = None
        VideoAddonContentProvider.__gui_item_list[2].clear()
        
    def resolve_dependencies(self):
        from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
        log.info("trying to resolve dependencies for %s" , self.video_addon)
        for dependency in self.video_addon.requires:
            addon_id, version, optional = dependency['addon'], dependency['version'], dependency['optional']
            
            # checking if archivCZSK version is compatible with this plugin
            if addon_id == 'enigma2.archivczsk':
                if  not util.check_version(aczsk.version, version):
                    log.debug("archivCZSK version %s>=%s" , aczsk.version, version)
                else:
                    log.debug("archivCZSK version %s<=%s" , aczsk.version, version)
                    raise AddonError(_("You need to update archivCZSK at least to") + " " + version + " " + _("version"))
                
            log.info("%s requires %s addon, version %s" , self.video_addon, addon_id, version)
            if ArchivCZSK.has_addon(addon_id):
                tools_addon = ArchivCZSK.get_addon(addon_id)
                log.info("required %s founded" , tools_addon)
                if  not util.check_version(tools_addon.version, version):
                    log.debug("version %s>=%s" , tools_addon.version, version)
                    self._dependencies.append(tools_addon)
                else:
                    log.debug("version %s<=%s" , tools_addon.version, version)
                    if not optional:
                        log.error("cannot execute %s " , self.video_addon)
                        raise AddonError("Cannot execute addon %s, dependency %s version %s needs to be at least version %s" 
                                        % (self.video_addon, tools_addon.id, tools_addon.version, version))
                    else:
                        log.debug("skipping")
                        continue
            else:
                log.info("required %s addon not founded" , addon_id)
                if not optional:
                    log.info("cannot execute %s addon" , self.video_addon)
                    raise Exception("Cannot execute %s, missing dependency %s" % (self.video_addon, addon_id))
                else:
                    log.debug("skipping")
        
    def include_dependencies(self):
        for addon in self._dependencies:
            addon.include()
            self.__addon_sys.add_addon(addon)
                 
    def release_dependencies(self):
        log.debug("trying to release dependencies for %s" , self.video_addon)
        for addon in self._dependencies:
            addon.deinclude()
        del self._dependencies[:]
      
    def get_content(self, session, params, successCB, errorCB):
        log.debug('get_content - params:%s' % str(params))
        self.__clear_list()
        self.content_deferred = defer.Deferred()
        self.content_deferred.addCallbacks(successCB, errorCB)
        # setting timeout for resolving content
        loading_timeout = int(self.video_addon.get_setting('loading_timeout'))
        if loading_timeout > 0:
            socket.setdefaulttimeout(loading_timeout)
        
        thread_task = task.Task(self._get_content_cb, self.run_script, session, params)
        thread_task.run()
        return self.content_deferred
    
    def run_script(self, session, params):    
        script_path = os.path.join(self.video_addon.path, self.video_addon.script)
        execfile(script_path, {'session':session,
                               'params':params,
                               '__file__':script_path,
                               'sys':self.__addon_sys, 'os':os})
        
    def _get_content_cb(self, success, result):
        log.debug('get_content_cb - success:%s result: %s' % (success, result))
        
        # resetting timeout for resolving content
        socket.setdefaulttimeout(None)
        
        if success:
            log.debug("successfully loaded %d items" % len(self.__gui_item_list[0]))
            lst_itemscp = [[], None, {}]
            lst_itemscp[0] = self.__gui_item_list[0][:]
            lst_itemscp[1] = self.__gui_item_list[1]
            lst_itemscp[2] = self.__gui_item_list[2].copy()
            self.content_deferred.callback(lst_itemscp)
        else:
            self.content_deferred.errback(result)
            
    def is_seekable(self):
        return self.video_addon.get_setting('seekable')
    
    def is_pausable(self):
        return self.video_addon.get_setting('pausable')

    def close(self):
        self.video_addon = None
    
    
    
class StreamContentProvider(ContentProvider, Downloads):
    
    def __init__(self, downloads_path, streams_path):
        ContentProvider.__init__(self)
        Downloads.__init__(self, downloads_path)
        self.streams_path = streams_path
        self.stream_root = None
        self.groups = []
        self.load_streams()
        self.seekable = False
        self.pausable = False
        
    def get_content(self, item):
        if item is None:
            return self.groups
        elif isinstance(item, PFolder):
            return item.channels
        

    def load_streams(self):
        groups = []
        self.stream_root = util.load_xml(self.streams_path)
        
        for group in self.stream_root.findall('group'):
            group_name = ''
            group_name = group.findtext('name')
            cat_channels = []
        
            for channel in group.findall('channel'):    
                name = channel.findtext('name')
                stream_url = channel.findtext('stream_url') or channel.findtext('streamUrl')
                picon = channel.findtext('picon')
                app = channel.findtext('app')
                swf_url = channel.findtext('swfUrl')
                page_url = channel.findtext('pageUrl')
                playpath = channel.findtext('playpath')
                advanced = channel.findtext('advanced')
                live_stream = channel.findtext('liveStream') or channel.findtext('live_stream')
                player_buffer = channel.findtext('playerBuffer') or channel.findtext('player_buffer')
                rtmp_buffer = channel.findtext('rtmpBuffer') or channel.findtext('rtmp_buffer')
                play_delay = channel.findtext('playDelay') or channel.findtext('play_delay')
                rtmp_timeout = channel.findtext('timeout')
            
                if name is None or stream_url is None:
                    log.info('skipping stream, cannot find name or url')
                    continue
                if picon is None: pass
                if app is None: app = u''
                if playpath is None: playpath = u''
                if swf_url is None: swf_url = u''
                if page_url is None: page_url = u''
                if advanced is None: advanced = u''
                if live_stream is None: live_stream = True
                else: live_stream = not live_stream == 'False'
                if rtmp_buffer is None: rtmp_buffer = int(config.plugins.archivCZSK.videoPlayer.liveBuffer.getValue())
                if rtmp_timeout is None: rtmp_timeout = int(config.plugins.archivCZSK.videoPlayer.rtmpTimeout.getValue())
                if player_buffer is None: player_buffer = int(config.plugins.archivCZSK.videoPlayer.bufferSize.getValue())
                if play_delay is None: play_delay = int(config.plugins.archivCZSK.videoPlayer.playDelay.getValue())
                
                
                if stream_url.startswith('rtmp'):
                    stream = RtmpStream(stream_url, app, playpath, page_url, swf_url, advanced)
                    stream.buffer = int(rtmp_buffer)
                    stream.timeout = int(rtmp_timeout)
                else:
                    stream = Stream(stream_url)
                
                stream.picon = picon
                stream.playBuffer = int(player_buffer)
                stream.playDelay = int(play_delay)
                stream.live = live_stream
            
                it = PVideo()
                it.name = name
                it.url = stream_url
                it.live = live_stream
                it.stream = stream
                it.xml = channel
                it.root_xml = group
                cat_channels.append(it)
            
            playlist = PPlaylist()
            playlist.name = group_name
            playlist.playlist = cat_channels[:]
            #cat_channels.insert(0, playlist)
            it = PFolder()
            it.name = group_name
            it.xml = group
            it.channels = cat_channels
            groups.append(playlist)
            
        self.groups = groups
        
    def is_seekable(self):
        return False
    
    def is_pausable(self):
        return False
            
        
    def save_streams(self):
        log.debug('saving streams to %s' , self.streams_path)
        ElementTree(self.xmlRootElement).write(self.streams_path)
    
    def remove_stream(self, stream):
        log.debug('removing stream %s' , stream.name)
        self.stream.root_xml.remove(stream.xml)
        del stream
            
    def remove_folder(self, folder):
        log.debug('removing folder %s' , folder.name)
        self.stream_root.remove(folder.xml)
