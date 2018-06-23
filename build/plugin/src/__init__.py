# -*- coding: utf-8 -*-
from Components.Language import language
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext, sys, datetime, traceback
#from logging import StreamHandler

PluginLanguageDomain = "archivCZSK"
PluginLanguagePath = "Extensions/archivCZSK/locale"

def localeInit():
    lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    print "[WebInterface] set language to ", lang
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        #print "[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt)
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)

def removeDiac(text):
    searchExp = text
    try:
        #log.logDebug("Remove diacritics is '%s'."%type(text))
        if isinstance(searchExp, str):
            #log.logDebug("Remove diacritics is str, do nothing return '%s'."%searchExp)
            return searchExp
        import unicodedata
        #searchExp = ''.join((c for c in unicodedata.normalize('NFD', unicode(searchExp, 'utf-8', 'ignore')) 
        #                              if unicodedata.category(c) != 'Mn')).encode('utf-8')
        searchExp = ''.join((c for c in unicodedata.normalize('NFD', searchExp) 
                                    if unicodedata.category(c) != 'Mn')).encode('utf-8')
    except:
        log.logError("Remove diacritics '%s' failed.\n%s"%(text,traceback.format_exc()))
        
    return searchExp

def toString(text):
    if isinstance(text, unicode):
        return text.encode('utf-8')
    elif isinstance(text, str):
        return text

class UpdateInfo(object):
    CHECK_UPDATE_TIMESTAMP = None
    CHECK_ADDON_UPDATE_TIMESTAMP = None

    @staticmethod
    def resetDates():
        UpdateInfo.CHECK_UPDATE_TIMESTAMP = None
        UpdateInfo.CHECK_ADDON_UPDATE_TIMESTAMP = None

class log(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False
    LOG_FILE = ""
    

    @staticmethod
    def logDebug(msg):
        if log.logDebugEnabled:
            log.writeLog(msg, 'DEBUG')
    @staticmethod
    def logInfo(msg):
        log.writeLog(msg, 'INFO')
    @staticmethod
    def logError(msg):
        log.writeLog(msg, 'ERROR')
    @staticmethod
    def writeLog(msg, type):
        try:
            if not log.logEnabled:
                return
            #if log.LOG_FILE=="":
            log.LOG_FILE = os.path.join(config.plugins.archivCZSK.logPath.getValue(),'archivCZSK.log')
            f = open(log.LOG_FILE, 'a')
            dtn = datetime.datetime.now()
            f.write(dtn.strftime("%H:%M:%S.%f")[:-3] +" ["+type+"] %s\n" % msg)
            f.close()
        except:
            log.error("write log failed.")
            pass
        finally:
            print "####ArchivCZSK#### ["+type+"] "+msg

    @staticmethod
    def changeMode(mode):
        log.mode = mode
        if mode == 2:
            log.logDebugEnabled = True
        else:
            log.logDebugEnabled = False

    @staticmethod
    def debug(text, *args):
        try:
            if log.mode == log.DEBUG:
                if len(args) == 1 and isinstance(args[0], tuple):
                    text = text % args[0]
                elif len(args) >=1:
                    text = text % args
                print "[ArchivCZSK] DEBUG:".ljust(20), toString(text)
        except:
            pass

    @staticmethod
    def info(text, *args):
        try:
            if log.mode >= log.INFO:
                if len(args) == 1 and isinstance(args[0], tuple):
                    text = text % args[0]
                elif len(args) >=1:
                    text = text % args
                print "[ArchivCZSK] INFO:".ljust(20), toString(text)
        except:
            pass

    @staticmethod
    def error(text, *args):
        try:
            if log.mode >= log.ERROR:
                if len(args) == 1 and isinstance(args[0], tuple):
                    text = text % args[0]
                elif len(args) >=1:
                    text = text % args
                print "[ArchivCZSK] ERROR:".ljust(20), toString(text)
        except:
            pass



# set logger
#default_formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
#console_handler = StreamHandler()
#console_handler.setFormatter(default_formatter)
#root = logging.getLogger(__name__)
#root.addHandler(console_handler)
#root.setLevel(logging.DEBUG)
