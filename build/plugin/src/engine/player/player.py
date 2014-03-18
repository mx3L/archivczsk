# -*- coding: UTF-8 -*-
'''
Created on 20.3.2012

@author: marko
'''
import os
import traceback

from enigma import  eServiceCenter, iServiceInformation, eServiceReference, iSeekableService, iPlayableService, iPlayableServicePtr, eTimer, eConsoleAppContainer, getDesktop
from Screens.MessageBox import MessageBox
from Screens.InfoBar import MoviePlayer
from Screens.HelpMenu import HelpableScreen

from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, \
	InfoBarServiceNotifications, InfoBarPVRState, \
	InfoBarServiceErrorPopupSupport

from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.ActionMap import HelpableActionMap
from Components.config import config, ConfigSubsection
from ServiceReference import ServiceReference

try:
	from Plugins.Extensions.SubsSupport import SubsSupport, initSubsSettings
except ImportError as e:
	traceback.print_exc()
	raise Exception("Please install SubsSupport plugin")
config.plugins.archivCZSK.subtitles = ConfigSubsection()

from controller import VideoPlayerController, GStreamerDownloadController, RTMPController
from info import videoPlayerInfo
from infobar import ArchivCZSKMoviePlayerInfobar, ArchivCZSKMoviePlayerSummary, InfoBarAspectChange, InfoBarPlaylist, StatusScreen
from util import Video, getBufferInfo, setBufferSize
import setting

from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import settings
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.engine.items import RtmpStream, PVideo, PPlaylist
from Plugins.Extensions.archivCZSK.engine.tools import util
from Plugins.Extensions.archivCZSK.engine.exceptions.play import UrlNotExistError, RTMPGWMissingError
from Plugins.Extensions.archivCZSK.gui.base import BaseArchivCZSKScreen

# possible services
SERVICEDVB_ID = 0x1
SERVICEMP3_ID = 4097
SERVICEMP4_ID = 4113
SERVICEMRUA_ID = 4370

# rtmpgw bin
RTMPGW_PATH = '/usr/bin/rtmpgw'
NETSTAT_PATH = 'netstat'

# standard players with playlist support

class StandardVideoPlayer(MoviePlayer, InfoBarPlaylist):
	def __init__(self, session, sref, playlist, playlistName, playlistCB):
		self.onPlayService = []
		self.sref = sref
		MoviePlayer.__init__(self, session, sref)
		InfoBarPlaylist.__init__(self, playlist, playlistCB, playlistName)
		# SubsSupport.__init__(self, subPath=subtitles, alreadyPlaying=True)
		self.skinName = "MoviePlayer"

	def playService(self):
		for f in self.onPlayService:
			f()
		self.session.nav.playService(self.sref)

class StandardStreamVideoPlayer(MoviePlayer, InfoBarPlaylist):
	def __init__(self, session, sref, playlist, playlistName, playlistCB):
		self.onPlayService = []
		self.sref = sref
		MoviePlayer.__init__(self, session, sref)
		onStartShow = repeat = len(playlist) > 1
		autoPlay = False
		InfoBarPlaylist.__init__(self, playlist, playlistCB, playlistName,
								autoPlay=autoPlay, repeat=repeat, onStartShow=onStartShow, showProtocol=True)
		# SubsSupport.__init__(self, subPath=subtitles, alreadyPlaying=True)
		self.skinName = "MoviePlayer"

	def playService(self):
		for f in self.onPlayService:
			f()
		self.session.nav.playService(self.sref)

###################################################################################

class ArchivCZSKMoviePlayer(BaseArchivCZSKScreen, InfoBarPlaylist, SubsSupport, ArchivCZSKMoviePlayerInfobar, InfoBarBase, InfoBarShowHide, \
		InfoBarSeek, InfoBarAudioSelection, HelpableScreen, InfoBarNotifications, \
		InfoBarServiceNotifications, InfoBarPVRState, \
		InfoBarAspectChange, InfoBarServiceErrorPopupSupport):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, sref, playlist, playlistName, playlistCB, subtitles=None,
				autoPlay=True, showProtocol=False, onStartShow=False, repeat=False):
		BaseArchivCZSKScreen.__init__(self, session)
		self.onPlayService = []
		self.settings = config.plugins.archivCZSK.videoPlayer
		self.sref = sref

		# # set default/non-default skin according to SD/HD mode
		if self.settings.useDefaultSkin.getValue():
			self.setSkinName("MoviePlayer")
		else:
			HD = getDesktop(0).size().width() == 1280
			if HD:
				self.setSkin("ArchivCZSKMoviePlayer_HD")
			else:
				self.setSkinName("MoviePlayer")


		# # init custom infobar (added info about download speed, buffer level..)
		ArchivCZSKMoviePlayerInfobar.__init__(self)


		# # custom actions for MP
		self["actions"] = HelpableActionMap(self, "ArchivCZSKMoviePlayerActions",
        	{
         	"leavePlayer": (self.leavePlayer, _("leave player?")),
         	"toggleShow": (self.toggleShow, _("show/hide infobar")),
         	"audioSelection":(self.audioSelection, _("show audio selection menu")),
         	"refreshSubs":(self.refreshSubs, _("refreshing subtitles position")),
         	"subsDelayInc":(self.subsDelayInc, _("increasing subtitles delay")),
         	"subsDelayDec":(self.subsDelayDec, _("decreasing subtitles delay"))
          	}, -3)

		InfoBarBase.__init__(self, steal_current_service=True)
		# init of all inherited screens
		for x in HelpableScreen, InfoBarShowHide, \
			    InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, \
				InfoBarServiceNotifications, HelpableScreen, InfoBarPVRState, \
				InfoBarAspectChange, InfoBarServiceErrorPopupSupport:
				x.__init__(self)

		# init subtitles
		initSubsSettings(config.plugins.archivCZSK.subtitles)
		SubsSupport.__init__(self, subsPath=subtitles, defaultPath=config.plugins.archivCZSK.subtitlesPath.getValue(), forceDefaultPath=True, searchSupport=True)

		# playlist support
		InfoBarPlaylist.__init__(self, playlist, playlistCB, playlistName,
								 autoPlay=autoPlay, onStartShow=onStartShow, repeat=repeat, showProtocol=showProtocol)

		# to get real start of service, and for queries for video length/position
		self.video = Video(session)

		# # bindend some video events to functions
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		{
			iPlayableService.evStart: self.__serviceStarted,
			iPlayableService.evUpdatedEventInfo: self.__evUpdatedEventInfo,
			iPlayableService.evUser + 10: self.__evAudioDecodeError,
			iPlayableService.evUser + 11: self.__evVideoDecodeError,
			iPlayableService.evUser + 12: self.__evPluginError,
		})
		self.statusDialog = session.instantiateDialog(StatusScreen)
		self.onClose.append(self.statusDialog.doClose)
		self.isStream = self.sref.getPath().find('://') != -1
		self.returning = False

	def __evUpdatedEventInfo(self):
		self.isStream = self.sref.getPath().find('://') != -1

	def __evAudioDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sAudioType = currPlay.info().getInfoString(iServiceInformation.sUser + 10)
		print "[__evAudioDecodeError] audio-codec %s can't be decoded by hardware" % (sAudioType)
		self.session.open(MessageBox, _("This Dreambox can't decode %s streams!") % sAudioType, type=MessageBox.TYPE_INFO, timeout=20)

	def __evVideoDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sVideoType = currPlay.info().getInfoString(iServiceInformation.sVideoType)
		print "[__evVideoDecodeError] video-codec %s can't be decoded by hardware" % (sVideoType)
		self.session.open(MessageBox, _("This Dreambox can't decode %s streams!") % sVideoType, type=MessageBox.TYPE_INFO, timeout=20)

	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser + 12)
		print "[__evPluginError]" , message
		self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=20)

	def __serviceStarted(self):
		self.video.restartService()
		d = self.video.startService()
		d.addCallbacks(self._serviceStartedReal, self._serviceNotStarted)

	def _serviceStartedReal(self, callback=None):
		serviceName = self.video.getName()
		self.summaries.updateOLED(serviceName)

	def _serviceNotStarted(self, failure):
		log.info('cannot get service reference')

	def aspectChange(self):
		super(ArchivCZSKMoviePlayer,self).aspectChange()
		aspectStr = self.getAspectStr()
		self.statusDialog.setStatus(aspectStr, "#00ff00")

	def refreshSubs(self):
		if not self.isSubsLoaded():
			self.statusDialog.setStatus(_("No external subtitles loaded"))
		else:
			self.playAfterSeek()
			self.statusDialog.setStatus(_("Refreshing subtitles..."))

	def subsDelayInc(self):
		if not self.isSubsLoaded():
			self.statusDialog.setStatus(_("No external subtitles loaded"))
		else:
			delay = self.getSubsDelay()
			delay += 200
			self.setSubsDelay(delay)
			if delay > 0:
				self.statusDialog.setStatus("+%d ms" % delay)
			else:
				self.statusDialog.setStatus("%d ms" % delay)

	def subsDelayDec(self):
		if not self.isSubsLoaded():
			self.statusDialog.setStatus(_("No external subtitles loaded"))
		else:
			delay = self.getSubsDelay()
			delay -= 200
			self.setSubsDelay(delay)
			if delay > 0:
				self.statusDialog.setStatus("+%d ms" % delay)
			else:
				self.statusDialog.setStatus("%d ms" % delay)

	# override InfobarShowhide method
	def epg(self):
		pass

	def createSummary(self):
		return ArchivCZSKMoviePlayerSummary

	def playService(self):
		for f in self.onPlayService:
			f()
		self.session.nav.playService(self.sref)

	def leavePlayer(self):
		self.is_closing = True
		self.session.openWithCallback(self.leavePlayerConfirmed, MessageBox, text=_("Stop playing this movie?"), type=MessageBox.TYPE_YESNO)

	def leavePlayerConfirmed(self, answer):
		if answer:
			self.exitVideoPlayer()

	def exitVideoPlayer(self):
		# not sure about this one, user with eplayer can try both modes
		# disabled for gstreamer -> freezes e2 after stopping live rtmp stream
		# default is disabled

		if config.plugins.archivCZSK.videoPlayer.exitFix.getValue():
			# from tdt duckbox
			# make sure that playback is unpaused otherwise the
			# player driver might stop working
			self.setSeekState(self.SEEK_STATE_PLAY)
		self.close()


# adds support for videoplayer controller
class CustomVideoPlayer(ArchivCZSKMoviePlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB,
				 playAndDownload=False, subtitles=None, autoPlay=True, showProtocol=False, onStartShow=False, repeat=False):
		ArchivCZSKMoviePlayer.__init__(self, session, sref, playlist, playlistName, playlistCB, subtitles,
									   autoPlay=autoPlay, showProtocol=showProtocol, onStartShow=onStartShow, repeat=repeat)
		self.videoPlayerController = videoPlayerController
		self.useVideoController = self.videoPlayerController is not None
		self.playAndDownload = playAndDownload
		if self.useVideoController:
			self.videoPlayerController.set_video_player(self)

	def _serviceStartedReal(self, callback=None):
		super(CustomVideoPlayer, self)._serviceStartedReal(None)
		if self.useVideoController:
			self.videoPlayerController.start(self.playAndDownload)

##################  default MP methods ################

	def _seekFwd(self):
		super(CustomVideoPlayer, self).seekFwd()

	def _seekBack(self):
		super(CustomVideoPlayer, self).seekBack()

	def _doSeekRelative(self, pts):
		super(CustomVideoPlayer, self).doSeekRelative(pts)

	def _unPauseService(self):
		super(CustomVideoPlayer, self).unPauseService()

	def _pauseService(self):
		super(CustomVideoPlayer, self).pauseService()

	def _doEofInternal(self, playing):
		super(CustomVideoPlayer, self).doEofInternal(playing)

	def _exitVideoPlayer(self):
		super(CustomVideoPlayer, self).exitVideoPlayer()

#######################################################

	def seekFwd(self):
		if self.useVideoController:
			if self.isStream:
				self.seekFwdManual()
			else:
				self.videoPlayerController.seek_fwd()
		else:
			self._seekFwd()

	def seekBack(self):
		if self.useVideoController:
			if self.isStream:
				self.seekBackManual()
			else:
				self.videoPlayerController.seek_fwd()
		else:
			self._seekBack()

	def doSeekRelative(self, pts):
		if self.useVideoController:
			self.videoPlayerController.do_seek_relative(pts)
		else:
			self._doSeekRelative(pts)

	def pauseService(self):
		if self.useVideoController:
			self.videoPlayerController.pause_service()
		else:
			self._pauseService()

	def unPauseService(self):
		if self.useVideoController:
			self.videoPlayerController.unpause_service()
		else:
			self._unPauseService()

	def doEofInternal(self, playing):
		if self.useVideoController:
			self.videoPlayerController.do_eof_internal(playing)
		else:
			self._doEofInternal(playing)

	def leavePlayerConfirmed(self, answer):
		if answer and self.execing:
			self.exitVideoPlayer()

	def exitVideoPlayer(self):
		if self.useVideoController:
			self.videoPlayerController.exit_video_player()
		else:
			self._exitVideoPlayer()


class GStreamerVideoPlayer(CustomVideoPlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload=False, subtitles=None):
		CustomVideoPlayer.__init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload, subtitles)
		self.gstreamerSetting = self.settings
		self.useBufferControl = False
		self.setBufferMode(int(self.gstreamerSetting.bufferMode.getValue()))

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evBuffering: self._evUpdatedBufferInfo,
            })
		self.playService()

	def _evUpdatedBufferInfo(self):
		if self.playAndDownload:
			return
		streamed = self.session.nav.getCurrentService().streamed()
		bufferInfo = getBufferInfo(streamed)

		if(bufferInfo['percentage'] > 95):
			self.bufferFull()

		if(bufferInfo['percentage'] == 0 and (bufferInfo['avg_in_rate'] != 0 and bufferInfo['avg_out_rate'] != 0)):
			self.bufferEmpty()

		info = {
				'bitrate':0,
				'buffer_percent':bufferInfo['percentage'],
				'buffer_secondsleft':bufferInfo['space'],
				'buffer_size':bufferInfo['size'],
				'download_speed':bufferInfo['avg_in_rate'],
				'buffer_slider':0
				}

		log.debug("BufferPercent %d\nAvgInRate %d\nAvgOutRate %d\nBufferingLeft %d\nBufferSize %d"
				, bufferInfo['percentage'], bufferInfo['avg_in_rate'], bufferInfo['avg_out_rate'], bufferInfo['space'], bufferInfo['size'])
		self.updateInfobar(info)

	def _serviceStartedReal(self, callback=None):
		super(GStreamerVideoPlayer, self)._serviceStartedReal(None)
		bufferSize = int(self.gstreamerSetting.bufferSize.getValue())
		if bufferSize > 0:
			self.setBufferSize(bufferSize * 1024)

	def setBufferMode(self, mode=None):
		if self.playAndDownload:
			return

		if mode == 3:
			log.debug("manual buffer control")
			self.useBufferControl = True

	def setBufferSize(self, size):
		""" set buffer size for streams in Bytes """

		# servicemp4 already set bufferSize
		if not self.gstreamerSetting.servicemp4.getValue():
			streamed = self.session.nav.getCurrentService().streamed()
			setBufferSize(streamed, size)

	def bufferFull(self):
		if self.useBufferControl:
			if self.seekstate != self.SEEK_STATE_PLAY :
				log.debug("Buffer filled start playing")
				self.setSeekState(self.SEEK_STATE_PLAY)

	def bufferEmpty(self):
		if self.useBufferControl:
			if self.seekstate != self.SEEK_STATE_PAUSE :
				log.debug("Buffer drained pause")
				self.setSeekState(self.SEEK_STATE_PAUSE)


class EPlayer3VideoPlayer(CustomVideoPlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload=False, subtitles=None):
		CustomVideoPlayer.__init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload, subtitles)
		self.playService()


class EPlayer2VideoPlayer(CustomVideoPlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload=False, subtitles=None):
		CustomVideoPlayer.__init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload, subtitles)
		self.playService()


class GSTStreamVideoPlayer(GStreamerVideoPlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload=False, subtitles=None):
		onStartShow = repeat = len(playlist) > 1
		CustomVideoPlayer.__init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload, subtitles,
								   autoPlay=False, onStartShow=onStartShow, showProtocol=True, repeat=repeat)
		self.gstreamerSetting = self.settings
		self.useBufferControl = False
		self.setBufferMode(int(self.gstreamerSetting.bufferMode.getValue()))

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evBuffering: self._evUpdatedBufferInfo,
            })
		self.playService()

class EP3StreamVideoPlayer(CustomVideoPlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload=False, subtitles=None):
		onStartShow = repeat = len(playlist) > 1
		CustomVideoPlayer.__init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload, subtitles,
								   autoPlay=False, showProtocol=True, onStartShow=onStartShow, repeat=repeat)
		self.playService()

class EP2StreamVideoPlayer(CustomVideoPlayer):
	def __init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload=False, subtitles=None):
		onStartShow = repeat = len(playlist) > 1
		CustomVideoPlayer.__init__(self, session, sref, videoPlayerController, playlist, playlistName, playlistCB, playAndDownload, subtitles,
								   autoPlay=False, showProtocol=True, onStartShow=onStartShow, repeat=repeat)
		self.playService()

class DownloadSupport(object):
	def __init__(self, content_provider, download):
		self.content_provider = content_provider
		self.download = download
		self.gstDownload = None
		self.onClose.append(self.__onClose)

	def __onClose(self):
		if self.download and self.download.playMode:
			self._askSaveDownloadCB()

	def playAndDownload(self, gstreamer=False):
		"""starts downloading and then playing after playDelay value"""

		def playNDownload(callback=None):
			if callback:
				self.content_provider.download(self.play_it, self._showPlayDownloadDelay, DownloadManagerMessages.finishDownloadCB, playDownload=True)
			else:
				self.callback and self.callback()

		from Plugins.Extensions.archivCZSK.gui.download import DownloadManagerMessages
		from Plugins.Extensions.archivCZSK.engine.downloader import getFileInfo, GStreamerDownload

		if self.content_provider is None:
			log.info('Cannot download.. You need to set your content provider first')
			return

		# we use gstreamer to play and download stream
		if gstreamer:
			# find out local path
			filename = self.play_it.filename
			name = self.play_it.name
			downloadsPath = self.content_provider.downloads_path
			url = self._getPlayUrl(self.play_it)
			subs = self.play_it.subs
			if url.startswith('http'):
				info = getFileInfo(url, filename, self.playSettings['extra-headers'])
				path = os.path.join(downloadsPath, info[0])
			path = path.encode('ascii', 'ignore')
			log.debug("download path: %s", path)

			# set prebuffering settings and play..
			prebufferSeconds = 0
			prebufferPercent = 1
			self.gstDownload = GStreamerDownload(path, prebufferSeconds, prebufferPercent)
			self._playStream(name, url, subs, playAndDownloadGst=True)
			return

		# we are downloading by wget/twisted and playing it by gstreamer/eplayer2,3
		text=_("Play and download mode is not supported by all video formats.") + "\n"
		text+=_("Player can start to behave unexpectedly ot no to play video at all.") + "\n"
		text+=_("Do yo want to continue?")
		self.session.openWithCallback(playNDownload, MessageBox, text, type=MessageBox.TYPE_YESNO)

	def playDownload(self, download):
		"""starts playing already downloading item"""
		from Plugins.Extensions.archivCZSK.engine.downloader import Download

		if download and isinstance(download, Download):
			self.download = download
			download_it = PVideo()
			download_it.name = download.name
			download_it.url = download.local
			subs = os.path.splitext(self.download.local)[0] + '.srt'
			subs = os.path.isfile(subs) and subs or None
			self.setMediaItem(download_it)
			self._playStream(download.name, download.local, subs, True)
		else:
			log.info("Provided download instance is None or not instance of Download")


	def _playAndDownloadCB(self, callback=None):
		# what is downloading is always seekable and pausable
		self.seekable = True
		self.pausable = True

		name = self.download.name
		url = self.download.local
		subsPath = os.path.splitext(self.download.local)[0] + '.srt'

		if os.path.isfile(subsPath):
			subs = subsPath
		else:
			subs = None

		self._playStream(name, url, subs, True)

	def _showPlayDownloadDelay(self, download):
		"""called on download start"""
		self.download = download

		# download is not running already, so we dont continue
		if not self.download.downloaded and not self.download.running:
			log.debug("download %s not started at all", self.download.name)
			self.download = None
			self.exit()
		else:
			self.session.openWithCallback(self._playAndDownloadCB, MessageBox, '%s %d %s' % (_('Video starts playing in'), \
									 self.playDelay, _("seconds.")), type=MessageBox.TYPE_INFO, timeout=self.playDelay, enable_input=False)


	def _askSaveDownloadCB(self):
		def saveDownload(callback=None):
			if not callback:
				from Plugins.Extensions.archivCZSK.engine.downloader import DownloadManager
				DownloadManager.getInstance().removeDownload(self.download)

		downloadedSucc = self.download.downloaded
		downloadedErr = not self.download.downloaded and not self.download.running
		downloading = not self.download.downloaded and self.download.running
		if downloadedSucc:
			self.session.openWithCallback(saveDownload,
										  MessageBox,
										  _("Do you want to save") + ' ' + self.download.name.encode('utf-8', 'ignore') + ' ' + _("to disk?"),
										  type=MessageBox.TYPE_YESNO)
		elif downloadedErr:
			self.session.openWithCallback(saveDownload,
										  MessageBox,
										  _("Do you want to save") + " " + _('not succesfully finished download') + " " + self.download.name.encode('utf-8', 'ignore') + ' ' + _("to disk?"),
										  type=MessageBox.TYPE_YESNO)
		elif downloading:
			self.session.openWithCallback(saveDownload,
										  MessageBox,
										  _("Do you want to continue downloading") + ' ' + self.download.name.encode('utf-8', 'ignore') + ' ' + _("to disk?"),
										  type=MessageBox.TYPE_YESNO)
		self.download.playMode = False


class RTMPGWSupport(object):
	__port = 8902

	def __init__(self):
		self.__streamPart = 'http://0.0.0.0:'
		self.__rtmpgwProcess = None
		self.useRtmpgw = not self.settings.seeking.getValue()
		self.onClose.append(self.stopRTMPGWProcess)

	def _getRTMPGWPlayUrl(self):
		return self.__streamPart + str(self.__port)


	def startRTMPGWProcess(self, media_it):
		log.debug('starting rtmpgw process')
		ret = util.check_program(RTMPGW_PATH)
		if ret is None:
			raise RTMPGWMissingError()

		if RTMPGWSupport.__port > 8905:
			RTMPGWSupport.__port = 8902
		else:
			RTMPGWSupport.__port += 1
		port = RTMPGWSupport.__port

		stream = media_it.stream
		url = media_it.url
		live = media_it.live
		try:
			cmd = "%s %s --sport %d" % (RTMPGW_PATH, stream.getRtmpgwUrl(), port)
		except Exception:
			urlList = url.split()
			rtmpTimeout = self.settings.rtmpTimeout.getValue()
			rtmpBuffer = (live and self.liveRTMPBuffer) or (not live and self.archiveRTMPBuffer)
			rtmp_url = []
			for url in urlList[1:]:
				rtmp = url.split('=', 1)
				rtmp_url.append(' --' + rtmp[0])
				rtmp_url.append("'%s'" % rtmp[1])
			rtmpUrl = "'%s'" % urlList[0] + ' '.join(rtmp_url)
			if not '--buffer' in rtmpUrl:
				rtmpUrl = '%s --buffer %d' % (rtmpUrl, int(rtmpBuffer))
			if not '--timeout' in rtmpUrl:
				rtmpUrl = '%s --timeout %d' % (rtmpUrl, int(rtmpTimeout))
			cmd = '%s --quiet --rtmp %s --sport %d' % (RTMPGW_PATH, rtmpUrl, self.__port)
		log.debug('rtmpgw server streaming: %s' , cmd)
		self.__rtmpgwProcess = eConsoleAppContainer()
		self.__rtmpgwProcess.appClosed.append(self.__endRTMPGWProcess)
		self.__rtmpgwProcess.execute(cmd)

	def __endRTMPGWProcess(self, status):
		log.debug('rtmpgw process exited with status %d' , status)
		self.__rtmpgwProcess = None

	def stopRTMPGWProcess(self):
		if self.__rtmpgwProcess is not None:
			self.__rtmpgwProcess.sendCtrlC()

class Player(DownloadSupport, RTMPGWSupport):
	"""Player for playing PVideo/PPlaylist content"""
	items = (PVideo, PPlaylist)

	def __init__(self, session, callback=None, content_provider=None):
		self.onClose = []
		self.settings = config.plugins.archivCZSK.videoPlayer
		RTMPGWSupport.__init__(self)
		DownloadSupport.__init__(self, content_provider=content_provider, download=None)
		self.session = session
		self.oldService = session.nav.getCurrentlyPlayingServiceReference()

		# player settings
		self.playDelay = int(self.settings.playDelay.getValue())
		self.autoPlay = self.settings.autoPlay.getValue()
		self.liveRTMPBuffer = int(self.settings.liveBuffer.getValue())
		self.archiveRTMPBuffer = int(self.settings.archiveBuffer.getValue())
		self.playerBuffer = int(self.settings.bufferSize.getValue())
		self.verifyLink = config.plugins.archivCZSK.linkVerification.getValue()
		self.hdmuFix = config.plugins.archivCZSK.hdmuFix.getValue()
		self.seekable = True
		self.pausable = True

		# current video player
		self.videoPlayer = None

		# current playlist/media item
		self.it = None

		# current play item
		self.play_it = None

		# current playlist
		self.playlist = []
		self.playlistName = 'Únknown'

		# additional play settings for video player
		self.playSettings = None

		# for amiko hdmu fix
		self.rassFuncs = []

		# set ContentScreen callback
		self.callback = callback


	def setContentProvider(self, content_provider):
		self.content_provider = content_provider


	def setMediaItem(self, it, seekable=True, pausable=True, idx=0):
		if not isinstance(it, Player.items):
			log.error("""[Player] setMediaItem: incompatible media item %s""", str(it))
			return
		self.it = it
		if isinstance(it, PPlaylist):
			self.play_it = it.playlist[idx]
			self.playlist = it.playlist
		elif isinstance(it, PVideo):
			self.play_it = it
			self.playlist = [it]
		self.playlistName = it.name
		self.playSettings = self.play_it.settings
		self.seekable = seekable
		self.pausable = pausable
		stream = self.play_it.stream
		if stream:
			self.playDelay = int(stream.playDelay)
			self.playerBuffer = int(stream.playerBuffer)


	def setPlayItem(self, it):
		if not isinstance(it, PVideo):
			log.error("""[Player] playItem: incompatible play item %s""", str(it))
			return
		setting.resetSettings()
		self.play_it = it
		self.playSettings = it.settings


	def play(self):
		"""starts playing media stream"""
		if self.play_it:
			srefName = self.play_it.name
			playUrl = self._getPlayUrl(self.play_it)
			self.stopRTMPGWProcess()
			if playUrl.startswith('rtmp') and self.useRtmpgw:
				self.startRTMPGWProcess(self.play_it)
				playUrl = self._getRTMPGWPlayUrl()
				self.seekable = False
				self.pausable = False
			subtitlesUrl = self.play_it.subs
			verifyLink = self.verifyLink
			self._playStream(srefName, playUrl, subtitlesUrl, verifyLink=verifyLink)
		else:
			log.info("Nothing to play. You need to set VideoItem first.")


	def playFromPlaylist(self, idx):
		if isinstance(self.it, PPlaylist):
			try:
				self.setPlayItem(self.it.playlist[idx])
			except IndexError:
				log.info('[PlaylistController] index %d doesn\'t exist playlist', idx)
			else:
				self.play()


	def _playlistCallback(self, command):
		if 'init' in command:
			pass
		elif 'play_idx' in command:
			self.playFromPlaylist(command['play_idx'])


	def _getPlayUrl(self, media_it):
		stream = media_it.stream
		url = media_it.url
		live = media_it.live
		if url.startswith('rtmp'):
			rtmpTimeout = int(self.settings.rtmpTimeout.getValue())
			rtmpBuffer = isinstance(stream, RtmpStream) and stream.buffer
			rtmpBuffer = int(rtmpBuffer or (live and self.liveRTMPBuffer)\
								    or (not live and self.archiveRTMPBuffer))
			rtmpUrl = stream and stream.getUrl()
			rtmpUrl = rtmpUrl or url
			if ' timeout=' not in rtmpUrl:
				rtmpUrl = "%s timeout=%d" % (rtmpUrl, rtmpTimeout)
			if ' buffer=' not in rtmpUrl:
				rtmpUrl = "%s buffer=%d" % (rtmpUrl, rtmpBuffer)
			log.debug('[Player] getPlayUrl:  %s', rtmpUrl)
			return rtmpUrl
		else:
			log.debug('[Player] getPlayUrl:  %s', url)
			return url


	def _createServiceRef(self, streamUrl, name):
		if isinstance(streamUrl, unicode):
			streamUrl = streamUrl.encode('utf-8', 'ignore')
		if isinstance(name, unicode):
			name = name.encode('utf-8', 'ignore')

		if streamUrl.endswith('.ts') and videoPlayerInfo.type == 'gstreamer':
			sref = eServiceReference(SERVICEDVB_ID, 0, streamUrl)
		elif self.settings.servicemp4.getValue():
			sref = eServiceReference(SERVICEMP4_ID, 0, streamUrl)
		elif self.settings.servicemrua.getValue():
			sref = eServiceReference(SERVICEMRUA_ID, 0, streamUrl)
		else:
			sref = eServiceReference(SERVICEMP3_ID, 0, streamUrl)
		sref.setName(name)
		return sref

	def __getVideoPlayer(self):
		session = self.session
		if isinstance(session.current_dialog, (CustomVideoPlayer, StandardVideoPlayer, StandardStreamVideoPlayer)):
			return session.current_dialog
		for dialog in session.dialog_stack:
			if isinstance(dialog, (CustomVideoPlayer, StandardVideoPlayer, StandardStreamVideoPlayer)):
				return dialog
		return None


	def _playStream(self, srefName, streamURL, subtitlesURL, playAndDownload=False, playAndDownloadGst=False, verifyLink=False):
		if verifyLink:
			timeout = int(config.plugins.archivCZSK.linkVerificationTimeout.getValue())
			ret = util.url_exist(streamURL, timeout)
			if ret is not None and not ret:
				raise UrlNotExistError()

		self.session.nav.stopService()
		sref = self._createServiceRef(streamURL, srefName)

		# we dont need any special kind of play settings
		# since we play from local path
		if not playAndDownload:
			# load play settings
			setting.loadSettings(self.playSettings['user-agent'],
							 	 self.playSettings['extra-headers'],
							 	 playAndDownloadGst)


		if self.videoPlayer is None:
			self.videoPlayer = self.__getVideoPlayer()

		# use currently opened media player
		if self.videoPlayer:
			self.videoPlayer.sref = sref
			self.videoPlayer.playService()
			if hasattr(self.videoPlayer, 'loadSubs'):
				self.videoPlayer.resetSubs(True)
				self.videoPlayer.loadSubs(subtitlesURL)
		# create new media player
		else:
			videoPlayerController = None
			useVideoController = self.settings.useVideoController.getValue()

			# fix for HDMU sh4 image..
			if self.hdmuFix:
				self.rassFuncs = ServiceEventTracker.EventMap[14][:]
				ServiceEventTracker.EventMap[14] = []

			# rtmp seek fix
			# TODO player shouldnt know about video addon methods
				   # need rewrite
			if streamURL.startswith('rtmp') and \
		 		self.settings.seeking.getValue() and \
		 		self.content_provider.__class__.__name__ == 'VideoAddonContentProvider' and \
		  		self.content_provider.video_addon.get_setting('rtmp_seek_fix'):
					videoPlayerController = RTMPController()

			elif useVideoController:
				videoPlayerController = VideoPlayerController(self.session, download=self.download, \
													 	  seekable=self.seekable, pausable=self.pausable)
			self._openVideoPlayer(sref, subtitlesURL, videoPlayerController, playAndDownloadGst, playAndDownload)


	def _openVideoPlayer(self, sref, subs, vpc, gstd, pad):
		videoPlayerSetting = self.settings.type.getValue()
		playerType = self.settings.detectedType.getValue()

		if videoPlayerSetting == 'standard':
			self.session.openWithCallback(self.exit, StandardVideoPlayer, sref, self.playlist,
										  self.playlistName, self._playlistCallback)

		elif videoPlayerSetting == 'custom':
			if playerType == 'gstreamer':
				if gstd:
					path = self.gstDownload.path
					prebufferP = self.gstDownload.preBufferPercent
					prebufferS = self.gstDownload.preBufferSeconds
					videoPlayerController = GStreamerDownloadController(path, prebufferP, prebufferS)
					pad = True
				self.session.openWithCallback(self.exit, GStreamerVideoPlayer, sref, vpc, self.playlist, \
											  self.playlistName, self._playlistCallback, pad, subs)
			elif playerType == 'eplayer3':
				self.session.openWithCallback(self.exit, EPlayer3VideoPlayer, sref, vpc, self.playlist, \
											  self.playlistName, self._playlistCallback, pad, subs)
			elif playerType == 'eplayer2':
				self.session.openWithCallback(self.exit, EPlayer2VideoPlayer, sref, vpc, self.playlist, \
											  self.playlistName, self._playlistCallback, pad, subs)

	def exit(self, callback=None):
		for f in self.onClose:
			f()
		# fix for HDMU sh4 image..
		if self.hdmuFix:
			ServiceEventTracker.EventMap[14] = self.rassFuncs

		setting.resetSettings()
		self.content_provider = None
		self.videoPlayer = None
		self.session.nav.playService(self.oldService)
		if self.callback:
			self.callback()



class StreamPlayer(Player):

	def _openVideoPlayer(self, sref, subs, vpc, gstd, pad):
		videoPlayerSetting = self.settings.type.getValue()
		playerType = self.settings.detectedType.getValue()

		if videoPlayerSetting == 'standard':
			self.session.openWithCallback(self.exit, StandardStreamVideoPlayer, sref,
										  self.playlist, self.playlistName, self._playlistCallback)

		elif videoPlayerSetting == 'custom':
			if playerType == 'gstreamer':
				if gstd:
					path = self.gstDownload.path
					prebufferP = self.gstDownload.preBufferPercent
					prebufferS = self.gstDownload.preBufferSeconds
					videoPlayerController = GStreamerDownloadController(path, prebufferP, prebufferS)
					pad = True
				self.session.openWithCallback(self.exit, GSTStreamVideoPlayer, sref, vpc, self.playlist,
											  self.playlistName, self._playlistCallback, pad, subs)
			elif playerType == 'eplayer3':
				self.session.openWithCallback(self.exit, EP3StreamVideoPlayer, sref, vpc, self.playlist,
											  self.playlistName, self._playlistCallback, pad, subs)
			elif playerType == 'eplayer2':
				self.session.openWithCallback(self.exit, EP2StreamVideoPlayer, sref, vpc, self.playlist,
											  self.playlistName, self._playlistCallback, pad, subs)
