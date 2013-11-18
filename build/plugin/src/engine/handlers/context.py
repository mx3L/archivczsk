from item import ItemHandler
from Plugins.Extensions.archivCZSK.gui.exception import AddonExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PContextMenuItem

class ContextMenuItemHandler(ItemHandler):
    handles = (PContextMenuItem)
    def __init__(self, session, content_screen, content_provider):
        ItemHandler.__init__(self, session, content_screen)
        self.content_provider = content_provider
    
    def open_item(self, item, *args, **kwargs):
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
