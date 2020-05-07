from enigma import getDesktop, eConsoleAppContainer, eTimer
from Plugins.Extensions.archivCZSK.compat import eConnectCallback

import json

def get_desktop_width_and_height():
    desktop_size = getDesktop(0).size()
    return (desktop_size.width(), desktop_size.height())


class PythonProcess(object):
    def __init__(self, processPath):
        self.toRead = None
        self.pPayload = None
        self.data = ""
        self.__stopping = False
        self.processPath = processPath
        self.appContainer = eConsoleAppContainer()
        self.stdoutAvail_conn = eConnectCallback(self.appContainer.stdoutAvail, self.dataOutCB)
        self.stderrAvail_conn = eConnectCallback(self.appContainer.stderrAvail, self.dataErrCB)
        self.appContainer_conn = eConnectCallback(self.appContainer.appClosed, self.finishedCB)

    def recieveMessages(self, data):
        def getMessage(data):
            mSize = int(data[:7])
            mPayload = data[7:mSize]
            mPart = mSize > len(data)
            return mSize, mPayload, mPart

        def readMessage(payload):
            try:
                message = json.loads(payload)
            except EOFError:
                pass
            except Exception:
                pass
            else:
                self.toRead = None
                self.pPayload = None
                self.handleMessage(message)

        def readStart(data):
            mSize, mPayload, mPart = getMessage(data)
            if not mPart:
                data = data[mSize:]
                readMessage(mPayload)
                if len(data) > 0:
                    readStart(data)
            else:
                self.toRead = mSize - len(data)
                self.pPayload = mPayload

        def readContinue(data):
            nextdata = data[:self.toRead]
            self.pPayload += nextdata
            data = data[len(nextdata):]
            self.toRead -= len(nextdata)
            if self.toRead == 0:
                readMessage(self.pPayload)
                if len(data) > 0:
                    readStart(data)

        if self.pPayload is not None:
            readContinue(data)
        else:
            readStart(data)

    def handleMessage(self, data):
        self.callbacks['messageCB'](data)

    def start(self, callbacks):
        self.callbacks = callbacks
        cmd = "python %s" % self.processPath
        self.appContainer.execute(cmd)

    def running(self):
        return self.appContainer.running()

    def stop(self):
        def check_stopped():
            if not self.appContainer.running():
                self.stopTimer.stop()
                del self.stopTimer_conn
                del self.stopTimer
                del self.__i
                return
            if self.__i == 0:
                self.__i += 1
                self.appContainer.kill()
            elif self.__i == 1:
                self.stopTimer.stop()
                del self.stopTimer_conn
                del self.stopTimer
                raise Exception("cannot kill process")

        if self.__stopping:
            return
        self.__stopping = True
        self.__i = 0

        if self.appContainer.running():
            self.appContainer.sendCtrlC()
            self.stopTimer = eTimer()
            self.stopTimer_conn = eConnectCallback(self.stopTimer.timeout, check_stopped)
            self.stopTimer.start(2000, False)

    def write(self, data):
        dump = json.dumps(data)
        dump = "%07d%s" % (len(dump), dump)
        try:
            self.appContainer.write(dump)
        # DMM image
        except TypeError:
            self.appContainer.write(dump, len(dump))

    def dataErrCB(self, data):
        self.error = data

    def dataOutCB(self, data):
        self.recieveMessages(data)

    def finishedCB(self, retval):
        self.callbacks['finishedCB'](retval)