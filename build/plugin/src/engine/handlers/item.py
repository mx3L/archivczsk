from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.gui import info, context

INFO_HANDLERS= {
                "item":info.showItemInfo,
                "csfd":info.showCSFDInfo,
               }

class ItemHandler(object):
    """ Template class - handles item interaction """
    handles = ()
    def __init__(self, session, content_screen, info_handlers=None):
        self.session = session
        self.content_screen = content_screen
        self.info_handlers = info_handlers or []
        
        #current item
        self.item = None
        
    def __repr__(self):
        return "[" + self.__class__.__name__ + "]"
        
    def open_item(self, item, *args, **kwargs):
        self.item = item
        log.debug("%s opening %s", repr(self), repr(item))
        self._open_item(item, *args, **kwargs)
        
    def _open_item(self, item, *args, **kwargs):
        """ 
        define how to open item in subclass
        """
        pass

    def _init_menu(self, item):
        """ hook - you can add here your init code"""
        pass
    
    def _init_info(self, item):
        """ hook - you can add here your init code"""
        pass 
    
    def menu_item(self, item, *args, **kwargs):
        """opens context menu of item"""
        self.item = item
        self._init_menu(item)
        if item.context:
            log.debug("%s opening context menu of %s", repr(self), repr(item))
            context.showContextMenu(self.session, item.name, item.thumb, item.context, self._menu_item_cb)
    
    def _menu_item_cb(self, idx):
        if idx is not None:
            ctx_item = self.item.context[idx]
            if ctx_item.can_execute():
                ctx_item.execute()
            else:
                self.open_item(ctx_item)
    
    def info_item(self, item, mode=None, *args, **kwargs):
        """opens info about item according to defined mode"""
        self.item = item
        self._init_info(item)
        if mode in INFO_HANDLERS:
            log.debug("%s opening info of %s", repr(self), repr(item))
            INFO_HANDLERS[mode](self.session, item)
    
    def can_handle(self, item):
        """
        @return: True if can handle item
        @return: False if cannot handle item
        """
        return isinstance(item, self.handles)
