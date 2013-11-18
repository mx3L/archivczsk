from item import ItemHandler
from media import MediaItemHandler, PlaylistItemHandler
from content import ContentHandler
from Plugins.Extensions.archivCZSK.engine.items import PFolder, PVideo, PPlaylist

class StreamVideoItemHandler(MediaItemHandler):
    handles = (PVideo, )
    def __init__(self, session, content_screen, content_provider):
        info_handlers = ['item']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_handlers)
        
    def init_menu(self, item):
        MediaItemHandler.init_menu(item)
        #item.add_context_menu_item(_("Remove"), action=self.ask_remove_stream, params={'item':item})
        
    def ask_remove_stream(self, item):
        self.content_screen.showInfo(_('Not implemented yet'))
        #self.item = item
        #message = _("Do you want to remove") + item.name.encode('utf-8') + _("stream?")
        #self.session.openWithCallback(self.remove_stream, MessageBox, message, type=MessageBox.TYPE_YESNO)
        
    def remove_stream(self, callback=None):
        if callback is not None:
            self.content_provider.remove_stream(self.item)
            self.content_screen.refreshList()
            
            
class StreamPlaylistItemHandler(PlaylistItemHandler):
    handles = (PPlaylist, )
    def __init__(self, session, content_screen, content_provider):
        info_handlers = ['item']
        PlaylistItemHandler.__init__(self, session, content_screen, content_provider, info_handlers)


class StreamContentHandler(ContentHandler):

    def __init__(self, session, content_screen, content_provider):
        handlers = []
        handlers.append(StreamPlaylistItemHandler(session, content_screen, content_provider))
        handlers.append(StreamVideoItemHandler(session, content_screen, content_provider))
        ContentHandler.__init__(self, session, content_screen, content_provider, handlers)
        
    def exit_item(self):
        parent_content = self.content_screen.popParent()
        if parent_content is not None:
            self.content_screen.load(parent_content)
        else:
            #self.content_provider.save_streams()
            self.content_screen.close(None)
