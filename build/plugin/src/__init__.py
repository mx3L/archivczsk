# -*- coding: utf-8 -*-
import os, gettext, sys, datetime, traceback

from Components.Language import language
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE

from Plugins.Extensions.archivCZSK.engine.tools.logger import log, create_rotating_log, toString

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


class UpdateInfo(object):
    CHECK_UPDATE_TIMESTAMP = None
    CHECK_ADDON_UPDATE_TIMESTAMP = None

    @staticmethod
    def resetDates():
        UpdateInfo.CHECK_UPDATE_TIMESTAMP = None
        UpdateInfo.CHECK_ADDON_UPDATE_TIMESTAMP = None
