# -*- coding: UTF-8 -*-
#################################################################################
#
#    Subtitles library 0.53 for Enigma2
#    Coded by mx3L (c) 2014
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#################################################################################

from os import path as os_path, listdir
import os
from re import compile as re_compile
import re
import shutil
import urllib2
from threading import Thread
from Queue import Queue

from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import ConfigSubsection, ConfigSelection, ConfigYesNo, \
    configfile, getConfigListEntry, config, NoSave, ConfigText, ConfigDirectory
from Screens.LocationBox import LocationBox
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename
from Tools.ISO639 import LanguageCodes
from Tools.LoadPixmap import LoadPixmap

from enigma import RT_HALIGN_RIGHT, RT_VALIGN_TOP, eSize, ePoint, RT_HALIGN_LEFT, \
    RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListboxPythonMultiContent, \
    gFont, getDesktop, eServiceCenter, iServiceInformation, eServiceReference, \
    iSeekableService, iPlayableService, iPlayableServicePtr, eTimer, addFont, gFont, loadPNG, ePythonMessagePump
from skin import parseColor, parsePosition
try:
    from Screens.AudioSelection import QuickSubtitlesConfigMenu
except ImportError:
    QuickSubtitlesConfigMenu = None

from process import SubsLoader, DecodeError, ParseError, ParserNotFoundError, \
    LoadError

from seek import SubsSeeker, SubtitlesCaptchaError, SubtitlesDownloadError
from parsers import SrtParser
from utils import HeadRequest, which
from e2_utils import Task, getCaptcha, delay, messageCB, E2SettingsProvider, MyLanguageSelection, unrar

# localization function
from . import __

def warningMessage(session, text):
    session.open(MessageBox, text, type=MessageBox.TYPE_WARNING, timeout=5)

def debug(text, *args):
    if DEBUG:
        if len(args) == 1 and isinstance(args[0], tuple):
            text = text % args[0]
        else:
            text = text % (args)
        print "[SubsSupport]", text.encode('utf-8')


# set the name of plugin in which this library belongs
# PLUGIN_NAME = 'mediaplayer2'

# set debug mode
DEBUG = False

# set supported encodings, you have to make sure, that you have corresponding python
# libraries in %PYTHON_PATH%/encodings/ (ie. iso-8859-2 requires iso_8859_2.py library)

# to choose encodings for region you want, visit:
# http://docs.python.org/release/2.4.4/lib/standard-encodings.html

# Common encodings for all languages
ALL_LANGUAGES_ENCODINGS = ['utf-8', 'utf-16']

# other encodings
CENTRAL_EASTERN_EUROPE_ENCODINGS = ['windows-1250', 'iso-8859-2', 'maclatin2', 'IBM852']
WESTERN_EUROPE_ENCODINGS = ['windows-1252', 'iso-8859-15', 'macroman', 'ibm1140', 'IBM850']
RUSSIAN_ENCODINGS = ['windows-1251', 'cyrillic', 'maccyrillic', 'koi8_r', 'IBM866']
ARABIC_ENCODINGS = ['windows-1256', 'iso-8859-6', 'IBM864']
TURKISH_ENCODINGS= ['windows-1254', 'iso-8859-9', 'latin5', 'macturkish', 'ibm1026', 'IBM857']
GREEK_ENCODINGS = ['windows-1253', 'iso-8859-7', 'macgreek']

ENCODINGS = {__("Central and Eastern Europe") : CENTRAL_EASTERN_EUROPE_ENCODINGS,
             __("Western Europe"):WESTERN_EUROPE_ENCODINGS,
             __("Russia"):RUSSIAN_ENCODINGS,
             __("Arabic"): ARABIC_ENCODINGS,
             __("Turkish"):TURKISH_ENCODINGS,
             __("Greek"):GREEK_ENCODINGS}


# fontname-R: regular font - mandatory
# fontname-B: bold font - optional, if missing regular font will be used
# fontname-I: italic font - optional, if missing regular font will be used

E2_FONT_PATH = '/usr/share/fonts/'
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts")

# we use fonts from local path and enigma2 fonts path
FONTS_LOCAL = [(fontfile, FONT_PATH) for fontfile in os.listdir(FONT_PATH)]
FONTS_E2 = []  # [(fontfile, E2_FONT_PATH) for fontfile in os.listdir(E2_FONT_PATH)]
FONTS = FONTS_LOCAL + FONTS_E2

FONT = {
        "Default":
          {
            "regular":"Regular",
            "italic":"Regular",
            "bold":"Regular",
            "path":"Regular"
          }
        }

RE_FONT = '(.+?)\.ttf$'
RE_FONT_RIB = '(.+?)-(R|I|B)\.ttf$'


# looking for fonts in selected paths
for fontfile, path in FONTS:
    font = re.search(RE_FONT, fontfile)
    font_rib = re.search(RE_FONT_RIB, fontfile)

    if font_rib and (font_rib.group(1) in FONT):
        continue
    if font and (font.group(1) in FONT):
        continue

    if font_rib:
        fontname = font_rib.group(1)
        fonttype = font_rib.group(2)
        regular = fontname + '-R.ttf'
        italic = fontname + '-I.ttf'
        bold = fontname + '-B.ttf'

        if fonttype == 'R':
            FONT[fontname] = {}
            FONT[fontname]["path"] = path
            FONT[fontname]["regular"] = fontfile

            if (italic, path) in FONTS:
                FONT[fontname]["italic"] = italic
            else:
                print "[SubsSupport] missing %s font file" % italic
                FONT[fontname]["italic"] = fontfile
            if (bold, path) in FONTS:
                FONT[fontname]["bold"] = bold
            else:
                print "[SubsSupport] missing %s font file" % bold
                FONT[fontname]["bold"] = fontfile

    elif font:
        FONT[font.group(1)] = {"regular":fontfile,
                               "italic":fontfile,
                               "bold":fontfile,
                               "path":path}

# initializing fonts
print "[SubsSupport] initializing fonts in %s" % FONT_PATH

for f in FONT.keys():
    print "[SubsSupport] initializing %s" % f
    regular = FONT[f]['regular']
    italic = FONT[f]['italic']
    bold = FONT[f]['bold']
    path = FONT[f]['path']

    if f == 'Default':
        continue

    # e2 fonts are already initialized
    if path == E2_FONT_PATH:
        continue

    addFont(os.path.join(path, regular), regular, 100, False)
    addFont(os.path.join(path, italic), italic, 100, False)
    addFont(os.path.join(path, bold), bold, 100, False)

# initializing parsers
PARSERS = [SrtParser]

# initializing settings
subtitles_settings = None

def initSubsSettings(configSubsection=None):
    global subtitles_settings
    if configSubsection:
        print '[SubsSupport] using provided ConfigSubsection to store config'
        subtitles_settings = configSubsection
    elif 'PLUGIN_NAME' in globals():
        print '[SubsSupport] using config.plugins.%s.%s to store config' % (PLUGIN_NAME, 'subtitles')
        plugin_settings = getattr(config.plugins, PLUGIN_NAME)
        setattr(plugin_settings, 'subtitles', ConfigSubsection())
        subtitles_settings = getattr(plugin_settings, 'subtitles')
    else:
        print '[SubsSupport] using global config'
        config.plugins.subtitlesSupport = ConfigSubsection()
        subtitles_settings = config.plugins.subtitlesSupport

    subtitles_settings.showSubtitles = ConfigYesNo(default=True)
    subtitles_settings.autoLoad = ConfigYesNo(default=True)

    choicelist = []
    for e in ENCODINGS.keys():
        choicelist.append(e)
    subtitles_settings.encodingsGroup = ConfigSelection(default=__("Central and Eastern Europe"), choices=choicelist)

    choicelist = []
    for f in FONT.keys():
        choicelist.append(f)
    subtitles_settings.fontType = ConfigSelection(default="Ubuntu", choices=choicelist)

    choicelist = []
    for i in range(10, 60, 1):
        choicelist.append(("%d" % i, "%d" % i))

    # set default font size of subtitles
    subtitles_settings.fontSize = ConfigSelection(default="43", choices=choicelist)

    choicelist = []
    for i in range(0, 101, 1):
        choicelist.append(("%d" % i, "%d" % i))
    # set default position of subtitles (0-100) 0-top ,100-bottom
    subtitles_settings.position = ConfigSelection(default="94", choices=choicelist)

    # set available colors for subtitles/shadows
    # format is RRRGGGBBB
    colorlist = []
    colorlist.append(("ff0000", __("red")))
    colorlist.append(("DCDCDC", __("grey")))
    colorlist.append(("00ff00", __("green")))
    colorlist.append(("ff00ff", __("purple")))
    colorlist.append(("ffff00", __("yellow")))
    colorlist.append(("ffffff", __("white")))
    colorlist.append(("00ffff", __("blue")))
    colorlist.append(("000000", __("black")))

    # load custom colors
    COLORFILE = os.path.join(os.path.dirname(__file__), 'colors.txt')
    print '[SubsSupport] looking for custom colors in', COLORFILE
    with open(COLORFILE, 'r') as f:
        for line in f:
            color = re.search('^(\w+)\s+([0-9A-Fa-f]{6})$', line)
            if color is not None:
                alias = color.group(1)
                hex_color = color.group(2)
                print '[SubsSupport] adding custom color', alias
                colorlist.append((hex_color, alias))

    # set default color of subtitles
    subtitles_settings.color = ConfigSelection(default="ffffff", choices=colorlist)

    # shadow settings
    subtitles_settings.shadow = ConfigSubsection()
    subtitles_settings.shadow.type = ConfigSelection(default="border", choices=[("offset", __("offset")), ("border", __('border'))])
    subtitles_settings.shadow.color = ConfigSelection(default="000000", choices=colorlist[:])

    choicelist = []
    for i in range(0, 8, 1):
        choicelist.append(("%d" % i, "%d" % i))
    subtitles_settings.shadow.size = ConfigSelection(default="2", choices=choicelist)

    choicelist = []
    for i in range(-8, 0, 1):
        choicelist.append(("%d" % i, "%d" % i))
    subtitles_settings.shadow.xOffset = ConfigSelection(default="-3", choices=choicelist)
    subtitles_settings.shadow.yOffset = ConfigSelection(default="-3", choices=choicelist)

    subtitles_settings.engine = ConfigSelection(default="standard", choices=[('standard', __("Block")), ('extended', __("Row (experimental)"))])

    subtitles_settings.expert = ConfigSubsection()
    choicelist = []
    for i in range(0, 20000, 200):
        choicelist.append(("%d" % i, "%d ms" % i))
    subtitles_settings.expert.playerDelay = ConfigSelection(default="0", choices=choicelist)
    choicelist = []
    for i in range(0, 10, 100):
        choicelist.append(("%d" % i, "%d ms" % i))
    subtitles_settings.expert.startDelay = ConfigSelection(default="50", choices=choicelist)
    choicelist = []
    for i in range(0, 1000, 50):
        choicelist.append(("%d" % i, "%d ms" % i))
    subtitles_settings.expert.hideDelay = ConfigSelection(default="200", choices=choicelist)
    choicelist = []
    for i in range(100, 1000, 100):
        choicelist.append(("%d" % i, "%d ms" % i))
    subtitles_settings.expert.ptsDelayCheck = ConfigSelection(default="200", choices=choicelist)
    choicelist = []
    for i in range(100, 1000, 100):
        choicelist.append(("%d" % i, "%d ms" % i))
    subtitles_settings.expert.syncDelay = ConfigSelection(default="300", choices=choicelist)
    choicelist = []
    for i in range(200, 3000, 200):
        choicelist.append(("%d" % i, "%d ms" % i))
    subtitles_settings.expert.refreshDelay = ConfigSelection(default="1000", choices=choicelist)

    subtitles_settings.search = ConfigSubsection()
    subtitles_settings.search.downloadPath = ConfigDirectory(default="/tmp")
    subtitles_settings.search.tmpPath = ConfigDirectory(default="/tmp")
    subtitles_settings.search.lang1 = ConfigText(default=language.getLanguage()[:2])
    subtitles_settings.search.lang2 = ConfigText(default=language.getLanguage()[:2])
    subtitles_settings.search.lang3 = ConfigText(default=language.getLanguage()[:2])
    subtitles_settings.search.defaultSort = ConfigSelection(default='lang', choices=[('lang',__("Language")),('provider',__("Provider"))])
    subtitles_settings.search.downloadToMovieDir = ConfigYesNo(default=False)
    subtitles_settings.search.saveAsMovieName = ConfigYesNo(default=False)
    subtitles_settings.search.askOverrideExistingSubs = ConfigYesNo(default=True)
    subtitles_settings.search.addLangToSubsFileName = ConfigYesNo(default=False)

# source from openpli
class SubsSupportEmbedded(object):
    def __init__(self, embeddedSupport, preferEmbedded):
        self.embeddedSupport = embeddedSupport
        self.preferEmbedded = preferEmbedded
        self.selected_subtitle = None
        self.subtitle_window = self.session.instantiateDialog(SubsEmbeddedScreen)
        self.subtitle_window.hide()
        if isinstance(self, InfoBarBase):
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
                {
                    iPlayableService.evStart: self.__serviceChanged,
                    iPlayableService.evEnd: self.__serviceChanged,
                    # iPlayableService.evUpdatedInfo: self.__updatedInfo
                })
            self.onClose.append(self.subtitle_window.doClose)

    def __isEmbeddedEnabled(self):
        return self.subtitle_window.shown

    embeddedEnabled = property(__isEmbeddedEnabled)

    def getCurrentServiceSubtitle(self):
        service = self.session.nav.getCurrentService()
        return service and service.subtitle()

    def __serviceChanged(self):
        if self.selected_subtitle:
            self.selected_subtitle = None
            self.subtitle_window.hide()

    def __updatedInfo(self):
        if not self.selected_subtitle:
            subtitle = self.getCurrentServiceSubtitle()
            cachedsubtitle = subtitle.getCachedSubtitle()
            if cachedsubtitle:
                self.enableSubtitle(cachedsubtitle)

    def enableSubtitle(self, selectedSubtitle):
        print '[SubsSupportEmbedded] enableSubtitle', selectedSubtitle
        subtitle = self.getCurrentServiceSubtitle()
        self.selected_subtitle = selectedSubtitle
        if subtitle and self.selected_subtitle:
            subtitle.enableSubtitles(self.subtitle_window.instance, self.selected_subtitle)
            self.subtitle_window.show()
            print '[SubsSupportEmbedded] enable embedded subtitles'
        else:
            print '[SubsSupportEmbedded] disable embedded subtitles'
            if subtitle:
                subtitle.disableSubtitles(self.subtitle_window.instance)
            self.subtitle_window.hide()

    def restartSubtitle(self):
        if self.selected_subtitle:
            print '[SubsSupportEmbedded] restart embedded subtitles'
            self.enableSubtitle(self.selected_subtitle)


class SubsSupport(SubsSupportEmbedded):
    """User class for subtitles

        If this class is not subclass of InfoBarBase  you have to use public function of this class to
        to connect your media player (resume,pause,exit,after seeking, subtitles setup)
        functions with subtitles

    @param session: set active session
    @param subsPath: set path for subtitles to load
    @param defaultPath: set default path when loading external subtitles
    @param forceDefaultPath: always use default path when loading external subtitles
    @param autoLoad: tries to load automatically subtitles according to name of file
    @param alreadyPlaying: flag indicates that service already started
    @param embeddedSupport: if you want to have also support for embedded subtitles
    """

    def __init__(self, session=None, subsPath=None, defaultPath=None, forceDefaultPath=False, autoLoad=True,
                 alreadyPlaying=False, showGUIInfoMessages=True, embeddedSupport=False, preferEmbedded=False, searchSupport=False):
        assert subtitles_settings is not None, 'you have to call initSubsSettings function first'
        if session is not None:
            self.session = session
        self.searchSupport = searchSupport
        SubsSupportEmbedded.__init__(self, embeddedSupport, preferEmbedded)
        self.__subsScreen = self.session.instantiateDialog(self._getSubsScreenCls())
        self.__subsScreen.hide()
        self.__subsEngine = self._getSubsEngineCls()(self.session, self.__subsScreen)
        self.__subsLoader = SubsLoader(PARSERS, ALL_LANGUAGES_ENCODINGS + ENCODINGS[subtitles_settings.encodingsGroup.getValue()])
        rowParsing = not subtitles_settings.engine.getValue() == 'standard'
        self.__subsLoader.set_row_parsing(rowParsing)
        self.__loaded = False
        self.__working = False
        self.__firstStart = True
        self.__autoLoad = autoLoad
        self.__subsPath = None
        self.__subsDir = None
        self.__subsEnc = None
        self.__playerDelay = 0
        self.__subsDelay = 0
        self.__startDelay = 1200
        self.__defaultPath = None
        self.__isServiceSet = False
        self.__subclassOfInfobarBase = isinstance(self, InfoBarBase)
        self.__forceDefaultPath = forceDefaultPath
        self.__showGUIInfoMessages = showGUIInfoMessages
        self.__checkTimer = eTimer()
        self.__starTimer = eTimer()
        self.__starTimer.callback.append(self.__updateSubs)
        try:
            from Screens.InfoBar import InfoBar
            InfoBar.instance.subtitle_window.hide()
        except Exception:
            pass

        if self.__subclassOfInfobarBase:
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evStart: self.__serviceStarted,
                iPlayableService.evEnd: self.__serviceStopped,
                iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
            })
            self["SubsActions"] = HelpableActionMap(self, "SubtitlesActions",
                {
                "subtitles": (self.subsMenu, __("show subtitles menu")),
                } , -5)

            self.onClose.append(self.exitSubs)

        if defaultPath is not None and os.path.isdir(defaultPath):
            self.__defaultPath = defaultPath
            self.__subsDir = defaultPath

        if subsPath is not None and self.__autoLoad:
            self.loadSubs(subsPath)
            if alreadyPlaying and self.__subclassOfInfobarBase:
                self.resumeSubs()


    def loadSubs(self, subsPath, newService=True):
        """loads subtitles from subsPath
        @param subsPath: path to subtitles (http url supported)
        @param newService: set False if service remains the same
        @return: True if subtitles was successfully loaded
        @return: False if subtitles wasnt successfully loaded
        """
        self.__working = True
        self.__subsPath = None
        if self.__defaultPath is not None:
            self.__subsDir = self.__defaultPath
        else:
            self.__subsDir = None

        if subsPath is not None:
            if not subsPath.startswith('http'):
                if self.__defaultPath is not None and self.__forceDefaultPath:
                    self.__subsDir = self.__defaultPath
                else:
                    if os.path.isdir(os.path.dirname(subsPath)):
                        self.__subsDir = os.path.dirname(subsPath)
                    else:
                        self.__subsDir = self.__defaultPath
                if not os.path.isfile(subsPath):
                    print '[Subtitles] trying to load not existing path:', subsPath
                    subsPath = None

            if subsPath is not None:
                subsList, self.__subsEnc = self.__processSubs(subsPath, self.__subsEnc)
                if subsList is not None:
                    self.__subsPath = subsPath
                    if newService:
                        self.__subsEngine.reset()
                    self.__subsEngine.pause()
                    self.__subsEngine.setPlayerDelay(self.__playerDelay)
                    self.__subsEngine.setSubsList(subsList)
                    self.__loaded = True
                    self.__working = False
                    return True
                else:
                    self.__subsEnc = None
                    self.__subsPath = None
        self.__working = False
        return False


    def startSubs(self, time):
        """If subtitles are loaded then start to play them after time set in ms"""
        def wrapped():
            self.__startTimer.start(time, True)

        if self.__working or self.__loaded:
            self.__afterWork(wrapped)

    def isSubsLoaded(self):
        return self.__loaded

    def getSubsFileFromSref(self):
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        if os.path.isdir(os.path.dirname(ref.getPath())):
            self.__subsDir = os.path.dirname(ref.getPath())
            for parser in PARSERS:
                for ext in parser.parsing:
                    subsPath = os.path.splitext(ref.getPath())[0] + ext
                    if os.path.isfile(subsPath):
                        return subsPath
        return None

    def resumeSubs(self):
        if self.__loaded:
            print '[Subtitles] resuming subtitles'
            if subtitles_settings.showSubtitles.value:
                self.showSubsDialog()
            else:
                self.hideSubsDialog()
            self.__subsEngine.resume()

    def pauseSubs(self):
        if self.__loaded:
            print '[Subtitles] pausing subtitles'
            self.__subsEngine.pause()

    def playAfterSeek(self):
        if self.__loaded:
            if subtitles_settings.showSubtitles.value:
                self.showSubsDialog()
            else:
                self.hideSubsDialog()
            self.__subsEngine.sync()

    def showSubsDialog(self):
        if self.__loaded:
            print '[Subtitles] show dialog'
            self.__subsScreen.show()

    def hideSubsDialog(self):
        if self.__loaded:
            print '[Subtitles] hide dialog'
            if self.__subsScreen:
                self.__subsScreen.hide()

    def setPlayerDelay(self, delayInMs):
        self.__playerDelay = delayInMs

    def setSubsDelay(self, delayInMs):
        if self.__loaded:
            self.__subsDelay = delayInMs
            self.__subsEngine.setSubsDelay(self.__subsDelay)

    def getSubsDelay(self):
        if self.__loaded:
            return self.__subsDelay
        return None

    def subsMenu(self):
        if not self.__working and not (self.__subclassOfInfobarBase and not self.__isServiceSet):
            self.session.openWithCallback(self.__subsMenuCB, SubsMenu, self,
                                          self.__subsPath, self.__subsDir, self.__subsEnc, self.embeddedSupport, self.embeddedEnabled, self.searchSupport)

    def resetSubs(self, resetEnc=True, resetEngine=True, newSubsScreen=False, newService=True):
        """
        Resets subtitle state -> stops engine, reload encodings, reset paths..
        @param resetEnc : start trying encodings from beginning of  current encodings-group list
        @param resetEngine: clean active subtitle, subtitle list, reset engine vars
        @param newSubsSCreen: recreates subtitles screen
        @param newService: set to True if new servicereference is in use
        """
        # start trying encodings from beginning of encodings_group list
        if resetEnc:
            self.__subsEnc = None
        self.__subsLoader.change_encodings(ALL_LANGUAGES_ENCODINGS + ENCODINGS[subtitles_settings.encodingsGroup.getValue()])
        self.__subsEngine.pause()
        # stop subtitles, clean active subtitle,  subtitles list, reset delay
        # if new service -> remove service
        if resetEngine:
            self.__subsDelay = 0
            self.__subsEngine.reset()
            if newService:
                self.__firstStart = False
        # hide subtitles, reload screen with new settings
        # if  newSubsScreen, remove current subscreen and create new one
        self.__resetSubsScreen(newSubsScreen)
        self.__subsPath = None
        self.__loaded = False

    def __resetSubsScreen(self, newSubsScreen=False):
        self.__subsScreen.hide()
        if newSubsScreen:
            self.__subsEngine.setRenderer(None)
            self.session.deleteDialog(self.__subsScreen)
            self.__subsScreen = self.session.instantiateDialog(self._getSubsScreenCls())
            self.__subsEngine.setRenderer(self.__subsScreen)
        else:
            self.__subsScreen.reloadSettings()
        if subtitles_settings.showSubtitles.value:
            self.__subsScreen.show()
        else:
            self.__subsScreen.hide()


    def exitSubs(self):
        """This method should be called at the end of usage of this class"""
        self.hideSubsDialog()

        if self.__subsEngine:
            self.__subsEngine.exit()
            self.__subsEngine = None

        if self.__subsScreen:
            self.session.deleteDialog(self.__subsScreen)
            self.__subsScreen = None

        self.__starTimer.stop()
        self.__starTimer = None

        self.__checkTimer.stop()
        self.__checkTimer = None

        subtitles_settings.showSubtitles.setValue(True)
        subtitles_settings.showSubtitles.save()
        print '[SubsSupport] closing subtitleDisplay'


    def __subsMenuCB(self, subsPath, subsEmbedded, settingsChanged, changeEncoding, turnOff, forceReload=False):
        if turnOff:
            print '[SubsSupport] turn off'
            if self.embeddedSupport and self.embeddedEnabled:
                self.enableSubtitle(None)
            if self.__loaded:
                self.resetSubs(newService=False)
        elif self.embeddedSupport and subsEmbedded:
            print '[SubsSupport] loading embedded subtitles'
            if self.__loaded:
                self.resetSubs()
            self.__subsScreen.hide()
            self.enableSubtitle(subsEmbedded)
        elif subsPath is not None:
            if self.embeddedEnabled:
                self.enableSubtitle(None)
            changedEncodingGroup = subtitles_settings.encodingsGroup.isChanged()
            changedShadowType = subtitles_settings.shadow.type.isChanged()
            changedEngine = subtitles_settings.engine.isChanged()
            newScreen = (changedEngine or changedShadowType)
            self.__subsScreen.show()
            if self.__subsPath == subsPath:
                if not settingsChanged and not ((changeEncoding or changedEncodingGroup) or newScreen or forceReload):
                    print '[SubsSupport] no changes made'
                elif settingsChanged and not (newScreen or changedEncodingGroup or forceReload):
                    print '[SubSupport] reloading SubScreen'
                    self.__subsEngine.pause()
                    self.__resetSubsScreen()
                    self.__subsEngine.resume()
                else:
                    self.__subsEngine.pause()
                    if changedEncodingGroup or ((changedEngine or changedShadowType) and not changeEncoding) or forceReload:
                        self.__subsEnc = None
                    if changedEncodingGroup:
                        self.__subsLoader.change_encodings(ALL_LANGUAGES_ENCODINGS + ENCODINGS[subtitles_settings.encodingsGroup.getValue()])
                    if changedEngine:
                        self.__subsLoader.toggle_row_parsing()
                    if newScreen:
                        self.__resetSubsScreen(newSubsScreen=True)
                    self.__subsEngine.reset(position=False)
                    if self.loadSubs(subsPath, newService=False):
                        self.__subsEngine.refresh()
            else:
                self.pauseSubs()
                self.__subsEnc = None
                if changedEngine:
                    self.__subsLoader.toggle_row_parsing()
                if changedEncodingGroup:
                        self.__subsLoader.change_encodings(ALL_LANGUAGES_ENCODINGS + ENCODINGS[subtitles_settings.encodingsGroup.getValue()])
                if newScreen:
                    self.__resetSubsScreen(newSubsScreen=True)
                self.__subsEngine.reset()
                if self.__loaded:
                    if self.loadSubs(subsPath, newService=False):
                        self.__subsEngine.refresh()
                else:
                    if self.loadSubs(subsPath, newService=False):
                        self.__subsEngine.resume()


    def __processSubs(self, subsPath, subsEnc):
        showMessages = self.__showGUIInfoMessages and not (self.__firstStart and self.__subclassOfInfobarBase)
        try:
            return self.__subsLoader.load(subsPath, subsEnc)
        except LoadError:
            if showMessages:
                warningMessage(self.session, __("Cannot load subtitles. Invalid path"))
                return None, None
        except DecodeError:
            if showMessages:
                warningMessage(self.session, __("Cannot decode subtitles. Try another encoding group"))
                return None, None
        except ParserNotFoundError:
            if showMessages:
                warningMessage(self.session, __("Cannot parse subtitles. Not supported subtitles format"))
                return None, None
        except ParseError:
            if showMessages:
                warningMessage(self.session, __("Cannot parse subtitles. Invalid subtitles format"))
                return None, None
        finally:
            self.__firstStart = False

    def __updateSubs(self):
        if self.isSubsLoaded():
            self.resumeSubs()
            return

        subsPath = self.getSubsFileFromSref()
        if subsPath is not None:
            if self.loadSubs(subsPath):
                self.resumeSubs()
        self.__working = False

    def _getSubsScreenCls(self):
        if subtitles_settings.engine.value == 'standard':
            return SubsScreen
        else:
            return SubsRowScreen

    def _getSubsEngineCls(self):
        return SubsEngine

    def __afterWork(self, fnc):
        def checkWorking():
            if self.__working:
                self.__checkTimer.start(200, True)
            else:
                self.__checkTimer.stop()
                fnc()

        self.__checkTimer.stop()
        self.__starTimer.stop()

        if self.__working:
            del self.__checkTimer.callback[:]
            self.__checkTimer.callback.append(checkWorking)
            self.__checkTimer.start(200, True)
        else:
            fnc()


############ Methods triggered by videoEvents when SubsSupport is subclass of Screen ################
    def __serviceStarted(self):
        print '[SubsSupport] Service Started'
        def startSubs():
            self.__starTimer.start(self.__startDelay, True)

        self.__isServiceSet = True
        # subtitles are loading or already loaded
        if self.__working or self.__loaded:
            self.__afterWork(startSubs)
        else:
            self.resetSubs(True)
            if self.__subsPath is None and self.__autoLoad:
                startSubs()

    def __serviceStopped(self):
        self.__isServiceSet = False

    def __seekableStatusChanged(self):
        if not hasattr(self, 'seekstate'):
            return
        if self.seekstate == self.SEEK_STATE_PLAY:
            self.pauseSubs()
        elif self.seekstate == self.SEEK_STATE_PAUSE:
            self.resumeSubs()
        elif self.seekstate == self.SEEK_STATE_EOF:
            self.resetSubs(True)

########### Methods which extends InfobarSeek seek methods

    def doSeekRelative(self, pts):
        if self.__loaded:
            # self.__subsEngine.preSeek(pts)
            super(SubsSupport, self).doSeekRelative(pts)
            self.playAfterSeek()
        else:
            super(SubsSupport, self).doSeekRelative(pts)
    def doSeek(self, pts):
        if self.__loaded:
            super(SubsSupport, self).doSeek(pts)
            self.playAfterSeek()
        else:
            super(SubsSupport, self).doSeek(pts)

############################################################

class SubsEmbeddedScreen(Screen):
    def __init__(self, session):
        desktop = getDesktop(0)
        size = desktop.size()
        self.skin = """<screen position="0,0" size="%s,%s" zPosition="-1" backgroundColor="transparent" flags="wfNoBorder" />""" % (size.width(), size.height())
        Screen.__init__(self, session)

class SubsScreen(Screen):

    def __init__(self, session):
        desktop = getDesktop(0)
        size = desktop.size()
        self.sc_width = size.width()
        self.sc_height = size.height()
        self.subShown = False
        # eLabel on older versions of e2 doesnt have border option
        self.__eLabelHasBorderParams = False
        self.__shadowType = 'border'
        fontSize = int(subtitles_settings.fontSize.getValue())
        fontType = subtitles_settings.fontType.getValue()
        if fontType not in FONT:
            fontType = "Default"
            subtitles_settings.fontType.setValue("Default")
            subtitles_settings.fontType.save()

        self.font = {"regular":gFont(FONT[fontType]['regular'], fontSize),
                     "italic":gFont(FONT[fontType]['italic'], fontSize),
                     "bold":gFont(FONT[fontType]['bold'], fontSize)}

        self.selectedFont = "regular"
        position = int(subtitles_settings.position.getValue())
        vSize = fontSize * 4 + 15  # 3 rows + reserve
        color = subtitles_settings.color.getValue()
        self.currentColor = color
        position = int(position * (float(self.sc_height - vSize) / 100))

        self.skin = """
            <screen name="SubtitleDisplay" position="0,0" size="%s,%s" zPosition="-1" backgroundColor="transparent" flags="wfNoBorder">
                    <widget name="subtitles" position="0,%s" size="%s,%s" valign="center" halign="center" transparent="1"/>
            </screen>""" % (str(self.sc_width), str(self.sc_height), str(position), str(self.sc_width), str(vSize))

        Screen.__init__(self, session)
        self.stand_alone = True
        print 'initializing subtitle display'

        self["subtitles"] = Label("")

        self.onLayoutFinish.append(self.__checkElabelCaps)
        self.onLayoutFinish.append(self.reloadSettings)

    def __checkElabelCaps(self):
        if hasattr(self["subtitles"].instance, 'setBorderWidth') and hasattr(self["subtitles"].instance, 'setBorderColor'):
            self.__eLabelHasBorderParams = True
        elif self.__shadowType == 'border':
            self.__shadowType = 'offset'

    def setShadowType(self, type):
        if type == 'border' and self.__eLabelHasBorderParams:
            self.__shadowType = 'border'
        else:
            self.__shadowType = 'offset'

    def setShadowWidth(self, width):
        self["subtitles"].instance.setBorderWidth(int(width))

    def setShadowColor(self, color, border=False):
        color = "#" + color
        if self.__shadowType == 'border':
            self["subtitles"].instance.setBorderColor(parseColor(color))
        else:
            self["subtitles"].instance.setShadowColor(parseColor(color))

    def setShadowOffset(self, offset):
        self["subtitles"].instance.setShadowOffset(parsePosition(offset, self.scale))

    def setShadow(self, type, color, size=None, xOffset=None, yOffset=None):
        self.setShadowType(type)
        self.setShadowColor(color)
        if self.__shadowType == 'border' and size:
            self.setShadowWidth(size)
        elif self.__shadowType == 'offset' and (xOffset and yOffset):
            self.setShadowOffset(str(-xOffset) + ',' + str(-yOffset))


    def setColor(self, color):
        self.currentColor = color
        color = "#" + color
        self["subtitles"].instance.setForegroundColor(parseColor(color))

    def setPosition(self, position):
        self["subtitles"].instance.move(ePoint(0, position))

    def setFonts(self, font):
        self.font = font
        self['subtitles'].instance.setFont(self.font['regular'])

    def reloadSettings(self):
        color = subtitles_settings.color.getValue()

        shadowType = subtitles_settings.shadow.type.getValue()
        shadowColor = subtitles_settings.shadow.color.getValue()
        shadowSize = int(subtitles_settings.shadow.size.getValue())
        shadowXOffset = int(subtitles_settings.shadow.xOffset.getValue())
        shadowYOffset = int(subtitles_settings.shadow.yOffset.getValue())

        fontSize = int(subtitles_settings.fontSize.getValue())
        vSize = fontSize * 4 + 15
        position = int(subtitles_settings.position.getValue())
        position = int(position * (float(self.sc_height - vSize) / 100))

        self.setColor(color)
        self.setPosition(position)
        self.setShadow(shadowType, shadowColor, shadowSize, shadowXOffset, shadowYOffset)
        self.setFonts({"regular":gFont(FONT[subtitles_settings.fontType.getValue()]['regular'], fontSize),
                       "italic":gFont(FONT[subtitles_settings.fontType.getValue()]['italic'], fontSize),
                       "bold":gFont(FONT[subtitles_settings.fontType.getValue()]['bold'], fontSize)})

    def setSubtitle(self, sub):
        self.subShown = True
        if sub['style'] != self.selectedFont:
            self.selectedFont = sub['style']
            self['subtitles'].instance.setFont(self.font[sub['style']])
        if sub['color'] != 'default':
            self.setColor(sub['color'])
        elif self.currentColor != subtitles_settings.color.getValue():
            self.setColor(subtitles_settings.color.getValue())
        self["subtitles"].setText(sub['text'].encode('utf-8'))

    def hideSubtitle(self):
        if self.subShown:
            self.subShown = False
            self["subtitles"].setText("")

class SubsRowScreen(Screen):
    def __init__(self, session):
        desktop = getDesktop(0)
        size = desktop.size()
        self.sc_width = size.width()
        self.sc_height = size.height()
        self.subShown = False
        # eLabel on older versions of e2 doesnt have border option
        self.__eLabelHasBorderParams = False
        self.__shadowType = 'border'
        fontSize = int(subtitles_settings.fontSize.getValue())
        fontType = subtitles_settings.fontType.getValue()
        if fontType not in FONT:
            fontType = "Default"
            subtitles_settings.fontType.setValue("Default")
            subtitles_settings.fontType.save()

        self.font = {"regular":gFont(FONT[fontType]['regular'], fontSize),
                     "italic":gFont(FONT[fontType]['italic'], fontSize),
                     "bold":gFont(FONT[fontType]['bold'], fontSize)}

        position = int(subtitles_settings.position.getValue())
        vSize = fontSize * 4 + 15  # 3 rows + reserve
        color = subtitles_settings.color.getValue()
        position = int(position * (float(self.sc_height - vSize) / 100))

        self.colorRow1 = 'default'
        self.colorRow2 = 'default'
        self.colorRow3 = 'default'
        self.colorRow4 = 'default'
        self.fontRow1 = 'regular'
        self.fontRow2 = 'regular'
        self.fontRow3 = 'regular'
        self.fontRow4 = 'regular'

        self.skin = """
            <screen name="SubtitleDisplay" position="0,0" size="%s,%s" zPosition="-1" backgroundColor="transparent" flags="wfNoBorder">
                    <widget name="subrow1" position="0,%s" size="%s,%s" valign="center" halign="center" transparent="1"/>
                    <widget name="subrow2" position="0,%s" size="%s,%s" valign="center" halign="center" transparent="1"/>
                    <widget name="subrow3" position="0,%s" size="%s,%s" valign="center" halign="center" transparent="1"/>
                    <widget name="subrow4" position="0,%s" size="%s,%s" valign="center" halign="center" transparent="1"/>
            </screen>""" % (str(self.sc_width), str(self.sc_height), str(position), str(self.sc_width), str(vSize),
                            str(position), str(self.sc_width), str(vSize), str(position), str(self.sc_width), str(vSize), str(position), str(self.sc_width), str(vSize))

        Screen.__init__(self, session)
        self.stand_alone = True
        print 'initializing subtitle display'

        self["subrow1"] = Label("")
        self["subrow2"] = Label("")
        self["subrow3"] = Label("")
        self["subrow4"] = Label("")

        self.onLayoutFinish.append(self.__checkElabelCaps)
        self.onLayoutFinish.append(self.reloadSettings)

    def __checkElabelCaps(self):
        if hasattr(self["subrow1"].instance, 'setBorderWidth') and hasattr(self["subrow1"].instance, 'setBorderColor'):
            self.__eLabelHasBorderParams = True
        elif self.__shadowType == 'border':
            self.__shadowType = 'offset'

    def setShadowType(self, type):
        if type == 'border' and self.__eLabelHasBorderParams:
            self.__shadowType = 'border'
        else:
            self.__shadowType = 'offset'

    def setShadowWidth(self, width):
        self["subrow1"].instance.setBorderWidth(int(width))
        self["subrow2"].instance.setBorderWidth(int(width))
        self["subrow3"].instance.setBorderWidth(int(width))
        self["subrow4"].instance.setBorderWidth(int(width))

    def setShadowColor(self, color, border=False):
        color = "#" + color
        if self.__shadowType == 'border':
            self["subrow1"].instance.setBorderColor(parseColor(color))
            self["subrow2"].instance.setBorderColor(parseColor(color))
            self["subrow3"].instance.setBorderColor(parseColor(color))
            self["subrow4"].instance.setBorderColor(parseColor(color))
        else:
            self["subrow1"].instance.setShadowColor(parseColor(color))
            self["subrow2"].instance.setShadowColor(parseColor(color))
            self["subrow3"].instance.setShadowColor(parseColor(color))
            self["subrow4"].instance.setShadowColor(parseColor(color))

    def setShadowOffset(self, offset):
        self["subrow1"].instance.setShadowOffset(parsePosition(offset, self.scale))
        self["subrow2"].instance.setShadowOffset(parsePosition(offset, self.scale))
        self["subrow3"].instance.setShadowOffset(parsePosition(offset, self.scale))
        self["subrow4"].instance.setShadowOffset(parsePosition(offset, self.scale))

    def setShadow(self, type, color, size=None, xOffset=None, yOffset=None):
        self.setShadowType(type)
        self.setShadowColor(color)
        if self.__shadowType == 'border' and size:
            self.setShadowWidth(size)
        elif self.__shadowType == 'offset' and (xOffset and yOffset):
            self.setShadowOffset(str(-xOffset) + ',' + str(-yOffset))

    def setColor(self, color):
        color = "#" + color
        self["subrow1"].instance.setForegroundColor(parseColor(color))
        self["subrow2"].instance.setForegroundColor(parseColor(color))
        self["subrow3"].instance.setForegroundColor(parseColor(color))
        self["subrow4"].instance.setForegroundColor(parseColor(color))

    def setPosition(self, position):
        self["subrow1"].instance.move(ePoint(0, position))
        self["subrow2"].instance.move(ePoint(0, position))
        self["subrow3"].instance.move(ePoint(0, position))
        self["subrow4"].instance.move(ePoint(0, position))

    def setFonts(self, font):
        self.font = font
        self["subrow1"].instance.setFont(self.font['regular'])
        self["subrow2"].instance.setFont(self.font['regular'])
        self["subrow3"].instance.setFont(self.font['regular'])
        self["subrow4"].instance.setFont(self.font['regular'])

    def reloadSettings(self):
        color = subtitles_settings.color.getValue()

        shadowType = subtitles_settings.shadow.type.getValue()
        shadowColor = subtitles_settings.shadow.color.getValue()
        shadowSize = int(subtitles_settings.shadow.size.getValue())
        shadowXOffset = int(subtitles_settings.shadow.xOffset.getValue())
        shadowYOffset = int(subtitles_settings.shadow.yOffset.getValue())

        fontSize = int(subtitles_settings.fontSize.getValue())
        vSize = fontSize * 4 + 15
        position = int(subtitles_settings.position.getValue())
        position = int(position * (float(self.sc_height - vSize) / 100))

        self.setColor(color)
        self.setPosition(position)
        self.setShadow(shadowType, shadowColor, shadowSize, shadowXOffset, shadowYOffset)
        self.setFonts({"regular":gFont(FONT[subtitles_settings.fontType.getValue()]['regular'], fontSize),
                       "italic":gFont(FONT[subtitles_settings.fontType.getValue()]['italic'], fontSize),
                       "bold":gFont(FONT[subtitles_settings.fontType.getValue()]['bold'], fontSize)})

    def setSubtitle(self, sub):
        self.subShown = True
        lenRows = len(sub['rows'])
        if lenRows == 1:
            self["subrow2"].setText("")
            self["subrow3"].setText("")
            self["subrow4"].setText("")
        elif lenRows == 2:
            self["subrow3"].setText("")
            self["subrow4"].setText("")
        elif lenRows == 3:
            self["subrow4"].setText("")
        for idx, row in enumerate(sub['rows']):
            self._setSubRow(row, idx + 1, lenRows)

    def _getSubRow(self, rowNum):
        return self.get('subrow' + str(rowNum))

    def _setSubRow(self, sub, rowNum, lenRows):
        if lenRows == 1:
            text = sub['text']
        elif lenRows == 2:
            if rowNum == 1:
                text = sub['text'] + u'\n'
            elif rowNum == 2:
                text = u'\n' + sub['text']
        elif lenRows == 3:
            if rowNum == 1:
                text = sub['text'] + u'\n\n'
            elif rowNum == 2:
                text = u'\n' + sub['text'] + u'\n'
            elif rowNum == 3:
                text = u'\n\n' + sub['text']
        elif lenRows == 4:
            if rowNum == 1:
                text = sub['text'] + u'\n\n\n'
            elif rowNum == 2:
                text = u'\n' + sub['text'] + u'\n\n'
            elif rowNum == 3:
                text = u'\n\n' + sub['text'] + u'\n'
            elif rowNum == 4:
                text = u'\n\n\n' + sub['text']
        else:
            return
        subRow = self._getSubRow(rowNum)

        if sub['style'] != 'regular':
            setattr(self, 'fontRow' + str(rowNum), sub['style'])
            subRow.instance.setFont(self.font[sub['style']])
        elif getattr(self, 'fontRow' + str(rowNum)) != 'regular':
            setattr(self, 'fontRow' + str(rowNum), sub['style'])
            subRow.instance.setFont(self.font['regular'])

        if sub['color'] != 'default':
            setattr(self, 'colorRow' + str(rowNum), sub['color'])
            color = "#" + sub['color']
            subRow.instance.setForegroundColor(parseColor(color))
        elif getattr(self, 'colorRow' + str(rowNum)) != 'default':
            setattr(self, 'colorRow' + str(rowNum), 'default')
            color = subtitles_settings.color.getValue()
            color = "#" + color
            subRow.instance.setForegroundColor(parseColor(color))
        subRow.setText(text.encode('utf-8'))

    def hideSubtitle(self):
        if self.subShown:
            self.subShown = False
            self["subrow1"].setText("")
            self["subrow2"].setText("")
            self["subrow3"].setText("")
            self["subrow4"].setText("")

class SubsEngine(object):
    def __init__(self, session, renderer):
        self.session = session
        self.renderer = renderer
        self.subsList = None
        self.position = 0
        self.sub = None
        self.subsDelay = 0
        self.playerDelay = 0
        self.syncDelay = 300
        self.hideInterval = 200 * 90
        self.__seek = None
        self.__pts = None
        self.__ptsDelay = None
        self.__callbackPts = None
        self.preDoPlay = [self.updateSubPosition]
        self.refreshTimer = eTimer()
        self.refreshTimer.callback.append(self.play)
        self.refreshTimerDelay = 1000
        self.hideTimer = eTimer()
        self.hideTimer.callback.append(self.checkHideSub)
        self.hideTimer.callback.append(self.incSubPosition)
        self.hideTimer.callback.append(self.doPlay)
        self.getPlayPtsTimer = eTimer()
        self.getPlayPtsTimer.callback.append(self.getPts)
        self.getPlayPtsTimer.callback.append(self.validPts)
        self.getPlayPtsTimer.callback.append(self.callbackPts)
        self.getPlayPtsTimerDelay = 200
        self.resume = self.play
        self.addNotifiers()

    def addNotifiers(self):
        def hideInterval(configElement):
            self.hideInterval = int(configElement.value) * 90
        def playerDelay(configElement):
                self.playerDelay = int(configElement.value) * 90
        def syncDelay(configElement):
            self.syncDelay = int(configElement.value)
        def getPlayPtsTimerDelay(configElement):
            self.getPlayPtsTimerDelay = int(configElement.value)
        def refreshTimerDelay(configElement):
            self.refreshTimerDelay = int(configElement.value)

        subtitles_settings.expert.hideDelay.addNotifier(hideInterval)
        subtitles_settings.expert.playerDelay.addNotifier(playerDelay)
        subtitles_settings.expert.syncDelay.addNotifier(syncDelay)
        subtitles_settings.expert.ptsDelayCheck.addNotifier(getPlayPtsTimerDelay)
        subtitles_settings.expert.refreshDelay.addNotifier(refreshTimerDelay)

    def removeNotifiers(self):
        del subtitles_settings.expert.hideDelay.notifiers[:]
        del subtitles_settings.expert.playerDelay.notifiers[:]
        del subtitles_settings.expert.syncDelay.notifiers[:]
        del subtitles_settings.expert.ptsDelayCheck.notifiers[:]
        del subtitles_settings.expert.refreshDelay.notifiers[:]

    def getPlayPts(self, callback, delay=None):
        self.getPlayPtsTimer.stop()
        self.__callbackPts = callback
        self.__ptsDelay = delay
        self.__pts = None
        if delay is None:
            delay = 1
        self.getPlayPtsTimer.start(delay, True)

    def getPts(self):
        try:
            if not self.__seek:
                service = self.session.nav.getCurrentService()
                self.__seek = service.seek()
        except Exception:
            return
        r = self.__seek.getPlayPosition()
        if r[0]:
            self.__pts = None
        else:
            self.__pts = long(r[1]) + self.playerDelay

    def validPts(self):
        pass

    def callbackPts(self):
        if self.__pts is not None:
            self.getPlayPtsTimer.stop()
            self.__callbackPts()
        else:
            delay = self.getPlayPtsTimerDelay
            if self.__ptsDelay is not None:
                delay = self.__ptsDelay
            self.getPlayPtsTimer.start(delay)

    def setSubsList(self, subslist):
        self.subsList = subslist

    def setRenderer(self, renderer):
        self.renderer = renderer

    def setPlayerDelay(self, playerDelay):
        self.playerDelay = playerDelay * 90

    def setSubsDelay(self, delay):
        self.subsDelay = delay * 90

    def reset(self, position=True):
        self.stopTimers()
        self.hideSub()
        if position:
            self.position = 0
        self.__seek = None
        self.__pts = None
        self.__callbackPts = None
        self.sub = None
        self.subsDelay = 0

    def refresh(self):
        self.stopTimers()
        self.hideSub()
        self.refreshTimer.start(self.refreshTimerDelay, True)

    def pause(self):
        self.stopTimers()
        self.hideSub()

    def play(self):
        self.stopTimers()
        self.hideSub()
        self.getPlayPts(self.prePlay)

    def sync(self):
        self._oldPts = None
        def checkPts():
            if self._oldPts is None:
                self._oldPts = self.__pts
                self.getPlayPts(checkPts, self.syncDelay)
            # video is frozen no progress made
            elif self._oldPts == self.__pts:
                self._oldPts = None
                self.getPlayPts(checkPts, self.syncDelay)
            # abnormal pts
            elif (self.__pts > self._oldPts + self.syncDelay * 90 + (200 * 90)) or (
                    self.__pts < self._oldPts + self.syncDelay * 90 - (200 * 90)):
                self._oldPts = None
                self.getPlayPts(checkPts, self.syncDelay)
                # normal playback
            else:
                del self._oldPts
                self.updateSubPosition()
                self.doPlay()
        self.stopTimers()
        self.hideSub()
        self.getPlayPts(checkPts, self.syncDelay)

    def prePlay(self):
        for f in self.preDoPlay:
            f()
        self.doPlay()

    def doPlay(self):
        if self.position == len(self.subsList):
            print  '[SubsEngine] reached end of subtitle list'
            self.position = len(self.subsList) - 1
            self.stopTimers()
        else:
            self.sub = self.subsList[self.position]
            self.getPlayPts(self.doWait)

    def doWait(self):
        subStartPts = self.sub['start'] + self.subsDelay
        if self.__pts < subStartPts:
            diffPts = subStartPts - self.__pts
            diffMs = diffPts / 90
            if diffMs > 50:
                self.getPlayPts(self.doWait, diffMs)
            else:
                print '[SubsEngine] sub shown sooner by %dms' % diffMs
                self.renderSub()
        else:
            if self.sub['end'] + self.subsDelay - self.__pts < 0:
                # print '[SubsEngine] %s < 0, skipping' % str(self.sub['end'] - self.__pts)
                self.getPlayPts(self.skipSubs, 100)
            else:
                print '[SubsEngine] sub shown later by %dms' % ((self.__pts - subStartPts) / 90)
                self.renderSub()

    def skipSubs(self):
        if self.position == len(self.subsList) - 1:
            self.incSubPosition()
        else:
            self.updateSubPosition()
        self.doPlay()

    def renderSub(self):
        duration = int(self.sub['duration'])
        self.renderer.setSubtitle(self.sub)
        self.hideTimer.start(duration, True)

    def checkHideSub(self):
        if self.subsList[-1] == self.sub:
            self.hideSub()
        elif self.subsList[self.position]['end'] + self.hideInterval < self.subsList[self.position + 1]['start']:
            self.hideSub()

    def hideSub(self):
        self.renderer.hideSubtitle()

    def incSubPosition(self):
        self.position += 1

    def updateSubPosition(self):
        playPts = self.__pts
        print '[SubsEngine] pre-update sub position:', self.position
        subStartPts = self.subsList[self.position]['start'] + self.subsDelay
        # seek backwards
        if subStartPts > playPts:
            subPrevStartPts = self.subsList[self.position - 1]['start'] + self.subsDelay
            while self.position > 0 and subPrevStartPts > playPts:
                self.position -= 1
                subPrevStartPts = self.subsList[self.position - 1]['start'] + self.subsDelay
        # seek forward
        elif subStartPts < playPts:
            while self.position < len(self.subsList) - 1 and subStartPts < playPts:
                self.position += 1
                subStartPts = self.subsList[self.position]['start'] + self.subsDelay
        print '[SubsEngine] post-update sub position:', self.position

    def showDialog(self):
        self.renderer.show()

    def hideSubtitlesDialog(self):
        self.renderer.hide()

    def stopTimers(self):
        if self.refreshTimer is not None:
            self.refreshTimer.stop()
        if self.getPlayPtsTimer is not None:
            self.getPlayPtsTimer.stop()
        if self.hideTimer is not None:
            self.hideTimer.stop()

    def exit(self):
        self.hideTimer = None
        self.refreshTimer = None
        self.getPlayPtsTimer = None
        self.removeNotifiers()


class PanelList(MenuList):
    def __init__(self, list, height=30):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setItemHeight(height)
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 17))

def PanelListEntry(name, mode):
    res = [(name, mode)]
    res.append(MultiContentEntryText(pos=(5, 5), size=(330, 25), font=0, flags=RT_VALIGN_CENTER, text=name))
    return res

def PanelColorListEntry(name, value, colorName, colorValue, sizePanelX):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=1, flags=RT_HALIGN_LEFT, text=name, color=colorName))
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=1, flags=RT_HALIGN_RIGHT, text=value, color=colorValue))
    return res

class SubsMenu(Screen):
    skin = """
        <screen position="center,center" size="500,400" zPosition="1" >
            <widget name="title_label" position="0,5" size="500,35" valign="center" halign="center" font="Regular;25" transparent="1" foregroundColor="white" />
            <widget name="subfile_label" position="0,50" size="500,50" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="#DAA520" />
            <widget name="subfile_list" position="center,100" size="300,30" transparent="1" />
            <eLabel position="5,135" size="490,1" backgroundColor="#999999" />
            <widget name="menu_list" position="0,140" size="500,245" transparent="1" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, infobar, subfile=None, subdir=None, encoding=None, embeddedSupport=False, embeddedEnabled=False, searchSupport=False):
        Screen.__init__(self, session)
        self.infobar = infobar
        self.subfile = subfile
        self.subdir = subdir
        self.encoding = encoding
        self.embeddedSupport = embeddedSupport
        self.embeddedEnabled = embeddedEnabled
        self.searchSupport = searchSupport
        self.embeddedSubtitle = None
        self.newSelection = False
        self.changeEncoding = False
        self.changedSettings = False
        self.turnOff = False
        self.forceReload = False

        self["title_label"] = Label(__("Currently choosed subtitles"))
        self["subfile_label"] = Label("")
        self["subfile_list"] = PanelList([], 25)
        self["menu_list"] = PanelList([], 28)
        self["actions"] = ActionMap(["SetupActions", "DirectionActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
            }, -2)

        self.onLayoutFinish.append(self.initTitle)
        self.onLayoutFinish.append(self.initGUI)
        self.onLayoutFinish.append(self.disableSelection)

    def disableSelection(self):
        self["subfile_list"].selectionEnabled(False)

    def initTitle(self):
        self.setTitle(__('Subtitles Menu'))

    def initGUI(self):
        self.initSubInfo()
        self.initMenu()

    def initSubInfo(self):
        subInfo = []
        if self.embeddedEnabled or self.embeddedSubtitle:
            self["subfile_label"].setText(__("Embedded Subtitles"))
            self["subfile_label"].instance.setForegroundColor(parseColor("#ffff00"))
        elif self.subfile is not None:
            self["subfile_label"].setText(os.path.split(self.subfile)[1].encode('utf-8'))
            self["subfile_label"].instance.setForegroundColor(parseColor("#DAA520"))

            if self.newSelection:
                pass
                # subInfo.append(PanelColorListEntry(__("State:"), __("not loaded"), 0xDAA520, 0xffff00, 300))
            elif self.encoding and not self.newSelection:
                # subInfo.append(PanelColorListEntry(__("State:"), __("loaded"), 0xDAA520, 0x00ff00, 300))
                subInfo.append(PanelColorListEntry(__("Encoding:"), self.encoding, 0xDAA520, 0xffffff, 300))
            elif not self.encoding and not self.newSelection:
                # subInfo.append(PanelColorListEntry(__("State:"), __("not loaded"), 0xDAA520, 0xffff00, 300))
                subInfo.append(PanelColorListEntry(__("Encoding:"), __("cannot decode"), 0xDAA520, 0xffffff, 300))
        else:
            self["subfile_label"].setText(__("None"))
            self["subfile_label"].instance.setForegroundColor(parseColor("#DAA520"))
        self["subfile_list"].setList(subInfo)

    def initMenu(self):
        self.menu = [(__('Choose subtitles'), 'choose')]
        if not self.embeddedEnabled:
            if self.subfile is not None and not self.newSelection:
                self.menu.append((__('Change encoding'), 'encoding'))
            self.menu.append((__('Subtitles settings'), 'setting'))
        elif self.embeddedEnabled and QuickSubtitlesConfigMenu:
            self.menu.append((__('Subtitles settings (embedded)'), 'setting_embedded'))
        if self.subfile is not None or self.embeddedEnabled:
            self.menu.append((__('Turn off subtitles'), 'subsoff'))
        list = [PanelListEntry(x, y) for x, y in self.menu]
        self["menu_list"].setList(list)

    def ok(self):
        mode = self["menu_list"].getCurrent()[0][1]
        if mode == 'choose':
            self.session.openWithCallback(self.subsChooserCB, SubsChooser, self.subdir, self.embeddedSupport, self.searchSupport)
        elif mode == 'setting':
            self.session.openWithCallback(self.subsSetupCB, SubsSetup)
        elif mode == 'setting_embedded':
            self.session.open(QuickSubtitlesConfigMenu, self.infobar)
        elif mode == 'encoding':
            self.changeEncoding = True
            self.cancel()
        elif mode == 'subsoff':
            self.turnOff = True
            self.cancel()

    def subsChooserCB(self, subfile=None, embeddedSubtitle=None, forceReload=False):
        if subfile is not None and self.subfile != subfile:
            self.subfile = subfile
            self.subdir = os.path.dirname(self.subfile)
            self.newSelection = True
            self.embeddedEnabled = False
            self.cancel()
        elif subfile is not None and self.subfile == subfile and forceReload:
            self.forceReload = True
            self.cancel()
        elif embeddedSubtitle and embeddedSubtitle != self.infobar.selected_subtitle:
            self.embeddedSubtitle = embeddedSubtitle
            self.cancel()
        # self.initGUI()

    def subsSetupCB(self, changedSettings=False):
        self.changedSettings = changedSettings

    def cancel(self):
        self.close(self.subfile, self.embeddedSubtitle, self.changedSettings, self.changeEncoding, self.turnOff, self.forceReload)


# rework
class SubsSetup(Screen, ConfigListScreen):
    skin = """
            <screen position="center,center" size="610,435" >
                <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
                <eLabel position="-1,55" size="612,1" backgroundColor="#999999" />
                <widget name="config" position="0,75" size="610,360" scrollbarMode="showOnDemand" />
            </screen>"""


    def __init__(self, session):
        Screen.__init__(self, session)
        self.list = [ ]
        self.showExpertSettings = subtitles_settings.expert.show = NoSave(ConfigYesNo(default=False))
        ConfigListScreen.__init__(self, self.list, session=session)
        self.setup_title = __("Subtitles setting")

        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.keyCancel,
                "green": self.keySave,
                "red": self.keyCancel,
                "blue": self.resetDefaults,
            }, -2)

        self["key_green"] = Label(__("Save"))
        self["key_red"] = Label(__("Cancel"))
        self["key_blue"] = Label(__("Reset Defaults"))
        self["key_yellow"] = Label("")

        self.buildMenu()
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle(__("External subtitles setting"))

    def buildMenu(self):
        del self.list[:]
        shadowType = subtitles_settings.shadow.type.getValue()
        showExpert = subtitles_settings.expert.show.getValue()
        # self.list.append(getConfigListEntry(__("Show subtitles"), subtitles_settings.showSubtitles))
        self.list.append(getConfigListEntry(__("Parsing/Rendering"), subtitles_settings.engine))
        self.list.append(getConfigListEntry(__("Font type"), subtitles_settings.fontType))
        self.list.append(getConfigListEntry(__("Font size"), subtitles_settings.fontSize))
        self.list.append(getConfigListEntry(__("Position"), subtitles_settings.position))
        self.list.append(getConfigListEntry(__("Color"), subtitles_settings.color))
        self.list.append(getConfigListEntry(__("Shadow type"), subtitles_settings.shadow.type))
        if shadowType == 'offset':
            self.list.append(getConfigListEntry(__("Shadow X-offset"), subtitles_settings.shadow.xOffset))
            self.list.append(getConfigListEntry(__("Shadow Y-offset"), subtitles_settings.shadow.yOffset))
        else:
            self.list.append(getConfigListEntry(__("Shadow size"), subtitles_settings.shadow.size))
        self.list.append(getConfigListEntry(__("Shadow color"), subtitles_settings.shadow.color))
        self.list.append(getConfigListEntry(__("Encoding"), subtitles_settings.encodingsGroup))
        self.list.append(getConfigListEntry(__("Show expert settings"), subtitles_settings.expert.show))
        if showExpert:
            self.list.append(getConfigListEntry(__("Hide delay"), subtitles_settings.expert.hideDelay))
            self.list.append(getConfigListEntry(__("Sync delay"), subtitles_settings.expert.syncDelay))
            self.list.append(getConfigListEntry(__("Player delay"), subtitles_settings.expert.playerDelay))
            self.list.append(getConfigListEntry(__("Refresh delay"), subtitles_settings.expert.refreshDelay))
            self.list.append(getConfigListEntry(__("PTS check delay"), subtitles_settings.expert.ptsDelayCheck))
        self["config"].list = self.list
        self["config"].setList(self.list)

    def resetDefaults(self):
        for x in self["config"].list:
            x[1].value = x[1].default
        self.buildMenu()

    def keySave(self):
        for x in self["config"].list:
            x[1].save()
        configfile.save()
        self.close(True)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        current = self["config"].getCurrent()[1]
        if current in [subtitles_settings.shadow.type, subtitles_settings.expert.show]:
            self.buildMenu()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        current = self["config"].getCurrent()[1]
        if current in [subtitles_settings.shadow.type, subtitles_settings.expert.show]:
            self.buildMenu()


def FileEntryComponent(name, absolute=None, isDir=False):
        res = [ (absolute, isDir) ]
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name))
        if isDir:
            png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/directory.png"))
        else:
            png = LoadPixmap(os.path.join(os.path.dirname(__file__), 'img','subtitles.png'))
        if png is not None:
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))
        return res



class SubFileList(FileList):
    def __init__(self, defaultDir):
        FileList.__init__(self, defaultDir, matchingPattern="(?i)^.*\." + '(' + '|'.join(parser.parsing[1:] for parser in PARSERS) + ')', useServiceRef=False)

    def changeDir(self, directory, select=None):
        self.list = []
        # if we are just entering from the list of mount points:
        if self.current_directory is None:
            if directory and self.showMountpoints:
                self.current_mountpoint = self.getMountpointLink(directory)
            else:
                self.current_mountpoint = None
        self.current_directory = directory
        directories = []
        files = []

        if directory is None and self.showMountpoints:  # present available mountpoints
            for p in harddiskmanager.getMountedPartitions():
                path = os_path.join(p.mountpoint, "")
                if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
                    self.list.append(FileEntryComponent(name=p.description, absolute=path, isDir=True))
            files = [ ]
            directories = [ ]
        elif directory is None:
            files = [ ]
            directories = [ ]
        elif self.useServiceRef:
            root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + directory)
            if self.additional_extensions:
                root.setName(self.additional_extensions)
            serviceHandler = eServiceCenter.getInstance()
            list = serviceHandler.list(root)

            while 1:
                s = list.getNext()
                if not s.valid():
                    del list
                    break
                if s.flags & s.mustDescent:
                    directories.append(s.getPath())
                else:
                    files.append(s)
            directories.sort()
            files.sort()
        else:
            if os_path.exists(directory):
                files = listdir(directory)
                files.sort()
                tmpfiles = files[:]
                for x in tmpfiles:
                    if os_path.isdir(directory + x):
                        directories.append(directory + x + "/")
                        files.remove(x)

        if directory is not None and self.showDirectories and not self.isTop:
            if directory == self.current_mountpoint and self.showMountpoints:
                self.list.append(FileEntryComponent(name="<" + __("List of Storage Devices") + ">", absolute=None, isDir=True))
            elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
                self.list.append(FileEntryComponent(name="<" + __("Parent Directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))

        if self.showDirectories:
            for x in directories:
                if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
                    name = x.split('/')[-2]
                    self.list.append(FileEntryComponent(name=name, absolute=x, isDir=True))

        if self.showFiles:
            for x in files:
                if self.useServiceRef:
                    path = x.getPath()
                    name = path.split('/')[-1]
                else:
                    path = directory + x
                    name = x

                if (self.matchingPattern is None) or re_compile(self.matchingPattern).search(path):
                    self.list.append(FileEntryComponent(name=name, absolute=x , isDir=False))

        self.l.setList(self.list)

        if select is not None:
            i = 0
            self.moveToIndex(0)
            for x in self.list:
                p = x[0][0]

                if isinstance(p, eServiceReference):
                    p = p.getPath()

                if p == select:
                    self.moveToIndex(i)
                i += 1

class SubsChooserMenuList(MenuList):
    def __init__(self, embeddedAvailable=False, searchSupport=False):
        MenuList.__init__(self, [], False, eListboxPythonMultiContent)
        self.l.setItemHeight(30)
        self.l.setFont(0, gFont("Regular", 20))
        menulist = []
        if embeddedAvailable:
            res = [('embedded')]
            res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'key_red.png'))))
            res.append(MultiContentEntryText(pos=(60, 5), size=(330, 25), font=0, flags=RT_VALIGN_CENTER, text=__("Choose from embedded subtitles")))
            menulist.append(res)
        if searchSupport:
            res = [('search')]
            res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(os.path.join(os.path.dirname(__file__), 'img','key_blue.png'))))
            res.append(MultiContentEntryText(pos=(60, 5), size=(330, 25), font=0, flags=RT_VALIGN_CENTER, text=__("Search subtitles")))
            menulist.append(res)
        if embeddedAvailable or searchSupport:
            self.l.setList(menulist)

class SubsChooser(Screen):
    skin = """
        <screen position="center,center" size="610,460" zPosition="3" >
           <!-- <widget source="filename" render="Label" position="10, 10" size="590,50"  valign="center" halign="center" font="Regular;21" /> -->
            <!-- <eLabel position="5,65" size="600,1" backgroundColor="#999999" /> -->
            <widget name="file_list" position="0,30" size="610,330" scrollbarMode="showOnDemand" />
            <eLabel position="5,370" size="600,1" backgroundColor="#999999" />
            <widget name="menu_list" position="0,380" size="610,80" scrollbarMode="showOnDemand" />
        </screen>
        """

    def __init__(self, session, subdir=None, embeddedSupport=False, searchSupport=False):
        Screen.__init__(self, session)
        self.session = session
        defaultDir = subdir
        if subdir is not None and not subdir.endswith('/'):
            defaultDir = subdir + '/'
        self.embeddedList = None
        self.embeddedSubtitle = None
        if embeddedSupport:
            service = self.session.nav.getCurrentService()
            subtitle = service and service.subtitle()
            self.embeddedList = subtitle and subtitle.getSubtitleList()
        self.searchSupport = searchSupport
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        videoName = ref and os.path.split(ref.getPath())[1]
        self["filename"] = StaticText(videoName)
        self["file_list"] = SubFileList(defaultDir)
        self["menu_list"] = SubsChooserMenuList(self.embeddedList, searchSupport)
        self["actions"] = NumberActionMap(["OkCancelActions", "ColorActions"],
            {
                "ok": self.ok,
                "cancel": self.close,
                "red": self.embeddedSubsSelection,
                "blue":self.searchSubs
            }, -2)

        self.onLayoutFinish.append(self.updateTitle)
        self.onLayoutFinish.append(self.disableMenuList)

    def updateTitle(self):
        self.setTitle(__("Choose Subtitles"))

    def disableMenuList(self):
        self["menu_list"].selectionEnabled(False)

    def checkEmbeddedSubsSelection(self, embeddedSubtitle=None):
        if embeddedSubtitle:
            self.close(None, embeddedSubtitle)

    def checkDownloadedSubsSelection(self, downloadedSubtitle=None):
        if downloadedSubtitle:
            self.close(downloadedSubtitle, False, True)

    def ok(self):
        if self['file_list'].canDescent():
            self['file_list'].descent()
        else:
            filePath = os.path.join(self['file_list'].current_directory, self['file_list'].getFilename())
            print '[SubsFileChooser]' , filePath
            self.close(filePath, False)

    def embeddedSubsSelection(self):
        if self.embeddedList:
            self.session.openWithCallback(self.checkEmbeddedSubsSelection, SubsEmbeddedSelection)

    def searchSubs(self):
        if self.searchSupport:
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            try:
                sPath = ref.getPath()
            except Exception:
                sPath =None
            try:
                sName = ref.getName()
                sName = sName and [sName] or None
            except Exception:
                sName = None
            self.session.openWithCallback(self.checkDownloadedSubsSelection, SubsSearch, sPath, sName)


# source from openpli
class SubsEmbeddedSelection(Screen):
    skin = """<screen name="SubsEmbeddedSelection" position="center,center" size="485,220">
        <widget source="streams" render="Listbox" scrollbarMode="showOnDemand" position="10,40" size="465,180" zPosition="3" transparent="1" >
            <convert type="TemplatedMultiContent">
                {"templates":
                    {"default": (25, [
                        MultiContentEntryText(pos = (0, 0),   size = (35, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # key,
                        MultiContentEntryText(pos = (40, 0),  size = (60, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # number,
                        MultiContentEntryText(pos = (110, 0), size = (120, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # description,
                        MultiContentEntryText(pos = (240, 0), size = (200, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 4), # language,
                    ], True, "showNever"),
                    },
                "fonts": [gFont("Regular", 20), gFont("Regular", 16)],
                "itemHeight": 25
                }
            </convert>
        </widget>
    </screen>"""
    def __init__(self, session):
        Screen.__init__(self, session)
        self["streams"] = List([], enableWrapAround=True)
        self["actions"] = ActionMap(["SetupActions", "DirectionActions", "MenuActions"],
        {
            "ok": self.keyOk,
            "cancel": self.cancel,
        }, -2)
        self.onLayoutFinish.append(self.updateTitle)
        self.onLayoutFinish.append(self.fillList)

    def updateTitle(self):
        self.setTitle(__("Choose subtitles"))

    def fillList(self):
        idx = 0
        streams = []
        subtitlelist = self.getSubtitleList()
        for x in subtitlelist:
            number = str(x[1])
            description = "?"
            language = ""

            try:
                if x[4] != "und":
                    if LanguageCodes.has_key(x[4]):
                        language = LanguageCodes[x[4]][0]
                    else:
                        language = x[4]
            except:
                language = ""

            if x[0] == 0:
                description = "DVB"
                number = "%x" % (x[1])

            elif x[0] == 1:
                description = "teletext"
                number = "%x%02x" % (x[3] and x[3] or 8, x[2])

            elif x[0] == 2:
                types = ("unknown", "embedded", "SSA file", "ASS file",
                        "SRT file", "VOB file", "PGS file")
                try:
                    description = types[x[2]]
                except:
                    description = __("unknown") + ": %s" % x[2]
                number = str(int(number) + 1)
            print x, number, description, language
            streams.append((x, "", number, description, language))
            idx += 1
        self["streams"].list = streams


    def getSubtitleList(self):
        service = self.session.nav.getCurrentService()
        subtitle = service and service.subtitle()
        subtitlelist = subtitle and subtitle.getSubtitleList()
        embeddedlist = []
        for x in subtitlelist:
            if x[0] == 2:
                types = ("unknown", "embedded", "SSA file", "ASS file",
                            "SRT file", "VOB file", "PGS file")
                # filter embedded subtitles
                if x[2] not in [1, 2, 3, 4, 5, 6]:
                    continue
            embeddedlist.append(x)
        return embeddedlist

        self.selectedSubtitle = None
        return subtitlelist

    def cancel(self):
        self.close()

    def keyOk(self):
        cur = self["streams"].getCurrent()
        self.close(cur[0][:4])


class SubsSearchSettingsProvider(E2SettingsProvider):
    def __init__(self, providerName, defaults):
        configSubSection = subtitles_settings.search
        E2SettingsProvider.__init__(self, providerName, configSubSection, defaults)

class SubsSeekerE2UnpackRar(SubsSeeker):
    def _unpack_rarsub(self, rar_path, dest_dir):
        #hack to use eConsoleAppContainer, we cannot
        # call it from SubSearchThread, so we return tuple
        # with packed file and destination directory instread of
        # unpacked file, we detect this situation and unpack it in main thread later
        return (rar_path, dest_dir)


class SubsSearchThread(Thread):
    def __init__(self, fnc, param, callback, errorback):
        Thread.__init__(self)
        self.messagePump = ePythonMessagePump()
        self.messages = Queue()
        self.fnc = fnc
        self.param = param
        self.callback = callback
        self.errorback = errorback
        self.canceled = False
        self.messagePump.recv_msg.get().append(self.finished)

    def cancel(self):
        self.canceled = True

    def run(self):
        if self.param not in (None, ""):
            try:
                subtitles = self.fnc(*self.param)
                self.messages.put((subtitles, self.callback))
                self.messagePump.send(0)
            except Exception, ex:
                self.messages.put((ex, self.errorback))
                self.messagePump.send(0)

    def finished(self, val):
        if not self.canceled:
            message = self.messages.get()
            message[1](message[0])


class Message(object):
    def __init__(self, infowidget, errorwidget):
        self.infowidget = infowidget
        self.errorwidget = errorwidget
        self.timer = eTimer()
        self.timer.callback.append(self.hide)

    def info(self, text, timeout=None):
        self.timer.stop()
        self.errorwidget.hide()
        self.infowidget.setText(text)
        self.infowidget.show()
        if timeout:
            self.timer.start(timeout, True)

    def error(self, text, timeout=None):
        self.timer.stop()
        self.infowidget.hide()
        self.errorwidget.setText(text)
        self.errorwidget.show()
        if timeout:
            self.timer.start(timeout, True)

    def hide(self):
        self.timer.stop()
        self.errorwidget.hide()
        self.infowidget.hide()


class SubsSearch(Screen):
    skin = """
    <screen name="SubsSearch" position="center,center" size="700,520" zPosition="3" >
        <widget source="threadsnum" render="Label" position="660, 10" size="40, 25" font="Regular;16" zPosition="3" transparent="1" />
        <widget source="movieinfo" render="Listbox" position="10,10" size="680,60" zPosition="3" scrollbarMode="showNever" transparent="1" >
            <convert type="TemplatedMultiContent">
                {"template": [
                        MultiContentEntryText(pos = (0, 0),  size = (80, 25),  font = 0, color = 0xDAA520, flags = RT_HALIGN_LEFT,  text = 0), # moviename,
                        MultiContentEntryText(pos = (85, 0), size = (550, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 1), # moviesize,
                    ],
                    "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                    "itemHeight": 23,
                    "selectionEnabled":False
                }
            </convert>
        </widget>
        <widget source="languages" render="Listbox" position="10,70" size="680,80" zPosition="3" scrollbarMode="showNever"  transparent="1" >
            <convert type="TemplatedMultiContent">
                {"templates":
                    {"default": (25, [
                        MultiContentEntryText(pos = (0, 0),   size = (200, 25),  font = 0, color = 0xDAA520, flags = RT_HALIGN_LEFT,  text = 0), # langname,
                        MultiContentEntryText(pos = (205, 0),   size = (400, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1)
                    ], False, "showNever"),
                    },
                "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                "itemHeight": 23,
                }
            </convert>
        </widget>
        <widget source="subtitles_header" render="Listbox" scrollbarMode="showNever" position="5,145" size="690,25" zPosition="3" transparent="1" >
            <convert type="TemplatedMultiContent">
                {"templates":
                    {"default": (23, [
                        MultiContentEntryText(pos = (0, 0),   size = (120, 25),  font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 0), # language,
                        MultiContentEntryText(pos = (140, 0),  size = (335, 25),  font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 1), # filename,
                        MultiContentEntryText(pos = (500, 0), size = (140, 25), font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 2), # provider,
                        MultiContentEntryText(pos = (650, 0), size = (20, 25), font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 4), # sync,
                    ], False, "showOnDemand"),
                    "old": (23, [
                        MultiContentEntryText(pos = (0, 0),   size = (90, 25),  font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 0), # language,
                        MultiContentEntryText(pos = (100, 0),  size = (335, 25),  font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 1), # filename,
                        MultiContentEntryText(pos = (445, 0), size = (130, 25), font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 2), # provider,
                        MultiContentEntryText(pos = (585, 0), size = (95, 25), font = 0, flags = RT_HALIGN_LEFT,  color=0xcccccc, text = 3), # size,
                    ], False, "showOnDemand"),


                    },
                "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                "itemHeight": 23
                }
            </convert>
        </widget>
        <eLabel position="5,175" size="690,1" backgroundColor="#999999" />
        <widget name="loadmessage"  position="5,180" size="690,290" valign="center" halign="center" font="Regular;19" foregroundColor="#ffffff" zPosition="4" />
        <widget name="errormessage" position="5,180" size="690,290" valign="center" halign="center" font="Regular;19" foregroundColor="#ff0000" zPosition="5" />
        <widget source="subtitles" render="Listbox" scrollbarMode="showOnDemand" position="5,180" size="690,290" zPosition="3" transparent="1" >
            <convert type="TemplatedMultiContent">
                {"templates":
                    {"default": (23, [
                        MultiContentEntryPixmapAlphaBlend(pos = (0, 0),   size = (24, 24), png=0), # key,
                        MultiContentEntryText(pos = (30, 0),   size = (100, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # language,
                        MultiContentEntryText(pos = (140, 0),  size = (335, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # filename,
                        MultiContentEntryText(pos = (500, 0), size = (140, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # size,
                        MultiContentEntryPixmapAlphaBlend(pos = (650, 0),   size = (24, 24), png=6), # syncPng,
                    ], True, "showOnDemand"),
                    "old": (23, [
                        MultiContentEntryPixmapAlphaBlend(pos = (0, 0),   size = (24, 24), png=0), # key,
                        MultiContentEntryText(pos = (30, 0),   size = (60, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # language,
                        MultiContentEntryText(pos = (100, 0),  size = (335, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # filename,
                        MultiContentEntryText(pos = (445, 0), size = (130, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # size,
                        MultiContentEntryText(pos = (585, 0), size = (95, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 4), # sync,
                    ], True, "showOnDemand"),
                    },
                "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                "itemHeight": 23
                }
            </convert>
        </widget>
        <eLabel position="5,475" size="690,1" backgroundColor="#999999" />
        <widget source="bottom_menu" render="Listbox" position="10,485" size="680,180" zPosition="3" scrollbarMode="showNever" transparent="1" >
            <convert type="TemplatedMultiContent">
                {"template": [
                        MultiContentEntryPixmapAlphaBlend(pos = (0, 0),   size = (35, 25), png=0), # key,
                        MultiContentEntryText(pos = (40, 0),  size = (170, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # number,
                        MultiContentEntryPixmapAlphaBlend(pos = (245, 0),   size = (35, 25), png=2), # key,
                        MultiContentEntryText(pos = (285, 0),  size = (170, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 3), # number,
                        MultiContentEntryPixmapAlphaBlend(pos = (470, 0),   size = (35, 25), png=4), # key,
                        MultiContentEntryText(pos = (510, 0), size = (170, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 5), # description,
                    ],
                    "fonts": [gFont("Regular", 20), gFont("Regular", 16)],
                    "itemHeight": 25,
                    "selectionEnabled":False
                }
            </convert>
        </widget>
    </screen> """
    SEARCH_THREADS = []
    MAX_THREADS = 3

    def __init__(self, session, filepath=None, searchTitles=None, streamed=None):
        Screen.__init__(self, session)
        filepath = filepath or ""
        self.streamed = streamed is not None and streamed or filepath.startswith(('http','rtmp','mms','hds','hls'))
        searchTitles = searchTitles or []
        if filepath:
            dirname = os.path.dirname(filepath)
            dirnameFix = dirname.replace('.',' ').replace('_',' ').replace('-',' ')
            filename = os.path.splitext(os.path.basename(filepath))[0]
            filenameFix = filename.replace('.',' ').replace('_',' ').replace('-',' ')
            if filename not in searchTitles:
                searchTitles.append(filename)
            if filenameFix not in searchTitles:
                searchTitles.append(filenameFix)
            if dirname not in searchTitles:
                searchTitles.append(dirname)
            if dirnameFix not in searchTitles:
                searchTitles.append(dirnameFix)
        else: searchTitles.append('')
        downloadPath = subtitles_settings.search.downloadPath.value
        tmpPath = subtitles_settings.search.tmpPath.value
        self.seeker = SubsSeekerE2UnpackRar(downloadPath, tmpPath, captcha_cb=self.captchaCb, delay_cb=self.delayCb, message_cb=messageCB, settings_provider_cls=SubsSearchSettingsProvider)
        self.searchExpression = searchTitles[0]
        self.searchTitles = searchTitles
        self.filepath = filepath
        self.settingsChanged = False
        self['loadmessage'] = Label("")
        self['errormessage'] = Label("")
        self['threadsnum'] = StaticText("T(0)")
        self['movieinfo'] = List([])
        self['searchstatus'] = List([])
        self['languages'] = List([])
        self['subtitles_header'] = List([])
        self['subtitles'] = List([])
        self['bottom_menu'] = List([])
        self["actions"] = ActionMap(["ColorActions", "DirectionActions", "OkCancelActions"],
        {
            "ok": self.keyOk,
            "cancel": self.keyCancel,
            "up": self.keyUp,
            "down": self.keyDown,
            "right":self.keyRight,
            "left":self.keyLeft,
            "red":self.keyRed,
            "green":self.keyGreen,
            "yellow":self.keyYellow,
        }, -2)
        self.message = Message(self['loadmessage'],self['errormessage'])
        self.working = False
        Task.startWorkerThread()
        self.onLayoutFinish.append(self.updateTitle)
        self.onLayoutFinish.append(self.updateMovieInfoList)
        self.onLayoutFinish.append(self.updateSearchInfoList)
        self.onLayoutFinish.append(self.updateSubtitlesHeaderList)
        self.onLayoutFinish.append(self.updateBottomList)
        self.onLayoutFinish.append(self.searchSubs)
        self.onShown.append(self.cleanFinishedThreads)
        self.onShown.append(self.updateNumThreads)
        self.onClose.append(self.cancelSearch)
        self.onClose.append(self.closeSeekers)
        self.onClose.append(Task.stopWorkerThread)

    def updateTitle(self):
        self.title = __("Subtitles search")

    def updateMovieInfoList(self):
        movieName = os.path.splitext(os.path.basename(self.filepath))[0]
        movieSize = self.getMovieSizeStr()
        movieInfoList = [(__('Title') +':', movieName.encode('utf-8')),
                                         (__('Size') +':', movieSize)]
        self['movieinfo'].list = movieInfoList

    def getMovieSizeStr(self):
        if os.path.isfile(self.filepath):
            return "%.2f MB" % float(os.path.getsize(self.filepath) / (1024 * 1024))
        elif self.filepath.startswith('http://'):
            try:
                resp = urllib2.urlopen(HeadRequest(self.filepath))
                return  "%.2f MB" % float(long(resp.info().get('Content-Length')) / (1024 * 1024))
            except (urllib2.URLError, urllib2.HTTPError):
                return __("N/A")
            finally:
                if 'resp' in locals():
                    locals()['resp'].close()
        return __("N/A")

    def updateSearchInfoList(self):
        lang1 = subtitles_settings.search.lang1.value
        lang2 = subtitles_settings.search.lang2.value
        lang3 = subtitles_settings.search.lang3.value
        lang1 = lang1 in LanguageCodes and LanguageCodes[lang1][0] or lang1
        lang2 = lang2 in LanguageCodes and LanguageCodes[lang2][0] or lang2
        lang3 = lang3 in LanguageCodes and LanguageCodes[lang3][0] or lang3
        languages = "%s, %s, %s" % (__(lang1),__(lang2),__(lang3))
        searchInfoList = [ (__("Search Expression:"), self.searchExpression),
                                          (__("Preferred languages:"), languages)]
        self['languages'].list = searchInfoList

    def updateSubtitlesHeaderList(self):
        header=[(__("Language"), __("Release"),__("Provider"), __("Size"), __("S")),]
        self['subtitles_header'].list = header

    def updateSubsList(self):
        subtitleListGUI = []
        for sub in self.subtitlesList:
            size = 'size' in sub and sub['size']  or "???"
            sync = 'sync' in sub and sub['sync'] or False
            syncText = sync and __("T") or __("F")
            syncPNG = sync and loadPNG(os.path.join(os.path.dirname(__file__),'img', 'check.png')) or None
            countryPng = loadPNG(os.path.join(os.path.dirname(__file__),'img','countries',sub['country']+'.png'))
            subtitleListGUI.append((countryPng,__(sub['language_name']), sub['filename'], sub['provider'], size, syncText, syncPNG), )
        self['subtitles'].list = subtitleListGUI
        self.working = False

    def updateBottomList(self):
        redPng = loadPNG(os.path.join(os.path.dirname(__file__), 'img','key_red.png'))
        redText = __("Update Expression")
        greenPng = loadPNG(os.path.join(os.path.dirname(__file__), 'img','key_green.png'))
        greenText = __("Reload")
        yellowPng = loadPNG(os.path.join(os.path.dirname(__file__), 'img','key_yellow.png'))
        yellowText = __("Settings")
        self['bottom_menu'].list = [(redPng, redText, greenPng, greenText, yellowPng, yellowText), ]

    def updateNumThreads(self):
        self['threadsnum'].text= str("T(%s)"%len(self.SEARCH_THREADS))

    def closeSeekers(self):
        for seeker in self.seeker.seekers:
            seeker.close()

    def keyOk(self):
        if not self.working and self['subtitles'].count():
            self.working = True
            self.downloadSub(self.subtitlesList[self["subtitles"].index])

    def keyCancel(self):
        if not self.working:
            self.close()

    def keyUp(self):
        if not self.working and self['subtitles'].count():
            self.message.hide()
            self['subtitles'].selectPrevious()

    def keyDown(self):
        if not self.working and self['subtitles'].count():
            self.message.hide()
            self['subtitles'].selectNext()

    def keyRight(self):
        if not self.working and self['subtitles'].count():
            self.message.hide()
            self['subtitles'].index = self['subtitles'].count() - 1

    def keyLeft(self):
        if not self.working and self['subtitles'].count():
            self.message.hide()
            self['subtitles'].index = 0

    def keyRed(self):
        if not self.working:
            self.updateSearchExpression()
            print 'change search expression'

    def keyGreen(self):
        if not self.working:
            if self.settingsChanged:
                self.searchSubs()
                self.settingsChanged = False
                print 'reload'

    def keyYellow(self):
        if not self.working:
            seekers = self.seeker.seekers
            self.openSettings(seekers)
            print 'subtitles settings'

    def cleanFinishedThreads(self):
        notLiveThreads = []
        for thread in self.SEARCH_THREADS:
            if not thread.is_alive():
                notLiveThreads.append(thread)
        for thread in notLiveThreads:
            self.SEARCH_THREADS.remove(thread)
        self.updateNumThreads()

    def cancelSearch(self):
        self.cleanFinishedThreads()
        for thread in self.SEARCH_THREADS:
            thread.cancel()
        print len(self.SEARCH_THREADS),'threads still running'

    def searchSubs(self):
        self.cleanFinishedThreads()
        if len(self.SEARCH_THREADS) == self.MAX_THREADS:
            print 'limit of used threads exceeded, wait until some thread finishes'
            return

        self.cancelSearch()
        self.subtitlesList = []
        self.subtitlesDict = {}
        self.updateSubsList()
        searchFnc = self.seeker.getSubtitles
        langs = [subtitles_settings.search.lang1.value,
                    subtitles_settings.search.lang2.value,
                    subtitles_settings.search.lang3.value]
        params = (None, self.searchExpression, self.filepath, langs)
        searchThread = SubsSearchThread(searchFnc, params, self.searchSubsSuccess, self.searchSubsError)
        self.SEARCH_THREADS.append(searchThread)
        self.message.info(__("loading subtitles list..."))
        searchThread.start()
        self.updateNumThreads()


    def searchSubsSuccess(self, subtitles):
        print '[SubsSearch] search success'
        self.message.hide()
        self.cleanFinishedThreads()
        self.subtitlesDict = subtitles
        subtitlesList = self.seeker.getSubtitlesList(subtitles)
        subtitlesList = self.seeker.sortSubtitlesList(subtitlesList, sort_sync=True)
        langs = [subtitles_settings.search.lang1.value,
                    subtitles_settings.search.lang2.value,
                    subtitles_settings.search.lang3.value]
        if subtitles_settings.search.defaultSort.value == 'lang':
            subtitlesList = self.seeker.sortSubtitlesList(subtitlesList, langs, sort_langs=True)
        elif subtitles_settings.search.defaultSort.value == 'provider':
            subtitlesList = self.seeker.sortSubtitlesList(subtitlesList, langs, sort_langs=True)
        self.subtitlesList = subtitlesList
        if len(self.subtitlesList) ==0:
            noSubtitlesMessage = __("No subtitles found :(")
            noSubtitlesMessage+="\n" +__("Try update(simplify) search expression and try again..")
            self.message.info(noSubtitlesMessage)
        self.updateSubsList()

    def searchSubsError(self, error):
        print '[SubsSearch] search error', str(error)
        self.message.error(error.message, 4000)
        self.cleanFinishedThreads()
        self.subtitlesList = []
        self.subtitlesDict = {}
        self.updateSubsList()

    def downloadSub(self, subtitle):
        def downloadSubsCB(success, result):
            if success:
                self.downloadSubsSuccess(result)
            else:
                self.downloadSubsError(result)
            self.working = False
        self.message.info(__('downloading subtitles...'))
        downloadFnc = self.seeker.downloadSubtitle
        Task(downloadSubsCB, downloadFnc, subtitle, self.subtitlesDict).run()

    def downloadSubsSuccess(self, subFiles):
        print '[SubsSearch] download success %s' % str(subFiles)
        def successRarUnpack(result):
            self.message.hide()
            files = []
            for subFile in result:
                if os.path.splitext(subFile)[1] in ['.srt','.sub']:
                    files.append(subFile)
            self.selectSubFile(files)

        def errorRarUnpack(result):
            self.message.error(result, 4000)

        if isinstance(subFiles, tuple):
            rarPath, destDir = subFiles[0], subFiles[1]
            if not which('unrar'):
                print '[SubsSearch] unrar missing... :('
                unrarMissingMessage = __('cannot unpack rar sub-archive, unrar not find, please install it')
                unrarMissingMessage+=__("opkg install unrar")
                self.message.error(unrarMissingMessage,4000)
            else:
                self.message.info(__("unpacking..."))
                unrar(rarPath, destDir,successRarUnpack, errorRarUnpack)
        else:
            self.selectSubFile(subFiles)

    def downloadSubsError(self, failure):
        print '[SubsSearch] download error', str(failure)
        try:
            failure.raiseException()
        except SubtitlesCaptchaError as e:
            self.message.error(__("captcha doesn't match, try again..."), 4000)
        except SubtitlesDownloadError as e:
            self.message.error(str(e),4000)
        except Exception as e:
            self.message.error(str(e), 4000)

    def selectSubFile(self, subFiles):
        if len(subFiles) ==1:
            subFile = subFiles[0]
            if os.path.isfile(subFile):
                self.selectSubFileCB(['',subFile])
            else:
                self.message.error("download error", 4000)
        else:
            choiceTitle = __("There are more subtitles in unpacked archive\n please select which one you want to use")
            choiceList = [(os.path.basename(subfile), subfile) for subfile in subFiles]
            self.session.openWithCallback(self.selectSubFileCB, ChoiceBox, choiceTitle, choiceList)


    def selectSubFileCB(self, callback):
        def askOverrideCB(answer):
            if answer:
                try:
                    shutil.move(subOrigPath, subPath)
                    self.close(subPath)
                except (OSError,IOError) as e:
                    print '[SubsSearch] error when moving to moviedir:',e
                    self.close(subOrigPath)
            else:
                self.close(subOrigPath)

        if callback:
            subOrigPath = callback[1]
            downloadToMovieDir = subtitles_settings.search.downloadToMovieDir.value
            saveAsMovieName = subtitles_settings.search.saveAsMovieName.value
            askOverWrite = subtitles_settings.search.askOverrideExistingSubs.value
            if self.filepath and downloadToMovieDir:
                print '[SubsSearch] downloading to moviedir'
                movieDir = os.path.dirname(self.filepath)
                subName = os.path.basename(subOrigPath)
                if saveAsMovieName:
                    movieName = os.path.splitext(os.path.basename(self.filepath))[0]
                    subExt = os.path.splitext(subOrigPath)[1]
                    subName = movieName + subExt
                    subPath = os.path.join(movieDir, subName)
                else:
                    subPath = os.path.join(movieDir, subName)
                if os.path.isfile(subPath) and askOverWrite:
                    overrideText = __("Subtitles with this name already exist\nDo you want to override them") +"?"
                    self.session.openWithCallback(askOverrideCB, MessageBox, overrideText, MessageBox.TYPE_YESNO)
                else:
                    try:
                        shutil.move(subOrigPath, subPath)
                        self.close(subPath)
                    except (OSError,IOError) as e:
                        print '[SubsSearch] error when moving to moviedir:',e
                        self.close(subOrigPath)
            else:
                self.close(subOrigPath)

    def captchaCb(self, imagePath):
        return getCaptcha(self.session, imagePath)

    def delayCb(self, seconds):
        delay(self.session, seconds, __("Subtitles will be downloaded in") + " " + str(seconds) + " " + __("seconds"))

    def updateSearchExpression(self):
        self.session.openWithCallback(self.updateSearchExpressionCB, VirtualKeyBoard, __("Set search expression"), text=self.searchExpression)

    def updateSearchExpressionCB(self, callback):
        if callback:
            self.searchExpression = callback
            self.updateSearchInfoList()
            self.searchSubs()

    def openSettings(self, seekers):
        self.session.openWithCallback(self.openSettingsCB, SubsSearchSettings, seekers, self.streamed)

    def openSettingsCB(self, callback=None):
            if subtitles_settings.search.downloadToMovieDir.value:
                self.seeker.download_path = subtitles_settings.search.tmpPath.value
                self.seeker.tmp_path = subtitles_settings.search.tmpPath.value
            else:
                if subtitles_settings.search.tmpPath.isChanged():
                    self.seeker.tmp_path = subtitles_settings.search.tmpPath.value
                if subtitles_settings.search.downloadPath.isChanged():
                    self.seeker.download_path = subtitles_settings.search.downloadPath.value
            self.updateSearchInfoList()
            if (subtitles_settings.search.lang1.isChanged() or
                subtitles_settings.search.lang2.isChanged() or
                subtitles_settings.search.lang3.isChanged()):
                self.searchSubs()
            self.settingsChanged = True


class SubsSearchSettings(Screen, ConfigListScreen):
    skin = """<screen name="SubsSearch" position="center,center" size="650,500" zPosition="3" >
        <widget name="key_red" position="10,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
        <widget name="key_green" position="170,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
        <widget name="key_yellow" position="330,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
        <widget name="key_blue" position="490,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
        <eLabel position="-1,55" size="650,1" backgroundColor="#999999" />
        <widget name="config" position="10,75" size="630,160" scrollbarMode="showOnDemand" />
        <widget source="providers" render="Listbox" scrollbarMode="showOnDemand" position="10,260" size="630,230" zPosition="3" transparent="1" >
            <convert type="TemplatedMultiContent">
                {"templates":
                    {"default": (23, [
                        MultiContentEntryText(pos = (0, 0),   size = (200, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # name,
                        MultiContentEntryText(pos = (210, 0),  size = (200, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # lang,
                        MultiContentEntryText(pos = (420, 0), size = (200, 25), font = 0, flags = RT_HALIGN_RIGHT, text = 2) # enabled,
                    ], True, "showOnDemand"),
                    "notselected": (23, [
                        MultiContentEntryText(pos = (0, 0),   size = (200, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # name,
                        MultiContentEntryText(pos = (210, 0),  size = (200, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # lang,
                        MultiContentEntryText(pos = (420, 0), size = (200, 25), font = 0, flags = RT_HALIGN_RIGHT,  text = 2) # enabled,
                    ], False, "showOnDemand")
                    },
                "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                "itemHeight": 23
                }
            </convert>
        </widget>
    </screen> """

    FOCUS_CONFIG, FOCUS_PROVIDERS = range(2)

    def __init__(self, session, seekers, streamed=False):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [], session=session)
        self.seekers = seekers
        self.streamed = streamed
        self.focus = self.FOCUS_CONFIG
        self['providers'] = List([])
        self["key_green"] = Label(__("Save"))
        self["key_red"] = Label(__("Cancel"))
        self["key_blue"] = Label(__("Reset Defaults"))
        self["key_yellow"] = Label("")
        self["actions"] = ActionMap(["DirectionActions", "SetupActions", "OkCancelActions"],
        {
            "ok": self.keyOk,
            "cancel": self.keyCancel,
            "save":self.keySave,
            "up": self.keyUp,
            "down": self.keyDown,
            "right":self.keyRight,
            "left":self.keyLeft
        }, -2)
        self.onLayoutFinish.append(self.buildMenu)
        self.onLayoutFinish.append(self.updateProvidersList)
        self.onLayoutFinish.append(self.setConfigFocus)

    def buildMenu(self):
        menuList = []
        menuList.append(getConfigListEntry(__("Preferred Language") + ' 1', subtitles_settings.search.lang1))
        menuList.append(getConfigListEntry(__("Preferred Language") + ' 2', subtitles_settings.search.lang2))
        menuList.append(getConfigListEntry(__("Preferred Language") + ' 3', subtitles_settings.search.lang3))
        menuList.append(getConfigListEntry(__("Sort by"), subtitles_settings.search.defaultSort))
        if self.streamed:
            subtitles_settings.search.downloadToMovieDir.value = False
        else:
            menuList.append(getConfigListEntry(__("Download to movie directory"), subtitles_settings.search.downloadToMovieDir))
        if subtitles_settings.search.downloadToMovieDir.value:
            menuList.append(getConfigListEntry(__("Save as movie name"), subtitles_settings.search.saveAsMovieName))
            menuList.append(getConfigListEntry(__("Ask when overriding existing subtitles"), subtitles_settings.search.askOverrideExistingSubs))
        else:
            menuList.append(getConfigListEntry(__("Download Path"), subtitles_settings.search.downloadPath))
        menuList.append(getConfigListEntry(__("Temp Path"), subtitles_settings.search.tmpPath))
        self["config"].list = menuList
        self["config"].setList(menuList)

    def updateProvidersList(self):
        providerListGUI = []
        for seeker in self.seekers:
            providerName = seeker.provider_name
            providerLangs = ','.join(seeker.supported_langs)
            providerEnabled = seeker.settings_provider.getSetting('enabled') and __("enabled") or __("disabled")
            providerListGUI.append((providerName.encode('utf-8'), providerLangs, providerEnabled))
        self['providers'].list = providerListGUI

    def setConfigFocus(self):
        self.focus = self.FOCUS_CONFIG
        self['config'].instance.setSelectionEnable(True)
        self['providers'].style = 'notselected'

    def keyOk(self):
        if self.focus == self.FOCUS_PROVIDERS:
            provider = self.seekers[self['providers'].index]
            self.openProviderSettings(provider)
        else:
            current = self['config'].getCurrent()[1]
            if current == subtitles_settings.search.downloadPath:
                currentPath = subtitles_settings.search.downloadPath.value
                self.session.openWithCallback(self.setDownloadPath, LocationBox, "", "", currentPath)
            elif current == subtitles_settings.search.tmpPath:
                currentPath = subtitles_settings.search.tmpPath.value
                self.session.openWithCallback(self.setTmpPath, LocationBox, "", "", currentPath)
            elif current in [subtitles_settings.search.lang1,
                                                    subtitles_settings.search.lang2,
                                                    subtitles_settings.search.lang3]:
                self.session.openWithCallback(self.setLanguage, MyLanguageSelection, current.value)

    def setLanguage(self, language=None):
        if language:
            self['config'].getCurrent()[1].value = language
            self.buildMenu()

    def setDownloadPath(self, downloadPath=None):
        if downloadPath:
            subtitles_settings.search.downloadPath.value = downloadPath
            self.buildMenu()

    def setTmpPath(self, tmpPath =None):
        if tmpPath:
            subtitles_settings.search.tmpPath.value = tmpPath
            self.buildMenu()

    def keySave(self):
        for x in self["config"].list:
            x[1].save()
        self.close()

    def keyCancel(self):
        self.close()

    def keyUp(self):
        if self.focus == self.FOCUS_CONFIG:
            self['config'].instance.moveSelection(self["config"].instance.moveUp)
        else:
            if self['providers'].index == 0:
                self.focus = self.FOCUS_CONFIG
                self['providers'].style = "notselected"
                self['config'].instance.setSelectionEnable(True)
                self['config'].setCurrentIndex(len(self['config'].list) - 1)
            else:
                self['providers'].selectPrevious()

    def keyDown(self):
        if self.focus == self.FOCUS_CONFIG:
            if self['config'].getCurrentIndex() != len(self['config'].list) - 1:
                self['config'].instance.moveSelection(self["config"].instance.moveDown)
            else:
                self.focus = self.FOCUS_PROVIDERS
                self['config'].instance.setSelectionEnable(False)
                self['providers'].style = 'default'
                self['providers'].index = 0
        else:
            self['providers'].selectNext()


    def keyRight(self):
        if self.focus == self.FOCUS_CONFIG:
            ConfigListScreen.keyRight(self)
            if self['config'].getCurrent()[1] in [subtitles_settings.search.downloadToMovieDir]:
                self.buildMenu()

    def keyLeft(self):
        if self.focus == self.FOCUS_CONFIG:
            ConfigListScreen.keyLeft(self)
            if self['config'].getCurrent()[1] in [subtitles_settings.search.downloadToMovieDir]:
                self.buildMenu()

    def openProviderSettings(self, provider):
        self.session.openWithCallback(self.openProviderSettingsCB, SubsSearchProviderMenu, provider)

    def openProviderSettingsCB(self, changed=False):
        if changed:
            self.updateProvidersList()


class SubsSearchProviderMenu(Screen, ConfigListScreen):
    skin = """
            <screen position="center,center" size="610,435" >
                <widget name="key_red" position="10,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_green" position="160,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_yellow" position="310,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
                <widget name="key_blue" position="460,5" zPosition="1" size="140,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
                <eLabel position="-1,55" size="612,1" backgroundColor="#999999" />
                <widget name="config" position="0,75" size="610,360" scrollbarMode="showOnDemand" />
            </screen>"""

    def __init__(self, session, provider):
        Screen.__init__(self, session)
        self.provider = provider
        ConfigListScreen.__init__(self, [], session=session)
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.keyCancel,
                "green": self.keySave,
                "red": self.keyCancel,
                "blue": self.resetDefaults,
            }, -2)

        self["key_green"] = Label(__("Save"))
        self["key_red"] = Label(__("Cancel"))
        self["key_blue"] = Label(__("Reset Defaults"))
        self["key_yellow"] = Label("")
        self.buildMenu()
        self.onLayoutFinish.append(self.updateTitle)
        # self.onLayoutFinish.append(self.buildMenu)

    def updateTitle(self):
        self.setTitle(self.provider.provider_name.encode('utf-8') + __("settings"))

    def buildMenu(self):
        settingsProvider = self.provider.settings_provider
        settingList = settingsProvider.getE2Settings()
        self["config"].list = settingList
        self["config"].setList(settingList)

    def resetDefaults(self):
        for x in self["config"].list:
            x[1].value = x[1].default
        self.buildMenu()

    def keySave(self):
        for x in self["config"].list:
            x[1].save()
        configfile.save()
        self.close(True)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)

    def keyRight(self):
        ConfigListScreen.keyRight(self)
