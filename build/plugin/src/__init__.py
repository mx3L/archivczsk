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


fileLogger = None

def create_rotating_log(path):
    try:
        import logging
        from logging.handlers import RotatingFileHandler
    except Exception:
        pass
    else:
        global fileLogger
        fileLogger = logging.getLogger("archivCZSK")
        handler = RotatingFileHandler(path, maxBytes=2 * 1024 * 1024,
                                    backupCount=2)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        fileLogger.setLevel(log.DEBUG)
        fileLogger.addHandler(handler)

class log(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO

    logEnabled = True
    logDebugEnabled = False

    @staticmethod
    def logDebug(msg, *args):
        if log.logDebugEnabled:
            log.writeLog('DEBUG', msg, *args)

    @staticmethod
    def debug(text, *args):
        log.logDebug(text, *args)

    @staticmethod
    def logInfo(msg, *args):
        log.writeLog('INFO', msg, *args)

    @staticmethod
    def info(text, *args):
        log.logInfo(text, args)

    @staticmethod
    def logError(msg, *args):
        log.writeLog('ERROR', msg, *args)

    @staticmethod
    def error(text, *args):
        log.logError(text, *args)

    @staticmethod
    def writeLog(type, msg, *args):
        try:
            if len(args) == 1 and isinstance(args[0], tuple):
                msg = msg % args[0]
            elif len(args) >= 1:
                msg = msg % args
            msg = toString(msg)

        except Exception as e:
            print "#####ArchivCZSK#### - cannot write log message:", str(e)
            traceback.print_exc()
            return

        if not log.logEnabled:
            return
        if fileLogger:
            if type == 'INFO':
                fileLogger.info(msg)
            elif type == 'ERROR':
                fileLogger.error(msg)
            elif type == 'DEBUG':
                fileLogger.debug(msg)
        else:
            print "####ArchivCZSK#### ["+type+"] "+ msg

    @staticmethod
    def changeMode(mode):
        log.mode = mode
        if mode == 2:
            log.logDebugEnabled = True
        else:
            log.logDebugEnabled = False

    @staticmethod
    def changePath(path):
        create_rotating_log(path + "/archivCZSK.log")