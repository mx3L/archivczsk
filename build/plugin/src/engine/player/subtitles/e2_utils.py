import os
import shutil
from threading import Thread
from twisted.python import log, failure
from twisted.internet import defer
from twisted.web.client import downloadPage
from Queue import Queue

from enigma import ePicLoad, ePythonMessagePump
from Components.Console import Console
from Components.config import ConfigText, ConfigSubsection, ConfigDirectory, ConfigYesNo, getConfigListEntry
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.Screen import Screen
from Screens.LanguageSelection import LanguageEntryComponent
from Components.Language import language
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Screens.MessageBox import MessageBox

class MyLanguageSelection(Screen):
    skin = """
    <screen name="MyLanguageSelection" position="center,center" size="380,400" title="Language selection" zPosition="3">
        <widget source="languages" render="Listbox" position="0,0" size="380,400" scrollbarMode="showOnDemand">
            <convert type="TemplatedMultiContent">
                {"template": [
                        MultiContentEntryText(pos = (80, 10), size = (200, 50), flags = RT_HALIGN_LEFT, text = 1), # index 1 is the language name,
                        MultiContentEntryPixmap(pos = (10, 5), size = (60, 40), png = 2), # index 2 is the pixmap
                    ],
                 "fonts": [gFont("Regular", 20)],
                 "itemHeight": 50
                }
            </convert>
        </widget>
    </screen>
    """
    def __init__(self, session, currentLanguage):
        Screen.__init__(self, session)
        self.oldActiveLanguage = currentLanguage
        self["languages"] = List([])
        self["actions"] = ActionMap(["OkCancelActions"],
        {
            "ok": self.save,
            "cancel": self.cancel,
        }, -1)
        self.updateList()
        self.onLayoutFinish.append(self.selectActiveLanguage)

    def selectActiveLanguage(self):
        self.setTitle(_("Language selection"))
        pos = 0
        for pos, x in enumerate(self['languages'].list):
            if x[0] == self.oldActiveLanguage:
                self["languages"].index = pos
                break

    def updateList(self):
        languageList = language.getLanguageList()
        if not languageList:  # no language available => display only english
            list = [ LanguageEntryComponent("en", "English", "en_EN") ]
        else:
            list = [ LanguageEntryComponent(file=x[1][2].lower(), name=x[1][0], index=x[0]) for x in languageList]
        self["languages"].list = list

    def save(self):
        self.close(self['languages'].list[self['languages'].index][0][:2])

    def cancel(self):
        self.close()


class Captcha(object):
    def __init__(self, session, captchaCB, imagePath, destPath='/tmp/captcha.png'):
        self.session = session
        self.captchaCB = captchaCB
        self.destPath = destPath.encode('utf-8')
        imagePath = imagePath.encode('utf-8')

        if os.path.isfile(imagePath):
            self.openCaptchaDialog(imagePath)
        else:
            downloadPage(imagePath, destPath).addCallback(self.downloadCaptchaSuccess).addErrback(self.downloadCaptchaError)

    def openCaptchaDialog(self, captchaPath):
        self.session.openWithCallback(self.captchaCB, CaptchaDialog, captchaPath)

    def downloadCaptchaSuccess(self, txt=""):
        print "[Captcha] downloaded successfully:"
        self.openCaptchaDialog(self.dest)

    def downloadCaptchaError(self, err):
        print "[Captcha] download error:", err
        self.captchaCB('')


class CaptchaDialog(VirtualKeyBoard):
    skin = """
    <screen name="CaptchDialog" position="center,center" size="560,460" zPosition="99" title="Virtual keyboard">
        <ePixmap pixmap="skin_default/vkey_text.png" position="9,165" zPosition="-4" size="542,52" alphatest="on" />
        <widget source="country" render="Pixmap" position="490,0" size="60,40" alphatest="on" borderWidth="2" borderColor="yellow" >
            <convert type="ValueToPixmap">LanguageCode</convert>
        </widget>
        <widget name="header" position="10,10" size="500,20" font="Regular;20" transparent="1" noWrap="1" />
        <widget name="captcha" position="10, 50" size ="540,110" alphatest="blend" zPosition="-1" />
        <widget name="text" position="12,165" size="536,46" font="Regular;46" transparent="1" noWrap="1" halign="right" />
        <widget name="list" position="10,220" size="540,225" selectionDisabled="1" transparent="1" />
    </screen>
    """
    def __init__(self, session, captcha_file):
        VirtualKeyBoard.__init__(self, session, _('Type text of picture'))
        self["captcha"] = Pixmap()
        self.Scale = AVSwitch().getFramebufferScale()
        self.picPath = captcha_file
        self.picLoad = ePicLoad()
        self.picLoad.PictureData.get().append(self.decodePicture)
        self.onLayoutFinish.append(self.showPicture)

    def showPicture(self):
        self.picLoad.setPara([self["captcha"].instance.size().width(), self["captcha"].instance.size().height(), self.Scale[0], self.Scale[1], 0, 1, "#002C2C39"])
        self.picLoad.startDecode(self.picPath)

    def decodePicture(self, PicInfo=""):
        ptr = self.picLoad.getData()
        self["captcha"].instance.setPixmap(ptr)

    def showPic(self, picInfo=""):
        ptr = self.picLoad.getData()
        if ptr != None:
            self["captcha"].instance.setPixmap(ptr.__deref__())
            self["captcha"].show()

class DelayMessageBox(MessageBox):
    def __init__(self, session, seconds, message):
        MessageBox.__init__(self, session, message, type=MessageBox.TYPE_INFO, timeout=seconds, close_on_any_key=False, enable_input=False)
        self.skinName = "MessageBox"

# object for stopping workerThread
WorkerStop = object()

# queue for function to be executed in workerThread
fnc_queue = Queue(1)

class ThreadException(Exception):
    pass

class WorkerThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.name = "SubsDownload-workerThread"

    def run(self):
        o = fnc_queue.get()
        while o is not WorkerStop:
            function, args, kwargs, onResult = o
            del o
            try:
                result = function(*args, **kwargs)
                success = True
            except:
                success = False
                result = failure.Failure()
            del function, args, kwargs
            try:
                onResult(success, result)
            except:
                log.err()
            del onResult, result
            o = fnc_queue.get()
        print("worker thread stopped")


    def join(self, timeout=None):
        print("stopping working thread")
        fnc_queue.put(WorkerStop)
        Thread.join(self, timeout)


class Task(object):
    """Class for running single python task
        at time in worker thread"""

    instance = None
    worker_thread = None

    @staticmethod
    def getInstance():
        if Task.instance is None:
            return Task()
        return Task.instance

    @staticmethod
    def startWorkerThread():
        print("[Task] starting workerThread")
        Task.worker_thread = WorkerThread()
        Task.worker_thread.start()

    @staticmethod
    def stopWorkerThread():
        print("[Task] stopping workerThread")
        Task.worker_thread.join()
        Task.worker_thread = None

    def __init__(self, callback, fnc, *args, **kwargs):
        print('[Task] initializing')
        Task.instance = self
        self.callback = callback
        self.fnc = fnc
        self.args = args
        self.kwargs = kwargs
        # input queue to send results from reactor thread
        # to running function in workerThread
        self.fnc_in_queue = Queue(1)
        # output queue to send function decorated by callFromThread
        # from workerThread to reactor thread and run it there
        self.fnc_out_queue = Queue(1)
        self.m_pump = ePythonMessagePump()
        self.m_pump.recv_msg.get().append(self.callbackFromThread)

    def run(self):
        print('[Task] running')
        self._running = True
        self._aborted = False
        o = (self.fnc, self.args, self.kwargs, self.onComplete)
        fnc_queue.put(o)

    def callbackFromThread(self, val):
        print 'callbackFromThread', val
        self.fnc_out_queue.get()()

    def setResume(self):
        print("[Task] resuming")
        self._aborted = False

    def setCancel(self):
        """ setting flag to abort executing compatible task
             (ie. controlling this flag in task execution) """

        print('[Task] cancelling...')
        self._aborted = True

    def isCancelling(self):
        return self._aborted

    def onComplete(self, success, result):
        def wrapped_finish():
            Task.instance = None
            self.callback(success, result)

        if success:
            print('[Task] completed with success')
        else:
            print('[Task] completed with failure')

        # To make sure that, when we abort processing of task,
        # that its always the same type of failure
        if self._aborted:
            success = False
            result = failure.Failure(ThreadException())
        self.fnc_out_queue.put(wrapped_finish)
        self.m_pump.send(0)


def callFromThread(func):
    """calls function from child thread in main(reactor) thread,
        and wait(in child thread) for result. Used mainly for GUI calls
        """
    def wrapped(*args, **kwargs):
        def _callFromThread():
            result = defer.maybeDeferred(func, *args, **kwargs)
            result.addBoth(fnc_in_queue.put)

        task = Task.getInstance()
        fnc_in_queue = task.fnc_in_queue
        fnc_out_queue = task.fnc_out_queue
        m_pump = task.m_pump
        fnc_out_queue.put(_callFromThread)
        m_pump.send(0)
        result = fnc_in_queue.get()
        print("result is %s" % str(result))
        if isinstance(result, failure.Failure):
            result.raiseException()
        return result
    return wrapped

def messageCB(text):
    print text.encode('utf-8')

@callFromThread
def getCaptcha(session, imagePath):
    def getCaptchaCB(word):
        if word is None:
            d.callback('')
        else:
            d.callback(word)
    d = defer.Deferred()
    Captcha(session, getCaptchaCB, imagePath)
    return d

@callFromThread
def delay(session, seconds, message):
    def delayCB(callback=None):
        d.callback(None)
    d = defer.Deferred()
    session.openWithCallback(delayCB, DelayMessageBox, seconds, message)
    return d


class E2SettingsProvider(dict):
    def __init__(self, providerName,configSubSection, defaults):
        self.__providerName = providerName
        setattr(configSubSection, providerName, ConfigSubsection())
        self.__rootConfigListEntry = getattr(configSubSection, providerName)
        self.__defaults = defaults
        self.createSettings()

    def __repr__(self):
        return '[E2SettingsProvider-%s]'%self.__providerName.encode('utf-8')

    def __setitem__(self, key, value):
        self.setSetting(key, value)

    def __getitem__(self, key):
        return self.getSetting(key)

    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, "
                                "got %d" % len(args))
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]

    def createSettings(self):
        for name, value in self.__defaults.iteritems():
            type = value['type']
            default = value['default']
            self.createConfigEntry(name, type, default)

    def createConfigEntry(self, name, type, default, *args, **kwargs):
        if type == 'text':
            setattr(self.__rootConfigListEntry, name, ConfigText(default=default, fixed_size=False))
        elif type == 'directory':
            setattr(self.__rootConfigListEntry, name, ConfigDirectory(default=default))
        elif type =='yesno':
            setattr(self.__rootConfigListEntry, name, ConfigYesNo(default=default))
        else:
            print repr(self),'cannot create entry of unknown type:', type

    def getConfigEntry(self, key):
        try:
            return getattr(self.__rootConfigListEntry, key)
        except Exception:
            return None

    def getE2Settings(self):
        settingList = []
        sortList =  self.__defaults.items()
        sortedList = sorted(sortList,key=lambda x:x[1]['pos'])
        for name, value in sortedList:
            settingList.append(getConfigListEntry(value['label'], self.getConfigEntry(name)))
        return settingList

    def getSetting(self, key):
        try:
            return self.getConfigEntry(key).value
        except Exception as e:
            print repr(self),e, 'returning empty string for key:',key
            return ""

    def setSetting(self, key, val):
        try:
            self.getConfigEntry(key).value = val
        except Exception as e:
            print repr(self), e,'cannot set setting:',key,':',val

def unrar(rarPath, destDir, successCB, errorCB):
    def rarSubNameCB(result, retval, extra_args):
        if retval == 0:
            print '[Unrar] getting rar sub name', result
            rarSubNames = result.split('\n')
            rarPath = extra_args[0]
            destDir = extra_args[1]
            try:
                for subName in rarSubNames:
                    os.unlink(os.path.join(destDir, subName))
            except OSError as e:
                print e
            #unrar needs rar Extension?
            if os.path.splitext(rarPath)[1] !='.rar':
                oldRarPath = rarPath
                rarPath =  os.path.splitext(rarPath)[0]+'.rar'
                shutil.move(oldRarPath,rarPath)
            cmdRarUnpack = 'unrar e "%s" %s'%(rarPath,destDir)
            Console().ePopen(cmdRarUnpack, rarUnpackCB, (tuple(rarSubNames),))
        else:
            try:
                os.unlink(extra_args[0])
            except OSError:
                pass
            print '[Unrar] problem when getting rar sub name:',result
            errorCB(_("unpack error: cannot get subname"))

    def rarUnpackCB(result, retval, extra_args):
        if retval == 0:
            print '[Unrar] successfully unpacked rar archive'
            result = []
            rarSubNames = extra_args[0]
            for subName in rarSubNames:
                result.append(os.path.join(destDir, subName))
            successCB(result)
        else:
            print '[Unrar] problem when unpacking rar archive', result
            try:
                os.unlink(extra_args[0])
            except OSError:
                pass
            errorCB(_("unpack error: cannot open archive"))

    cmdRarSubName = 'unrar lb "%s"'% rarPath
    extraArgs = (rarPath, destDir)
    Console().ePopen(cmdRarSubName, rarSubNameCB, extraArgs)
