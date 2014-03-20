from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox

from item import ItemHandler
from Plugins.Extensions.archivCZSK.engine.items import PUserCategory, PCategory, PExit

class CategoryItemHandlerTemplate(ItemHandler):
    def __init__(self, session, content_screen, content_provider):
        ItemHandler.__init__(self, session, content_screen)
        self.content_provider = content_provider

    def _open_item(self, item):
        self.content_screen.workingStarted()
        if not self.content_screen.refreshing:
            self.content_screen.save()
        else:
            self.content_screen.refreshing = False
        list_items = [PExit()]
        list_addons = self.content_provider.get_content(item.params)
        list_items.extend(list_addons)
        content = {'parent_it':item,
                          'lst_items':list_items,
                          'refresh':False}
        self.content_screen.load(content)
        self.content_screen.workingFinished()


    def can_handle(self, item):
        return item.__class__ in self.handles

class CategoryItemHandler(CategoryItemHandlerTemplate):
    handles = (PCategory,)

class UserCategoryItemHandler(CategoryItemHandlerTemplate):
    handles = (PUserCategory,)

    def _init_menu(self, item):
        self.item = item
        item.add_context_menu_item(_("Rename"),
                                   action=self._rename_category,
                                   params={'category':item})
        item.add_context_menu_item(_("Remove"),
                                   action=self._ask_remove_category,
                                   params={'category':item})
        CategoryItemHandlerTemplate._init_menu(self, item)

    def _rename_category(self, category):
        self.session.openWithCallback(self._rename_category_cb, InputBox, _("Set new category name:"))

    def _rename_category_cb(self, category_name):
        if category_name:
            self.content_screen.workingStarted()
            self.content_provider.rename_category(self.item, category_name)
            self.content_screen.refreshList()
            self.content_screen.workingFinished()


    def _ask_remove_category(self, category):
        message = _("Do you want to remove") + " '" + category.name.encode('utf-8') + " '" + _("category") + " ?"
        self.session.openWithCallback(self._remove_category, MessageBox,
                                      text=message,
                                      type=MessageBox.TYPE_YESNO)

    def _remove_category(self, cb):
        if cb:
            self.content_screen.workingStarted()
            self.content_provider.remove_category(self.item)
            self.content_screen.refreshList()
            self.content_screen.workingFinished()
