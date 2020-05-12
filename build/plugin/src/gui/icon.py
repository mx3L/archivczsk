import os

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from Plugins.Extensions.archivCZSK.settings import IMAGE_PATH
from enigma import ePicLoad, getDesktop

class IconD(Screen):
    def __init__(self, session):
        self.skin = """
            <screen position="center,center" size="1280,720" backgroundColor="#002C2C39">
                <widget name="myPic" position="center,center" size="1000,620" zPosition="11" alphatest="on" />
            </screen>"""
        self.picPath = os.path.join(IMAGE_PATH, 'icon.png')
        whatWidth = getDesktop(0).size().width()
        if whatWidth >= 3000:
            self.skin = """
                <screen position="center,center" size="3840,2160" backgroundColor="#002C2C39">
                    <widget name="myPic" position="center,center" size="3000,1860" zPosition="11" alphatest="on" />
                </screen>"""
            self.picPath = os.path.join(IMAGE_PATH, 'icon4k.png')
        if whatWidth >= 1900 and whatWidth < 3000:
            self.skin = """
                <screen position="center,center" size="1920,1080" backgroundColor="#002C2C39">
                    <widget name="myPic" position="center,center" size="1500,930" zPosition="11" alphatest="on" />
                </screen>"""
            self.picPath = os.path.join(IMAGE_PATH, 'icon2k.png')
        Screen.__init__(self, session)
        self.PicLoad = ePicLoad()
        self["myPic"] = Pixmap()
        self["actions"] = ActionMap(["OkCancelActions"], {
            "ok": self.close,
            "cancel": self.close
        }, -1)
        self.PicLoad.PictureData.get().append(self.DecodePicture)
        self.onLayoutFinish.append(self.ShowPicture)

    def ShowPicture(self):
        if self.picPath is not None:
            self.PicLoad.setPara([
                        self["myPic"].instance.size().width(),
                        self["myPic"].instance.size().height(),
                        100,
                        100,
                        0,
                        1,
                        "#002C2C39"])
            self.PicLoad.startDecode(self.picPath)

    def DecodePicture(self, PicInfo = ""):
        if self.picPath is not None:
            ptr = self.PicLoad.getData()
            self["myPic"].instance.setPixmap(ptr)
