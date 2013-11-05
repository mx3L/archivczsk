# -*- coding: UTF-8 -*-
'''
Created on 28.4.2012

@author: marko
'''
from Screens.MessageBox import MessageBox
from Components.Button import Button
from Components.ActionMap import NumberActionMap

from Plugins.Extensions.archivCZSK import _
from base import BaseArchivCZSKMenuListScreen
from common import PanelListEntryHD

PanelListEntry = PanelListEntryHD

def openShortcuts(session, addon, cb):
	session.openWithCallback(cb, ShortcutsScreen, addon)

class ShortcutsScreen(BaseArchivCZSKMenuListScreen):
	def __init__(self, session, addon):
		BaseArchivCZSKMenuListScreen.__init__(self, session)
		
		self.addon = addon
		self.lst_items = self.addon.provider.get_shortcuts()
		self.title = _("Shortcut") + ' ' + addon.name.encode('utf-8', 'ignore')
		
		self["key_red"] = Button(_("Remove shortcut"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		self["actions"] = NumberActionMap(["archivCZSKActions"],
			{
				"ok": self.ok,
				"cancel": self.cancel,
				"red": self.askRemoveShortcut,
				"up": self.up,
				"down": self.down,
			}, -2)
			
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(self.title)
		
	def askRemoveShortcut(self):
		it = self.getSelectedItem()
		if it is not None:
			self.session.openWithCallback(self.removeShortcut,
										MessageBox, _('Do you want to delete') + ' ' + it.name.encode('utf-8', 'ignore') + '?',
										type=MessageBox.TYPE_YESNO)	
	
	def removeShortcut(self, callback=None):
		if callback:
			it_shortcut = self.getSelectedItem()
			self.addon.provider.remove_shortcut(it_shortcut.get_id())
			self.lst_items = self.addon.provider.get_shortcuts()
			self.updateMenuList()

	def updateMenuList(self):
		menu_list = []
		for idx, x in enumerate(self.lst_items):
			menu_list.append(PanelListEntry(x.name, idx, x.thumb))
		self["menu"].setList(menu_list)		
	

	def ok(self):
		self.close(self.getSelectedItem())
		
	def cancel(self):
		self.close(None)

