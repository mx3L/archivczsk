# -*- coding: UTF-8 -*-
import os
import info
import traceback

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import config, ConfigDirectory, ConfigText, ConfigNumber
from Screens.LocationBox import LocationBox
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Plugins.Extensions.archivCZSK import _, settings, log, removeDiac
from Plugins.Extensions.archivCZSK.resources.addons import \
    config as addon_config
from base import BaseArchivCZSKScreen
from common import Tabs



def openArchivCZSKMenu(session):
    session.open(ArchivCZSKConfigScreen)

def openAddonMenu(session, addon, cb):
    if cb is None:
        session.open(ArchivCZSKAddonConfigScreen, addon)
    else:
        session.openWithCallback(cb, ArchivCZSKAddonConfigScreen, addon)


class BaseArchivCZSKConfigScreen(BaseArchivCZSKScreen, ConfigListScreen):

    def __init__(self, session, categories=[]):
        BaseArchivCZSKScreen.__init__(self, session)
        ConfigListScreen.__init__(self, [], session=session, on_change=self.changedEntry)
        self.onChangedEntry = [ ]

        self.categories = categories
        self.selected_category = 0
        self.config_list_entries = []

        self.initializeSkin()

        self["key_yellow"] = Label(_("Changelog"))
        self["key_green"] = Label(_("Save"))
        self["key_red"] = Label(_("Cancel"))
        self["key_blue"] = Label(_("Next"))
        self["categories"] = Tabs([c['label'] for c in categories])

        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.keyCancel,
                "green": self.keySave,
                "ok": self.keyOk,
                "red": self.keyCancel,
                "blue": self.nextCategory,
                "yellow": self.changelog
            }, -2)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()

    def initializeSkin(self):
        self.skin = """
        <screen position="center,center" size="610,435" >
            <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <eLabel position="5,57" size="600,1" backgroundColor="#ffffff" />
            <widget name="categories" position="10,60" size="590,40" tab_size="140,30" tab_fontInactive="Regular;18" tab_fontActive="Regular;21" tab_backgroundColorActive="#000000" tab_backgroundColorInactive="#000000" />
            <widget name="config" position="10,105" size="590,320" scrollbarMode="showOnDemand" />
        </screen>"""

    def nextCategory(self):
        if len(self.categories) > 0:
            self.changeCategory()

    def refreshConfigList(self):
        if len(self.categories) > 0:
            config_list = self.categories[self.selected_category]['subentries']
            if hasattr(config_list, '__call__'):
                config_list = config_list()

            self.config_list_entries = config_list

        self["config"].list = self.config_list_entries
        self["config"].setList(self.config_list_entries)

    def changeCategory(self):
        current_category = self.selected_category
        if self.selected_category == len(self.categories) - 1:
            self.selected_category = 0
        else:
            self.selected_category += 1

        config_list = self.categories[self.selected_category]['subentries']

        # for dynamic menus we can use functions to retrieve config list
        if hasattr(config_list, '__call__'):
            config_list = config_list()

        self.config_list_entries = config_list

        self["categories"].setActiveTab(self.selected_category)
        self["config"].list = self.config_list_entries
        self["config"].setList(self.config_list_entries)


    def changelog(self):
        clog = u''
        changelog_path = os.path.join(settings.PLUGIN_PATH, 'changelog.txt')
        if os.path.isfile(changelog_path):
            with open(changelog_path, 'r') as f:
                text = f.read()
            try:
                clog = text
            except Exception:
                log.logError('ArchivCZSK changelog cannot be decoded')
                pass
        info.showChangelog(self.session, "ArchivCZSK", clog)

    def keyOk(self):
        current = self["config"].getCurrent()[1]
        if isinstance(current, ConfigDirectory):
            self.session.openWithCallback(self.pathSelected, LocationBox, "", "", current.value)
        elif isinstance(current, ConfigNumber):
            pass
        elif isinstance(current, ConfigText):
            entryName = self["config"].getCurrent()[0]
            self.session.openWithCallback(self.virtualKBCB, VirtualKeyBoardCFG, entryName=entryName, configEntry=current)
        
    def keySave(self):
        self.saveAll()
        self.close(True)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)

    def keyRight(self):
        ConfigListScreen.keyRight(self)

    def pathSelected(self, path):
        if path is not None:
            self["config"].getCurrent()[1].value = path

    def virtualKBCB(self, res=None, config_entry=None):
        if res is not None and config_entry is not None:
            try:
                if 'XcursorX' in res:
                    res = res.replace('XcursorX','')
            except:
                pass
            config_entry.setValue(res)


class ArchivCZSKConfigScreen(BaseArchivCZSKConfigScreen):
    def __init__(self, session):

        categories = [
                      {'label':_("Main"), 'subentries':settings.get_main_settings},
                      {'label':_("Player"), 'subentries':settings.get_player_settings},
                      {'label':_("Path"), 'subentries':settings.get_path_settings},
                      {'label':_("Misc"), 'subentries':settings.get_misc_settings}
                     ]

        BaseArchivCZSKConfigScreen.__init__(self, session, categories=categories)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onShown.append(self.buildMenu)

    def layoutFinished(self):
        self.setTitle("ArchivCZSK" + " - " + _("Configuration"))


    def buildMenu(self):
        self.refreshConfigList()

    def keyOk(self):
        current = self["config"].getCurrent()[1]
        if current == config.plugins.archivCZSK.videoPlayer.info:
            info.showVideoPlayerInfo(self.session)
        else:
            super(ArchivCZSKConfigScreen, self).keyOk()


class ArchivCZSKAddonConfigScreen(BaseArchivCZSKConfigScreen):
    def __init__(self, session, addon):
        self.session = session
        self.addon = addon

        # to get addon config including global settings
        categories = addon_config.getArchiveConfigList(addon)

        BaseArchivCZSKConfigScreen.__init__(self, session, categories=categories)
        self.skinName = ["ArchivCZSKAddonConfigScreen", "ArchivCZSKConfigScreen"]


        self.onShown.append(self.buildMenu)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle(self.addon.name.encode('utf-8', 'ignore') + " - " + _("Settings"))

    def changelog(self):
        info.showChangelog(self.session, self.addon.name, self.addon.changelog)

    def buildMenu(self):
        self.refreshConfigList()


class VirtualKeyBoardCFG(VirtualKeyBoard):
    def __init__(self, session, entryName, configEntry):
        try:
            self.configEntry = configEntry
            
            #VirtualKeyBoard.__init__(self, session, entryName.encode('utf-8'), configEntry.getValue().encode('utf-8'))
            VirtualKeyBoard.__init__(self, session, title=removeDiac(entryName), text=removeDiac(configEntry.getValue()))
            self.skinName = "VirtualKeyBoard"

            #from Plugins.Extensions.archivCZSK.engine.tools.util import decode_string
            #VirtualKeyBoard.__init__(self, session, entryName, configEntry.getValue())
            #self.skinName = "VirtualKeyBoard"
        except:
            log.logError("Init VirtualKeyBoardCFG failed.\n%s"%traceback.format_exc())
            raise
        

    def ok(self):
        try:
            #self.close(self.text.encode("utf-8"), self.configEntry)
            self.close(removeDiac(self["text"].getText()), self.configEntry)
        except:
            log.logError("OK VirtualKeyBoardCFG failed.\n%s"%traceback.format_exc())
            raise

    def cancel(self):
        self.close(None, None)

