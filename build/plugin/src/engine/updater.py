'''
Created on 25.6.2012

@author: marko
'''
import os, shutil

from tools import unzip, util, parser
from Plugins.Extensions.archivCZSK.engine.exceptions.updater import UpdateXMLVersionError
from Plugins.Extensions.archivCZSK import log

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
        
        log.debug("checking updates for %s", addon.name)
        self._get_server_addon(addon, update_xml)
        
        broken = self.remote_addons_dict[addon.id]['broken']
        remote_version = self.remote_addons_dict[addon.id]['version']
        local_version = addon.version
        
        if util.check_version(local_version, remote_version):
            log.debug("%s local version %s < remote version %s", addon.name, local_version, remote_version)
            log.debug("%s is not up to date", addon.name)
            return True, broken
        else:
            log.debug("%s local version %s >= remote version %s", addon.name, local_version, remote_version)
            log.debug("%s is up to date", addon.name)
        return False, broken
          
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
        self._download_update_xml()
            
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

        try:
            util.download_to_file(remote_file, local_file, debugfnc=log.debug)
        except:
            shutil.rmtree(tmp_base)
            return None
        return local_file      
            
            
    def _download_update_xml(self):
        """downloads update xml of repository"""
        try:
            util.download_to_file(self.update_xml_url, self.update_xml_file, debugfnc=log.debug)
        except Exception:
            log.debug('cannot download %s update xml', self.repository.name)
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


