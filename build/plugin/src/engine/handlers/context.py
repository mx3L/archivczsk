from item import ItemHandler
from folder import FolderItemHandler
from Plugins.Extensions.archivCZSK.gui.exception import AddonExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PContextMenuItem

class ContextMenuItemHandler(ItemHandler):
    handles = (PContextMenuItem)
    def __init__(self, session, content_screen, content_provider):
        ItemHandler.__init__(self, session, content_screen)
        self.content_provider = content_provider
        self.folder_handler = FolderItemHandler(session, content_screen, content_provider)
    
    def _open_item(self, item, *args, **kwargs):
        if item.can_execute():
            return item.execute()
        else:
            item.params = item.get_params()
            return self.folder_handler._open_item(item, *args, **kwargs)