'''
Created on 15.10.2012

@author: marko
'''
import os

from Components.Language import language
from Components.config import config, ConfigSubsection, ConfigSelection, \
    ConfigDirectory, ConfigYesNo, ConfigText, ConfigNothing, getConfigListEntry, \
    NoSave
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from Plugins.Extensions.archivCZSK import log, _
from engine.player.info import videoPlayerInfo
from engine.tools import stb


LANGUAGE_SETTINGS_ID = language.getLanguage()[:2]

############ STB Info ###############

(MANUFACTURER, MODEL, ARCH, VERSION) = stb.getBoxtype()
AZBOX = (MODEL == 'Azbox')

######### Plugin Paths ##############

PLUGIN_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), 'Extensions', 'archivCZSK')
IMAGE_PATH = os.path.join(PLUGIN_PATH, 'gui/icon')
SKIN_PATH = os.path.join(PLUGIN_PATH, 'gui/skins')
REPOSITORY_PATH = os.path.join(PLUGIN_PATH, 'resources/repositories')
STREAM_PATH = os.path.join(PLUGIN_PATH, 'streams/streams.xml')

CUSTOM_FONTS_PATH = os.path.join(SKIN_PATH,'font.json')
CUSTOM_COLORS_PATH = os.path.join(SKIN_PATH,'color.json')
CUSTOM_SIZES_PATH = os.path.join(SKIN_PATH,'sizes.json')

############ Updater Paths #############

TMP_PATH = '/tmp/archivCZSK/'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'

config.plugins.archivCZSK = ConfigSubsection()
config.plugins.archivCZSK.archives = ConfigSubsection()

############# SUPPORTED MEDIA #################

VIDEO_EXTENSIONS = ('.3gp', '3g2', '.asf', '.avi', '.flv', '.mp4', '.mkv', '.mpeg', '.mov' '.mpg', '.wmv', '.divx', '.vob', '.iso', '.ts', '.m3u8')
AUDIO_EXTENSIONS = ('.mp2', '.mp3', '.wma', '.ogg', '.dts', '.flac', '.wav')
SUBTITLES_EXTENSIONS = ('.srt',)
PLAYLIST_EXTENSIONS = ('.m3u', 'pls')
ARCHIVE_EXTENSIONS = ('.rar', '.zip', '.7zip')
PLAYABLE_EXTENSIONS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS + ARCHIVE_EXTENSIONS + PLAYLIST_EXTENSIONS + SUBTITLES_EXTENSIONS

################## Player config #####################################

config.plugins.archivCZSK.videoPlayer = ConfigSubsection()
config.plugins.archivCZSK.videoPlayer.info = NoSave(ConfigNothing())
playertype = [(videoPlayerInfo.type, videoPlayerInfo.getName())]
config.plugins.archivCZSK.videoPlayer.exitFix = ConfigYesNo(default=False)
config.plugins.archivCZSK.videoPlayer.detectedType = ConfigSelection(choices=playertype)

choicelist = [('standard', _('standard player')),
              ('custom', _('custom player (subtitle support)'))]
config.plugins.archivCZSK.videoPlayer.type = ConfigSelection(default="custom", choices=choicelist)
config.plugins.archivCZSK.videoPlayer.useVideoController = ConfigYesNo(default=True)
config.plugins.archivCZSK.videoPlayer.useDefaultSkin = ConfigYesNo(default=False)
config.plugins.archivCZSK.videoPlayer.autoPlay = ConfigYesNo(default=True)
config.plugins.archivCZSK.videoPlayer.confirmExit = ConfigYesNo(default=False)

# to use servicemrua instead of servicemp3/servicemp4
config.plugins.archivCZSK.videoPlayer.servicemrua = ConfigYesNo(default=False)

choicelist = []
for i in range(500, 20000, 500):
    choicelist.append(("%d" % i, "%d KB" % i))
config.plugins.archivCZSK.videoPlayer.bufferSize = ConfigSelection(default="5000", choices=choicelist)

for i in range(1, 100, 1):
    choicelist.append(("%d" % i, "%d MB" % i))
config.plugins.archivCZSK.videoPlayer.downloadBufferSize = ConfigSelection(default="8", choices=choicelist)

choicelist = []
for i in range(1, 50, 1):
    choicelist.append(("%d" % i, "%d s" % i))
config.plugins.archivCZSK.videoPlayer.bufferDuration = ConfigSelection(default="5", choices=choicelist)

choicelist = []
for i in range(0, 250, 1):
    choicelist.append(("%d" % i, "%d s" % i))
config.plugins.archivCZSK.videoPlayer.playDelay = ConfigSelection(default="20", choices=choicelist)

choicelist = []
for i in range(10, 240, 5):
    choicelist.append(("%d" % i, "%d s" % i))
config.plugins.archivCZSK.videoPlayer.rtmpTimeout = ConfigSelection(default="20", choices=choicelist)

choicelist = []
for i in range(1000, 50000, 1000):
    choicelist.append(("%d" % i, "%d ms" % i))
config.plugins.archivCZSK.videoPlayer.archiveBuffer = ConfigSelection(default="10000", choices=choicelist)

choicelist = []
for i in range(1000, 50000, 1000):
    choicelist.append(("%d" % i, "%d ms" % i))
config.plugins.archivCZSK.videoPlayer.liveBuffer = ConfigSelection(default="10000", choices=choicelist)


############ Main config #################

config.plugins.archivCZSK.main_menu = ConfigYesNo(default=True)
config.plugins.archivCZSK.extensions_menu = ConfigYesNo(default=False)
config.plugins.archivCZSK.epg_menu = ConfigYesNo(default=True)
config.plugins.archivCZSK.autoUpdate = ConfigYesNo(default=True)
config.plugins.archivCZSK.preload = ConfigYesNo(default=True)
config.plugins.archivCZSK.confirmExit = ConfigYesNo(default=False)

skinChoices = [os.path.splitext(fname)[0] for fname in os.listdir(SKIN_PATH) if fname.endswith('.xml') ]
skinChoices.append('auto')
config.plugins.archivCZSK.skin = ConfigSelection(default="auto", choices=skinChoices)

choicelist = [('1', _("info")), ('2', _("debug"))]
config.plugins.archivCZSK.debugMode = ConfigSelection(default='1', choices=choicelist)

def changeLogMode(configElement):
    log.changeMode(int(configElement.value))

config.plugins.archivCZSK.debugMode.addNotifier(changeLogMode)

############ Paths #######################

config.plugins.archivCZSK.dataPath = ConfigDirectory(default=os.path.join(PLUGIN_PATH, "resources/data"))
config.plugins.archivCZSK.downloadsPath = ConfigDirectory(default="/media/hdd")
config.plugins.archivCZSK.subtitlesPath = ConfigDirectory(default="/tmp")

########### Misc #########################

config.plugins.archivCZSK.showBrokenAddons = ConfigYesNo(default=True)
config.plugins.archivCZSK.showVideoSourceSelection = ConfigYesNo(default=True)
config.plugins.archivCZSK.convertPNG = ConfigYesNo(default=True)
config.plugins.archivCZSK.clearMemory = ConfigYesNo(default=False)
config.plugins.archivCZSK.hdmuFix = ConfigYesNo(default=False)


def get_player_settings():
    list = []
    player = config.plugins.archivCZSK.videoPlayer.type.getValue()
    useServiceMRUA = config.plugins.archivCZSK.videoPlayer.servicemrua.getValue()
    list.append(getConfigListEntry(_("Show more info about player"), config.plugins.archivCZSK.videoPlayer.info))
    list.append(getConfigListEntry(_("Video player"), config.plugins.archivCZSK.videoPlayer.type))
    if player == 'custom':
        list.append(getConfigListEntry(_("Use video controller"), config.plugins.archivCZSK.videoPlayer.useVideoController))
        list.append(getConfigListEntry(_("Use default skin"), config.plugins.archivCZSK.videoPlayer.useDefaultSkin))
        if videoPlayerInfo.type != 'gstreamer':
            list.append(getConfigListEntry(_("Exit fix"), config.plugins.archivCZSK.videoPlayer.exitFix))
        if videoPlayerInfo.type == 'gstreamer':
            list.append(getConfigListEntry(_("Buffer size"), config.plugins.archivCZSK.videoPlayer.bufferSize))
    if player == 'standard' and AZBOX:
        list.append(getConfigListEntry(_("Use servicemrua (AZBOX)"), config.plugins.archivCZSK.videoPlayer.servicemrua))
    list.append(getConfigListEntry(_("RTMP Timeout"), config.plugins.archivCZSK.videoPlayer.rtmpTimeout))
    list.append(getConfigListEntry(_("TV archive rtmp buffer"), config.plugins.archivCZSK.videoPlayer.archiveBuffer))
    list.append(getConfigListEntry(_("Default live rtmp streams buffer"), config.plugins.archivCZSK.videoPlayer.liveBuffer))
    # if not (videoPlayerInfo.type == 'gstreamer'):
    list.append(getConfigListEntry(_("Play after"), config.plugins.archivCZSK.videoPlayer.playDelay))
    list.append(getConfigListEntry(_("Confirm exit when closing player"), config.plugins.archivCZSK.videoPlayer.confirmExit))
    return list

def get_main_settings():
    list = []
    list.append(getConfigListEntry(_("Skin"), config.plugins.archivCZSK.skin))
    list.append(getConfigListEntry(_("Allow auto-update"), config.plugins.archivCZSK.autoUpdate))
    # list.append(getConfigListEntry(_("Preload"), config.plugins.archivCZSK.preload))
    list.append(getConfigListEntry(_("Debug mode"), config.plugins.archivCZSK.debugMode))
    list.append(getConfigListEntry(_("Add to extensions menu"), config.plugins.archivCZSK.extensions_menu))
    list.append(getConfigListEntry(_("Add to main menu"), config.plugins.archivCZSK.main_menu))
    list.append(getConfigListEntry(_("Add search option in epg menu"), config.plugins.archivCZSK.epg_menu))
    list.append(getConfigListEntry(_("Default category"), config.plugins.archivCZSK.defaultCategory))
    list.append(getConfigListEntry(_("Confirm exit when closing plugin"), config.plugins.archivCZSK.confirmExit))
    return list

def get_path_settings():
    list = []
    list.append(getConfigListEntry(_("Data path"), config.plugins.archivCZSK.dataPath))
    list.append(getConfigListEntry(_("Downloads path"), config.plugins.archivCZSK.downloadsPath))
    list.append(getConfigListEntry(_("Subtitles path"), config.plugins.archivCZSK.subtitlesPath))
    return list

def get_misc_settings():
    list = []
    list.append(getConfigListEntry(_("Show broken addons"), config.plugins.archivCZSK.showBrokenAddons))
    list.append(getConfigListEntry(_("Show video source selection"), config.plugins.archivCZSK.showVideoSourceSelection))
    list.append(getConfigListEntry(_("Convert captcha images to 8bit"), config.plugins.archivCZSK.convertPNG))
    list.append(getConfigListEntry(_("Drop caches on exit"), config.plugins.archivCZSK.clearMemory))
    if ARCH == 'sh4':
        list.append(getConfigListEntry(_("Amiko HDMU fix"), config.plugins.archivCZSK.hdmuFix))
    return list
