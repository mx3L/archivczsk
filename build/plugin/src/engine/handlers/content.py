from item import ItemHandler
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.engine.items import PExit

class ContentHandler(ItemHandler):
    def __init__(self, session, content_screen, content_provider=None, handlers=[]):
        ItemHandler.__init__(self, session, content_screen)
        
        self.session = session
        self.content_provider = content_provider
        self._handlers = handlers
        self.__class__.handles = zip([handler.__class__ for handler in handlers])
    
    def is_exit(self,item):
        return isinstance(item, PExit)
    
    def _get_handler(self, item):
        for handler in self._handlers:
            if handler.can_handle(item):
                return handler
            else:
                log.info("%s cannot handle %s" % (handler, item))
            
    def open_item(self, item, *args, **kwargs):
        if self.is_exit(item):
            self.exit_item()
        else:
            handler = self._get_handler(item)
            if handler is not None:
                handler.open_item(item, *args, **kwargs)
            else:
                log.info("cannot open item %s, cannot found its handler" % item)
                self.content_screen.stopLoading()
                self.content_screen.showList()
                self.content_screen.workingFinished()
      
    def _init_menu(self, item, *args, **kwargs):
        handler = self._get_handler(item)
        if handler is not None:
            handler._init_menu(item)
    
    def _init_info(self, item, *args, **kwargs):
        handler = self._get_handler(item)
        if handler is not None:
            handler._init_info(item)
            
    def exit_item(self):
        pass
