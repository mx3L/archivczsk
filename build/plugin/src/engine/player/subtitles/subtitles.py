# -*- coding: UTF-8 -*-
#################################################################################
#
#    Subtitles library 0.35 for Dreambox-Enigma2
#    Coded by mx3L (c)2012
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

import urllib2
import os
import traceback
from re import compile as re_compile
from os import path as os_path, listdir
from twisted.internet import defer


from enigma import  RT_HALIGN_RIGHT, RT_VALIGN_TOP, eSize, ePoint, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListboxPythonMultiContent, gFont, getDesktop, eServiceCenter, iServiceInformation, eServiceReference, iSeekableService, iPlayableService, iPlayableServicePtr, eTimer, addFont, gFont
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigSelection, ConfigYesNo, configfile, getConfigListEntry
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.FileList import FileList
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from Tools.Directories import SCOPE_SKIN_IMAGE, SCOPE_PLUGINS, resolveFilename, SCOPE_LANGUAGE
from Tools.LoadPixmap import LoadPixmap
from skin import parseColor

def debug(data):
    if DEBUG:
        print '[SubsSupport]', data.encode('utf-8')

# localization function
from . import _

# set the name of plugin in which this library belongs 
PLUGIN_NAME = 'archivCZSK'

#set debug mode
DEBUG = False

# set supported encodings, you have to make sure, that you have corresponding python
# libraries in %PYTHON_PATH%/encodings/ (ie. iso-8859-2 requires iso_8859_2.py library)

# to choose encodings for region you want, visit:
# http://docs.python.org/release/2.4.4/lib/standard-encodings.html

#Common encodings for all languages
ALL_LANGUAGES_ENCODINGS = ['utf-8']

#Common central European encodings
CENTRAL_EASTERN_EUROPE_ENCODINGS = ['windows-1250', 'iso-8859-2', 'maclatin2', 'IBM852']
WESTERN_EUROPE_ENCODINGS = ['windows-1252', 'iso-8859-15', 'macroman', 'ibm1140', 'IBM850']
RUSSIAN_ENCODING = ['windows-1251', 'cyrillic', 'maccyrillic', 'koi8_r', 'IBM866']


ENCODINGS = {_("Central and Eastern Europe") : CENTRAL_EASTERN_EUROPE_ENCODINGS,
             _("Western Europe"):WESTERN_EUROPE_ENCODINGS,
             _("Russia"):RUSSIAN_ENCODING }

#E2_FONT_PATH = '/usr/share/fonts/'
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts")

# fontname-R: regular font
# fontname-B: bold font
# fontname-I: italic font

# set your fonts - fonts has to be in directory fonts(fontname-R,fontname-I,fontname-B)
FONT = {
        "Ubuntu":({"regular":"Ubuntu-R.ttf",
                    "italic":"Ubuntu-I.ttf",
                    "bold":"Ubuntu-B.ttf"}),
        
        
        "Default": ({"regular":"Regular",
                     "italic":"Regular",
                     "bold":"Regular"})
        }
#initializing fonts
print "[Subtitles] initializing fonts in %s" % FONT_PATH
FONT_CP = FONT.copy()

for f in FONT_CP.keys():
    if f == 'Default':
        continue
    
    regular = FONT[f]['regular']
    italic = FONT[f]['italic']
    bold = FONT[f]['bold']
    # only add font with all styles[italic,bold,regular]
    if os.path.isfile(os.path.join(FONT_PATH, regular)) and os.path.isfile(os.path.join(FONT_PATH, italic)) and os.path.isfile(os.path.join(FONT_PATH, bold)):
        addFont(os.path.join(FONT_PATH, regular), regular, 100, False)
        addFont(os.path.join(FONT_PATH, italic), italic, 100, False)
        addFont(os.path.join(FONT_PATH, bold), bold, 100, False)
    else:
        del FONT[f]

FONT_CP = None

# initializing parsers
PARSERS = []
#pkgparsers = __import__('parsers')
for module in os.listdir(os.path.join(os.path.dirname(__file__), 'parsers')):
    if module == '__init__.py' or module == 'baseparser.py' or module[-3:] != '.py':
        continue
    module = module[:-3]
    #parser = __import__('parsers', fromlist=[module]).parserClass
    exec 'import %s.%s' % ('parsers', module)
    parsermod = eval('%s.%s' % ('parsers', module))
    parser = parsermod.parserClass
    debug('found %s %s' % (parser, dir(parser)))
    PARSERS.append(parser)
del module

#initializing settings
plugin_settings = getattr(config.plugins, PLUGIN_NAME)
setattr(plugin_settings, 'subtitles', ConfigSubsection())
subtitles_settings = getattr(plugin_settings, 'subtitles')

subtitles_settings.showSubtitles = ConfigYesNo(default=True)
subtitles_settings.autoLoad = ConfigYesNo(default=True)

choicelist = []
for i in range(-100000, 100000, 100):
    choicelist.append(("%d" % i, "%d ms" % i))
subtitles_settings.playerDelay = ConfigSelection(default=_("0"), choices=choicelist)

choicelist = []
for e in ENCODINGS.keys():
    choicelist.append(e)
subtitles_settings.encodingsGroup = ConfigSelection(default=_("Central and Eastern Europe"), choices=choicelist)

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

# set available colors for subtitles
choicelist = []
choicelist.append(("red", _("red")))
#choicelist.append(("#dcfcfc", _("grey")))
choicelist.append(("#00ff00", _("green")))
choicelist.append(("#ff00ff", _("purple")))
choicelist.append(("yellow", _("yellow")))
choicelist.append(("white", _("white")))
choicelist.append(("#00ffff", _("blue")))

subtitles_settings.color = ConfigSelection(default="white", choices=choicelist) 

                      
class SubsSupport(object):
    """
    User class for subtitles
    
    @param session: set active session
    @param subPath: set path for subtitles to load
    @param defaultPath: set default path when loading external subtitles
    @param forceDefaultPath: always use default path when loading external subtitles
    @param autoLoad: tries to load automatically subtitles according to name of file
    @param subclasOfScreen: if set to True this class should be subclass of E2 Screen class.
                            if set to False you have to use public function of this class to
                            to connect your media player (resume,pause,exit,after seeking, subtitles setup)
                            functions with subtitles
    @param alreadyPlaying: flag indicates that service already started
    @param showGUIInfoMessages: if set to True then shows GUI messages about subtitle processing 
    """
    
    def __init__(self, session=None, subPath=None, defaultPath=None, forceDefaultPath=False,
                 autoLoad=True, subclassOfScreen=True, alreadyPlaying=False, showGUIInfoMessages=False):
        if session is not None:
            self.session = session
        self.__subsScreen = self.session.instantiateDialog(SubsScreen)
        self.__subsEngine = SubsEngine(self.session, self.__subsScreen)
        self.__subsDict = None
        self.__loaded = False
        self.__playing = False
        self.__working = False
        self.__autoLoad = autoLoad
        self.__subsPath = None
        self.__subsDir = None
        self.__subsEnc = None
        self.__delayStep = 100
        self.__subsDelay = 0
        self.__playerDelay = int(subtitles_settings.playerDelay.getValue())
        self.__subsEngine.setPlayerDelay(self.__playerDelay)
        self.__startDelay = 1000
        self.__defaultPath = None
        self.__forceDefaultPath = forceDefaultPath
        self.__showGUIInfoMessages = showGUIInfoMessages
        self.__encodings = ALL_LANGUAGES_ENCODINGS + ENCODINGS[subtitles_settings.encodingsGroup.getValue()]
        self.__startTimer = eTimer()
        self.__startTimer.callback.append(self.__updateSubs)
        self.__startTimerRunning = False
        
        if subclassOfScreen:
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evStart: self.__serviceStarted,
                iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
            })
            self["SubsActions"] = HelpableActionMap(self, "SubtitlesActions",
                {
                "subtitles": (self.subsMenu, _("show subtitles menu")),
                "subsDelayDec":(self.subsDelayDec, _("increase subtitles delay")),
                "subsDelayInc": (self.subsDelayInc, _("decrease subtitles delay"))
                } , -6)
        
            self.onClose.append(self.exitSubs)
    
        if defaultPath is not None and os.path.isdir(defaultPath):
            self.__defaultPath = defaultPath
            self.__subsDir = defaultPath 
            
        if subPath is not None and self.__autoLoad:
            self.loadSubs(subPath)
            if alreadyPlaying and subclassOfScreen:
                self.resumeSubs()
                

#########  Public methods ##################
    
    def loadSubs(self, subsPath, newService=True):
        """
        loads subtitles from subsPath
        
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
            if subsPath.startswith('http'):
                pass
            else:
                if self.__defaultPath is not None and self.__forceDefaultPath:
                        self.__subsDir = self.__defaultPath
                else:
                    if os.path.isdir(os.path.dirname(subsPath)):
                        self.__subsDir = os.path.dirname(subsPath)
                    else:
                        self.__subsDir = self.__defaultPath
                if not os.path.isfile(subsPath):
                    subsPath = None
            
            if subsPath is not None:
                self.__subsDict, self.__subsEnc = self.__processSubs(subsPath)
 
            if self.__subsDict is not None:
                self.__subsPath = subsPath
                if newService:
                    self.__subsEngine.reset(newService)
                self.__subsEngine.pause()
                self.__subsEngine.setPlayerDelay(self.__playerDelay)
                self.__subsEngine.setSubsDict(self.__subsDict)
                self.__loaded = True
                self.__working = False
                return True
            else:
                self.__working = False
                self.resetSubs(True)
                return False
            
        self.__working = False
        self.resetSubs(True)
        return False
    
        
    def startSubs(self, time):
        """If subtitles are loaded then start to play them after time set in ms"""
        if self.__working or self.isSubsLoaded():
            while self.__working:
                pass
            self.__startTimer.start(time, True) 
            self.__startTimerRunning = True
        
    def isSubsLoaded(self):
        return self.__loaded
    
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
            self.__subsEngine.playAfterSeek()
        
    def showSubsDialog(self):
        if self.__loaded:
            print '[Subtitles] show dialog'   
            self.__subsScreen.show()
    
    def hideSubsDialog(self):
        if self.__loaded:
            print '[Subtitles] hide dialog' 
            if self.__subsScreen:
                self.__subsScreen.hide()
                
    def setPlayerDelay(self, delay):
        """set player delay in ms"""
        self.__playerDelay = delay
        
    def subsMenu(self):
        """opens subtitles settings"""
        if not self.__working:
            self.session.openWithCallback(self.__subsMenuCB, SubsMenu, self.__subsPath, self.__subsDir, self.__subsEnc)
            
    def subsDelayInc(self):
        if self.__loaded:
            self.__subsDelay += self.__delayStep
            self.__subsEngine.setSubsDelay(self.__subsDelay)
            self.__subsScreen.showDelay(self.__subsDelay)
    
    def subsDelayDec(self):
        if self.__loaded:
            self.__subsDelay -= self.__delayStep
            self.__subsEngine.setSubsDelay(self.__subsDelay)
            self.__subsScreen.showDelay(self.__subsDelay)
            
    def resetSubs(self, resetEnc=True, resetEngine=True, newService=True):
        if resetEnc:
            self.__subsEnc = None
        self.__encodings = ALL_LANGUAGES_ENCODINGS + ENCODINGS[subtitles_settings.encodingsGroup.getValue()]
        self.__subsEngine.pause()
        if resetEngine:
            self.__subsDelay = 0
            self.__subsEngine.reset(newService)
        self.__subsScreen.hide()
        self.__subsScreen.reloadSettings()
        self.__subsPath = None
        self.__subsDict = None
        self.__loaded = False
    
    def reloadSubsScreen(self):
        self.pauseSubs()
        self.__subsScreen.hide()
        self.__subsScreen.reloadSettings()
        self.resumeSubs()
            
    def exitSubs(self):
        """This method should be called at the end of usage of this class"""
        self.hideSubsDialog()
        
        if self.__subsEngine is not None:
            self.__subsEngine.exit()
        del self.__subsEngine
        
        if self.__subsScreen is not None:
            self.__subsScreen.exit()
            self.session.deleteDialog(self.__subsScreen)
        del self.__subsScreen
        
        self.__subsDict = None
        if self.__startTimerRunning:
            self.__startTimer.stop()
        del self.__startTimer
        
        subtitles_settings.showSubtitles.setValue(True)
        subtitles_settings.showSubtitles.save()
        print '[SubsSupport] closing subtitleDisplay'
        
###############################################################

##################### Private methods ########################
    
    def __subsMenuCB(self, subfile, settings_changed, changed_encoding=False, changed_encoding_group=False):
        # subtitles loaded and changed settings
        if self.__loaded and (self.__subsPath == subfile) and settings_changed and not (changed_encoding or changed_encoding_group):
            print '[SubsSupport] reset SubsScreen' 
            self.reloadSubsScreen()
                
        elif changed_encoding or changed_encoding_group:
            print '[SubsSupport] changed encoding or encoding_group'
            if changed_encoding_group:
                self.resetSubs(resetEnc=True, resetEngine=False, newService=False)
            else:
                self.resetSubs(resetEnc=False, resetEngine=False, newService=False)
            self.loadSubs(subfile, newService=False)
            self.playAfterSeek()
        
        elif subfile != self.__subsPath:
            print '[SubsSupport] changed subsfile'
            if self.__loaded:
                self.resetSubs(resetEnc=True, resetEngine=True, newService=False)
                self.loadSubs(subfile, newService=False)
                self.playAfterSeek()
            else:
                self.loadSubs(subfile, newService=False)
                self.resumeSubs()
        
    def __processSubs(self, subsPath):
        try:
            #loading subtitles from file/url and decoding text to unicode
            spp = SubProcessPath(subsPath, self.__encodings, self.__subsEnc)
            encoding = spp.getEncoding()
            subText = spp.getDecodedText()

            if encoding is None or subText is None:
                if self.__showGUIInfoMessages:
                    self.session.open(MessageBox, text=_("Cannot decode subtitles. Try another encoding group"),
                                      type=MessageBox.TYPE_WARNING, timeout=5)
                print 'Cannot decode subtitles. Try another encoding group'
                return None, None
                
            # parsing subtitles to dict
            subDict = None
            for parser in PARSERS:
                if parser.canParse(subsPath):
                    subDict = parser().parse(subText)
                    if subDict is None:
                        continue
                    break
                
            # try to parse by all parsers  
            # in case extension was not set right
            if subDict is None:
                for parser in PARSERS:
                    subDict = parser().parse(subText)
                    if subDict is None:
                        continue
                    break
                
            if subDict is None:
                if self.__showGUIInfoMessages:
                    self.session.open(MessageBox, text=_("Cannot parse subtitles"),
                                      type=MessageBox.TYPE_WARNING, timeout=5)
                print 'Cannot parse subtitles'
                return None, None
                
            ## removing style tags and adding style accordingly
            ss = SubStyler(subDict)
            subsDict = ss.subDict
            return subsDict, encoding
        
        except Exception:
            if self.__showGUIInfoMessages:
                self.session.open(MessageBox, text=_("Uknown error when processing subtitles"),
                                   type=MessageBox.TYPE_WARNING, timeout=5)
            traceback.print_exc()
            return None, None
        
    def __updateSubs(self):
        if self.isSubsLoaded():
            self.resumeSubs()
            return
        
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        if os.path.isdir(os.path.dirname(ref.getPath())):
            self.__subsDir = os.path.dirname(ref.getPath())
            subPath = os.path.splitext(ref.getPath())[0] + '.srt'
            if os.path.isfile(subPath):
                self.loadSubs(subPath)
            else:
                self.__working = False
        self.__working = False
        self.resumeSubs()
        
     
############ Methods triggered by videoEvents when SubsSupport is subclass of Screen ################

    def __serviceStarted(self):
        print '[SubsSupport] Service Started'
        # subtitles are loading or already loaded 
        if self.__working or self.isSubsLoaded():
            while self.__working:
                pass
            self.__startTimer.start(self.__startDelay, True)
            return
        
        self.resetSubs(True)    
        if self.__subsPath is None and self.__autoLoad:
            self.__working = True
            self.__startTimer.start(self.__startDelay, True)
    
    def __seekableStatusChanged(self):
        if not hasattr(self, 'seekstate'):
            return
        if self.seekstate == self.SEEK_STATE_PLAY:
            self.pauseSubs()
        elif self.seekstate == self.SEEK_STATE_PAUSE:
            self.resumeSubs()
        elif self.seekstate == self.SEEK_STATE_EOF:
            self.resetSubs(True)   
            
########################################################



########### Methods which extends InfobarSeek seek methods 

    def doSeekRelative(self, pts):
        print '[SubsSupport] doSeekRelative'
        super(SubsSupport, self).doSeekRelative(pts)
        self.playAfterSeek()
                
    def doSeek(self, pts):
        print '[SubsSupport] doSeek'
        super(SubsSupport, self).doSeek(pts)
        self.playAfterSeek()   
        
############################################################  
        
        

class SubsScreen(Screen):
        
    def __init__(self, session):
        desktop = getDesktop(0)
        size = desktop.size()
        self.sc_width = size.width()
        self.sc_height = size.height()
        fontSize = int(subtitles_settings.fontSize.getValue())
        fontType = subtitles_settings.fontType.getValue()
        if fontType not in FONT:
            fontType = "Default"
            subtitles_settings.fontType.setValue("Default")
            subtitles_settings.fontType.save()
        
        self.font = {"regular":gFont(FONT[fontType]['regular'], fontSize),
                     "italic":gFont(FONT[fontType]['italic'], fontSize),
                     "bold":gFont(FONT[fontType]['bold'], fontSize)}
        
        self.selected_font = "regular"
        
        delayPositionX = 50
        delayPositionY = 100
        self.delayTimer = eTimer()
        self.delayTimer.callback.append(self.hideDelay)
        self.delayTimerRunning = False
        self.delayTimerDelay = 1100
        
        position = int(subtitles_settings.position.getValue())
        vSize = fontSize * 3 + 5# 3 rows + reserve
        color = subtitles_settings.color.getValue()
        position = int(position * (float(self.sc_height - vSize) / 100)) 
        
        self.skin = """
            <screen name="SubtitleDisplay" position="0,0" size="%s,%s" zPosition="-1" backgroundColor="transparent" flags="wfNoBorder">
                    <widget name="delay" position="%s,%s" size="140,35" valign="center" halign="center" font="Regular;30" transparent="1" foregroundColor="yellow" shadowColor="#40101010" shadowOffset="3,3" />
                    <widget name="subtitles" position="0,%s" size="%s,%s" valign="center" halign="center" font="%s;%s" transparent="1" foregroundColor="%s" shadowColor="#40101010" shadowOffset="3,3" />
            </screen>""" % (str(self.sc_width), str(self.sc_height), str(delayPositionX), str(delayPositionY), str(position), str(self.sc_width), str(vSize), str(FONT[fontType]['regular']), str(fontSize), color)
            
        Screen.__init__(self, session)
        self.stand_alone = True
        print 'initializing subtitle display'
        
        self["subtitles"] = Label("")
        self["delay"] = Label("")
        
    def setColor(self, color):
        self["subtitles"].instance.setForegroundColor(parseColor(color))
        
    def setPosition(self, position):
        self["subtitles"].instance.move(ePoint(0, position))
        
    def setFonts(self, font):
        self.font = font
        self['subtitles'].instance.setFont(self.font['regular'])
        
    def reloadSettings(self):
        self.setColor(subtitles_settings.color.getValue())
        
        fontSize = int(subtitles_settings.fontSize.getValue())
        vSize = fontSize * 3
        position = int(subtitles_settings.position.getValue())
        position = int(position * (float(self.sc_height - vSize) / 100))
        
        self.setPosition(position)
        self.setFonts({"regular":gFont(FONT[subtitles_settings.fontType.getValue()]['regular'], fontSize),
                     "italic":gFont(FONT[subtitles_settings.fontType.getValue()]['italic'], fontSize),
                     "bold":gFont(FONT[subtitles_settings.fontType.getValue()]['bold'], fontSize)}) 
        
    def setSubtitle(self, sub):
        if sub['style'] != self.selected_font:
            self.selected_font = sub['style']
            self['subtitles'].instance.setFont(self.font[sub['style']])
        self["subtitles"].setText(sub['text'].encode('utf-8'))
    
    def hideSubtitle(self):
        self["subtitles"].setText("")
        
    def showDelay(self, delay):
        if delay > 0:
            self['delay'].setText("+%d ms" % delay)
        else:
            self['delay'].setText("%d ms" % delay)
        self.delayTimer.start(self.delayTimerDelay, True)
        self.delayTimerRunning = True
        
    def hideDelay(self):
        self['delay'].setText("")
        self.delayTimerRunning = False
    
    def exit(self):
        if self.delayTimerRunning:
            self.delayTimer.stop()
        del self.delayTimer
            
        
        

class SubsEngine(object):

    def __init__(self, session, subsScreen):
        self.subsScreen = subsScreen
        self.session = session
        self.srtsub = None
        self.video = Video(session)
        
        self.playerDelay = 0
        self.subsDelay = 0

        # subtitles state
        self.paused = True
        self.showSubs = False
        # current subtitle its position
        self.actsub = None
        self.pos = 0
        
        # positions of video player
        self.playPts = None
        self.oldPlayPts = None

        # timers, 
        self.timer1 = None
        self.timer1_running = False
        self.timer2 = None
        self.timer2_running = False
        self.seek_timer = None
        self.seek_timer_delay = 800 # to read correct pts after seeking
        self.seek_timer_running = False
        self.skip_timer = None
        self.skip_timer_delay = 100
        self.skip_timer_running = False
        self.timers_init = False


    def setSubsDict(self, subsDict):
        self.srtsub = subsDict
        
    def setPlayerDelay(self, playerDelay):
        self.playerDelay = playerDelay * 90
        
    def setSubsDelay(self, delay):
        self.subsDelay = delay * 90
        
    
    def reset(self, newService):
        self.pause()
        if newService:
            self.isServiceSet = False
            self.video.resetService()
        self.subsDelay = 0
        self.playPts = None
        self.oldPlayPts = None
        self.showSubs = False
        self.actsub = None
        self.srtsub = None
        self.playPts = None
        self.pos = 0
        
        
    def wait(self):   
        self.playPts = self.getPlayPts()
        #debug('pts: %s' % str(self.playPts))
            
        if self.playPts < self.actsub['start'] + self.subsDelay:
            diff = self.actsub['start'] + self.subsDelay - self.playPts
            diff = diff / 90
            #debug('difference: %s' % diff)
            # if difference is more then 100ms then wait
            if diff > 100:
                #debug('%s > 100, waiting' % diff)            
                self.timer1.start(diff, True)
                self.timer1_running = True
            else:
                self.show()
        else:
            if self.actsub['end'] + self.subsDelay - self.playPts < 0:
                #debug('%s < 0, skipping' % str(self.actsub['end'] + self.subsDelay - self.playPts))
                self.skipSubtitle()
            else:
                self.show()
                                                    
    def skipSubtitle(self):
        self.pos = self.pos + 1
        self.skip_timer_running = True
        self.skip_timer.start(self.skip_timer_delay, True)
 
    def skipTimerStop(self):
        self.skip_timer_running = False
        
    def resume(self):
        if not self.paused:
            return
        else:
            self.play() 
        
    def createTimers(self):
        self.timer1 = eTimer()
        self.timer1.callback.append(self.wait)
        self.timer2 = eTimer()
        self.timer2.callback.append(self.hide)
        self.seek_timer = eTimer()
        self.seek_timer.callback.append(self.setPlayPts)
        self.seek_timer.callback.append(self.doPlayAfterSeek)
        self.seek_timer_delay = 800 # to read correct pts after seeking
        self.skip_timer = eTimer()
        self.skip_timer.callback.append(self.setPlayPts)
        self.skip_timer.callback.append(self.play)
        self.skip_timer.callback.append(self.skipTimerStop)
        self.skip_timer_delay = 100
        self.timers_init = True
        
    @defer.inlineCallbacks    
    def play(self):
        def doPlay():
            if not self.timers_init:
                self.createTimers()
            self.doPlay()
        # we have to make sure that we have service to work with
        if not self.isServiceSet:
            self.isServiceSet = yield self.video.startService()
            if not self.isServiceSet:
                debug("cannot retrieve service, stopping")
                self.pause()
            else: doPlay()
        else: doPlay()

              
    def doPlay(self):
        self.paused = False
        
        if self.pos == 0:
            if len(self.srtsub) > 0:   
                sub = self.srtsub[0]
                self.actsub = sub
                self.wait()
            #subtitles didnt load correctly
            else:
                self.pause()
                   
        elif self.pos > 0 and self.pos < len(self.srtsub):
            sub = self.srtsub[self.pos]
            self.actsub = sub
            self.wait()
        
        #there arent more subtitles to show so we end
        else:
            self.pause()
                
    def pause(self):
        if self.paused:
            return
        self.paused = True
        self.subsScreen.hideSubtitle()
        self.stopTimers()
            
    def stopTimers(self):
        if self.timer1 is not None and self.timer1_running:
            self.timer1.stop()
            self.timer1_running = False
        if self.timer2 is not None and self.timer2_running:
            self.timer2.stop()
            self.timer2_running = False
        if self.skip_timer is not None and self.skip_timer_running:
            self.skip_timer.stop()
            self.skip_timer_running = False
        if self.seek_timer is not None and self.seek_timer_running:
            self.seek_timer.stop()
            self.seek_timer_running = False
        
        
    def playAfterSeek(self):
        if self.seek_timer is None:
            return
        self.pause()
        self.seek_timer.start(self.seek_timer_delay, True)
        self.seek_timer_running = True
                    
    def doPlayAfterSeek(self):
        self.seek_timer_running = False
        ptsBefore = self.oldPlayPts
        
        if self.playPts is None:
            return
                        
        elif self.playPts < ptsBefore: #seek backward
            while self.srtsub[self.pos]['start'] + self.subsDelay > self.playPts and self.pos > 0:
                self.pos = self.pos - 1
        else: #seek forward
            while self.srtsub[self.pos]['start'] + self.subsDelay < self.playPts and self.pos < len(self.srtsub) - 1:
                self.pos = self.pos + 1
        self.resume()
                      
    def show(self):
        self.timer1_running = False
        self.showSubs = True
        duration = int(self.actsub['duration'])#+self.delay
        self.subsScreen.setSubtitle(self.actsub)
        self.timer2.start(duration, True)
        self.timer2_running = True
            
            
    def hide(self):
        self.timer2_running = False
        self.showSubs = False
        self.subsScreen.hideSubtitle()
        
        if self.pos + 1 >= len(self.srtsub):
            self.pause()
        else:
            self.pos = self.pos + 1
            self.play()
    
    def showDialog(self): 
        self.subsScreen.show()
    
    def hideSubtitlesDialog(self): 
        self.subsScreen.hide()
                    
        
    def getPlayPts(self):
        pts = self.video.getCurrentPosition()
        if pts is None:
            pts = 0
        return pts
    
    def setPlayPts(self):
        self.oldPlayPts = self.playPts
        self.playPts = self.getPlayPts()
    
    def exit(self):
        self.pause()
        del self.timer1
        del self.timer2
        del self.seek_timer
        del self.skip_timer
        

class SubsEngine2(object):

    def __init__(self, session, subsScreen, srtDict, playerDelay):
        self.subsScreen = subsScreen
        self.session = session
        self.srtsub = srtDict
        self.service = None
        self.seek = None
        self.pos = 0
        self.playPts = None
        self.oldPlayPts = None
        self.actsub = None
        self.showSubs = False
        self.check_timer = None
        self.check_timer_delay = 200 # to read correct pts after seeking
        self.check_timer_running = False
        self.paused = True
        
        
    def reset(self, service=True):
        self.pause()
        if service:
            self.service = None
        self.seek = None
        self.playPts = None
        self.oldPlayPts = None
        self.showSubs = False
        self.actsub = None
        self.srtsub = None
        self.playPts = None
        self.pos = 0
        
        
    def wait(self):   
        self.playPts = self.getPlayPts()

        if self.playPts is None:
            return
        
        if self.showSubs:
            if (self.playPts - self.actsub['start']) >= 0 and (self.playPts - self.actsub['end']) <= 0:
                return
            else:
                self.hide()
                self.actsub = None
                return
              
        for sub in self.srtsub:
            diff = sub['start'] - self.playPts
            if diff > -18000 and diff < 18000:
                self.actsub = sub
                self.show()
                break
                                                     
    def resume(self):
        if not self.paused:
            return
        else:
            self.play()
              
        
    def play(self):
        self.paused = False   
        if self.check_timer is None:
            self.check_timer = eTimer()
            self.check_timer.callback.append(self.wait)
       
        while self.service is None:
            self.service = self.session.nav.getCurrentService()
        
        if self.seek is None:
            self.seek = self.service.seek()
        
        if len(self.srtsub) < 0:
            self.pause()
        if not self.check_timer_running:
            self.check_timer.start(self.check_timer_delay)
            self.check_timer_running = True
                
    def pause(self):
        if self.paused:
            return
        self.paused = True
        self.subsScreen.hideSubtitle()
        if self.check_timer is not None and self.check_timer_running:
            self.check_timer.stop()
            self.check_timer_running = False
        
    def playAfterSeek(self):
        pass
                      
    def show(self):
        self.showSubs = True
        self.subsScreen.setSubtitle(self.actsub)
  
    def hide(self):
        self.showSubs = False
        self.subsScreen.hideSubtitle()

    def showDialog(self):
        self.subsScreen.show()
    
    def hideSubtitlesDialog(self): 
        self.subsScreen.hide()
                    
    def getPlayPts(self):
        r = self.seek.getPlayPosition()
        if r[0]:
            return None
        return long(r[1])
    
    def exit(self):
        self.pause()
        del self.check_timer
    

    
        
class PanelList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setItemHeight(35)
        self.l.setFont(0, gFont("Regular", 22))
            
def PanelListEntry(name, idx, png=''):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(5, 5), size=(330, 30), font=0, flags=RT_VALIGN_TOP, text=name))
    return res        
        
        
class SubsMenu(Screen):
    skin = """
        <screen position="center,center" size="500,400" title="Main Menu" >
            <widget name="info_sub" position="0,5" size="500,40" valign="center" halign="center" font="Regular;25" transparent="1" foregroundColor="white" />
            <widget name="info_subfile" position="0,55" size="500,40" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="#DAA520" />
            <widget name="enc_sub" position="0,90" size="100,25" valign="center" halign="left" font="Regular;16" transparent="1" foregroundColor="white" />
            <widget name="enc_subfile" position="110,90" size="200,25" valign="center" halign="left" font="Regular;16" transparent="1" foregroundColor="#DAA520" />
            <widget name="menu" position="0,125" size="500,275" transparent="1" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, subfile=None, subdir=None, encoding=None):
        Screen.__init__(self, session)
        
        self["menu"] = PanelList([])
        self["info_sub"] = Label(_("Currently choosed subtitles"))
        self["info_subfile"] = Label("")
        self["enc_sub"] = Label("")
        self["enc_subfile"] = Label("")
        
        if subfile is not None:
            self["info_subfile"].setText(os.path.split(subfile)[1].encode('utf-8'))
            self["enc_sub"].setText(_("encoding"))
            if encoding:
                self["enc_subfile"].setText(encoding.encode('utf-8'))
            else:
                self["enc_subfile"].setText(_("cannot decode"))
        else:
            self["info_subfile"].setText(_("None"))
        
        self.title = _('Subtitles')
        self.lst = [unicode(_('Choose subtitles'), 'utf-8'),
                    unicode(_('Subtitles settings'), 'utf-8')]
        if subfile is not None:
            self.lst.append(unicode(_('Change encoding'), 'utf-8'))
            
        self.subfile = subfile
        self.subdir = subdir
        self.change_encoding = False
        self.change_encoding_group = False
        self.changed_settings = False
        self.__working = False
        
        self.onShown.append(self.setWindowTitle)

        self["actions"] = NumberActionMap(["SetupActions", "DirectionActions"],
            {
                "ok": self.okClicked,
                "cancel": self.cancel,
                "up": self.up,
                "down": self.down,
            }, -2)          
        self.onLayoutFinish.append(self.createMenu)
        
    def setWindowTitle(self):
        self.setTitle(self.title)
        
    def createMenu(self): 
        list = []
        for idx, x in enumerate(self.lst):
            list.append(PanelListEntry(x.encode('utf-8'), idx))      
        self["menu"].setList(list)
        self.__working = False
        
    def okClicked(self):
        if not self.__working:
            self.__working = True
            if self["menu"].getSelectedIndex() == 0:
                self.session.openWithCallback(self.fileChooserCB, SubsFileChooser, self.subdir)
            elif self["menu"].getSelectedIndex() == 1:
                self.session.openWithCallback(self.subsSetupCB, SubsSetup)
            elif self["menu"].getSelectedIndex() == 2:
                self.change_encoding = True
                self.__working = False
                self.cancel()
            
    def up(self):
        if not self.__working:
            self["menu"].up()

    def down(self):
        if not self.__working:
            self["menu"].down()
            
    def fileChooserCB(self, file=None):
        if file is not None:
            if self.subfile is not None and self.subfile == file:
                pass
            else: 
                self.subfile = file
                self.subdir = os.path.split(self.subfile)[0]
                self["info_subfile"].setText(os.path.split(self.subfile)[1].encode('utf-8'))
                self["enc_sub"].setText("")
                self["enc_subfile"].setText("")
        self.__working = False
            
    def subsSetupCB(self, changed=False, changedEncodingGroup=False):
        if changed:
            self.changed_settings = True
        if changedEncodingGroup:
            self.change_encoding_group = True
        self.__working = False
        
    def cancel(self):
        if not self.__working:
            self.close(self.subfile, self.changed_settings, self.change_encoding, self.change_encoding_group)     


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

        self.onChangedEntry = [ ]
        self.list = [ ]
        self.currentEncodingGroup = subtitles_settings.encodingsGroup.getValue()
        ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
        self.setup_title = _("Subtitles setting")
        
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.keyCancel,
                "green": self.keySave,
                "ok": self.keyOk,
                "red": self.keyCancel,
            }, -2)

        self["key_green"] = Label(_("Save"))
        self["key_red"] = Label(_("Cancel"))
        self["key_blue"] = Label("")
        self["key_yellow"] = Label("")
        
        self.buildMenu()
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle(_("Subtitles setting"))

    def buildMenu(self):
        del self.list[:]       
        self.list.append(getConfigListEntry(_("Show subtitles"), subtitles_settings.showSubtitles))
        self.list.append(getConfigListEntry(_("Font type"), subtitles_settings.fontType))
        self.list.append(getConfigListEntry(_("Font size"), subtitles_settings.fontSize))
        self.list.append(getConfigListEntry(_("Position"), subtitles_settings.position))                                                 
        self.list.append(getConfigListEntry(_("Color"), subtitles_settings.color))
        self.list.append(getConfigListEntry(_("Encoding"), subtitles_settings.encodingsGroup))
        self["config"].list = self.list
        self["config"].setList(self.list)

    def keyOk(self):
        current = self["config"].getCurrent()[1]
        pass
    
    def keySave(self):
        for x in self["config"].list:
            x[1].save()
        configfile.save()
        if self.currentEncodingGroup != subtitles_settings.encodingsGroup.getValue():
            self.close(True, True)
        self.close(True, False)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close(False, False)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)  

    def keyRight(self):
        ConfigListScreen.keyRight(self)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()



def FileEntryComponent(name, absolute=None, isDir=False):
        res = [ (absolute, isDir) ]
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name))
        if isDir:
            png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/directory.png"))
        else:
            png = LoadPixmap(os.path.join(os.path.dirname(__file__), 'subtitles.png'))
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

        if directory is None and self.showMountpoints: # present available mountpoints
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
                self.list.append(FileEntryComponent(name="<" + _("List of Storage Devices") + ">", absolute=None, isDir=True))
            elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
                self.list.append(FileEntryComponent(name="<" + _("Parent Directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))

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
    
class SubsFileChooser(Screen):
    skin = """
        <screen position="center,center" size="610,435" >
            <widget name="filelist" position="0,55" size="610,350" scrollbarMode="showOnDemand" />
        </screen>
        """
            
    def __init__(self, session, subdir=None):
        Screen.__init__(self, session)
        self.session = session
        defaultDir = subdir
        if subdir is not None and not subdir.endswith('/'):
            defaultDir = subdir + '/'
        print '[SubsFileChooser] defaultdir', defaultDir
        self.filelist = SubFileList(defaultDir)
        self["filelist"] = self.filelist
        
        self["actions"] = NumberActionMap(["OkCancelActions", "DirectionActions"],
            {
                "ok": self.okClicked,
                "cancel": self.close,
                "up": self.up,
                "down": self.down,
            }, -2)    
        
        self.onLayoutFinish.append(self.layoutFinished)
        
    def layoutFinished(self):
        self.setTitle(_("Choose Subtitles"))
        
    def okClicked(self):
        if self.filelist.canDescent():
            self.filelist.descent()
        else:
            filePath = os.path.join(self.filelist.current_directory, self.filelist.getFilename())
            print '[SubsFileChooser]' , filePath 
            self.close(filePath)
            
    def up(self):
        self['filelist'].up()

    def down(self):
        self['filelist'].down()


class SubProcessPath(object):
    def __init__(self, subfile, encodings, current_encoding=None):
        self.subfile = subfile
        
        self.text = None
        self.encoding = None
        self.encodings = encodings
        self.current_encoding = current_encoding
        
        if subfile[0:4] == 'http':
            try:
                print "[Subtitles] downloading from %s" % subfile
                text = self.request(subfile)
            except Exception:
                print "[Subtitles] cannot download subtitles %s" % subfile
                traceback.print_exc()
            else:
                self.text, self.encoding = self.decode(text) 
        else:
            try:
                f = open(subfile, 'r')
            except IOError:
                print '[Subtitles] cannot open subtitle file %s' % subfile
                self.text = None
            else:
                text = f.read()
                f.close()
                self.text, self.encoding = self.decode(text)
                 
    def getEncoding(self):
        return self.encoding
    
    def getDecodedText(self):
        return self.text     
    
    def decode(self, text):
        utext = None
        used_encoding = None
        current_encoding_idx = -1
        current_idx = 0
        
        if self.current_encoding is not None:
            current_encoding_idx = self.encodings.index(self.current_encoding)
            current_idx = current_encoding_idx + 1
            if current_idx >= len(self.encodings):
                current_idx = 0
        
        while current_idx != current_encoding_idx:
            enc = self.encodings[current_idx]
            try:
                print 'trying enc', enc
                utext = text.decode(enc)
                used_encoding = enc
                return utext, used_encoding
            except Exception:
                if enc == self.encodings[-1] and current_encoding_idx == -1:   
                    print '[Subtitles] cannot decode file'
                    return None, None
                elif enc == self.encodings[-1] and current_encoding_idx != -1:
                    current_idx = 0
                    continue
                else:
                    current_idx += 1
                    continue
        return text.decode(self.current_encoding), self.current_encoding
    
    
    def request(self, url):
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data   
            
        
class SubStyler(object):
    def __init__(self, subDict):
        self.subDict = subDict
        self.addStyle()

    
    def getStyledSubs(self):
        return self.subDict
        
    def removeTags(self, text):
        text = text.replace('<i>', '')
        text = text.replace('</i>', '')
        text = text.replace('<I>', '')
        text = text.replace('</I>', '')
        text = text.replace('<b>', '')
        text = text.replace('</b>', '')
        text = text.replace('<B>', '')
        text = text.replace('</B>', '')
        text = text.replace('<u>', '')
        text = text.replace('</u>', '')
        text = text.replace('<U>', '')
        text = text.replace('</U>', '')
        return text
        
            
    def addStyle(self):
        """adds style to subtitles using tags"""  
        for sub in self.subDict:
            sub['style'] = 'regular'
            if sub['text'].find('<i>') != -1 or sub['text'].find('<I>') != -1:
                sub['style'] = 'italic'
                sub['text'] = self.removeTags(sub['text'])
            
            elif sub['text'].find('<b>') != -1 or sub['text'].find('<B>') != -1:
                sub['style'] = 'bold'
                sub['text'] = self.removeTags(sub['text'])
                
            elif sub['text'].find('<u>') != -1 or sub['text'].find('<U>') != -1:
                sub['style'] = 'regular'
                sub['text'] = self.removeTags(sub['text'])
                

class Video(object):
    def __init__(self, session, serviceTryLimit=30):
        self.session = session
        self.service = None
        self.__serviceTimer = None
        self.__serviceTimerTryDelay = 300 #ms
        self.__serviceTryTime = 0
        self.__serviceTryLimit = serviceTryLimit * 1000
        self.__deferred = None
    
    def resetService(self):
        self.service = None

    @defer.inlineCallbacks    
    def startService(self, new=False):
        
        def fireDeferred():
            self.__deferred.callback(None)
            self.__deferred = None
            
        def getService():
            if self.__deferred is None:
                return
            
            if self.service is None:
                if self.__serviceTryTime < self.__serviceTryLimit:
                    self.__serviceTimer.start(self.__serviceTimerTryDelay, True)
                else:
                    del self.__serviceTimer
                    fireDeferred()
            else:
                del self.__serviceTimer
                fireDeferred()
            return self.__deferred
                
        def setService():
            self.__serviceTryTime += self.__serviceTimerTryDelay
            self.service = self.session.nav.getCurrentService()
            getService()
        
        self.__deferred = defer.Deferred()
        self.__serviceTimer = eTimer()
        self.__serviceTimer.callback.append(setService)    
        yield getService()
        
        setService = False
        if self.service is not None:
            setService = True
        defer.returnValue(setService)
        
    def __getSeekable(self):
        if self.service is None:
            return None
        return self.service.seek()
    
    def getCurrentPosition(self):
        seek = self.__getSeekable()
        if seek is None:
            return None
        r = seek.getPlayPosition()
        if r[0]:
            return None
        return long(r[1])

    def getCurrentLength(self):
        seek = self.__getSeekable()
        if seek is None:
            return None
        r = seek.getLength()
        if r[0]:
            return None
        return long(r[1])
