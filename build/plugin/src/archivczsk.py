'''
Created on 21.10.2012

@author: marko
'''

import os
import shutil
import threading
import traceback

from Components.config import config, configfile
from Screens.MessageBox import MessageBox
from Components.Console import Console
from skin import loadSkin

from engine.addon import VideoAddon, XBMCAddon
from engine.exceptions.updater import UpdateXMLVersionError
from engine.tools.task import Task
from engine.tools.util import check_program
from gui.common import showInfoMessage
from gui.content import ArchivCZSKContentScreen
import settings

from . import _, log
from Plugins.Extensions.archivCZSK.compat import DMM_IMAGE


# loading repositories and their addons
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
    def load_skin():
        from enigma import getDesktop
        desktop_width = getDesktop(0).size().width()
        if  desktop_width >= 1280:
            if DMM_IMAGE:
                if desktop_width == 1920:
                    skin_default_path = os.path.join(settings.SKIN_PATH, "default_dmm_fhd.xml")
                else:
                    skin_default_path = os.path.join(settings.SKIN_PATH, "default_dmm_hd.xml")
            else:
                if desktop_width == 1920:
                    skin_default_path = os.path.join(settings.SKIN_PATH, "default_fhd.xml")
                else:
                    skin_default_path = os.path.join(settings.SKIN_PATH, "default_hd.xml")
        else:
            skin_default_path = os.path.join(settings.SKIN_PATH, "default_sd.xml")
        skin_name = config.plugins.archivCZSK.skin.value
        skin_path = os.path.join(settings.SKIN_PATH, skin_name + ".xml")
        if skin_name == 'auto' or not os.path.isfile(skin_path):
            skin_path = skin_default_path
        log.info("loading skin %s" % skin_path)
        loadSkin(skin_path)

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
    def get_addons():
        return ArchivCZSK.__addons.values()

    @staticmethod
    def get_video_addons():
        return [addon for addon in ArchivCZSK.get_addons() if isinstance(addon, VideoAddon)]

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
        self.to_update_addons = []
        self.updated_addons = []
        self.first_time = os.path.exists(os.path.join(settings.PLUGIN_PATH, 'firsttime'))

        if ArchivCZSK.__need_restart:
            self.ask_restart_e2()

        elif self.first_time:
            self.opened_first_time()

        elif config.plugins.archivCZSK.autoUpdate.value:
            self.download_commit()
        else:
            self.open_archive_screen()

    def download_commit(self):
        path = os.path.join(os.path.dirname(__file__), 'commit')
        self.__console = Console().ePopen('curl -kfo %s https://raw.githubusercontent.com/mx3L/archivczsk-doplnky/master/commit' % path, self.check_commit_download)


    def check_commit_download(self, data, retval, extra_args):
        if retval == 0:
            self.check_addon_updates()
        else:
            log.info("commit not downloaded")
            self.open_archive_screen()

    def opened_first_time(self):
        os.remove(os.path.join(settings.PLUGIN_PATH, 'firsttime'))
        config.plugins.archivCZSK.videoPlayer.useDefaultSkin.setValue(False)
        config.plugins.archivCZSK.videoPlayer.useDefaultSkin.save()

        text = _("This is the first time you started archivyCZSK") + "\n\n"
        text += _("For optimal usage of this plugin, you need to check") + "\n"
        text += _("if you have all neccessary video plugins installed") + "."
        showInfoMessage(self.session, text, 0, self.open_player_info)


    def open_player_info(self, callback=None):
        import gui.info as info
        info.showVideoPlayerInfo(self.session, self.download_commit)

    def check_addon_updates(self):
        lock = threading.Lock()
        threads = []
        def check_repository(repository):
            try:
                to_update = repository.check_updates()
                with lock:
                    self.to_update_addons += to_update
            except UpdateXMLVersionError:
                log.info('cannot retrieve update xml for repository %s', repository)
            except Exception:
                traceback.print_exc()
                log.info('error when checking updates for repository %s', repository)
        for repo_key in self.__repositories.keys():
            repository = self.__repositories[repo_key]
            threads.append(threading.Thread(target=check_repository, args=(repository,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        update_string = '\n'.join(addon.name for addon in self.to_update_addons)
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
        for addon in self.to_update_addons:
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

        # first screen to open when starting plugin,
        # so we start worker thread where we can run our tasks(ie. loading archives)
        Task.startWorkerThread()
        self.session.openWithCallback(self.close_archive_screen, ArchivCZSKContentScreen, self)

    def close_archive_screen(self):
        if not config.plugins.archivCZSK.preload.getValue():
            self.__addons.clear()
            self.__repositories.clear()
            ArchivCZSK.__loaded = False

        self.__console = None
        # We dont need worker thread anymore so we stop it
        Task.stopWorkerThread()

        # finally save all cfg changes - edit by shamman
        configfile.save()

        # clear tmp content by shamman
        filelist = [ f for f in os.listdir("/tmp") if f.endswith(".url") ]
        for f in filelist:
            try:
                os.remove(os.path.join('/tmp', f))
            except OSError:
                continue
        filelist = [ f for f in os.listdir("/tmp") if f.endswith(".png") ]
        for f in filelist:
            try:
                os.remove(os.path.join('/tmp', f))
            except OSError:
                continue
        shutil.rmtree("/tmp/archivCZSK", True)

        if config.plugins.archivCZSK.clearMemory.getValue():
            try:
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("1")
            except IOError as e:
                print 'cannot drop caches : %s' % str(e)
