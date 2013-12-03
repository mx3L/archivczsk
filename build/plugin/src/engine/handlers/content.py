from item import ItemHandler
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.gui import context
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
    
    def info_item(self, item, mode, *args, **kwargs):
        handler = self._get_handler(item)
        if handler is not None:
            handler.info_item(item, mode, *args, **kwargs)
            
    def _init_menu(self, item):
        handler = self._get_handler(item)
        if handler is not None:
            handler._init_menu(item)
            
    def menu_item(self, item, global_context=None, *args, **kwargs):
        self.item = item
        self.global_context = global_context
        self._init_menu(item)
        if item.context or global_context:
            log.debug("%s opening context menu of %s", repr(self), repr(item))
            context.showContextMenu(self.session, item.name, item.thumb, item.context, global_context, self._menu_item_cb)
    
    def _menu_item_cb(self, idx):
        if idx is not None:
            if idx < len(self.item.context):
                ctx_item = self.item.context[idx]
                if ctx_item.can_execute():
                    return ctx_item.execute()
                else:
                    self.open_item(ctx_item)
            else:
                global_idx = idx - len(self.item.context)
                ctx_item = self.global_context[global_idx]
                ctx_item[2]()
        del self.global_context
            
    def exit_item(self):
        pass
