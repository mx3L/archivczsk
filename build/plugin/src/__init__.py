# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext, sys
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
        print "[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt)
        t = gettext.gettext(txt)
    return t
    
localeInit()
language.addCallback(localeInit)

class log(object):
    ERROR = 0
    INFO = 1
    DEBUG = 2
    mode = INFO
    
    @staticmethod
    def changeMode(mode):
        log.mode = mode
    
    @staticmethod
    def debug(text, *args):
        if log.mode == log.DEBUG:
            if len(args) == 1 and isinstance(args[0], tuple):
                text = text % args[0]
            elif len(args) >=1:
                text = text % args
            print "[ArchivCZSK] DEBUG:", text.encode('utf-8')
    
    @staticmethod    
    def info(text, *args):
        if log.mode >= log.INFO:
            if len(args) == 1 and isinstance(args[0], tuple):
                text = text % args[0]
            elif len(args) >=1:
                text = text % args
            print "[ArchivCZSK] INFO:", text.encode('utf-8') 
    
    @staticmethod  
    def error(text, *args):
        if log.mode >= log.ERROR:
            if len(args) == 1 and isinstance(args[0], tuple):
                text = text % args[0]
            elif len(args) >=1:
                text = text % args
            print "[ArchivCZSK] ERROR:", text.encode('utf-8')
  

# set logger
#default_formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
#console_handler = StreamHandler()
#console_handler.setFormatter(default_formatter)
#root = logging.getLogger(__name__)
#root.addHandler(console_handler)
#root.setLevel(logging.DEBUG)
