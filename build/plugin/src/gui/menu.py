# -*- coding: UTF-8 -*-
import os

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import config, ConfigDirectory, ConfigText
from Screens.LocationBox import LocationBox
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Plugins.Extensions.archivCZSK import _, settings
from Plugins.Extensions.archivCZSK.resources.repositories import \
    config as addon_config
from base import BaseArchivCZSKScreen
from common import CategoryWidgetSD, CategoryWidgetHD
import info


def openArchivCZSKMenu(session):
    session.open(ArchiveCZSKConfigScreen)

def openAddonMenu(session, addon, cb):
    if cb is None:
        session.open(ArchivCZSKAddonConfigScreen, addon)
    else:
        session.openWithCallback(cb, ArchivCZSKAddonConfigScreen, addon)

class BaseArchivCZSKConfigScreen(BaseArchivCZSKScreen, ConfigListScreen):
    WIDTH_HD = 610
    HEIGHT_HD = 435

    WIDTH_SD = 610
    HEIGHT_SD = 435

    def __init__(self, session, categories=[]):
        BaseArchivCZSKScreen.__init__(self, session)
        ConfigListScreen.__init__(self, [], session=session, on_change=self.changedEntry)
        self.onChangedEntry = [ ]

        self.categories = categories
        self.selected_category = 0
        self.config_list_entries = []
        self.category_widgets = []
        self.category_widgets_y = 100

        self.initializeCategories()
        self.initializeSkin()

        self["key_yellow"] = Label(_("Changelog"))
        self["key_green"] = Label(_("Save"))
        self["key_red"] = Label(_("Cancel"))
        self["key_blue"] = Label(_("Next"))

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
        if self.HD:
            self.skin = """
            <screen position="center,center" size="%s,%s" >
                <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
                <eLabel position="-1,55" size="612,1" backgroundColor="#999999" />""" % (self.WIDTH_HD, self.HEIGHT_HD)
            self.skin += '\n' + self.getCategoriesWidgetString()

            self.skin += """<widget name="config" position="0,%s" size="%s,%s" scrollbarMode="showOnDemand" />
                        </screen>""" % (self.category_widgets_y, self.WIDTH_HD, self.HEIGHT_HD - self.category_widgets_y - 10)
        else:
            self.skin = """
            <screen position="center,center" size="%s,%s" >
                <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
                <eLabel position="-1,55" size="612,1" backgroundColor="#999999" />""" % (self.WIDTH_HD, self.HEIGHT_HD)
            self.skin += '\n' + self.getCategoriesWidgetString()

            self.skin += """<widget name="config" position="0,%s" size="%s,%s" scrollbarMode="showOnDemand" />
                        </screen>""" % (self.category_widgets_y, self.WIDTH_SD, self.HEIGHT_SD - self.category_widgets_y - 10)

        # print "initialized skin %s" % self.skin
    def initializeCategories(self):
        self.createCategoryWidgets()

    def createCategoryWidget(self, name, label, x_position, y_position):
        if self.HD:
            return CategoryWidgetHD(self, name, label, x_position, y_position)
        else:
            return CategoryWidgetSD(self, name, label, x_position, y_position)

    def createCategoryWidgets(self):
        space = 5
        x_position = 5
        y_position = 60
        width = self.WIDTH_HD
        if not self.HD : width = self.WIDTH_SD

        for idx, category in enumerate(self.categories):
            cat_widget = self.createCategoryWidget('category' + str(idx), category['label'], x_position, y_position)
            self.category_widgets.append(cat_widget)
            x_position += cat_widget.x_size + space
            if (x_position + cat_widget.x_size + space) > width and self.categories[-1] != category:
                x_position = 5
                y_position += space + cat_widget.y_size
                self.category_widgets_y += (2 * space) + cat_widget.y_size


    def getCategoriesWidgetString(self):
        return '\n'.join(cat_widget.get_skin_string() for cat_widget in self.category_widgets)

    def nextCategory(self):
        if len(self.categories) > 0:
            self.changeCategory()

    def refreshConfigList(self):
        if len(self.categories) > 0:
            config_list = self.categories[self.selected_category]['subentries']
            if hasattr(config_list, '__call__'):
                config_list = config_list()

            self.config_list_entries = config_list

        self.category_widgets[self.selected_category].activate()
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

        self.category_widgets[current_category].deactivate()
        self.category_widgets[self.selected_category].activate()

        self["config"].list = self.config_list_entries
        self["config"].setList(self.config_list_entries)


    def changelog(self):
        changelog_path = os.path.join(settings.PLUGIN_PATH, 'changelog.txt')
        if os.path.isfile(changelog_path):
            changelog_text = open(changelog_path, "r").read()
            info.showChangelog(self.session, _('ArchivCZSK Changelog'), changelog_text)

    def keyOk(self):
        current = self["config"].getCurrent()[1]
        if isinstance(current, ConfigDirectory):
            self.session.openWithCallback(self.pathSelected, LocationBox, "", "", current.value)
        elif isinstance(current, ConfigText):
            entryName = self["config"].getCurrent()[0]
            self.session.openWithCallback(self.virtualKBCB, VirtualKeyBoardCFG, entryName, current)

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
            config_entry.setValue(res)


class ArchiveCZSKConfigScreen(BaseArchivCZSKConfigScreen):
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

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        current = self["config"].getCurrent()[1]
        if current in [
                        config.plugins.archivCZSK.linkVerification,
                        config.plugins.archivCZSK.videoPlayer.type,
                        config.plugins.archivCZSK.videoPlayer.servicemp4,
                        config.plugins.archivCZSK.videoPlayer.servicemrua,
                        config.plugins.archivCZSK.videoPlayer.bufferMode]:
            self.buildMenu()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        current = self["config"].getCurrent()[1]
        if current in [
                       config.plugins.archivCZSK.linkVerification,
                       config.plugins.archivCZSK.videoPlayer.type,
                       config.plugins.archivCZSK.videoPlayer.servicemp4,
                       config.plugins.archivCZSK.videoPlayer.servicemrua,
                       config.plugins.archivCZSK.videoPlayer.bufferMode]:
            self.buildMenu()

    def keyOk(self):
        current = self["config"].getCurrent()[1]
        if current == config.plugins.archivCZSK.videoPlayer.info:
            info.showVideoPlayerInfo(self.session)
        else:
            super(ArchiveCZSKConfigScreen, self).keyOk()


class ArchivCZSKAddonConfigScreen(BaseArchivCZSKConfigScreen):
    def __init__(self, session, addon):
        self.session = session
        self.addon = addon

        # to get addon config including global settings
        categories = addon_config.getArchiveConfigList(addon)

        BaseArchivCZSKConfigScreen.__init__(self, session, categories=categories)


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
        self.configEntry = configEntry
        VirtualKeyBoard.__init__(self, session, entryName.encode('utf-8'), configEntry.getValue().encode('utf-8'))
        self.skinName = "VirtualKeyBoard"

    def ok(self):
        self.close(self.text.encode("utf-8"), self.configEntry)

    def cancel(self):
        self.close(None, None)
