import os

from Components.Language import language
from Components.config import config, ConfigSubsection, ConfigSelection, \
    ConfigDirectory, ConfigYesNo, ConfigNothing, getConfigListEntry, \
    NoSave
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from Plugins.Extensions.archivCZSK import log, _
from Plugins.Extensions.archivCZSK.engine.player.info import videoPlayerInfo
from Plugins.Extensions.archivCZSK.engine.tools import stb


LANGUAGE_SETTINGS_ID = language.getLanguage()[:2]
MENU_SEPARATOR = getConfigListEntry("----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------", NoSave(ConfigNothing()))

############ STB Info ###############

(MANUFACTURER, MODEL, ARCH, VERSION) = stb.getBoxtype()

######### Plugin Paths ##############
ENIGMA_PLUGIN_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), 'Extensions')
PLUGIN_PATH = os.path.join(ENIGMA_PLUGIN_PATH, 'archivCZSK')
IMAGE_PATH = os.path.join(PLUGIN_PATH, 'gui/icon')
SKIN_PATH = os.path.join(PLUGIN_PATH, 'gui/skins')
REPOSITORY_PATH = os.path.join(PLUGIN_PATH, 'resources/repositories')

CUSTOM_FONTS_PATH = os.path.join(SKIN_PATH,'font.json')
CUSTOM_COLORS_PATH = os.path.join(SKIN_PATH,'color.json')
CUSTOM_SIZES_PATH = os.path.join(SKIN_PATH,'sizes.json')

############ Updater Paths #############


#USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'

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

choicelist = [('standard', _('standard player')),
              ('custom', _('custom player (subtitle support)'))]
config.plugins.archivCZSK.videoPlayer.type = ConfigSelection(default="custom", choices=choicelist)
config.plugins.archivCZSK.videoPlayer.autoPlay = ConfigYesNo(default=True)
config.plugins.archivCZSK.videoPlayer.confirmExit = ConfigYesNo(default=False)

choicelist = []
for i in range(10, 240, 5):
    choicelist.append(("%d" % i, "%d s" % i))
config.plugins.archivCZSK.videoPlayer.rtmpTimeout = ConfigSelection(default="20", choices=choicelist)

choicelist = []
for i in range(1000, 50000, 1000):
    choicelist.append(("%d" % i, "%d ms" % i))
config.plugins.archivCZSK.videoPlayer.rtmpBuffer = ConfigSelection(default="10000", choices=choicelist)

############ Main config #################

config.plugins.archivCZSK.main_menu = ConfigYesNo(default=True)
config.plugins.archivCZSK.extensions_menu = ConfigYesNo(default=False)
config.plugins.archivCZSK.epg_menu = ConfigYesNo(default=True)
config.plugins.archivCZSK.archivAutoUpdate = ConfigYesNo(default=True)
config.plugins.archivCZSK.autoUpdate = ConfigYesNo(default=True)
config.plugins.archivCZSK.preload = ConfigYesNo(default=True)


skinChoices = [os.path.splitext(fname)[0] for fname in os.listdir(SKIN_PATH) if fname.endswith('.xml') ]
skinChoices.append('auto')
config.plugins.archivCZSK.skin = ConfigSelection(default="auto", choices=skinChoices)
config.plugins.archivCZSK.showVideoInfo = ConfigYesNo(default=True)
config.plugins.archivCZSK.downloadPoster = ConfigYesNo(default=True)
choicelist = []
#choicelist.append(("%d" % 0, "%d" % 0))
for i in range(0, 310, 10):
    choicelist.append(("%d" % i, "%d" % i))
config.plugins.archivCZSK.posterImageMax = ConfigSelection(default="10", choices=choicelist)

choicelistCsfd = [('1', _("Internal")), ('2', _("CSFD")), ('3', _("CSFDLite"))]
config.plugins.archivCZSK.csfdMode = ConfigSelection(default='1', choices=choicelistCsfd)

############ Paths #######################

config.plugins.archivCZSK.dataPath = ConfigDirectory(default=os.path.join(PLUGIN_PATH, "resources/data"))
config.plugins.archivCZSK.downloadsPath = ConfigDirectory(default="/media/hdd")
config.plugins.archivCZSK.posterPath = ConfigDirectory(default="/tmp")
config.plugins.archivCZSK.tmpPath = ConfigDirectory(default="/tmp")
config.plugins.archivCZSK.logPath = ConfigDirectory(default="/tmp")

########### Misc #########################

choicelist = [('1', _("info")), ('2', _("debug"))]
config.plugins.archivCZSK.debugMode = ConfigSelection(default='1', choices=choicelist)
config.plugins.archivCZSK.showBrokenAddons = ConfigYesNo(default=True)
config.plugins.archivCZSK.showVideoSourceSelection = ConfigYesNo(default=True)
config.plugins.archivCZSK.convertPNG = ConfigYesNo(default=True)
config.plugins.archivCZSK.clearMemory = ConfigYesNo(default=False)
config.plugins.archivCZSK.confirmExit = ConfigYesNo(default=False)

def changeLogMode(configElement):
    log.changeMode(int(configElement.value))

config.plugins.archivCZSK.debugMode.addNotifier(changeLogMode)



def get_player_settings():
    list = []
    list.append(getConfigListEntry(_("Show more info about player"), config.plugins.archivCZSK.videoPlayer.info))
    list.append(getConfigListEntry(_("RTMP Timeout"), config.plugins.archivCZSK.videoPlayer.rtmpTimeout))
    list.append(getConfigListEntry(_("RTMP Buffer"), config.plugins.archivCZSK.videoPlayer.rtmpBuffer))
    list.append(getConfigListEntry(_("Confirm exit when closing player"), config.plugins.archivCZSK.videoPlayer.confirmExit))
    return list

def get_main_settings():
    list = []
    list.append(getConfigListEntry(_("Skin"), config.plugins.archivCZSK.skin))
    list.append(getConfigListEntry(_("Default category"), config.plugins.archivCZSK.defaultCategory))
    list.append(getConfigListEntry(_("Allow archivCZSK auto update"), config.plugins.archivCZSK.archivAutoUpdate))
    list.append(getConfigListEntry(_("Allow addons auto update"), config.plugins.archivCZSK.autoUpdate))
    list.append(MENU_SEPARATOR)
    list.append(getConfigListEntry(_("Show movie info"), config.plugins.archivCZSK.showVideoInfo))
    list.append(getConfigListEntry(_("Show movie poster"), config.plugins.archivCZSK.downloadPoster))
    list.append(getConfigListEntry(_("Max posters on HDD"), config.plugins.archivCZSK.posterImageMax))
    list.append(MENU_SEPARATOR)
    # list.append(getConfigListEntry(_("Preload"), config.plugins.archivCZSK.preload))
    list.append(getConfigListEntry(_("Add to extensions menu"), config.plugins.archivCZSK.extensions_menu))
    list.append(getConfigListEntry(_("Add to main menu"), config.plugins.archivCZSK.main_menu))
    # if i know this is not functional
    #list.append(getConfigListEntry(_("Add search option in epg menu"), config.plugins.archivCZSK.epg_menu))
    list.append(MENU_SEPARATOR)
    list.append(getConfigListEntry(_("CSFD plugin"), config.plugins.archivCZSK.csfdMode))
    
    
    return list

def get_path_settings():
    list = []
    list.append(getConfigListEntry(_("Data path"), config.plugins.archivCZSK.dataPath))
    list.append(getConfigListEntry(_("Temp path"), config.plugins.archivCZSK.tmpPath))
    list.append(getConfigListEntry(_("Downloads path"), config.plugins.archivCZSK.downloadsPath))
    list.append(getConfigListEntry(_("Posters path"), config.plugins.archivCZSK.posterPath))
    
    list.append(getConfigListEntry(_("Log path"), config.plugins.archivCZSK.logPath))
    return list

def get_misc_settings():
    list = []
    list.append(getConfigListEntry(_("Debug mode"), config.plugins.archivCZSK.debugMode))
    list.append(getConfigListEntry(_("Confirm exit when closing plugin"), config.plugins.archivCZSK.confirmExit))
    list.append(getConfigListEntry(_("Show broken addons"), config.plugins.archivCZSK.showBrokenAddons))
    list.append(getConfigListEntry(_("Show video source selection"), config.plugins.archivCZSK.showVideoSourceSelection))
    list.append(getConfigListEntry(_("Convert captcha images to 8bit"), config.plugins.archivCZSK.convertPNG))
    list.append(getConfigListEntry(_("Drop caches on exit"), config.plugins.archivCZSK.clearMemory))
    return list
