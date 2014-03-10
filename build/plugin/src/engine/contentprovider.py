'''
Created on 3.10.2012

@author: marko
'''
import os
import socket
import sys
from twisted.internet import defer
from xml.etree.cElementTree import ElementTree

from Components.config import config

from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import version as aczsk
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.settings import VIDEO_EXTENSIONS, SUBTITLES_EXTENSIONS
from Plugins.Extensions.archivCZSK.engine.exceptions.addon import AddonError
from Plugins.Extensions.archivCZSK.engine.player.player import Player, StreamPlayer
from Plugins.Extensions.archivCZSK.resources.repositories import repo_modules
import xmlshortcuts
from tools import task, util
from downloader import DownloadManager
from items import PVideo, PFolder, PPlaylist, PDownload, Stream, RtmpStream


class SysPath(list):
    """to append sys path only to addon which belongs to"""
    def __init__(self, addons):
        self.addons = addons
    def append(self, val):
        print '[AddonSysPath] append', val
        for addon in self.addons:
            if val.find(addon.id) != -1:
                addon.loader.add_path(val)

class CustomSysImporter(util.CustomImporter):
    def __init__(self, custom_sys):
        util.CustomImporter.__init__(self, 'custom_sys',  log=log.debug)
        self.add_module('sys', custom_sys)

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

    def __getattr__(self, attr):
        if attr=='path':
            return self.path
        return getattr(sys, attr)

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
        self.capabilities = []
        self.on_start = []
        self.on_stop = []
        self.on_pause = []
        self.on_resume = []
        self.__started = False
        self.__paused = False

    def __str__(self):
        return "%s"% self.__class__.__name__

    def is_seekable(self):
        return True

    def is_pausable(self):
        return True

    def get_capabilities(self):
        return self.capabilities

    def get_content(self, params={}):
        """get content with help of params
          @return: should return list of items created in items module"""
        pass

    def start(self):
        if self.__started:
            log.info("[%s] cannot start, provider is already started",self)
            return
        self.__started = True
        self.__paused = False
        for f in self.on_start:
            f()
        log.info("[%s] started", self)

    def stop(self):
        if not self.__started:
            log.info("[%s] cannot stop, provider is already stopped",self)
            return
        self.__started = False
        self.__paused = False
        for f in self.on_stop:
            f()
        log.info("[%s] stopped", self)

    def resume(self):
        if not self.__started:
            log.info("[%s] cannot resume, provider not started yet",self)
            return
        if not self.__paused:
            log.info("[%s] cannot resume, provider is already running",self)
            return
        self.__paused = False
        for f in self.on_resume:
            f()
        log.info("[%s] resumed", self)

    def pause(self):
        if not self.__started:
            log.info("[%s] cannot pause, provider not started yet",self)
            return
        if self.__paused:
            log.info("[%s] cannot pause, provider is already paused",self)
            return
        self.__paused = True
        for f in self.on_pause:
            f()
        log.info("[%s] paused", self)


class Media(object):
    def __init__(self, player_cls, allowed_download=True):
        self.player = None
        self.player_cls = player_cls
        self.player_cfg = config.plugins.archivCZSK.videoPlayer
        self.capabilities.append('play')
        if allowed_download:
            self.capabilities.append('play_and_download')
            #self.capabilities.append('play_and_download_gst')
        self.on_stop.append(self.__delete_player)

    def __delete_player(self):
        self.player = None

    def play(self, session, item, mode, cb=None):
        if not self.player:
            use_video_controller = self.player_cfg.useVideoController.value
            self.player = self.player_cls(session, cb, use_video_controller)
        seekable = self.is_seekable()
        pausable = self.is_pausable()
        self.player.setMediaItem(item, seekable=seekable, pausable=pausable)
        self.player.setContentProvider(self)
        if mode in self.capabilities:
            if mode == 'play':
                self.player.play()
            elif mode == 'play_and_download':
                self.player.playAndDownload()
            elif mode == 'play_and_download_gst':
                self.player.playAndDownload(True)
        else:
            log.info('Invalid playing mode - %s', str(mode))


class Favorites(object):
    def __init__(self, shortcuts_path):
        self.shortcuts = xmlshortcuts.ShortcutXML(shortcuts_path)
        self.capabilities.append('favorites')
        self.on_stop.append(self.save_shortcuts)

    def create_shortcut(self, item):
        return self.shortcuts.createShortcut(item)

    def remove_shortcut(self, id_shortcut):
        return self.shortcuts.removeShortcut(id_shortcut)

    def get_shortcuts(self):
        return self.shortcuts.getShortcuts()

    def save_shortcuts(self):
        self.shortcuts.writeFile()


class Downloads(object):
    def __init__(self, downloads_path, allowed_download):
        self.downloads_path = downloads_path
        if allowed_download:
            self.capabilities.append('download')

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


    def download(self, item, startCB, finishCB, playDownload=False, mode="", overrideCB=None):
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
        downloadManager.addDownload(d, overrideCB)

    def remove_download(self, item):
        if item is not None and isinstance(item, PDownload):
            log.debug('removing item %s from disk' % item.name)
            os.remove(item.path.encode('utf-8'))
        else:
            log.info('cannot remove item %s from disk, not PDownload instance', str(item))


class VideoAddonContentProvider(ContentProvider, Media, Downloads, Favorites):

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
        return cls.__resolving_provider.video_addon

    def __init__(self, video_addon, downloads_path, shortcuts_path):
        allowed_download = not video_addon.get_setting('!download')
        self.video_addon = video_addon
        ContentProvider.__init__(self)
        Media.__init__(self, Player, allowed_download)
        Downloads.__init__(self,downloads_path, allowed_download)
        Favorites.__init__(self,shortcuts_path)
        self._dependencies = []
        self._sys_importer = CustomSysImporter(self.__addon_sys)
        self.on_start.append(self.__clean_sys_modules)
        self.on_start.append(self.__set_resolving_provider)
        self.on_stop.append(self.__unset_resolving_provider)
        self.on_stop.append(self.__restore_sys_modules)
        self.on_pause.append(self.__pause_resolving_provider)
        self.on_resume.append(self.__resume_resolving_provider)

    def __clean_sys_modules(self):
        self.saved_modules = {}
        for mod_name in repo_modules:
            if mod_name in sys.modules:
                mod = sys.modules[mod_name]
                del sys.modules[mod_name]
                self.saved_modules[mod_name] = mod
        del sys.modules['sys']

    def __restore_sys_modules(self):
        sys.modules['sys'] = sys
        sys.modules.update(self.saved_modules)
        del self.saved_modules

    def __set_resolving_provider(self):
        VideoAddonContentProvider.__resolving_provider = self
        VideoAddonContentProvider.__addon_sys.add_addon(self.video_addon)
        self.video_addon.include()
        self.resolve_dependencies()
        self.include_dependencies()
        sys.meta_path.append(self._sys_importer)

    def __unset_resolving_provider(self):
        VideoAddonContentProvider.__resolving_provider = None
        VideoAddonContentProvider.__addon_sys.clear_addons()
        self.video_addon.deinclude()
        self.release_dependencies()
        sys.meta_path.remove(self._sys_importer)

    def __pause_resolving_provider(self):
        self.video_addon.deinclude()
        for addon in self._dependencies:
            addon.deinclude()
        sys.meta_path.remove(self._sys_importer)

    def __resume_resolving_provider(self):
        self.video_addon.include()
        for addon in self._dependencies:
            addon.include()
        sys.meta_path.append(self._sys_importer)

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



class StreamContentProvider(ContentProvider, Media, Downloads):

    def __init__(self, downloads_path, streams_path):
        ContentProvider.__init__(self)
        Media.__init__(self, StreamPlayer, False)
        Downloads.__init__(self, downloads_path, False)
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
