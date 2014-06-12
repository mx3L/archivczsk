'''
Created on 22.5.2012

@author: marko
'''
import json
import time

from Components.Label import Label, LabelConditional, MultiColorLabel
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, \
    MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists

from Plugins.Extensions.archivCZSK import settings, _, log
from Plugins.Extensions.archivCZSK.engine.tools.util import BtoMB, BtoKB, BtoGB, \
    toString
from enigma import loadPNG, RT_HALIGN_RIGHT, RT_VALIGN_TOP, eSize, eListbox, \
    ePoint, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, \
    eListboxPythonMultiContent, gFont, getDesktop, ePicLoad, eServiceCenter, \
    iServiceInformation, eServiceReference, iSeekableService, iPlayableService, \
    iPlayableServicePtr, eTimer
from skin import parseColor
import skin


try:
    fonts = json.load(settings.CUSTOM_FONTS_PATH)
    REGULAR_FONT = fonts['regular']
    BOLD_FONT = fonts['bold']
    ITALIC_FONT = fonts['italic']
except Exception as e:
    log.error("cannot load custom fonts - %s"%str(e))
    REGULAR_FONT = "Regular"#"Ubuntu-R.ttf"
    BOLD_FONT = "Regular"#"Ubuntu-B.ttf"
    ITALIC_FONT = "Regular" #"Ubuntu-I.ttf"

try:
    colors = json.load(settings.CUSTOM_COLORS_PATH)
    class Color:
        RED = colors['red']
        GREEN = colors['green']
        BLUE = colors['blue']
        YELLOW = colors['yellow']
        YELLOW_MILD = colors['yellow_mild']
        WHITE = colors['white']
        BLACK = colors['black']
        GREY = colors['grey']
except Exception as e:
    log.error("cannot load custom colors- %s"%str(e))
    class Color:
        RED = 0xff0000
        GREEN = 0x00ff00
        BLUE = 0x0000ff
        YELLOW = 0xffff00
        YELLOW_MILD= 0xFCE083
        WHITE = 0xffffff
        BLACK = 0x000000
        GREY = 0xdddddd

try:
    size = json.load(settings.CUSTOM_SIZES_PATH)
    class Size:
        SMALL = size['small']
        MEDIUM = size['medium']
        BIG = size['big']
except Exception as e:
    log.error("cannot load custom sizes- %s"%str(e))
    class Size:
        SMALL = 18
        MEDIUM = 21
        BIG = 23

PNG_PATH = settings.IMAGE_PATH + '/'
SPINNER_PATH = PNG_PATH + 'spinner/'

class Font:
    REGULAR_SMALL = 0
    REGULAR_MEDIUM = 1
    REGULAR_BIG = 2
    ITALIC_SMALL = 3
    ITALIC_MEDIUM = 4
    ITALIC_BIG = 5
    BOLD_SMALL = 6
    BOLD_MEDIUM = 7
    BOLD_BIG = 8

def MultiContentEntryFormattedText(pos=(0, 0), size=(0, 0), fontSize=Size.MEDIUM, flags=RT_HALIGN_LEFT | RT_VALIGN_TOP, text="", color=None, color_sel=None, backcolor=None, backcolor_sel=None, border_width=None, border_color=None):
    if ("[B]" in text and "[/B]" in text) or ("[b]" in text and "[/b]" in text) :
        if fontSize == Size.SMALL:
            font = Font.BOLD_SMALL
        elif fontSize == Size.MEDIUM:
            font = Font.BOLD_MEDIUM
        elif fontSize == Size.BIG:
            font = Font.BOLD_BIG
        if color is None:
            color = Color.YELLOW_MILD
    elif ("[I]" in text and "[/I]" in text) or ("[i]" in text and "[/i]" in text) :
        if fontSize == Size.SMALL:
            font = Font.ITALIC_SMALL
        elif fontSize == Size.MEDIUM:
            font = Font.ITALIC_MEDIUM
        elif fontSize == Size.BIG:
            font = Font.ITALIC_BIG
        else:
            font = Font.ITALIC_SMALL
    else:
        if fontSize == Size.SMALL:
            font = Font.REGULAR_SMALL
        elif fontSize == Size.MEDIUM:
            font = Font.REGULAR_MEDIUM
        elif fontSize == Size.BIG:
            font = Font.REGULAR_BIG
        else:
            font = Font.REGULAR_MEDIUM
    text = text.replace("[B]", "").replace("[/B]", "").replace("[b]", "").replace("[/b]", "")
    text = text.replace("[I]", "").replace("[/I]", "").replace("[i]", "").replace("[/i]", "")
    return  MultiContentEntryText(pos, size, font, flags, text, color, color_sel, backcolor, backcolor_sel, border_width, border_color)

class PanelList(MenuList):
    def __init__(self, list, itemHeight=29):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setItemHeight(itemHeight)
        self.l.setFont(Font.REGULAR_SMALL, gFont(REGULAR_FONT, 18))
        self.l.setFont(Font.REGULAR_MEDIUM, gFont(REGULAR_FONT, 21))
        self.l.setFont(Font.REGULAR_BIG, gFont(REGULAR_FONT, 23))
        self.l.setFont(Font.ITALIC_SMALL, gFont(ITALIC_FONT, 18))
        self.l.setFont(Font.ITALIC_MEDIUM, gFont(ITALIC_FONT, 21))
        self.l.setFont(Font.ITALIC_BIG, gFont(ITALIC_FONT, 23))
        self.l.setFont(Font.BOLD_SMALL, gFont(BOLD_FONT, 18))
        self.l.setFont(Font.BOLD_MEDIUM, gFont(BOLD_FONT, 21))
        self.l.setFont(Font.BOLD_BIG, gFont(BOLD_FONT, 23))

class PanelListDownload(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setItemHeight(56)
        self.l.setFont(Font.REGULAR_MEDIUM, gFont("Regular", 21))
        self.l.setFont(Font.REGULAR_BIG, gFont("Regular", 23))
        self.l.setFont(Font.REGULAR_SMALL, gFont("Regular", 17))

def PanelListEntryHD(name, idx, png='', textcolor=None):
    res = [(name)]
    if fileExists(png):
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(png)))
        res.append(MultiContentEntryFormattedText(pos=(60, 5), size=(950, 30), fontSize=Size.MEDIUM, flags=RT_VALIGN_TOP, text=toString(name), color=textcolor))
    else:
        res.append(MultiContentEntryFormattedText(pos=(5, 5), size=(950, 30), fontSize=Size.MEDIUM, flags=RT_VALIGN_TOP, text=toString(name), color=textcolor))
    return res

def PanelListEntrySD(name, idx, png='', textcolor=None):
    res = [(name)]
    if fileExists(png):
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(png)))
        res.append(MultiContentEntryFormattedText(pos=(60, 5), size=(950, 30), fontSize=Size.MEDIUM, flags=RT_VALIGN_TOP, text=toString(name), color=textcolor))
    else:
        res.append(MultiContentEntryFormattedText(pos=(5, 5), size=(330, 30), fontSize=Size.MEDIUM, flags=RT_VALIGN_TOP, text=toString(name), color=textcolor))
    return res

def PanelListDownloadEntry_SD(name, download):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(0, 5), size=(610, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_LEFT, text=toString(name)))
    if download.state == 'success_finished':
        res.append(MultiContentEntryText(pos=(0, 5), size=(570, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=_('finished'), color=0x00FF00))
    elif download.state == 'error_finished':
        res.append(MultiContentEntryText(pos=(0, 5), size=(570, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=_('finished with errors'), color=0xff0000))
    elif download.state == 'downloading':
        res.append(MultiContentEntryText(pos=(0, 5), size=(570, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=_('downloading')))
    return res


def PanelListDownloadEntry(name, download):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(0, 5), size=(640, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_LEFT, text=toString(name)))
    if download.state == 'success_finished':
        res.append(MultiContentEntryText(pos=(0, 5), size=(850, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=download.textState, color=0x00FF00))
    elif download.state == 'error_finished':
        res.append(MultiContentEntryText(pos=(0, 5), size=(850, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=download.textState, color=0xff0000))
    elif download.state == 'downloading':
        res.append(MultiContentEntryText(pos=(0, 5), size=(850, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=download.textState))
    return res


def PanelColorListEntry(name, value, color, sizePanelX):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_LEFT, text=name, color=color))
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=value, color=color))
    return res

def PanelColorListEntry2(name, value, colorName, colorValue, sizePanelX):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_LEFT, text=toString(name), color=colorName))
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_RIGHT, text=toString(value), color=colorValue))
    return res

def PanelListEntry2(name, sizePanelX, png=''):
    res = [(name)]
    if fileExists(png):
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 27), png=loadPNG(png)))
        res.append(MultiContentEntryText(pos=(60, 5), size=(sizePanelX - 60, 30), font=Font.REGULAR_SMALL, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=name))
    return res

def PanelListDownloadListEntry(pdownload):
    res = [(pdownload.name)]
    finishText = _('Finished:  ')
    if pdownload.finish_time is not None:
        finishText = _('Finished:  ') + time.strftime("%b %d %Y %H:%M:%S", time.localtime(pdownload.finish_time))

    sizeKB = BtoKB(pdownload.size)
    if sizeKB <= 1024 and sizeKB >= 0:
        size = ("%d KB        " % sizeKB)
    elif sizeKB <= 1024 * 1024:
        size = ("%d MB        " % BtoMB(pdownload.size))
    else:
        size = ("%.2f GB        " % BtoGB(pdownload.size))

    sizeText = _('Size:  ') + size
    stateText = pdownload.textState

    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(pdownload.thumb)))
    res.append(MultiContentEntryText(pos=(60, 5), size=(760, 30), font=Font.REGULAR_MEDIUM, flags=RT_HALIGN_LEFT, text=toString(pdownload.name)))
    res.append(MultiContentEntryText(pos=(0, 38), size=(900, 18), font=Font.REGULAR_SMALL, flags=RT_VALIGN_TOP | RT_HALIGN_RIGHT, text=sizeText, color=0xE6A800))

    if pdownload.state == 'success_finished':
        res.append(MultiContentEntryText(pos=(0, 38), size=(900, 18), font=Font.REGULAR_SMALL, flags=RT_VALIGN_TOP | RT_HALIGN_LEFT, text=finishText, color=0xE6A800))
        res.append(MultiContentEntryText(pos=(0, 38), size=(900, 18), font=Font.REGULAR_SMALL, flags=RT_VALIGN_TOP | RT_HALIGN_CENTER, text=stateText, color=0x00FF00))
    elif pdownload.state == 'error_finished':
        res.append(MultiContentEntryText(pos=(0, 38), size=(900, 18), font=Font.REGULAR_SMALL, flags=RT_VALIGN_TOP | RT_HALIGN_LEFT, text=finishText, color=0xE6A800))
        res.append(MultiContentEntryText(pos=(0, 38), size=(900, 18), font=Font.REGULAR_SMALL, flags=RT_VALIGN_TOP | RT_HALIGN_CENTER, text=stateText, color=0xff0000))
    elif pdownload.state == 'downloading':
        res.append(MultiContentEntryText(pos=(0, 38), size=(900, 18), font=Font.REGULAR_SMALL, flags=RT_VALIGN_TOP | RT_HALIGN_CENTER, text=stateText, color=0xE6A800))
    return res



class MyConditionalLabel(LabelConditional):
    def __init__(self, text, conditionalFunction):
        LabelConditional.__init__(self, text, withTimer=False)
        self.conditionalFunction = conditionalFunction


class TipBar():
    def __init__(self, tip_list=[], startOnShown=False, tip_timer_refresh=10):

        self["tip_pixmap"] = Pixmap()
        self["tip_label"] = Label("")

        self.tip_list = tip_list
        self.tip_selection = 0
        self.tip_timer_refresh = tip_timer_refresh * 1000
        self.tip_timer = eTimer()
        self.tip_timer_running = False
        self.tip_timer.callback.append(self.changeTip)
        if startOnShown:
            self.onFirstExecBegin.append(self.startTipTimer)

        self.onStartWork.append(self.__stop)
        self.onStopWork.append(self.__start)

        self.onClose.append(self.__exit)

    def updateTipList(self, tip_list):
        self.tip_list = tip_list

    def changeTip(self):
        if len(self.tip_list) > 0:
            if self.tip_selection + 1 >= len(self.tip_list):
                self.tip_selection = 0
            else:
                self.tip_selection += 1
            self["tip_pixmap"].instance.setPixmap(self.tip_list[self.tip_selection][0])
            self["tip_label"].setText(self.tip_list[self.tip_selection][1])
        else:
            self["tip_pixmap"].instance.setPixmap(None)
            self["tip_label"].setText("")


    def __stop(self):
        self["tip_pixmap"].hide()
        self["tip_label"].hide()
        self.stopTipTimer()

    def __start(self):
        self["tip_pixmap"].show()
        self["tip_label"].show()
        self.startTipTimer()

    def startTipTimer(self):
        if not self.tip_timer_running:
            self.tip_timer.start(self.tip_timer_refresh)
            self.tip_timer_running = True

    def stopTipTimer(self):
        if self.tip_timer_running:
            self.tip_timer.stop()
            self.tip_timer_running = False

    def __exit(self):
        self.stopTipTimer()
        del self.tip_timer


class LoadingScreen(Screen):
    skin = """
        <screen position="center,center" size="76,76" flags="wfNoBorder" backgroundColor="background" >
        <eLabel position="2,2" zPosition="1" size="72,72" font="Regular;18" backgroundColor="background"/>
        <widget name="spinner" position="14,14" zPosition="2" size="48,48" alphatest="on" transparent="1" />
        </screen>"""

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)

        self["spinner"] = Pixmap()
        self.curr = 0
        self.__shown = False

        self.timer = eTimer()
        self.timer.timeout.get().append(self.showNextSpinner)

    def start(self):
        self.__shown = True
        self.show()
        self.timer.start(130, True)

    def stop(self):
        self.hide()
        self.timer.stop()
        self.__shown = False

    def isShown(self):
        return self.__shown

    def showNextSpinner(self):
        self.timer.stop()
        self.curr += 1
        spin = SPINNER_PATH + str(self.curr) + ".png"
        if not fileExists(spin):
            self.curr = 0
            spin = SPINNER_PATH + str(self.curr) + ".png"
        self["spinner"].instance.setPixmapFromFile(spin)
        self.timer.start(130, True)


class CutLabel(Label):
    def __init__(self, text, cutLeft=True, replaceChar='.', replaceCharNum=4):
        self.maxChars = 9999
        self.cutLeft = cutLeft
        self.replaceChar = replaceChar
        self.replaceCharNum = replaceCharNum
        self.testInstance = None
        Label.__init__(self, text)

    def applySkin(self, desktop, parent):
        # testInstance = self.GUI_WIDGET(parent)
        testInstance = self.testInstance
        testInstance.hide()
        testSkinAttributes = []
        if self.skinAttributes:
            for (attrib, value) in self.skinAttributes:
                if attrib == 'size':
                    x, y = value.split(',')
                    x = '2000'
                    new_value = x + ',' + y
                    testSkinAttributes.append((attrib, new_value))
                else:
                    testSkinAttributes.append((attrib, value))
            skin.applyAllAttributes(testInstance, desktop, testSkinAttributes, parent.scale)
        Label.applySkin(self, desktop, parent)
        maxWidth = self.instance.size().width()

        # some random text
        text = 'DSADJASNKDNSJANDJKSANDJKSANDNASJKNDSJKANDJKSANDJKAS'
        text += 'FDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFSDFDSFDS'
        text += 'FDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFSDFDSFDS'
        text += 'FDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFDSFSDFDSFDS'

        testInstance.setText(text)
        actWidth = testInstance.calculateSize().width()
        pixsPerChar = float(actWidth) / float(len(text))
        print actWidth, '/', len(text), '=', pixsPerChar
        print maxWidth
        if pixsPerChar > 0:
            self.maxChars = int(maxWidth / pixsPerChar)
        print self.maxChars

    def GUIcreate(self, parent):
        self.testInstance = self.GUI_WIDGET(parent)
        Label.GUIcreate(self, parent)

    def GUIdelete(self):
        self.testInstance = None
        Label.GUIdelete(self)


    def setText(self, text):
        print len(text), self.maxChars
        if len(text) > self.maxChars:
            cutChars = len(text) - self.maxChars
            if self.cutLeft:
                text = text[cutChars:]
                text = "%s %s" % (self.replaceChar * self.replaceCharNum, text[self.replaceCharNum + 1:])
            else:
                text = text[:self.cutChars]
                text = "%s %s" % (text[:-self.replaceCharNum + 1], self.replaceChar * self.replaceCharNum)
        Label.setText(self, text)


class MultiLabelWidget():
    def __init__(self, widget1, widget2):
        position = widget1.position
        size1 = widget1.instance.calculateSize()
        widget2.instance.move(ePoint(position[0] + size1.width() + 10, position[1]))


class CategoryWidget():
    color_black = "#000000"
    color_white = "#ffffff"
    color_red = "#ff0000"
    color_grey = "#5c5b5b"

    def __init__(self, screen, name, label):
        # print 'intializing category widget %s-%s' % (name, label.encode('utf-8'))
        self.screen = screen
        self.name = name
        self.label = label
        if isinstance(label, unicode):
            self.label = label.encode('utf-8')
        self.x_position = 0
        self.y_position = 0
        self.x_size = 100
        self.y_size = 100
        self.active = False

        self.foregroundColor_inactive = self.color_white
        self.backgroundColor_inactive = self.color_black
        self.foregroundColor_active = self.color_red
        self.backgroundColor_active = self.color_black

        self.screen[self.name] = Label(self.label)

    def get_skin_string(self):
        return """<widget name="%s" size="%d,%d" position="%d,%d" zPosition="1" backgroundColor="%s" foregroundColor="%s" font="Regular;20"  halign="center" valign="center" />"""\
             % (self.name, self.x_size, self.y_size, self.x_position, self.y_position, self.backgroundColor_inactive, self.foregroundColor_inactive)

    def setText(self, text):
        self.screen[self.name].setText(text)

    def activate(self):
        self.active = True
        self.setText(self.label)
        self.screen[self.name].instance.setForegroundColor(parseColor(self.foregroundColor_active))
        self.screen[self.name].instance.setBackgroundColor(parseColor(self.backgroundColor_active))

    def deactivate(self):
        self.active = False
        self.setText(self.label)
        self.screen[self.name].instance.setForegroundColor(parseColor(self.foregroundColor_inactive))
        self.screen[self.name].instance.setBackgroundColor(parseColor(self.backgroundColor_inactive))


class CategoryWidgetHD(CategoryWidget):
    def __init__(self, screen, name, label, x_position, y_position):
        CategoryWidget.__init__(self, screen, name, label)
        self.x_position = x_position
        self.y_position = y_position
        self.x_size = 130
        self.y_size = 30

class CategoryWidgetSD(CategoryWidget):
    def __init__(self, screen, name, label, x_position, y_position):
        CategoryWidget.__init__(self, screen, name, label)
        self.x_position = x_position
        self.y_position = y_position
        self.x_size = 80
        self.y_size = 30

class ButtonLabel(MultiColorLabel):
    TYPE_NORMAL = 0
    TYPE_PRESSED = 1
    TYPE_DISABLED = 2

    def __init__(self, text, state=0):
        MultiColorLabel.__init__(self, text)
        self.changeLabel(state)

    def changeLabel(self, idx):
        self.setForegroundColorNum(idx)
        self.setBackgroundColorNum(idx)


def showInfoMessage(session, message, timeout=3, cb=None):
    if cb is not None:
        session.openWithCallback(cb, MessageBox, text=toString(message), timeout=timeout, type=MessageBox.TYPE_INFO)
    else:
        session.open(MessageBox, text=toString(message), timeout=timeout, type=MessageBox.TYPE_INFO)

def showWarningMessage(session, message, timeout=3, cb=None):
    if cb is not None:
        session.openWithCallback(cb, MessageBox, text=toString(message), timeout=timeout, type=MessageBox.TYPE_WARNING)
    else:
        session.open(MessageBox, text=toString(message), timeout=timeout, type=MessageBox.TYPE_WARNING)

def showErrorMessage(session, message, timeout=3, cb=None):
    if cb is not None:
        session.openWithCallback(cb, MessageBox, text=toString(message), timeout=timeout, type=MessageBox.TYPE_ERROR)
    else:
        session.open(MessageBox, text=toString(message), timeout=timeout, type=MessageBox.TYPE_ERROR)

def showYesNoDialog(session, message, cb):
    session.openWithCallback(cb, MessageBox, text=toString(message), type=MessageBox.TYPE_YESNO)





