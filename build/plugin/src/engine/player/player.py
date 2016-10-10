import traceback

from enigma import eServiceReference, iPlayableService, eTimer
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config 
from Components.Label import Label
from Components.ServiceEventTracker import InfoBarBase, ServiceEventTracker
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from skin import parseColor
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import (InfoBarShowHide,
        InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Notifications import AddNotificationWithID, RemovePopup

try:
    from Plugins.Extensions.SubsSupport import (SubsSupport,
            SubsSupportStatus, initSubsSettings)
except ImportError as e:
    traceback.print_exc()
    raise Exception("Please install SubsSupport plugin")

from Plugins.Extensions.archivCZSK import _, settings, log
from Plugins.Extensions.archivCZSK.compat import eConnectCallback
from Plugins.Extensions.archivCZSK.engine.items import PVideo, PPlaylist
from Plugins.Extensions.archivCZSK.engine.tools import e2util
from Plugins.Extensions.archivCZSK.engine.tools.util import toString

config_archivczsk = config.plugins.archivCZSK

def getPlayPositionPts(session):
    service = session.nav.getCurrentService()
    seek = service and service.seek()
    position = seek and seek.getPlayPosition()
    position = position and not position[0] and position[1] or None
    return position

def getPlayPositionInSeconds(session):
    position = getPlayPositionPts(session)
    if position is not None:
        position = position / 90000
    return position

def getDurationPts(session):
    service = session.nav.getCurrentService()
    seek = service and service.seek()
    duration = seek and seek.getLength()
    duration = duration and not duration[0] and duration[1] or None
    return duration

def getDurationInSeconds(session):
    duration = getDurationPts(session)
    if duration is not None:
        duration = duration / 90000
    return duration

class ArchivCZSKPlaylist(Screen):
    def __init__(self, session, playlist, title, index=0):
        self.playlist = playlist
        self.index = index
        Screen.__init__(self, session)
        self.skinName = ["ArchivCZSKPlaylistScreen"]
        self["title"] = StaticText(toString(title))
        self["list"] = List(self.buildPlaylist())
        self["actions"] = ActionMap(["OkCancelActions"],
                {
                    "ok": self.ok,
                    "cancel": boundFunction(self.close, None),
                }, -1 )
        self.onLayoutFinish.append(self.setPlaylistIndex)

    def setPlaylistIndex(self):
        self["list"].index = self.index

    def buildPlaylist(self):
        list = []
        for item in self.playlist:
            list.append((toString(item.name),))
        return list

    def ok(self):
        self.close(self["list"].index)


class Player(object):
    def __init__(self, session, callback=None, content_provider=None):
        self.session = session
        self.old_service = session.nav.getCurrentlyPlayingServiceReference()
        self.settings = config_archivczsk.videoPlayer
        self.video_player = None
        self.playlist_dialog = None
        self.playlist = []
        self.curr_idx = 0
        self._play_item = None
        self.callback = callback

    def play_item(self, item = None, idx = None):
        log.info("play_item(%s, %s)"%(item,toString(idx)))
        play_item = None
        if item is not None:
            idx = idx or 0
            if isinstance(item, PPlaylist):
                self.playlist_item = item
                self.playlist = item.playlist
                play_item = item.playlist[idx]
            elif isinstance(item, PVideo):
                if item not in self.playlist:
                    self.playlist_item = None
                    self.playlist = [item]
                play_item = item
        elif idx is not None and self.playlist and idx >= 0 and idx < len(self.playlist) -1:
            play_item = self.playlist[idx]

        if play_item is not None and self._play_item != play_item:
            self._play_item = play_item
            self.curr_idx = self.playlist.index(play_item)
            self.play_stream(play_item.url, play_item.settings, play_item.subs, play_item.name)

    def play_stream(self, play_url, play_settings=None, subtitles_url=None, title=None):
        log.info("play_stream(%s, %s, %s, %s)"%(play_url, play_settings, subtitles_url, title))
        if play_url.startswith("rtmp"):
            rtmp_timeout = int(self.settings.rtmpTimeout.value)
            rtmp_buffer = int(self.settings.rtmpBuffer.value)
            if ' timeout=' not in play_url:
                play_url = "%s timeout=%d" % (play_url, rtmp_timeout)
            if ' buffer=' not in play_url:
                play_url = "%s buffer=%d" % (play_url, rtmp_buffer)
        headers = {}
        if play_settings.get("user-agent"):
            headers["User-Agent"] = play_settings["user-agent"]
        if play_settings.get("extra-headers"):
            headers.update(play_settings["extra-headers"])
        if headers:
            play_url += "#" + "&".join("%s=%s"%(k,v) for k,v in headers.iteritems())

        service_ref = eServiceReference(play_settings.get("stype", 4097), 0, toString(play_url))
        if title is not None:
            service_ref.setName(toString(title))

        if self.video_player is None:
            self.video_player = self.session.openWithCallback(self.player_exit_callback,
                    ArchivCZSKMoviePlayer, self.player_callback)

        self.video_player.play_service_ref(service_ref, 
                self._play_item.subs, play_settings.get("resume_time_sec"))

    def player_callback(self, callback):
        log.info("player_callback(%r)" % (callback,))
        if callback is not None:
            if callback[0] == "eof":
                if callback[1]:
                    self.player_callback(("playlist", "next"))
                else:
                    self.video_player.close()
            elif callback[0] == "exit":
                exit_player = True
                if len(callback) == 2:
                    exit_player = callback[1]
                else:
                    if self.settings.confirmExit.value:
                        self.session.openWithCallback(
                                lambda x:self.player_callback(("exit", x)),
                                MessageBox, text=_("Stop playing this movie?"), 
                                type=MessageBox.TYPE_YESNO)
                        exit_player = False
                if exit_player:
                    playpos = getPlayPositionInSeconds(self.session)
                    duration = getDurationInSeconds(self.session)
                    self.video_player.close()
            elif callback[0] == "playlist":
                if callback[1] == "show":
                    if self.playlist_item is not None:
                        title = self.playlist_item.name
                    else:
                        title = self._play_item.name
                    self.playlist_dialog = self.session.openWithCallback(
                            lambda x: self.player_callback(("playlist", "idx", x)),
                            ArchivCZSKPlaylist, self.playlist, title, self.curr_idx)
                elif callback[1] == "prev":
                    idx = self.curr_idx
                    if idx == 0:
                        idx = len(self.playlist) - 1
                    else:
                        idx -= 1
                    self.play_item(idx = idx)
                elif callback[1] == "next":
                    idx = self.curr_idx
                    # maybe ignore/make optional
                    if idx == len(self.playlist) -1:
                        self.video_player.close()
                    else:
                        idx += 1
                        self.play_item(idx = idx)
                elif callback[1] == "idx":
                    self.play_item(idx = callback[2])

    def player_exit_callback(self, playpos=None):
        log.info("player_exit_callback(%s)", playpos)
        self.video_player = None
        if self.playlist_dialog and self.playlist_dialog.__dict__:
            self.playlist_dialog.close()
            self.playlist_dialog = None
        self._play_item = None
        self.playlist = []
        self.curr_idx = 0
        self.session.nav.playService(self.old_service)
        self.old_service = None
        if self.callback is not None:
            self.callback()
            self.callback = None


class StatusScreen(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.stand_alone = True
        width, height = e2util.get_desktop_width_and_height()
        skin = '<screen position="%d,%d" size="%d,%d" backgroundColor="transparent" flags="wfNoBorder">'%(
                0.05 * width, 0.05 * height, 0.9 * width, 0.1 * height)
        skin+= '<widget name="status" position="0,0" size="%d,%d" valign="center" halign="left" font="Regular;22" transparent="1" shadowColor="#40101010" shadowOffset="3,3" />'%(
                0.9 * width, 0.1 * height)
        skin+= '</screen>'
        self.skin = skin
        self["status"] = Label()
        self.timer = eTimer()
        self.timer_conn = eConnectCallback(self.timer.timeout, self.hide)
        self.onClose.append(self.__on_close)

    def __on_close(self):
        self.timer.stop()
        del self.timer_conn
        del self.timer

    def set_status(self, text, color="yellow", timeout=1500):
        self['status'].setText(toString(text))
        self['status'].instance.setForegroundColor(parseColor(color))
        self.show()
        self.timer.start(timeout, True)

class InfoBarAspectChange(object):

    V_DICT = {'16_9_letterbox'  : {'aspect' : '16:9', 'policy2' : 'letterbox', 'title'   : '16:9 ' + _("Letterbox")},
           '16_9_panscan'       : {'aspect' : '16:9', 'policy2' : 'panscan', 'title'     : '16:9 ' + _("Pan&scan")},
           '16_9_nonlinear'     : {'aspect' : '16:9', 'policy2' : 'panscan', 'title'     : '16:9 ' + _("Nonlinear")},
           '16_9_bestfit'       : {'aspect' : '16:9', 'policy2' : 'bestfit', 'title'     : '16:9 ' + _("Just scale")},
           '16_9_4_3_pillarbox' : {'aspect' : '16:9', 'policy'  : 'pillarbox', 'title'   : '4:3 ' + _("PillarBox")},
           '16_9_4_3_panscan'   : {'aspect' : '16:9', 'policy'  : 'panscan', 'title'     : '4:3 ' + _("Pan&scan")},
           '16_9_4_3_nonlinear' : {'aspect' : '16:9', 'policy'  : 'nonlinear', 'title'   : '4:3 ' + _("Nonlinear")},
           '16_9_4_3_bestfit'   : {'aspect' : '16:9', 'policy'  : 'bestfit', 'title'     : _("Just scale")},
           '4_3_letterbox'      : {'aspect' : '4:3',  'policy'  : 'letterbox', 'policy2' : 'policy', 'title' : _("Letterbox")},
           '4_3_panscan'        : {'aspect' : '4:3',  'policy'  : 'panscan', 'policy2'   : 'policy', 'title' : _("Pan&scan")},
           '4_3_bestfit'        : {'aspect' : '4:3',  'policy'  : 'bestfit', 'policy2'   : 'policy', 'title' : _("Just scale")}}

    V_MODES = ['16_9_letterbox', '16_9_panscan', '16_9_nonlinear', '16_9_bestfit',
            '16_9_4_3_pillarbox', '16_9_4_3_panscan', '16_9_4_3_nonlinear', 
            '16_9_4_3_bestfit','4_3_letterbox', '4_3_panscan', '4_3_bestfit']

    def __init__(self):
        self.aspectChanged = False
        try:
            self.defaultAspect = open("/proc/stb/video/aspect", "r").read().strip()
        except IOError:
            self.defaultAspect = None
        try:
            self.defaultPolicy = open("/proc/stb/video/policy", "r").read().strip()
        except IOError:
            self.defaultPolicy = None
        try:
            self.defaultPolicy2 = open("/proc/stb/video/policy2", "r").read().strip()
        except IOError:
            self.defaultPolicy2 = None
        self.currentVMode = self.V_MODES[0]

        self["aspectChangeActions"] = HelpableActionMap(self, "InfobarAspectChangeActions",
            {
             "aspectChange":(self.aspectChange, ("Change aspect ratio"))
              }, -3)
        self.onClose.append(self.__onClose)
        self.postAspectChange = []

    def __onClose(self):
        if self.aspectChanged:
            self.setAspect(self.defaultAspect, self.defaultPolicy, self.defaultPolicy2)

    def getAspectString(self):
        mode = self.V_DICT[self.currentVMode]
        return "%s: %s\n%s: %s" % (
                _("Aspect"), mode['aspect'], 
                _("Policy"), mode['title'])

    def setAspect(self, aspect, policy, policy2):
        log.info('aspect: %s policy: %s policy2: %s' % (str(aspect), str(policy), str(policy2)))
        if aspect:
            try:
                open("/proc/stb/video/aspect", "w").write(aspect)
            except IOError as e:
                print e
        if policy:
            try:
                open("/proc/stb/video/policy", "w").write(policy)
            except IOError as e:
                print e
        if policy2:
            try:
                open("/proc/stb/video/policy2", "w").write(policy2)
            except IOError as e:
                print e

    def aspectChange(self):
        self.aspectChanged = True
        modeIdx = self.V_MODES.index(self.currentVMode)
        if modeIdx == len(self.V_MODES) - 1:
            modeIdx = 0
        else:
            modeIdx += 1
        self.currentVMode = self.V_MODES[modeIdx]
        mode = self.V_DICT[self.currentVMode]
        self.setAspect(mode['aspect'], mode.get('policy'), mode.get('policy2'))
        for f in self.postAspectChange:
            f()

# pretty much openpli's one but simplified
class InfoBarSubservicesSupport(object):
    def __init__(self):
        self["InfoBarSubservicesActions"] = HelpableActionMap(self, 
                "ColorActions", { "green": (self.showSubservices, _("Show subservices"))}, -2)
        self.__timer = eTimer()
        self.__timer_conn = (self.__timer.timeout, self.__seekToCurrentPosition)
        self.onClose.append(self.__onClose)

    def __onClose(self):
        self.__timer.stop()
        del self.__timer_conn
        del self.__timer

    def showSubservices(self):
        service = self.session.nav.getCurrentService()
        service_ref = self.session.nav.getCurrentlyPlayingServiceReference()
        subservices = service and service.subServices()
        numsubservices = subservices and subservices.getNumberOfSubservices() or 0

        selection = 0
        choice_list = []
        for idx in range(0, numsubservices):
            subservice_ref = subservices.getSubservice(idx)
            if service_ref.toString() == subservice_ref.toString():
                selection = idx
            choice_list.append((subservice_ref.getName(), subservice_ref))
        if numsubservices > 1:
            self.session.openWithCallback(self.subserviceSelected, ChoiceBox,
                title = _("Please select subservice..."), list = choice_list, 
                selection = selection, skin_name="SubserviceSelection")

    def subserviceSelected(self, service_ref):
        if service_ref:
            self.__timer.stop()
            self.__playpos = getPlayPositionPts(self.session) or 0
            duration = getDurationPts(self.session) or 0
            if (self.__playpos > 0 and duration > 0
                    and self.__playpos < duration):
                self.__timer.start(500, True)
            self.session.nav.playService(service_ref[1])

    def __seekToCurrentPosition(self):
        if getPlayPositionPts(self.session) is None:
            self.__timer.start(500, True)
        else:
            seekToPts(self.session, self.__playpos)
            del self.__playpos

class ArchivCZSKMoviePlayer(InfoBarBase, SubsSupport, SubsSupportStatus, InfoBarSeek,
        InfoBarAudioSelection, InfoBarSubservicesSupport, InfoBarNotifications,
        InfoBarShowHide, InfoBarAspectChange, HelpableScreen, Screen):

    RESUME_POPUP_ID = "aczsk_resume_popup"

    def __init__(self, session, player_callback):
        Screen.__init__(self, session)
        self.skinName = ["ArchivCZSKMoviePlayer", "MoviePlayer"]
        InfoBarBase.__init__(self)
        InfoBarSeek.__init__(self)
        # disable slowmotion/fastforward
        self.seekFwd = self.seekFwdManual
        self.seekBack = self.seekBackManual
        initSubsSettings()
        SubsSupport.__init__(self, 
                defaultPath = config_archivczsk.tmpPath.value,
                forceDefaultPath = True,
                searchSupport = True)
        SubsSupportStatus.__init__(self)
        InfoBarAudioSelection.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarSubservicesSupport.__init__(self)
        InfoBarShowHide.__init__(self)
        InfoBarAspectChange.__init__(self)
        self.postAspectChange.append(self.__aspect_changed)
        HelpableScreen.__init__(self)
        self.status_dialog = self.session.instantiateDialog(StatusScreen)
        self.player_callback = player_callback
        self.__timer = eTimer()
        self.__timer_conn = eConnectCallback(self.__timer.timeout, self.__pts_available)
        self.__subtitles_url = None
        self.__resume_time_sec = None
        self["actions"] = HelpableActionMap(self, "ArchivCZSKMoviePlayerActions",
                {"showPlaylist": (boundFunction(self.player_callback, ("playlist", "show",)),
                    _("Show playlist")),
                    "nextEntry":(boundFunction(self.player_callback, ("playlist", "next",)),
                        _("Play next entry in playlist")),
                    "prevEntry":(boundFunction(self.player_callback, ("playlist", "prev",)),
                        _("Play previous entry in playlist")),
                    "cancel":(boundFunction(self.player_callback, ("exit",)),
                        _("Exit player")),
                }, -2)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
        {
            iPlayableService.evStart: self.__service_started,
        })
        self.onClose.append(self.__on_close)

    def __on_close(self):
        self.__timer.stop()
        del self.__timer_conn
        del self.__timer
        RemovePopup(self.RESUME_POPUP_ID)
        self.session.deleteDialog(self.status_dialog)

    def __aspect_changed(self):
        self.status_dialog.set_status(self.getAspectString(), "#00ff00")

    def __pts_available(self):
        if getPlayPositionPts(self.session) is None:
            self.__timer.start(500, True)
        else:
            if self.__resume_time_sec is not None:
                duration_sec = getDurationInSeconds(self.session)
                if (self.__resume_time_sec > 0 and 
                        duration_sec and duration_sec > 0 and
                        self.__resume_time_sec < duration_sec):
                    self.doSeek(self.__resume_time_sec * 90000)
                self.__resume_time_sec = None
                RemovePopup(self.RESUME_POPUP_ID)
            if self.__subtitles_url:
                self.loadSubs(toString(self.__subtitles_url))

    def __service_started(self):
        self.__timer.stop()
        self.resetSubs(True)
        if (self.__resume_time_sec is not None or
                self.__subtitles_url is not None):
            if self.__resume_time_sec is not None:
                Notifications.AddNotificationWithID(self.RESUME_POPUP_ID,
                        MessageBox, _("Resuming playback"), timeout=0,
                        type=MessageBox.TYPE_INFO, enable_input=False)
            self.__timer.start(500, True)

    def play_service_ref(self, service_ref, subtitles_url=None, resume_time_sec=None):
        self.__subtitles_url = subtitles_url
        self.__resume_time_sec = resume_time_sec

        self.session.nav.stopService()
        self.session.nav.playService(service_ref)

    def doEofInternal(self, playing):
        log.info("doEofInternal(%s)"%playing)
        self.player_callback(("eof", playing))

