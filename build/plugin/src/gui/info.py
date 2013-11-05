# -*- coding: UTF-8 -*-
'''
Created on 28.4.2012

@author: marko
'''
import os
from twisted.web.client import downloadPage

from Components.Label import Label, MultiColorLabel
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Components.AVSwitch import AVSwitch
from Components.config import config
from enigma import ePicLoad, getDesktop

from base import BaseArchivCZSKScreen
from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK.settings import ARCH,PLUGIN_PATH
from Plugins.Extensions.archivCZSK.gui.common import showYesNoDialog, showInfoMessage, PanelColorListEntry, PanelList
from Plugins.Extensions.archivCZSK.engine.player.info import videoPlayerInfo

def showChangelog(session, changelog_title, changelog_text):
	session.open(ChangelogScreen, changelog_title, changelog_text)

def showItemInfo(session, item):
	Info(session, item)
	
def showCSFDInfo(session, name):
	try:
		from Plugins.Extensions.CSFD.plugin import CSFD
	except ImportError:
		showInfoMessage(session, _("Plugin CSFD is not installed."))
	else:
		session.open(CSFD, name, False)
	
	
def showVideoPlayerInfo(session, cb=None):
	if cb:
		session.openWithCallback(cb, VideoPlayerInfoScreen)
	else:
		session.open(VideoPlayerInfoScreen)


class ChangelogScreen(BaseArchivCZSKScreen):
	def __init__(self, session, title, text=None):
		BaseArchivCZSKScreen.__init__(self, session)
		self.changelog = text
		self.title = title
		
		if self.changelog is not None:
			self["changelog"] = ScrollLabel(self.changelog.encode('utf-8', 'ignore'))
		else:
			self["changelog"] = ScrollLabel('')
				
		self["actions"] = NumberActionMap(["archivCZSKActions"],
		{
			"cancel": self.close,
			"up": self.pageUp,
			"down": self.pageDown,
		}, -2)	
		self.title = self.title.encode('utf-8', 'ignore') + ' changelog'
	
	def pageUp(self):
		self["changelog"].pageUp()

	def pageDown(self):
		self["changelog"].pageDown()


class Info(object):
	def __init__(self, session, it):
		self.session = session
		self.it = it
		self.dest = ''
		self.imagelink = ''
		if it.image is not None:
			self.imagelink = it.image.encode('utf-8', 'ígnore')
			self.dest = os.path.join('/tmp/', self.imagelink.split('/')[-1])

			if os.path.exists(self.dest):
				self.showInfo()
			else:
				self.downloadPicture()
		else:
			self.showInfo()
		
	def downloadPicture(self):
		print '[Info] downloadPicture'
		print '[Info]', self.imagelink, self.dest
		downloadPage(self.imagelink, self.dest).addCallback(self.downloadPictureCallback).addErrback(self.downloadPictureErrorCallback)
		
	def downloadPictureCallback(self, txt=""):
		print '[Info] picture was succesfully downloaded'
		self.showInfo()
		
	def downloadPictureErrorCallback(self, err):
		print '[Info] picture was not succesfully downloaded', err
		self.showInfo()
		
	def closeInfo(self):
		print '[Info] closeInfo'
		
	def showInfo(self):
		print '[Info] showInfo'
		self.session.openWithCallback(self.closeInfo, ItemInfoScreen, self.it)

class ItemInfoScreen(BaseArchivCZSKScreen):
	def __init__(self, session, it):
		BaseArchivCZSKScreen.__init__(self, session)
		self.image_link = None
		self.it = it
		self.image_dest = None
		if it.image is not None:
			self.image_link = it.image.encode('utf-8', 'ignore')
			self.image_dest = os.path.join('/tmp/', self.image_link.split('/')[-1])
		self.plot = ''
		self.genre = ''
		self.rating = ''
		self.year = ''
		
		for key, value in it.info.iteritems():		
			if key == 'Plot' or key == 'plot':
				self.plot = value.encode('utf-8', 'ignore')
			if key == 'Genre' or key == 'genre':
				self.genre = value.encode('utf-8', 'ignore')
			if key == 'Rating' or key == 'rating':
				self.rating = value.encode('utf-8', 'ignore')
			if key == 'Year' or key == 'year':
				self.year = value.encode('utf-8', 'ignore')
			
		self["img"] = Pixmap()
		self["genre"] = Label(_("Genre: ") + self.genre)
		self["year"] = Label(_("Year: ") + self.year)
		self["rating"] = Label(_("Rating: ") + self.rating)
		self["plot"] = ScrollLabel(self.plot)
			
		self["actions"] = NumberActionMap(["archivCZSKActions"],
		{
			"cancel": self.close,
			"up": self.pageUp,
			"down": self.pageDown,
		}, -2)	
		self.title = self.it.name.encode('utf-8', 'ignore')
		self.Scale = AVSwitch().getFramebufferScale()
		self.picLoad = ePicLoad()
		self.picLoad.PictureData.get().append(self.decodePicture)
		self.onLayoutFinish.append(self.showPicture)
	
	def pageUp(self):
		self["plot"].pageUp()

	def pageDown(self):
		self["plot"].pageDown()
		
	def showPicture(self):
		if self.image_dest is not None:
			self.picLoad.setPara([self["img"].instance.size().width(), self["img"].instance.size().height(), self.Scale[0], self.Scale[1], 0, 1, "#002C2C39"])
			self.picLoad.startDecode(self.image_dest)

	def decodePicture(self, PicInfo=""):
		ptr = self.picLoad.getData()
		self["img"].instance.setPixmap(ptr)
		
		
		
class VideoPlayerInfoScreen(BaseArchivCZSKScreen):
	GST_INSTALL = 0
	GST_REINSTALL = 1
	GST_INSTALL_RTMP = 2

	GST_SCRIPT_PATH = os.path.join(PLUGIN_PATH, 'script','gst-plugins-archivczsk.sh')
	RTMP_SCRIPT_PATH = os.path.join(PLUGIN_PATH, 'script','rtmp-plugin.sh')
	
	def __init__(self, session):
		BaseArchivCZSKScreen.__init__(self, session)
		self.__settings = config.plugins.archivCZSK.videoPlayer
		self.selectedInstallType = self.GST_INSTALL
		self.restartNeeded = False
		
		if ARCH == 'mipsel':
			self["key_red"] = Label(_("Install GStreamer plugins"))
			self["key_green"] = Label(_("Install RTMP plugins"))
			self["key_yellow"] = Label(_("Re-Install GStreamer plugins"))
			self["key_blue"] = Label(_("Refresh"))
		else:
			self["key_red"] = Label("")
			self["key_green"] = Label("")
			self["key_yellow"] = Label("")
			self["key_blue"] = Label("")   
		self["detected player"] = Label(_("Detected player:"))
		self["detected player_val"] = Label("")
		self["protocol"] = Label(_("Supported protocols:"))
		self["protocol_list"] = PanelList([], 24)
		self["container"] = Label(_("Supported containers:"))
		self["container_list"] = PanelList([], 24)
		self["info_scrolllabel"] = ScrollLabel()
			
		self["actions"] = ActionMap(["archivCZSKActions"],
		{
			"up": self.pageUp,
			"down": self.pageDown,
			"right": self.pageDown,
			"left": self.pageUp,
			"cancel":self.cancel,
			"blue": self.updateGUI,
			"yellow": self.askReinstallGstPlugins,
			"red": self.askInstallGstPlugins,
			"green": self.askInstallRtmpPlugin,
		}, -2)
		
		self.onShown.append(self.setWindowTitle)
		self.onLayoutFinish.append(self.disableSelection)
		self.onLayoutFinish.append(self.setPlayer)
		self.onLayoutFinish.append(self.setInfo)
		self.onLayoutFinish.append(self.updateGUI)
	
	def setWindowTitle(self):
		self.title = _("VideoPlayer Info")
		
	def disableSelection(self):
		self["container_list"].selectionEnabled(False)
		self["protocol_list"].selectionEnabled(False)
		
	def updateGUI(self):
		containerWidth = self["container_list"].instance.size().width()
		protocolWidth = self["protocol_list"].instance.size().width()
		self.updateProtocolList(containerWidth)
		self.updateContainerList(protocolWidth)
		
	def setPlayer(self):
		self["detected player_val"].setText(videoPlayerInfo.getName())
		
	def setInfo(self):
		infoText=''
		if ARCH == 'mipsel':
			infoText += _("* If some of the tests FAIL you should")
			infoText += " " + _("try to install Gstreamer plugins in following order:")
			infoText += "\n   " + _("1. Press Red, If it doesnt help go to point 2")
			infoText += "\n   " + _("2. Press Green, If it doesnt help go to point 3")
			infoText += "\n   " + _("3. Press Yellow")
			infoText += "\n\n"
		infoText += _("* Status UNKNOWN means, that I dont know how to get info,")
		infoText += " " + _("it doesnt mean that protocol or container isn't supported") + "."
		infoText += "\n\n"
		infoText += _("* Videos are encoded by various codecs")
		infoText += ", " + _("to play them you need to have HW support of your receiver to decode them") + "."
		infoText += "\n" + _("For example if you have ASF(WMV) - OK state")
		infoText += ", " + _("it doesnt already mean that you can play WMV file")
		infoText += ", " + _("it just means that player can open WMV container and get ENCODED video out of it") + "."
		infoText += " " + _("In WMV container is used VC1 encoded video") + "."
		infoText += " " + _("If your player cannot decode VC1 codec, than you cannot play this video.")
		self["info_scrolllabel"].setText(infoText)
		
	def updateProtocolList(self,width):
		menuList = []
		menuList.append(self.buildEntry(_("HTTP Protocol"), videoPlayerInfo.isHTTPSupported(), width))
		menuList.append(self.buildEntry(_("HLS Protocol"), videoPlayerInfo.isHLSSupported(), width))
		menuList.append(self.buildEntry(_("MMS Protocol"), videoPlayerInfo.isMMSSupported(), width))
		menuList.append(self.buildEntry(_("RTMP Protocol"), videoPlayerInfo.isRTMPSupported(), width))
		menuList.append(self.buildEntry(_("RTSP Protocol"), videoPlayerInfo.isRTSPSupported(), width))
		self["protocol_list"].setList(menuList)
		
	def updateContainerList(self,width):
		menuList = []
		menuList.append(self.buildEntry(_("3GP container"), videoPlayerInfo.isMP4Supported(), width))
		menuList.append(self.buildEntry(_("ASF(WMV) Container"), videoPlayerInfo.isASFSupported(), width))
		menuList.append(self.buildEntry(_("AVI Container"), videoPlayerInfo.isAVISupported(), width))
		menuList.append(self.buildEntry(_("FLV Container"), videoPlayerInfo.isFLVSupported(), width))
		menuList.append(self.buildEntry(_("MKV Container"), videoPlayerInfo.isMKVSupported(), width))
		menuList.append(self.buildEntry(_("MP4 Container"), videoPlayerInfo.isMP4Supported(), width))
		self["container_list"].setList(menuList)

		
	def buildEntry(self, name, res, width):
		if res is None:
			return PanelColorListEntry(name, _("UNKNOWN"), 0xffff00, width)
		elif res:
			return PanelColorListEntry(name, _("OK"), 0x00ff00, width)
		else:
			return PanelColorListEntry(name, _("FAIL"), 0xff0000, width)
		
	def pageUp(self):
		self["info_scrolllabel"].pageUp()

	def pageDown(self):
		self["info_scrolllabel"].pageDown()
		
		
	def askInstallGstPlugins(self):
		if ARCH == 'mipsel' :
			self.selectedInstallType = self.GST_INSTALL
			message = _("Do you want to install gstreamer plugins?")
			showYesNoDialog(self.session, message, self.installGstPlugins)
		
	
	def askReinstallGstPlugins(self):
		if ARCH == 'mipsel':
			self.selectedInstallType = self.GST_REINSTALL
			message = _("Do you want to re-install gstreamer plugins?")
			showYesNoDialog(self.session, message, self.installGstPlugins)
	
	
	def askInstallRtmpPlugin(self):
		if ARCH == 'mipsel':
			self.selectedInstallType = self.GST_INSTALL_RTMP
			warnMessage = _("ATTENTION: Installation of this plugin can cause")
			warnMessage += '\n' + _("crash of Enigma2.")
			if videoPlayerInfo.isRTMPSupported():
				message = warnMessage
				message += '\n'
				message += '\n' + _("It looks like RTMP plugin is already installed")
				message += '\n' + _("Do you want to reinstall it?")
			else:
				message = warnMessage
				message += '\n\n' + _("Do you want to continue?")
			showYesNoDialog(self.session, message, self.installGstPlugins)
	
		
	def installGstPlugins(self, callback=None):
		if callback:
			cmdList = []
			if self.selectedInstallType == self.GST_INSTALL_RTMP:
				cmdList = [self.RTMP_SCRIPT_PATH]
			elif self.selectedInstallType == self.GST_INSTALL:
				params = " N"
				cmdList = [self.GST_SCRIPT_PATH + params]
			elif self.selectedInstallType == self.GST_REINSTALL:
				params = " A"
				cmdList = [self.GST_SCRIPT_PATH + params]
			self.session.openWithCallback(self.installGstPluginsCB, Console, cmdlist=cmdList)
		
	def installGstPluginsCB(self, callback=None):
		self.updateGUI()
		self.updatePlayerSettings()
		self.restartNeeded = True
		
	def updatePlayerSettings(self):
		if videoPlayerInfo.isRTMPSupported():
			self.__settings.seeking.setValue(True)
			self.__settings.seeking.save()
			
	def askRestartE2(self):
		message = _("Its highly recommended to restart Enigma2")
		message += " " + _("after installation of gstreamer plugins")
		message += "\n"
		message += "\n" + _("Do you want to restart Enigma2 now?")
		showYesNoDialog(self.session, message, self.restartE2)
		
	def restartE2(self, callback=None):
		if callback:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, 3)
		else: self.close()
		
	def cancel(self):
		if self.restartNeeded:
			self.askRestartE2()
		else: self.close()
