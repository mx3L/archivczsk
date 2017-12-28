from Screens.MessageBox import MessageBox

from item import ItemHandler
from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK.gui.exception import AddonExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PExit, PFolder, PSearchItem, PSearch


class FolderItemHandler(ItemHandler):
    handles = (PFolder,)

    def __init__(self, session, content_screen, content_provider):
        info_modes = ['item', 'csfd']
        ItemHandler.__init__(self, session, content_screen, info_modes)
        self.content_provider = content_provider

    def is_search(self, item):
        return isinstance(item, (PSearchItem))

    def _open_item(self, item, *args, **kwargs):
        def open_item_success_cb(result):
            list_items, screen_command, args = result

            if not list_items and screen_command is not None:
                self.content_screen.resolveCommand(screen_command, args)
            else:
                list_items.insert(0, PExit())
                if screen_command is not None:
                    self.content_screen.resolveCommand(screen_command, args)

                if not self.content_screen.refreshing:
                    self.content_screen.save()
                else:
                    self.content_screen.refreshing = False

                if self.is_search(item):
                    parent_content = self.content_screen.getParent()
                    if parent_content:
                        parent_content['refresh'] = True

                content = {'parent_it':item,
                        'lst_items':list_items, 
                        'refresh':False,
                        'index':kwargs.get('position', 0)}
                self.content_screen.load(content)
                self.content_screen.stopLoading()
                self.content_screen.showList()
                self.content_screen.workingFinished()

        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            log.logError("Folder get_content error cb.\n%s"%failure)
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()

        self.content_screen.workingStarted()
        self.content_screen.startLoading()
        self.content_screen.hideList()
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)

    def _init_menu(self, item, *args, **kwargs):
        item.add_context_menu_item(_("Open"), action=self.open_item, params={'item':item})
        if not self.is_search(item) and 'favorites' in self.content_provider.capabilities:
            item.add_context_menu_item(_("Add Shortcut"), action=self.ask_add_shortcut, params={'item':item})
        else:
            item.remove_context_menu_item(_("Add Shortcut"), action=self.ask_add_shortcut, params={'item':item})

    def ask_add_shortcut(self, item):
        self.item = item
        self.session.openWithCallback(self.add_shortcut_cb, MessageBox,
                                      text=_("Do you want to add") + " " + item.name.encode('utf-8') + " " + _("shortcut?"),
                                      type=MessageBox.TYPE_YESNO)

    def add_shortcut_cb(self, cb):
        if cb:
            self.content_provider.create_shortcut(self.item)
