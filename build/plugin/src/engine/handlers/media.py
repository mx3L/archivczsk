from item import ItemHandler
from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK.gui.download import DownloadManagerMessages
from Plugins.Extensions.archivCZSK.gui.exception import DownloadExceptionHandler, PlayExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PExit, PVideo, PPlaylist


class MediaItemHandler(ItemHandler):
    """ Template class - handles Media Item interaction """
    
    def __init__(self, session, content_screen, content_provider, info_methods=None):
        ItemHandler.__init__(self, session, content_screen, info_methods)
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
            self.content_provider.download(item, startCB=startCB, finishCB=finishCB, mode=mode)
        startCB = DownloadManagerMessages.startDownloadCB
        finishCB = DownloadManagerMessages.finishDownloadCB
        start_download(mode)
        
    def _init_menu(self, item):
        ItemHandler._init_menu(self, item)
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
                                                      'mode':'wget'})
            

class VideoItemHandler(MediaItemHandler):
    handles = (PVideo, )
    def __init__(self, session, content_screen, content_provider):
        info_handlers = ['csfd','item']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_handlers)
        

class PlaylistItemHandler(MediaItemHandler):
    handles = (PPlaylist, )
    def __init__(self, session, content_screen, content_provider, info_handlers=None):
        if not info_handlers:
            info_handlers = ['csfd','item']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_handlers)

    def show_playlist(self, item):
        self.content_screen.save()
        list_items = [PExit()]
        list_items.extend(item.playlist[:])
        content = {'parent_it':item,
                          'lst_items':list_items,
                          'refresh':False}
        self.content_screen.load(content)
        
    def _init_menu(self, item, *args, **kwargs):
        MediaItemHandler._init_menu(self, item)
        item.add_context_menu_item(_("Show playlist"),
                                   action=self.show_playlist,
                                   params={'item':item})
        