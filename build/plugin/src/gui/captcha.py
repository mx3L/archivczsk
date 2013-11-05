# -*- coding: UTF-8 -*-
'''
Created on 22.4.2012

@author: marko
'''
import os
from twisted.web.client import downloadPage

from enigma import ePicLoad, getDesktop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.config import config


from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK.engine.tools import util
from Plugins.Extensions.archivCZSK.gui.base import BaseArchivCZSKScreen


class Captcha(object):
    def __init__(self, session, image, captchaCB, dest='/tmp/captcha.png'):
        self.session = session
        self.captchaCB = captchaCB
        self.dest = dest
        
        if os.path.isfile(image):
            self.openCaptchaDialog(image)
        else:
            downloadPage(image, dest).addCallback(self.downloadCaptchaCB).addErrback(self.downloadCaptchaError)
        
        
    def openCaptchaDialog(self, captcha_file):
        if config.plugins.archivCZSK.convertPNG.getValue():
            captcha_file = util.convert_png_to_8bit(captcha_file)
        self.session.openWithCallback(self.captchaCB, CaptchaDialog, captcha_file)

    def downloadCaptchaCB(self, txt=""):
        print "[Captcha] downloaded successfully:"
        self.openCaptchaDialog(self.dest)
    
    def downloadCaptchaError(self, err):
        print "[Captcha] download captcha error:", err
        self.captchaCB('')
        


class CaptchaDialog(BaseArchivCZSKScreen,VirtualKeyBoard):
    def __init__(self, session, captcha_file):  
        BaseArchivCZSKScreen.__init__(self,session,False)
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
