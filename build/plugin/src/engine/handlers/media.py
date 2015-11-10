from twisted.internet import defer

from item import ItemHandler
from folder import FolderItemHandler
from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK.gui.context import ArchivCZSKSelectSourceScreen
from Plugins.Extensions.archivCZSK.gui.download import DownloadManagerMessages
from Plugins.Extensions.archivCZSK.gui.exception import AddonExceptionHandler, DownloadExceptionHandler, PlayExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PExit, PVideo, PVideoResolved, PVideoNotResolved, PPlaylist


class MediaItemHandler(ItemHandler):
    """ Template class - handles Media Item interaction """

    def __init__(self, session, content_screen, content_provider, info_modes):
        ItemHandler.__init__(self, session, content_screen, info_modes)
        self.content_provider = content_provider

    def _open_item(self, item, mode='play', *args, **kwargs):
        self.play_item(item, mode, args, kwargs)

    def play_item(self, item, mode='play', *args, **kwargs):
        def end_play():
            self.content_provider.resume()
            self.content_screen.workingFinished()

        @PlayExceptionHandler(self.session)
        def start_play(item, mode):
            self.content_provider.pause()
            try:
                self.content_provider.play(self.session, item, mode, end_play)
            except Exception:
                self.content_provider.resume()
                raise
        self.content_screen.workingStarted()
        start_play(item, mode)

    def download_item(self, item, mode="", *args, **kwargs):
        @DownloadExceptionHandler(self.session)
        def start_download(mode):
            try:
                self.content_provider.download(item, startCB=startCB, finishCB=finishCB, mode=mode, overrideCB=overrideCB)
            except Exception:
                self.content_screen.workingFinished()
                raise

        startCB = DownloadManagerMessages.startDownloadCB
        finishCB = DownloadManagerMessages.finishDownloadCB
        overrideCB = DownloadManagerMessages.overrideDownloadCB
        start_download(mode)

    def _init_menu(self, item):
        provider = self.content_provider
        if 'play' in provider.capabilities:
            item.add_context_menu_item(_("Play"),
                                                        action=self.play_item,
                                                        params={'item':item,
                                                        'mode':'play'})

        if 'play_and_download' in provider.capabilities:
            item.add_context_menu_item(_("Play and Download"),
                                       action=self.play_item,
                                       params={'item':item,
                                                      'mode':'play_and_download'})

        if 'play_and_download_gst' in provider.capabilities:
            item.add_context_menu_item(_("Play and download (Gstreamer)"),
                                       action=self.play_item,
                                       params={'item':item,
                                                      'mode':'play_and_download_gst'})

        if 'download' in provider.capabilities:
            item.add_context_menu_item(_("Download"),
                                       action=self.download_item,
                                       params={'item':item,
                                                      'mode':'auto'})


class VideoResolvedItemHandler(MediaItemHandler):
    handles = (PVideoResolved, )
    def __init__(self, session, content_screen, content_provider):
        info_handlers = ['csfd','item']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_handlers)



class VideoNotResolvedItemHandler(MediaItemHandler):
    handles = (PVideoNotResolved, )
    def __init__(self, session, content_screen, content_provider):
        info_modes = ['item','csfd']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, ['item','csfd'])

    def _init_menu(self, item):
        MediaItemHandler._init_menu(self, item)
        item.add_context_menu_item(_("Resolve videos"),
                                       action=self._resolve_videos,
                                       params={'item':item})

    def play_item(self, item, mode='play', *args, **kwargs):
        def wrapped(res_item):
            MediaItemHandler.play_item(self, res_item, mode)
        self._resolve_video(item, wrapped)

    def download_item(self, item, mode="", *args, **kwargs):
        def wrapped(res_item):
            MediaItemHandler.download_item(self, res_item, mode)
            self.content_screen.workingFinished()
        self._resolve_video(item, wrapped)

    def _filter_by_quality(self, items):
        pass

    def _resolve_video(self, item, callback):
        def selected_source(idx):
            if idx is not None:
                item = self.list_items[idx]
                del self.list_items
                callback(item)
            else:
                self.content_screen.workingFinished()
        def open_item_success_cb(result):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            list_items, screen_command, args = result
            self._filter_by_quality(list_items)
            item = None
            if len(list_items) > 1:
                self.list_items = list_items
                self.session.openWithCallback(selected_source, ArchivCZSKSelectSourceScreen, list_items)
            elif len(list_items) == 1:
                item = list_items[0]
            else: # no video
                self.content_screen.workingFinished()
            if item:
                callback(item)

        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()
        self.content_screen.hideList()
        self.content_screen.startLoading()
        self.content_screen.workingStarted()
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)


    def _resolve_videos(self, item):
        def open_item_success_cb(result):
            list_items, screen_command, args = result
            list_items.insert(0, PExit())
            if screen_command is not None:
                self.content_screen.resolveCommand(screen_command, args)
            else:
                self.content_screen.save()
                content = {'parent_it':item, 'lst_items':list_items, 'refresh':False}
                self.content_screen.stopLoading()
                self.content_screen.load(content)
                self.content_screen.showList()
                self.content_screen.workingFinished()

        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()

        self.content_screen.workingStarted()
        self.content_screen.hideList()
        self.content_screen.startLoading()
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)



class PlaylistItemHandler(MediaItemHandler):
    handles = (PPlaylist, )
    def __init__(self, session, content_screen, content_provider, info_modes=None):
        if not info_modes:
            info_modes = ['item','csfd']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_modes)

    def show_playlist(self, item):
        self.content_screen.save()
        list_items = [PExit()]
        list_items.extend(item.playlist[:])
        content = {'parent_it':item,
                          'lst_items':list_items,
                          'refresh':False}
        self.content_screen.load(content)

    def _init_menu(self, item, *args, **kwargs):
        provider = self.content_provider
        if 'play' in provider.capabilities:
            item.add_context_menu_item(_("Play"),
                                                        action=self.play_item,
                                                        params={'item':item,
                                                        'mode':'play'})
        item.add_context_menu_item(_("Show playlist"),
                                   action=self.show_playlist,
                                   params={'item':item})
