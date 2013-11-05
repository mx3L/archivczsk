'''
Created on 21.10.2012

@author: marko
'''

import traceback
import os
import shutil

from Screens.MessageBox import MessageBox
from Components.config import config, configfile

from . import _, log

import settings
# loading repositories and their addons
from gui.common import showYesNoDialog, showInfoMessage, showErrorMessage
from gui.content import VideoAddonsContentScreen
from engine.items import PVideoAddon
from engine.addon import VideoAddon, XBMCAddon
from engine.exceptions.updater import UpdateXMLVersionError
from engine.tools.task import Task

ta3 = 'plugin.video.ta3'
nova = 'plugin.video.dmd-czech.voyo'
btv = 'plugin.video.dmd-czech.btv'
huste = 'plugin.video.dmd-czech.huste'
ct = 'plugin.video.dmd-czech.ivysilani'
metropol = 'plugin.video.dmd-czech.metropol'
muvi = 'plugin.video.dmd-czech.muvi'
joj = 'plugin.video.dmd-czech.joj'
prima = 'plugin.video.dmd-czech.prima'
stream = 'plugin.video.dmd-czech.stream'
stv = 'plugin.video.dmd-czech.stv'
voyosk = 'plugin.video.voyosk'
barrandov = 'plugin.video.barrandov'

tv_archives = [stv, joj, ct, ta3, prima, nova, huste, muvi, metropol, btv, voyosk, stream, barrandov]


class ArchivCZSK():
    
    __loaded = False
    __need_restart = False
    
    __repositories = {}
    __addons = {}
    
    @staticmethod
    def isLoaded():
        return ArchivCZSK.__loaded
    
    @staticmethod
    def load_repositories():
        from engine.repository import Repository
        log.info('looking for repositories in %s', settings.REPOSITORY_PATH)
        for repo in os.listdir(settings.REPOSITORY_PATH):
            repo_path = os.path.join(settings.REPOSITORY_PATH, repo)
            if os.path.isfile(repo_path):
                continue
            log.info('found repository %s', repo)
            repo_xml = os.path.join(repo_path, 'addon.xml')
            try:
                repository = Repository(repo_xml)
            except Exception:
                traceback.print_exc()
                log.info('cannot load repository %s', repo)
                log.info("skipping")
                continue
            else:
                ArchivCZSK.add_repository(repository)
        ArchivCZSK.__loaded = True
        
      
    
    @staticmethod
    def get_repository(repository_id):
        return ArchivCZSK.__repositories[repository_id]
    
    @staticmethod
    def add_repository(repository):
        ArchivCZSK.__repositories[repository.id] = repository
    
    @staticmethod
    def get_addon(addon_id):
        return ArchivCZSK.__addons[addon_id]
    
    @staticmethod
    def get_xbmc_addon(addon_id):
        return XBMCAddon(ArchivCZSK.__addons[addon_id])
    
    @staticmethod
    def has_addon(addon_id):
        return addon_id in ArchivCZSK.__addons
    
    @staticmethod
    def add_addon(addon):
        ArchivCZSK.__addons[addon.id] = addon
        
    
    def __init__(self, session):
        self.session = session
        self.toupdate_addons = []
        self.updated_addons = []
        self.first_time = os.path.exists(os.path.join(settings.PLUGIN_PATH, 'firsttime'))
        
    
        update_string = ''
        if ArchivCZSK.__need_restart:
            self.ask_restart_e2()
            
        elif self.first_time:
            self.opened_first_time()
        
        elif config.plugins.archivCZSK.autoUpdate.value:
            self.check_addon_updates()
        else:
            self.open_archive_screen()
            
    def opened_first_time(self):
        os.remove(os.path.join(settings.PLUGIN_PATH, 'firsttime'))
        config.plugins.archivCZSK.videoPlayer.useDefaultSkin.setValue(False)
        config.plugins.archivCZSK.videoPlayer.useDefaultSkin.save()
        config.plugins.archivCZSK.linkVerification.setValue(False)
        config.plugins.archivCZSK.linkVerification.save()
        
        # fix GS on sh4 with servicemp4(older images)
        # on new sh4 images, servicemp4 has to be turned off
        # until servicemp4 for new images isn't compiled ..
        if settings.ARCH == 'sh4' and settings.SERVICEMP4:
            config.plugins.archivCZSK.hdmuFix.setValue(True)
            config.plugins.archivCZSK.hdmuFix.save()
            
        text =  _("This is the first time you started archivyCZSK") + "\n\n"
        text+= _("For optimal usage of this plugin, you need to check") + "\n"
        text+= _("if you have all neccessary video plugins installed") + "."
        showInfoMessage(self.session, text, 0, self.open_player_info)
        
        
    def open_player_info(self, callback=None):
        import gui.info as info
        info.showVideoPlayerInfo(self.session, self.check_addon_updates)

    
    def check_addon_updates(self):
        for repo_key in self.__repositories.keys():
            repository = self.__repositories[repo_key]
            try:
                self.toupdate_addons += repository.check_updates()
            except UpdateXMLVersionError:
                log.info('cannot retrieve update xml for repository %s', repository)
                # self.show_error(_("Cannot retrieve update xml for repository") + " [%s]" % repository.name.encode('utf-8'))
                continue
            except Exception:
                traceback.print_exc()
                log.info('error when checking updates for repository %s', repository)
                # self.show_error(_("Error when checking updates of repository") + " [%s]" % repository.name.encode('utf-8'))
                continue
        update_string = '\n'.join(addon.name for addon in self.toupdate_addons)
        if update_string != '':
            self.ask_update_addons(update_string)
        else:
            self.open_archive_screen()
            

    def ask_update_addons(self, update_string):
        self.session.openWithCallback(self.update_addons,
                                      MessageBox,
                                      _("Do you want to update") + " " + _("addons") + '?' + '\n\n' + update_string.encode('utf-8') ,
                                      type=MessageBox.TYPE_YESNO)

    def update_addons(self, callback=None, verbose=True):
        if not callback:
            self.open_archive_screen()
        else:
            updated_string = self._update_addons()
            print updated_string.encode('utf-8')
            self.session.openWithCallback(self.ask_restart_e2,
                                              MessageBox,
                                              _("Following addons were updated") + ':\n\n' + updated_string.encode('utf-8'),
                                              type=MessageBox.TYPE_INFO)
            
    def _update_addons(self):
        for addon in self.toupdate_addons:
            updated = False
            try:
                updated = addon.update()
            except Exception:
                traceback.print_exc()
                continue
            else:
                if updated:
                    self.updated_addons.append(addon)
            
        return '\n'.join(addon_u.name for addon_u in self.updated_addons)
            
    
    def ask_restart_e2(self, callback=None):
        ArchivCZSK.__need_restart = True
        self.session.openWithCallback(self.restart_e2, MessageBox, _("You need to restart E2. Do you want to restart it now?"), type=MessageBox.TYPE_YESNO)        
            
    
    def restart_e2(self, callback=None):
        if callback:
            from Screens.Standby import TryQuitMainloop
            self.session.open(TryQuitMainloop, 3)
        
    def open_archive_screen(self, callback=None):
        if not ArchivCZSK.__loaded:
            self.load_repositories()
        tv_video_addon = []
        video_addon = []
        for key in ArchivCZSK.__addons.keys():
            addon = ArchivCZSK.get_addon(key)
            if not isinstance(addon, VideoAddon):
                continue
            if (not config.plugins.archivCZSK.showBrokenAddons.getValue()
                and addon.get_info('broken')):
                continue
            if key in tv_archives:
                tv_video_addon.append(PVideoAddon(addon))
                log.debug('adding %s addon to tv group' , key)
            else:
                video_addon.append(PVideoAddon(addon))
                log.debug('adding %s addon to video group', key)
                
       
        tv_video_addon.sort(key=lambda addon:addon.name)
        video_addon.sort(key=lambda addon:addon.name)
        # first screen to open when starting plugin, so we start worker thread where we can run our tasks(ie. loading archives)
        Task.startWorkerThread()
        self.session.openWithCallback(self.close_archive_screen, VideoAddonsContentScreen, tv_video_addon, video_addon)
        
    def close_archive_screen(self):
        if not config.plugins.archivCZSK.preload.getValue():
            self.__addons.clear()
            self.__repositories.clear()
            ArchivCZSK.__loaded = False
            
        # We dont need worker thread anymore so we stop it  
        Task.stopWorkerThread()
        
        # finally save all cfg changes - edit by shamman
        configfile.save()
        
        # clear tmp content by shamman
        filelist = [ f for f in os.listdir("/tmp") if f.endswith(".url") ]
        for f in filelist:
            try:
                os.remove(f)
            except OSError:
                continue
        filelist = [ f for f in os.listdir("/tmp") if f.endswith(".png") ]
        for f in filelist:
            try:
                os.remove(f)
            except OSerror:
                continue
        shutil.rmtree("/tmp/archivCZSK", True)
        
        if config.plugins.archivCZSK.clearMemory.getValue():
            try:
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("1")
            except IOError as e:
                print 'cannot drop caches : %s' % str(e)
