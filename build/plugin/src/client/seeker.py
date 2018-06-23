'''
Created on 11.1.2013

@author: marko
'''
#from Plugins.Plugin import PluginDescriptor

import traceback
from Screens.MessageBox import MessageBox   
from Plugins.Extensions.archivCZSK import _, log, removeDiac
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, showErrorMessage
from Components.config import config



def getCapabilities():
    """
    Vrati zoznam vsetkych moznosti vyhladavania: tuple(nazov_vyhladavania, id_doplnku, mod_vyhladavania)
    """
    list = []
    #list.append((_('Search in') + ' ' + 'OnlineFiles', 'plugin.video.online-files', 'all'))
    list.append((_('Search in') + ' ' + 'Stream Cinema', 'plugin.video.stream-cinema', 'all'))
    list.append((_('Search in') + ' ' + 'Sosac', 'plugin.video.sosac.ph', 'all'))
    list.append((_('Search in') + ' ' + 'CSFD', 'csfd', 'all'))
    #list.append((_('Search in') + ' ' + 'Befun.cz', 'plugin.video.befun.cz', 'all'))
    #list.append((_('Search in') + ' ' + 'Koukni.cz', 'plugin.video.koukni.cz', 'koukni.cz'))
    list.append((_('Search in') + ' ' + 'Webshare.cz', 'plugin.video.online-files', 'webshare.cz'))
    list.append((_('Search in') + ' ' + 'Ulozto.cz', 'plugin.video.online-files', 'ulozto.cz'))
    list.append((_('Search in') + ' ' + 'Bezvadata.cz', 'plugin.video.online-files', 'bezvadata.cz'))
    list.append((_('Search in') + ' ' + 'Hellspy.cz', 'plugin.video.online-files', 'hellspy.cz'))
    list.append((_('Search in') + ' ' + 'Fastshare.cz', 'plugin.video.online-files', 'fastshare.cz'))
    
    return list

#    Napriklad:
#   
#    search_exp = u'Matrix'
#    search(session, search_exp, 'plugin.video.online-files')
 
def search(session, search_exp, addon_id, mode=None, cb=None):
    """
    Vyhlada v archivCZSK hladany vyraz prostrednictvom addonu s addon_id s modom vyhladavania mode
    @param : session - aktivna session
    @param : search_exp - hladany vyraz
    @param : addon_id - id addonu v ktorom chceme vyhladavat
    @param : mode - mod vyhladavania podporovany addonom
    """
    try:
        if search_exp is None or search_exp == "":
            showInfoMessage(session, _("Empty search expression"))
            return cb()
    
        archivCZSKSeeker = ArchivCZSKSeeker.getInstance(session, cb)
        if archivCZSKSeeker is not None:
            archivCZSKSeeker.search(search_exp, addon_id, mode)
    except:
        log.logError("Searching failed.\n%s"%traceback.format_exc())
        showInfoMessage(session, _("Search fatal error."))
        return cb()
    
def searchClose():
    """
    Uvolni pamat po unkonceni prace s vyhladavacom
    """
    if ArchivCZSKSeeker.instance is not None:
        ArchivCZSKSeeker.instance.close()
        

def isArchivCZSKRunning(session):
    for dialog in session.dialog_stack:
        # csfd plugin sa da otvorit len z ContentScreen    
        if dialog.__class__.__name__ == 'ContentScreen':
            return True
    return False
    
def getArchivCZSK():
    from Plugins.Extensions.archivCZSK.archivczsk import ArchivCZSK
    from Plugins.Extensions.archivCZSK.engine.tools.task import Task

    if config.plugins.archivCZSK.showVideoInfo.getValue():
        from Plugins.Extensions.archivCZSK.gui.content import ArchivCZSKAddonContentScreenAdvanced
        return ArchivCZSK, ArchivCZSKAddonContentScreenAdvanced, Task
    else:
        from Plugins.Extensions.archivCZSK.gui.content import ArchivCZSKAddonContentScreen
        return ArchivCZSK, ArchivCZSKAddonContentScreen, Task

class ArchivCZSKSeeker():
    instance = None
    
    @staticmethod
    def getInstance(session, cb=None):
        if ArchivCZSKSeeker.instance is None:
            try:
                return ArchivCZSKSeeker(session, cb)
            except ImportError:
                log.logError("Cannot search, archivCZSK is not installed")
                showInfoMessage(session, _('Cannot search, archivCZSK is not installed'), 5, cb=cb)
                print 'cannot found archivCZSK'
                return None
            except Exception:
                log.logError("ArchivCZSKSeeker fatala error.\n%s"%traceback.format_exc())
                traceback.print_exc()
                showErrorMessage(session, _('unknown error'), 5, cb=cb)
                return None
        return ArchivCZSKSeeker.instance
    
    def __init__(self, session, cb=None):
        self.session = session
        self.cb = cb
        self.archivCZSK, self.contentScreen, self.task = getArchivCZSK() 
        self.searcher = None
        self.addon = None
        self.searching = False
        if not isArchivCZSKRunning(session):
            self.task.startWorkerThread()
        ArchivCZSKSeeker.instance = self
        
    def __repr__(self):
        return '[ArchivCZSKSeeker]'
            
    def _successSearch(self, content):
        (searchItems, command, args) = content
        self.session.openWithCallback(self._contentScreenCB, self.contentScreen, self.addon, searchItems)
        
        
    def _errorSearch(self, failure):
        showErrorMessage(self.session, _('Error while trying to retrieve search list'), 5)
        if self.searcher is not None:
            self.searcher.close()
            self.searcher = None
        self.searching = False
        self.addon = None
        if self.cb:
            self.cb()
        
    def _contentScreenCB(self, cp):
        if self.searcher is not None:
            self.searcher.close()
            self.searcher = None
        self.searching = False
        self.addon = None
        if self.cb:
            self.cb()        

        
    def search(self, search_exp, addon_id, mode=None):
        if self.searching:
            showInfoMessage(self.session, _("You cannot search, archivCZSK Search is already running"))
            print "%s cannot search, searching is not finished" % self
            return
        if addon_id.lower() == 'csfd':
            CsfdSearch().showCSFDInfo(self.session, search_exp)
            return self.cb()
        else:
            searcher = getSearcher(self.session, addon_id, self.archivCZSK, self._successSearch, self._errorSearch)
            if searcher is not None:
                self.searcher = searcher
                self.searching = True
                self.addon = searcher.addon
                searcher.start()
                searcher.search(search_exp, mode)
            else:
                showInfoMessage(self.session, _("Cannot find searcher") + ' ' + addon_id.encode('utf-8'))
                return self.cb()
            
    def close(self):
        if self.searching:
            print '%s cannot close, searching is not finished yet' % self
            return False
        if not isArchivCZSKRunning(self.session):
            self.task.stopWorkerThread()
        ArchivCZSKSeeker.instance = None
        return True
        
        
def getSearcher(session, addon_name, archivczsk, succ_cb, err_cb):
    if addon_name == 'plugin.video.online-files':
        return OnlineFilesSearch(session, archivczsk, succ_cb, err_cb)
    elif addon_name == 'plugin.video.befun.cz':
        return BefunSearch(session, archivczsk, succ_cb, err_cb)
    elif addon_name == 'plugin.video.koukni.cz':
        return KoukniSearch(session, archivczsk, succ_cb, err_cb)
    elif addon_name == 'plugin.video.sosac.ph':
        return SosacSearch(session, archivczsk, succ_cb, err_cb)
    elif addon_name == 'plugin.video.stream-cinema':
        return StreamCinemaSearch(session, archivczsk, succ_cb, err_cb)
    else:
        return None
            

class Search(object):
    def __init__(self, session, archivczsk, succ_cb, err_cb):
        self.session = session
        self.addon = archivczsk.get_addon(self.addon_id)
        self.provider = self.addon.provider
        self.succ_cb = succ_cb
        self.err_cb = err_cb
        
    def start(self):
        self.provider.start()
        
    def search(self, search_exp, mode=None):
        """search according to search_exp and choosen mode"""
        pass
    
    def close(self):
        """releases resources"""
        self.provider.stop()


class OnlineFilesSearch(Search):
    addon_id = 'plugin.video.online-files'
    
    def search(self, search_exp, mode='all'):
        if mode == 'all':
            self.search_all(search_exp)
        elif mode == 'bezvadata.cz':
            self.bezvadata_search(search_exp)
        elif mode == 'ulozto.cz':
            self.ulozto_search(search_exp)
        elif mode == 'hellspy.cz':
            self.hellspy_search(search_exp)
        elif mode == 'fastshare.cz':
            self.fastshare_search(search_exp)
        elif mode == 'webshare.cz':
            self.webshare_search(search_exp)
        else:
            self.search_all(search_exp)
    
    def search_all(self, search_exp):
        params = {'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)

    def ulozto_search(self, search_exp):
        params = {'cp':'ulozto.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)

    def bezvadata_search(self, search_exp):
        params = {'cp':'bezvadata.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb) 
 
    def hellspy_search(self, search_exp):
        params = {'cp':'hellspy.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
    def fastshare_search(self, search_exp):
        params = {'cp':'fastshare.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
    def webshare_search(self, search_exp):
        params = {'cp':'webshare.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
        
class BefunSearch(Search):
    addon_id = 'plugin.video.befun.cz'
    
    def search(self, search_exp, mode='all'):
        params = {'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)

class SosacSearch(Search):
    addon_id = 'plugin.video.sosac.ph'
    
    def search(self, search_exp, mode='all'):
        params = {'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
class KoukniSearch(Search):
    addon_id = 'plugin.video.koukni.cz'
    
    def search(self, search_exp, mode='all'):
        params = {'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
        
class StreamCinemaSearch(Search):
    addon_id = 'plugin.video.stream-cinema'
    
    def search(self, search_exp, mode='all'):
        params = {'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
class CsfdSearch():
    def showCSFDInfo(self, session, item):
        try:
            name = removeDiac(item.name)
            name = name.replace('.', ' ').replace('_', ' ').replace('*','')
        
            # remove languages ... "Mother - CZ, EN, KO (2017)"
            name = re.sub("\s-\s[A-Z]{2}(,\s[A-Z]{2})*\s\(", " (", name)
        
            year = 0
            yearStr = ""
            try:
                mask = re.compile('([0-9]{4})', re.DOTALL)
                yearStr = mask.findall(name)[0]
                year = int(yearStr)
            except:
                pass
            # remove year
            name = re.sub("\([0-9]{4}\)","", name)

            name = name.strip()
            log.logDebug("Csfd search '%s', year=%s."%(name,year))

            csfdType = int(config.plugins.archivCZSK.csfdMode.getValue())

            if csfdType == 1:
                from Plugins.Extensions.archivCZSK.gui.archivcsfd import ArchivCSFD
                session.open(ArchivCSFD, name, year)
            elif csfdType == 2:
                from Plugins.Extensions.CSFD.plugin import CSFD
                session.open(CSFD, name)
            elif csfdType == 3:
                from Plugins.Extensions.CSFDLite.plugin import CSFDLite
                try:
                    session.open(CSFDLite, name, yearStr)
                except:
                    log.logDebug("Trying CsfdLite older version compatibility...")
                    session.open(CSFDLite, name)
            else:
                raise Exception("CsfdMode '%s' not supported." % csfdType)
        except:
            log.logError("Show CSFD info failed (plugin may not be installed).\n%s"%traceback.format_exc())
            try:
                showInfoMessage(session, _("Show CSFD info failed."), timeout=6)
            except:
                pass

#def main(session, **kwargs):
#    search_exp = u'Matrix'
#    search(session, search_exp, 'plugin.video.online-files')

 
#def Plugins(**kwargs):
#    return [PluginDescriptor(name='Test_Plugin', description='', where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)]

