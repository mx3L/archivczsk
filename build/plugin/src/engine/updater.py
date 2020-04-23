'''
Created on 25.6.2012
Updated on 28.10.2017 by chaoss

@author: marko
'''

import os
import shutil
import traceback
import threading
from tools import unzip, util, parser

from Plugins.Extensions.archivCZSK.engine.exceptions.updater import UpdateXMLVersionError
from Plugins.Extensions.archivCZSK import _, log, toString, settings
from Components.Console import Console
from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo
from Screens.MessageBox import MessageBox

def removePyOC(pyfile):
    if os.path.isfile(pyfile + 'c'):
        log.debug('removing %s', (pyfile + 'c'))
        os.remove(pyfile + 'c')
    elif os.path.isfile(pyfile + 'o'):
        log.debug('removing %s', (pyfile + 'o'))
        os.remove(pyfile + 'o')

def removeFiles(files):
    for f in files:
        if os.path.isfile(f):
            os.remove(f) 

class ArchivUpdater(object):
    def __init__(self, archivInstance):
        self.archiv = archivInstance
        self.tmpPath = config.plugins.archivCZSK.tmpPath.value
        if not self.tmpPath:
            self.tmpPath = "/tmp"
        self.tmpPath = "/tmp"
        self.__console = None
        self.remote_version=""
        self.commitValue=""
        self.commitFilePath = ""
        self.updateXmlFilePath = ""
        self.updateZipFilePath = ""
        self.BackupCreate = False
        self.backupDir = os.path.join(self.tmpPath, "archivCZSK_backup")
        self.updateXml = "http://cdn.rawgit.com/mx3L/archivczsk/{commit}/build/plugin/update/app.xml"
        self.updateZip = "http://cdn.rawgit.com/mx3L/archivczsk/{commit}/build/plugin/update/version/archivczsk-{version}.zip"
        self.commit = "https://raw.githubusercontent.com/mx3L/archivczsk/master/build/plugin/update/commit"
        self.needUpdate = False
        self.migration = {}
    
    def checkUpdate(self):
        self.downloadCommit()


    def downloadCommit(self):
        try:
            self.commitFilePath = os.path.join(os.path.dirname(self.tmpPath), 'archivczsk.commit')
            if os.path.exists(self.commitFilePath):
                os.remove(self.commitFilePath)
            self.__console = Console()
            self.__console.ePopen('curl -kfo %s %s' % (self.commitFilePath, self.commit), self.checkCommit)
        except:
            log.logError("ArchivUpdater download commit failed.\n%s"%traceback.format_exc())
            raise

    def checkCommit(self, data, retval, extra_args):
        try:
            if retval == 0 and os.path.exists(self.commitFilePath):
                self.doWork()
            else:
                log.logError("ArchivUpdater check commit failed. %s ### retval=%s"%(data, retval))
                self.continueToArchiv()
        except:
            log.logError("ArchivUpdater check commit failed.\n%s"%traceback.format_exc())
            self.continueToArchiv()
    
    def downloadUpdateXml(self):
        try:
            self.commitValue = open(self.commitFilePath).readline()[:-1]
        except Exception:
            log.logError("ArchivUpdater get commit value from file failed.\n%s"%traceback.format_exc())
            return False

        try:
            self.updateXml = self.updateXml.replace('{commit}', self.commitValue)
            self.updateXmlFilePath = os.path.join(os.path.dirname(self.tmpPath), 'archivczskupdate.xml')
            util.download_to_file(self.updateXml, self.updateXmlFilePath)
            return True
        except Exception:
            log.logError("ArchivUpdater download archiv update xml failed.\n%s"%traceback.format_exc())
            return False
    def downloadZip(self):
        try:
            self.updateZip = self.updateZip.replace('{commit}', self.commitValue)
            self.updateZip = self.updateZip.replace('{version}', self.remote_version)
            self.updateZipFilePath = os.path.join(os.path.dirname(self.tmpPath), 'archivczskupdate.zip')
            log.logDebug("ArchivUpdater downloading zip %s"%self.updateZip)
            util.download_to_file(self.updateZip, self.updateZipFilePath)
        except Exception:
            log.logError("ArchivUpdater download update zip failed.\n%s"%traceback.format_exc())
            raise
    def removeArchivTree(self):
        try:
            pth = settings.PLUGIN_PATH
            for i in os.listdir(pth):
                fullPath1 = os.path.join(pth,i)
                tmp = i.lower()
                if tmp=="categories.xml":
                    log.logDebug("File '%s' skipped."%i)
                    continue
                if i=="resources":
                    for sub in os.listdir(fullPath1):
                        fullPath2 = os.path.join(fullPath1,sub)
                        if sub.lower()=="data":
                            log.logDebug("Dir '%s' skipped."%sub)
                            continue
                        if sub.lower()=="repositories":
                            for sub2 in os.listdir(fullPath2):
                                fullPath3 = os.path.join(fullPath2, sub2)
                                if os.path.isdir(fullPath3):
                                    # remove addon.xml only
                                    addonXml = os.path.join(fullPath3, "addon.xml")
                                    log.logDebug("addon xml path %s" % addonXml)
                                    if os.path.isfile(addonXml):
                                        os.remove(addonXml)
                                        log.logDebug("File '%s' removed" % addonXml[-30:])
                                elif os.path.isfile(fullPath3):
                                    os.remove(fullPath3)
                                    log.logDebug("File '%s' removed" % sub2)
                            # repositories dir skipped partialy
                            continue
                        if os.path.isdir(fullPath2):
                            shutil.rmtree(fullPath2)
                            log.logDebug("Dir tree '%s' removed" % sub)
                        elif os.path.isfile(fullPath2):
                            os.remove(fullPath2)
                            log.logDebug("File '%s' removed" % sub)
                    # resources dir partialy skipped
                    continue
                if i=='gui':
                    for sub in os.listdir(fullPath1):
                        fullPath2 = os.path.join(fullPath1,sub)
                        if sub.lower()=="skins":
                            for sub2 in os.listdir(fullPath2):
                                fullPath3 = os.path.join(fullPath2, sub2)
                                if os.path.isfile(fullPath3) and sub2.startswith("default_"):
                                    os.remove(fullPath3)
                                    log.logDebug("File '%s' removed" % sub2)
                            # skins dir skipped partialy
                            continue
                        if os.path.isdir(fullPath2):
                            shutil.rmtree(fullPath2)
                            log.logDebug("Dir tree '%s' removed" % sub)
                        elif os.path.isfile(fullPath2):
                            os.remove(fullPath2)
                            log.logDebug("File '%s' removed" % sub)
                    continue

                if os.path.isdir(fullPath1):
                    shutil.rmtree(fullPath1)
                    log.logDebug("Dir tree '%s' removed" % i)
                elif os.path.isfile(fullPath1):
                    os.remove(fullPath1)
                    log.logDebug("File '%s' removed" % i)
        except:
            log.logError("ArchivUpdater remove archivCZSK tree failed.\n%s"% traceback.format_exc())
            raise
    
    def backupOrRevertUpdate(self, backup):
        try:
            # symlinks not working
            archivDir = settings.PLUGIN_PATH
            if backup:
                log.logDebug("ArchivUpdater creating backup before update...")
                #backup archiv
                if os.path.isdir(self.backupDir):
                    os.rmdir(self.backupDir)
                shutil.copytree(archivDir, self.backupDir)
            else:
                log.logDebug("ArchivUpdater rverting changes after unsuccessfull update...")
                #revert archiv from backup
                shutil.rmtree(archivDir)
                shutil.copytree(self.backupDir, archivDir)
        except:
            if backup:
                log.logError("ArchivUpdater backup before unzip failed.\n%s"%traceback.format_exc())
            else:
                log.logError("ArchivUpdater revert after unsuccessfull unzip failed.\n%s"%traceback.format_exc())
            raise Exception("Bacup/Revert archivCZSK failed.")

    def updateFailed(self, callback=None):
        self.continueToArchiv()
        
    def updateArchiv(self, callback=None, verbose=True):
        try:
            if not callback:
                log.logDebug("ArchivUpdater update canceled.")
                self.continueToArchiv()
            else:
                # copy files
                self.downloadZip()
                log.logDebug("ArchivUpdater download zip archivCZSK complete...")
                # remove tree
                self.backupOrRevertUpdate(True)
                self.BackupCreate = True
                self.removeArchivTree()
                # maybe zipper replace the file 
                log.logDebug("ArchivUpdater remove archivCZSK files complete...")
                # unzip
                unzipper = unzip.unzip()
                #.../Plugins/Extensions/
                log.logDebug("ArchivUpdater extracting to %s" % settings.ENIGMA_PLUGIN_PATH)
                unzipper.extract(self.updateZipFilePath, settings.ENIGMA_PLUGIN_PATH)
                log.logDebug("ArchivUpdater unzip archivCZSK complete...")
                self.removeTempFiles()

                # restart enigma
                strMsg = "%s" % _("Update archivCZSK complete.")
                self.archiv.session.openWithCallback(self.archiv.ask_restart_e2,
                        MessageBox,
                        strMsg,
                        type=MessageBox.TYPE_INFO)
        except:
            strMsg = "%s" % _("Update archivCZSK failed.")
            try:
                if self.BackupCreate:
                    self.backupOrRevertUpdate(False)
            except:
                strMsg = strMsg + "\n\nFATAL ERROR\n\n"+_("Please revert archivCZSK manualy from following location before restart!!!")+"\n\n"+toString(self.backupDir)
                pass
            log.logError("ArchivUpdater update archivCZSK from zip failed.\n%s"%traceback.format_exc())
            
            self.archiv.session.openWithCallback(self.updateFailed,
                    MessageBox,
                    strMsg,
                    type=MessageBox.TYPE_INFO)
            pass

    def doWork(self):
        try:
            def check_archiv():
                try:
                    if self.downloadUpdateXml():
                        from Plugins.Extensions.archivCZSK.version import version
                        local_version = version
                        xmlroot = util.load_xml(self.updateXmlFilePath).getroot()
                        self.remote_version = xmlroot.attrib.get('version')
                        log.logDebug("ArchivUpdater version local/remote: %s/%s" % (local_version, self.remote_version))

                        if util.check_version(local_version, self.remote_version):
                            self.needUpdate = True
                        else:
                            self.needUpdate = False
                    else:
                        self.needUpdate = False
                except:
                    log.logError("ArchivUpdater compare versions failed.\n%s"%traceback.format_exc())

            check_archiv()
            #thread = threading.Thread(target=check_archiv)
            #thread.start()
            #thread.join()

            if self.needUpdate:
                log.logInfo("ArchivUpdater update found...%s"%self.remote_version)
                strMsg = "%s %s?" %(_("Do you want to update archivCZSK to version"), toString(self.remote_version))
                self.archiv.session.openWithCallback(
                    self.updateArchiv,
                    MessageBox,
                    strMsg,
                    type = MessageBox.TYPE_YESNO)
            else:
                self.continueToArchiv()
        except:
            log.logError("ArchivUpdater update failed.\n%s"%traceback.format_exc())
            self.continueToArchiv()

    def continueToArchiv(self):
        self.removeTempFiles()
        if config.plugins.archivCZSK.autoUpdate.value and self.archiv.canCheckUpdate(False):
            # check plugin updates
            self.archiv.download_commit()
        else:
            self.archiv.open_archive_screen()

    def removeTempFiles(self):
        try:
            if os.path.isfile(self.commitFilePath):
                os.remove(self.commitFilePath)
            if os.path.isfile(self.updateXmlFilePath):
                os.remove(self.updateXmlFilePath)
            if os.path.isfile(self.updateZipFilePath):
                os.remove(self.updateZipFilePath)
            if os.path.isdir(self.backupDir):
                shutil.rmtree(self.backupDir)
        except:
            log.logError("ArchivUpdater remove temp files failed.\n%s"%traceback.format_exc())
            pass

    def getSetting(self, addonId, setting_key):
        try:
            setattr(config.plugins.archivCZSK.archives, addonId, ConfigSubsection())
            main = getattr(config.plugins.archivCZSK.archives, addonId)
            setattr(main, '%s' % setting_key, ConfigText(default=''))
            setting = getattr(main, '%s' % setting_key)
            return setting.getValue()
        except:
            log.logError("Get setting '%s.%s' failed.%s"%(addonId, setting_key, traceback.format_exc()))
    def saveSetting(self, addonId, setting_key, val, firstTime=False):
        try:
            
            if firstTime:
                setattr(config.plugins, 'archivCZSKpremium', ConfigSubsection())
                root1 = getattr(config.plugins, 'archivCZSKpremium')
                setattr(root1, 'archives', ConfigSubsection())
                root = getattr(root1, 'archives')
                setattr(root, '%s'%addonId, ConfigSubsection())
                main = getattr(root, '%s'%addonId)
            else:
                if addonId not in self.migration.keys():
                    setattr(config.plugins.archivCZSKpremium.archives, '%s'%addonId, ConfigSubsection())
                    main = getattr(config.plugins.archivCZSKpremium.archives, '%s'%addonId)
                else:
                    main = getattr(config.plugins.archivCZSKpremium.archives, '%s'%addonId)

            if addonId not in self.migration.keys():
                self.migration[addonId]=1

            setattr(main, '%s'%setting_key, ConfigText(default='', fixed_size=False))
            sett = getattr(main, '%s'%setting_key)
            sett.setValue(val)
            sett.save()
        except:
            log.logError("Save setting '%s.%s' failed.%s"%(addonId, setting_key, traceback.format_exc()))
    def getSettingArchiv(self, setting_key):
        try:
            setattr(config.plugins.archivCZSK, '%s' % setting_key, ConfigText(default=''))
            setting = getattr(config.plugins.archivCZSK, '%s' % setting_key)
            return setting.getValue()
        except:
            log.logError("Get setting '%s' failed.%s"%(setting_key, traceback.format_exc()))
    def saveSettingArchiv(self, setting_key, val):
        try:
            setattr(config.plugins.archivCZSKpremium, '%s'%setting_key, ConfigText(default='', fixed_size=False))
            sett = getattr(config.plugins.archivCZSKpremium, '%s'%setting_key)
            sett.setValue(val)
            sett.save()
        except:
            log.logError("Save setting '%s' failed.%s"%(setting_key, traceback.format_exc()))

    def updatePremium(self, callback=None):
        try:
            #download ZIP
            util.download_to_file('https://raw.githubusercontent.com/mtester270/archivczskpremium/master/archiv.zip', '/tmp/archivpremium.zip')
            #unpack
            unzipper = unzip.unzip()
            exDir = '/tmp/archivpremiumuzip'
            if os.path.isdir(exDir):
                shutil.rmtree(exDir)
            os.mkdir(exDir)
            unzipper.extract('/tmp/archivpremium.zip', exDir)
            os.remove('/tmp/archivpremium.zip')
            #copy
            shutil.copytree(os.path.join(exDir, 'archivCZSKpremium'), os.path.join(settings.ENIGMA_PLUGIN_PATH, 'archivCZSKpremium'))
            pthsite =os.path.join(exDir, 'site-packages')
            for i in os.listdir(pthsite):
                sitepck = os.path.join(pthsite,i)
                cpDir = os.path.join('/usr/lib/python2.7/site-packages', i)
                if not os.path.isdir(cpDir):
                    log.logDebug("UpdatePremium: add site-pckage %s"%i)
                    shutil.copytree(sitepck, cpDir)
                else:
                    log.logDebug("UpdatePremium: site-pckage %s already installed"%i)
            shutil.rmtree(exDir)


            #some custom setting
            val = self.getSetting('plugin_video_sosac_ph', 'streamujtv_user')
            self.saveSetting('plugin_video_sosac_ph', 'streamujtv_user', val, True)
            val = self.getSetting('plugin_video_sosac_ph', 'streamujtv_pass')
            self.saveSetting('plugin_video_sosac_ph', 'streamujtv_pass', val)
            val = self.getSetting('plugin_video_sosac_ph', 'auto_addon_order')
            self.saveSetting('plugin_video_sosac_ph', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_orangetv', 'orangetvuser')
            self.saveSetting('plugin_video_orangetv', 'orangetvuser', val)
            val = self.getSetting('plugin_video_orangetv', 'orangetvpwd')
            self.saveSetting('plugin_video_orangetv', 'orangetvpwd', val)
            val = self.getSetting('plugin_video_orangetv', 'auto_addon_order')
            self.saveSetting('plugin_video_orangetv', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_stream-cinema', 'wsuser')
            self.saveSetting('plugin_video_stream-cinema', 'wsuser', val)
            val = self.getSetting('plugin_video_stream-cinema', 'wspass')
            self.saveSetting('plugin_video_stream-cinema', 'wspass', val)
            val = self.getSetting('plugin_video_stream-cinema', 'trakt_enabled')
            self.saveSetting('plugin_video_stream-cinema', 'trakt_enabled', val)
            val = self.getSetting('plugin_video_stream-cinema', 'deviceid')
            self.saveSetting('plugin_video_stream-cinema', 'deviceid', val)
            val = self.getSetting('plugin_video_stream-cinema', 'trakt_filter')
            self.saveSetting('plugin_video_stream-cinema', 'trakt_filter', val)
            val = self.getSetting('plugin_video_stream-cinema', 'trakt_token')
            self.saveSetting('plugin_video_stream-cinema', 'trakt_token', val)
            val = self.getSetting('plugin_video_stream-cinema', 'trakt_refresh_token')
            self.saveSetting('plugin_video_stream-cinema', 'trakt_refresh_token', val)
            val = self.getSetting('plugin_video_stream-cinema', 'trakt_token_expire')
            self.saveSetting('plugin_video_stream-cinema', 'trakt_token_expire', val)
            val = self.getSetting('plugin_video_stream-cinema', 'use_https')
            self.saveSetting('plugin_video_stream-cinema', 'use_https', val)
            val = self.getSetting('plugin_video_stream-cinema', 'auto_addon_order')
            self.saveSetting('plugin_video_stream-cinema', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_o2tv', 'o2tvuser')
            self.saveSetting('plugin_video_o2tv', 'o2tvuser', val)
            val = self.getSetting('plugin_video_o2tv', 'o2tvpwd')
            self.saveSetting('plugin_video_o2tv', 'o2tvpwd', val)
            val = self.getSetting('plugin_video_o2tv', 'login_method')
            self.saveSetting('plugin_video_o2tv', 'login_method', val)
            val = self.getSetting('plugin_video_o2tv', 'deviceid')
            self.saveSetting('plugin_video_o2tv', 'deviceid', val)
            val = self.getSetting('plugin_video_o2tv', 'auto_addon_order')
            self.saveSetting('plugin_video_o2tv', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_online-files', 'webshare_enabled')
            self.saveSetting('plugin_video_online-files', 'webshare_enabled', val)
            val = self.getSetting('plugin_video_online-files', 'webshare_user')
            self.saveSetting('plugin_video_online-files', 'webshare_user', val)
            val = self.getSetting('plugin_video_online-files', 'webshare_pass')
            self.saveSetting('plugin_video_online-files', 'webshare_pass', val)
            val = self.getSetting('plugin_video_online-files', 'auto_addon_order')
            self.saveSetting('plugin_video_online-files', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_markiza_sk', 'auto_addon_order')
            self.saveSetting('plugin_video_markiza_sk', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_joj_sk', 'auto_addon_order')
            self.saveSetting('plugin_video_joj_sk', 'auto_addon_order', val)
            val = self.getSetting('plugin_video_rtvs_sk', 'auto_addon_order')
            self.saveSetting('plugin_video_rtvs_sk', 'auto_addon_order', val)

            self.saveSettingArchiv('skin', self.getSettingArchiv('skin'))
            self.saveSettingArchiv('showVideoInfo', self.getSettingArchiv('showVideoInfo'))
            self.saveSettingArchiv('downloadPoster', self.getSettingArchiv('downloadPoster'))
            self.saveSettingArchiv('posterImageMax', self.getSettingArchiv('posterImageMax'))
            self.saveSettingArchiv('csfdMode', self.getSettingArchiv('csfdMode'))
            self.saveSettingArchiv('downloadsPath', self.getSettingArchiv('downloadsPath'))
            self.saveSettingArchiv('posterPath', self.getSettingArchiv('posterPath'))
            self.saveSettingArchiv('tmpPath', self.getSettingArchiv('tmpPath'))
            self.saveSettingArchiv('defaultCategory', self.getSettingArchiv('defaultCategory'))
            self.saveSettingArchiv('clearMemory', self.getSettingArchiv('clearMemory'))
            
            
            # save settings
            bcpPath = '/tmp/oldarchivBackup'
            pth = settings.PLUGIN_PATH
            if os.path.isdir(bcpPath):
                shutil.rmtree(bcpPath)
            os.mkdir(bcpPath)
            os.mkdir(os.path.join(bcpPath,'resources'))
            osr = os.path.join(pth, 'osref.pyo')
            if os.path.isfile(osr):
                shutil.copyfile(osr, os.path.join(bcpPath, 'osref.pyo'))
            shutil.copyfile(os.path.join(pth, 'categories.xml'),os.path.join(bcpPath, 'categories.xml'))
            if os.path.isdir(os.path.join(pth,'resources')):
                try:
                    from distutils import dir_util
                    dir_util.copy_tree(os.path.join(pth,'resources','data'),os.path.join(bcpPath,'resources','data')) 
                except:
                    log.logError("Restore archiv data failed. %s"%traceback.format_exc())

            # remove old archivCZSK
            if callback:
                shutil.rmtree(pth)
        
            
            #restore
            if os.path.isfile(os.path.join(bcpPath, 'osref.pyo')):
                shutil.copy(os.path.join(bcpPath, 'osref.pyo'), os.path.join(settings.ENIGMA_PLUGIN_PATH,'archivCZSKpremium'))
            shutil.copy(os.path.join(bcpPath, 'categories.xml'), os.path.join(settings.ENIGMA_PLUGIN_PATH,'archivCZSKpremium'))
            if os.path.exists(os.path.join(bcpPath,'resources','data')):
                try:
                    from distutils import dir_util
                    dir_util.copy_tree(os.path.join(bcpPath,'resources','data'), os.path.join(settings.ENIGMA_PLUGIN_PATH,'archivCZSKpremium','resources','data'))
                except:
                    log.logError("Restore archiv data failed. %s"%traceback.format_exc())
            shutil.rmtree(bcpPath)

            strMsg = "%s" % _("Install ArchivCZSK premium complete.")
            self.archiv.session.openWithCallback(self.archiv.ask_restart_e2,
                    MessageBox,
                    strMsg,
                    type=MessageBox.TYPE_INFO)
        except:
            log.logDebug("UpdatePremium failed.\n%s"%traceback.format_exc())
            self.downloadCommit()

class Updater(object):
    """Updater for updating addons in repository, every repository has its own updater"""
    
    def __init__(self, repository, tmp_path):
        self.repository = repository
        self.remote_path = repository.update_datadir_url
        self.local_path = repository.path
        self.tmp_path = tmp_path
        self.update_xml_url = repository.update_xml_url
        self.update_xml_file = os.path.join(self.tmp_path, 'addons.xml')
        self.remote_addons_dict = {}
    
    def check_addon(self, addon, update_xml=True):
        """
        check if addon needs update and if its broken
        """
        try:
            log.debug("checking updates for %s", addon.name)
            self._get_server_addon(addon, update_xml)
        
            broken = self.remote_addons_dict[addon.id]['broken']
            remote_version = self.remote_addons_dict[addon.id]['version']
            local_version = addon.version
        
            if util.check_version(local_version, remote_version):
                log.logDebug("Addon '%s' need update (local %s < remote %s)." % (addon.name, local_version, remote_version))
                log.debug("%s local version %s < remote version %s", addon.name, local_version, remote_version)
                log.debug("%s is not up to date", addon.name)
                return True, broken
            else:
                log.logDebug("Addon '%s' (%s) is up to date." % (addon.name, local_version))
                log.debug("%s local version %s >= remote version %s", addon.name, local_version, remote_version)
                log.debug("%s is up to date", addon.name)
            return False, broken
        except:
            log.logError("Check addon '%s' update failed.\n%s" % (addon.name, traceback.format_exc()))
            raise
          
    def update_addon(self, addon):
        """updates addon"""
        
        log.debug("updating %s", addon.name)
        self._get_server_addon(addon)
    
        local_base = os.path.join(self.local_path, addon.id)        
        zip_file = self._download(addon)
        
        if zip_file is not None and os.path.isfile(zip_file):
            if os.path.isdir(local_base):
                shutil.rmtree(local_base)
            
            unzipper = unzip.unzip()
            unzipper.extract(zip_file, self.local_path)
            
            log.debug("%s was successfully updated to version %s", addon.name, self.remote_addons_dict[addon.id]['version'])
            return True
        log.debug("%s failed to update to version %s", addon.name, addon.version)
        return False
    
    
    def check_addons(self, new=True):
        """checks every addon in repository, and update its state accordingly"""
        log.debug('checking addons')
        update_needed = []
        self._get_server_addons()
        for addon_id in self.remote_addons_dict.keys():
            remote_addon = self.remote_addons_dict[addon_id]
            if remote_addon['id'] in self.repository._addons:
                local_addon = self.repository.get_addon(addon_id)
                if local_addon.check_update(False):
                    update_needed.append(local_addon)
            elif new:
                log.debug("%s not in local repository, adding dummy Addon to update", remote_addon['name'])
                log.logDebug("'%s' not in local repository, adding Addon to update"%remote_addon['name'])
                new_addon = DummyAddon(self.repository, remote_addon['id'], remote_addon['name'], remote_addon['version'])
                update_needed.append(new_addon)
            else:
                log.debug("dont want new addons skipping %s", remote_addon['id'])
        return update_needed        
            
            
    def update_addons(self, addons):
        """update addons in repository, according to their state"""
        log.debug('updating addons')
        update_success = []
        for addon in addons:
            if addon.need_update():
                if addon.update():
                    update_success.append(update_success)
        return update_success
                    
                
                
    def _get_server_addons(self):
        """loads info about addons from remote repository to remote_addons_dict"""
        log.logDebug("pre update xml")
        self._download_update_xml()
        log.logDebug("post update xml")
            
        pars = parser.XBMCMultiAddonXMLParser(self.update_xml_file)
        self.remote_addons_dict = pars.parse_addons()
            

    def _get_server_addon(self, addon, load_again=False):
        """load info about addon from remote repository"""
        
        if load_again:
            self._get_server_addons()
            
        if addon.id not in self.remote_addons_dict:
            pars = parser.XBMCMultiAddonXMLParser(self.update_xml_url)
            addon_el = pars.find_addon(addon.id)
            self.remote_addons_dict[addon.id] = pars.parse(addon_el)
        
    
    def _download(self, addon):
        """downloads addon zipfile to tmp"""
        zip_filename = "%s-%s.zip" % (addon.id, self.remote_addons_dict[addon.id]['version'])
        
        remote_base = self.remote_path + '/' + addon.id
        tmp_base = os.path.normpath(os.path.join(self.tmp_path, addon.relative_path))
        
        local_file = os.path.join(tmp_base, zip_filename)
        remote_file = remote_base + '/' + zip_filename
        if remote_file.find('{commit}') != -1:
            from Plugins.Extensions.archivCZSK.settings import PLUGIN_PATH
            try:
                commit = open(os.path.join(PLUGIN_PATH, 'commit')).readline()[:-1]
            except Exception:
                commit = '4ff9ac15d461a885f13125125ea501f3b12eb05d'
            remote_file = remote_file.replace('{commit}', commit)
        # hack for https github urls
        # since some receivers have have problems with https 
        if remote_file.find('https://raw.github.com') == 0:
            remote_file = remote_file.replace('https://raw.github.com', 'http://rawgithub.com')
        try:
            util.download_to_file(remote_file, local_file, debugfnc=log.debug)
        except:
            shutil.rmtree(tmp_base)
            return None
        return local_file      
            
            
    def _download_update_xml(self):
        """downloads update xml of repository"""
        
        # hack for https github urls
        # since some receivers have have problems with https
        if self.update_xml_url.find('{commit}') != -1:
            try:
                commit = open(os.path.join(settings.PLUGIN_PATH, 'commit')).readline()[:-1]
            except Exception:
                commit = '4ff9ac15d461a885f13125125ea501f3b12eb05d'
            self.update_xml_url = self.update_xml_url.replace('{commit}', commit)
        if self.update_xml_url.find('https://raw.github.com') == 0:
            update_xml_url = self.update_xml_url.replace('https://raw.github.com', 'http://rawgithub.com')
        else:
            update_xml_url = self.update_xml_url
        try:
            util.download_to_file(update_xml_url, self.update_xml_file)
        except Exception:
            log.error('cannot download %s update xml', self.repository.name)
            raise UpdateXMLVersionError()
        

class DummyAddon(object):
    """to add new addon to repository"""
    def __init__(self, repository, id, name, version):
        self.repository = repository
        self.name = name
        self.id = id
        self.relative_path = self.id
        self.version = version
        self.path = os.path.normpath(os.path.join(repository.path, self.relative_path))
        self.__need_update = True
        
    def need_update(self):
        return True
    
    def update(self):
        return self.repository._updater.update_addon(self)


