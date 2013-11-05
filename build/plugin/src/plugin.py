# -*- coding: UTF-8 -*-
'''
Created on 28.2.2012

@author: marko
'''
from Plugins.Plugin import PluginDescriptor
from Screens.PluginBrowser import *
from Components.PluginComponent import plugins
from Components.config import config

from Plugins.Extensions.archivCZSK import _
import gui.download as dwnld
from archivczsk import ArchivCZSK
from engine.downloader import DownloadManager
from gui.search import SearchClient
import version
from gsession import GlobalSession

def sessionstart(reason, session):
	GlobalSession.setSession(session)
	#saving active downloads to session
	if not hasattr(session, 'archivCZSKdownloads'):
		session.archivCZSKdownloads = []	
	if DownloadManager.getInstance() is None:
		DownloadManager(session.archivCZSKdownloads)

def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(version.title, main, "mainmenu", 32)]
	else:
		return []
	
def eventinfo(session, servicelist, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	print str(ref)
	session.open(SearchClient, ref)
	

def main(session, **kwargs):
	ArchivCZSK(session)

def startSetup(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(version.description, main, "archivy_czsk", 32)]
	return []

def Plugins(path, **kwargs):
	descr = version.description
	nameA = version.title
	list = [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart), PluginDescriptor(name=nameA, description=descr, where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="czsk.png"), ]
	if config.plugins.archivCZSK.extensions_menu.getValue():
		list.append(PluginDescriptor(name=nameA, description=descr, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	if config.plugins.archivCZSK.main_menu.getValue():
		list.append(PluginDescriptor(name=nameA, description=descr, where=PluginDescriptor.WHERE_MENU, fnc=startSetup))
	if config.plugins.archivCZSK.epg_menu.getValue():
		list.append(PluginDescriptor(name=_("Search in ArchivCZSK"), description=descr, where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo))
	return list


if config.plugins.archivCZSK.preload.getValue() and not ArchivCZSK.isLoaded():
	ArchivCZSK.load_repositories()
