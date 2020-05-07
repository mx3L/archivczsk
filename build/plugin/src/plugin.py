# -*- coding: UTF-8 -*-
from Components.config import config
from Plugins.Plugin import PluginDescriptor

from Plugins.Extensions.archivCZSK import _, create_rotating_log
from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
from Plugins.Extensions.archivCZSK.gsession import GlobalSession
from Plugins.Extensions.archivCZSK.gui.search import ArchivCZSKSearchClientScreen
from Plugins.Extensions.archivCZSK.engine.downloader import DownloadManager


NAME = _("ArchivCZSK")
DESCRIPTION = _("Playing CZ/SK archives")

def sessionStart(reason, session):
    GlobalSession.setSession(session)
    # saving active downloads to session
    if not hasattr(session, 'archivCZSKdownloads'):
        session.archivCZSKdownloads = []
    if DownloadManager.getInstance() is None:
        DownloadManager(session.archivCZSKdownloads)

def main(session, **kwargs):
    ArchivCZSK(session)

def menu(menuid, **kwargs):
    if menuid == "mainmenu":
        #return [(DESCRIPTION, main, menuid, 32)]
        return [(DESCRIPTION, main, "archivy_czsk", 32)]
    else:
        return []

def eventInfo(session, servicelist, **kwargs):
    ref = session.nav.getCurrentlyPlayingServiceReference()
    session.open(ArchivCZSKSearchClientScreen, ref)
def osrefresh(session, servicelist, **kwargs):
    try:
        from Plugins.Extensions.archivCZSK.osref import OSRefresh
        OSRefresh(session).refresh()
    except:
        pass
    try:
        from Plugins.Extensions.archivCZSK.osrefdsk import OSRefreshDSK
        OSRefreshDSK(session).refresh()
    except:
        pass
    try:
        from Plugins.Extensions.archivCZSK.osrefdcz import OSRefreshDCZ
        OSRefreshDCZ(session).refresh()
    except:
        pass
    try:
        from Plugins.Extensions.archivCZSK.osrefmg import OSRefreshMG
        OSRefreshMG(session).refresh()
    except:
        pass
    try:
        from Plugins.Extensions.archivCZSK.osrefo2 import OSRefreshO2
        OSRefreshO2(session).refresh()
    except:
        pass

def Plugins(path, **kwargs):
    list = [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionStart),
        PluginDescriptor(NAME, description=DESCRIPTION, where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="czsk.png")]
    if config.plugins.archivCZSK.extensions_menu.value:
        #list.append(PluginDescriptor(NAME, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
        list.append(PluginDescriptor(NAME, description=DESCRIPTION, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
    if config.plugins.archivCZSK.main_menu.value:
        #list.append(PluginDescriptor(NAME, where=PluginDescriptor.WHERE_MENU, fnc=menu))
        list.append(PluginDescriptor(NAME, description=DESCRIPTION, where=PluginDescriptor.WHERE_MENU, fnc=menu))
    if config.plugins.archivCZSK.epg_menu.value:
        list.append(PluginDescriptor(_("Search in ArchivCZSK"), where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventInfo))

    list.append(PluginDescriptor("OS_refresh", where=PluginDescriptor.WHERE_EVENTINFO, fnc=osrefresh))
    return list

if config.plugins.archivCZSK.preload.value and not ArchivCZSK.isLoaded():
    ArchivCZSK.load_repositories()
    ArchivCZSK.load_skin()
    ArchivCZSK.start_ydl()