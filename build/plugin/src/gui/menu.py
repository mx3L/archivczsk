# -*- coding: UTF-8 -*-
import os

from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, configfile, ConfigDirectory, ConfigText
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText


from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import settings
from Plugins.Extensions.archivCZSK.resources.repositories import config as addon_config

from common import CategoryWidgetSD, CategoryWidgetHD
from base import BaseArchivCZSKScreen
import info


def openArchivCZSKMenu(session):
    session.open(ArchiveCZSKConfigScreen)
    
def openAddonMenu(session, addon, cb):
    if cb is None:
        session.open(AddonConfigScreen, addon)
    else:
        session.openWithCallback(cb, AddonConfigScreen, addon)
    
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
                        
        #print "initialized skin %s" % self.skin
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
            f = open(changelog_path, "r")
            changelog_text = f.read()
            f.close()
            info.showChangelog(self.session, _('ArchivCZSK Changelog'), changelog_text)    
    
    def keyOk(self):
        current = self["config"].getCurrent()[1]
        if isinstance(current, ConfigDirectory):
            self.session.openWithCallback(self.pathSelected, SelectPath, current)
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
        
    def pathSelected(self, res=None, config_entry=None):
        if res is not None and config_entry is not None:
            config_entry.setValue(res)
            
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
        self.setTitle("ArchivCZSK"+" - "+_("Configuration"))
        
    
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
            
        
class AddonConfigScreen(BaseArchivCZSKConfigScreen):
    def __init__(self, session, addon):
        self.session = session
        self.addon = addon
        
        # to get addon config including global settings
        categories = addon_config.getArchiveConfigList(addon)
        
        BaseArchivCZSKConfigScreen.__init__(self, session, categories=categories)
        
        
        self.onShown.append(self.buildMenu)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle(self.addon.name.encode('utf-8', 'ignore')+" - "+_("Settings"))
            
    def changelog(self):
        info.showChangelog(self.session, self.addon.name, self.addon.changelog)
        
    def buildMenu(self):
        self.refreshConfigList() 


class SelectPath(Screen):
    skin = """<screen name="SelectPath" position="center,center" size="560,320">
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
            <widget name="target" position="0,60" size="540,22" valign="center" font="Regular;22" />
            <widget name="filelist" position="0,100" zPosition="1" size="560,220" scrollbarMode="showOnDemand"/>
            <widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        </screen>"""
    def __init__(self, session, configEntry):
        initDir = configEntry.getValue()
        if initDir is not None and not initDir.endswith('/'):
            initDir = initDir + '/'
        Screen.__init__(self, session)
        #inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
        #inhibitMounts = []
        self.configEntry = configEntry
        
        self["filelist"] = FileList(initDir, showDirectories=True, showFiles=False)
        self["target"] = Label()
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
        {
            "back": self.cancel,
            "left": self.left,
            "right": self.right,
            "up": self.up,
            "down": self.down,
            "ok": self.ok,
            "green": self.green,
            "red": self.cancel
            
        }, -1)
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Save"))
        self.onShown.append(self.setWindowTitle)
        
    def setWindowTitle(self):
        self.setTitle(_("Select directory"))

    def cancel(self):
        self.close(None, None)

    def green(self):
        self.close(self["filelist"].getSelection()[0], self.configEntry)

    def up(self):
        self["filelist"].up()
        self.updateTarget()

    def down(self):
        self["filelist"].down()
        self.updateTarget()

    def left(self):
        self["filelist"].pageUp()
        self.updateTarget()

    def right(self):
        self["filelist"].pageDown()
        self.updateTarget()

    def ok(self):
        if self["filelist"].canDescent():
            self["filelist"].descent()
            self.updateTarget()

    def updateTarget(self):
        currFolder = self["filelist"].getSelection()[0]
        if currFolder is not None:
            self["target"].setText(currFolder)
        else:
            self["target"].setText(_("Invalid Location"))
            
            
class VirtualKeyBoardCFG(VirtualKeyBoard):
    def __init__(self, session, entryName, configEntry):
        self.configEntry = configEntry
        VirtualKeyBoard.__init__(self, session, entryName.encode('utf-8'), configEntry.getValue().encode('utf-8'))
        self.skinName = "VirtualKeyBoard"
        
    def ok(self):
        self.close(self.text.encode("utf-8"), self.configEntry)
        
    def cancel(self):
        self.close(None, None)

        

    
    
    
    
    

