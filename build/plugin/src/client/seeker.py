'''
Created on 11.1.2013

@author: marko
'''
#from Plugins.Plugin import PluginDescriptor

import traceback
from Screens.MessageBox import MessageBox   
from Plugins.Extensions.archivCZSK import _ 
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, showErrorMessage



def getCapabilities():
    """
    Vrati zoznam vsetkych moznosti vyhladavania: tuple(nazov_vyhladavania, id_doplnku, mod_vyhladavania)
    """
    list = []
    #list.append((_('Search in') + ' ' + 'OnlineFiles', 'plugin.video.online-files', 'all'))
    list.append((_('Search in') + ' ' + 'Befun.cz', 'plugin.video.befun.cz', 'all'))
    list.append((_('Search in') + ' ' + 'Ulozto.cz', 'plugin.video.online-files', 'ulozto.cz'))
    list.append((_('Search in') + ' ' + 'Bezvadata.cz', 'plugin.video.online-files', 'bezvadata.cz'))
    list.append((_('Search in') + ' ' + 'Hellspy.cz', 'plugin.video.online-files', 'hellspy.cz'))
    list.append((_('Search in') + ' ' + 'Fastshare.cz', 'plugin.video.online-files', 'fastshare.cz'))
    list.append((_('Search in') + ' ' + 'Webshare.cz', 'plugin.video.online-files', 'webshare.cz'))
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
    if search_exp is None or search_exp == "":
        showInfoMessage(session, _("Empty search expression"))
        return cb()
    
    archivCZSKSeeker = ArchivCZSKSeeker.getInstance(session, cb)
    if archivCZSKSeeker is not None:
        archivCZSKSeeker.search(search_exp, addon_id, mode)
    
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
    from Plugins.Extensions.archivCZSK.gui.content import ContentScreen
    from Plugins.Extensions.archivCZSK.engine.tools.task import Task
    return ArchivCZSK, ContentScreen, Task

class ArchivCZSKSeeker():
    instance = None
    
    @staticmethod
    def getInstance(session, cb=None):
        if ArchivCZSKSeeker.instance is None:
            try:
                return ArchivCZSKSeeker(session, cb)
            except ImportError:
                showInfoMessage(session, _('Cannot search, archivCZSK is not installed'), 5, cb=cb)
                print 'cannot found archivCZSK'
                return None
            except Exception:
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
        searcher = getSearcher(self.session, addon_id, self.archivCZSK, self._successSearch, self._errorSearch)
        if searcher is not None:
            self.searcher = searcher
            self.searching = True
            self.addon = searcher.addon
            searcher.start()
            searcher.search(search_exp, mode)
        else:
            showInfoMessage(self.session, _("Cannot find searcher") + ' ' + addon_id.encode('utf-8'))
            
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
        params = {'cp':'fasthshare.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
    def webshare_search(self, search_exp):
        params = {'cp':'webshshare.cz', 'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
        
class BefunSearch(Search):
    addon_id = 'plugin.video.befun.cz'
    
    def search(self, search_exp, mode='all'):
        params = {'search':search_exp, 'search-no-history':True}
        self.provider.get_content(self.session, params, self.succ_cb, self.err_cb)
        
        


#def main(session, **kwargs):
#    search_exp = u'Matrix'
#    search(session, search_exp, 'plugin.video.online-files')

 
#def Plugins(**kwargs):
#    return [PluginDescriptor(name='Test_Plugin', description='', where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main)]

