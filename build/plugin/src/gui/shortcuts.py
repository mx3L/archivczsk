# -*- coding: UTF-8 -*-
'''
Created on 28.4.2012

@author: marko
'''
from Components.ActionMap import NumberActionMap
from Components.Button import Button
from Screens.MessageBox import MessageBox
from Tools.LoadPixmap import LoadPixmap

from Plugins.Extensions.archivCZSK import _
from common import toString
from base import BaseArchivCZSKListSourceScreen


def openShortcuts(session, addon, cb):
	session.openWithCallback(cb, ArchivCZSKShortcutsScreen, addon)

class ArchivCZSKShortcutsScreen(BaseArchivCZSKListSourceScreen):
	def __init__(self, session, addon):
		BaseArchivCZSKListSourceScreen.__init__(self, session)

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
			self.addon.provider.remove_shortcut(it_shortcut)
			self.lst_items = self.addon.provider.get_shortcuts()
			self.updateMenuList()
	
	def updateMenuList(self, index=0):
		self["menu"].list = [(LoadPixmap(toString(item.thumb)), toString(item.name)) for item in self.lst_items]
		self["menu"].index = index

	def ok(self):
		self.close(self.getSelectedItem())

	def cancel(self):
		self.close(None)

