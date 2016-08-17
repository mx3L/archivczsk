'''
Created on 2.2.2013

@author: marko
'''
from Components.config import config, ConfigInteger, ConfigSubsection, ConfigYesNo, ConfigText, NoSave
from Plugins.Extensions.archivCZSK import log
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'


def loadSettings(userAgent="", extraHeaders={}, downloadMode=False):
    if userAgent != "" or len(extraHeaders) > 0 or downloadMode:
        CustomVideoPlaySetting(userAgent, extraHeaders, downloadMode)
    else:
        DefaultVideoPlaySetting()
        
def resetSettings():
    DefaultVideoPlaySetting()

class VideoPlaySettingsProvider(object):
    def __init__(self):
        self.__config = config.plugins.archivCZSK.videoPlayer
        if not hasattr(config,'mediaplayer'):
            config.mediaplayer = ConfigSubsection()
        config.mediaplayer.useAlternateUserAgent = ConfigYesNo(default=True)
        config.mediaplayer.alternateUserAgent = ConfigText(default="")
        config.mediaplayer.extraHeaders = NoSave(ConfigText(default=""))
        
    def setExtraHeaders(self, dictHeaders):
        headersString = '|'.join([(key + ':' + value) for key, value in dictHeaders.iteritems()])
        if not hasattr(config.mediaplayer, 'extraHeaders'):
            config.mediaplayer.extraHeaders = NoSave(ConfigText(default=""))
        config.mediaplayer.extraHeaders.setValue(headersString)
        
    def setUserAgent(self, agent=""):
        if agent != "":
            config.mediaplayer.useAlternateUserAgent.setValue(True)
            config.mediaplayer.alternateUserAgent.setValue(agent)
        else:
            config.mediaplayer.useAlternateUserAgent.setValue(False)


class VideoPlaySetting(object):
    def __init__(self):
        self.vpsp = VideoPlaySettingsProvider()
        log.info("Loading %s", self.__class__.__name__)
        
class CustomVideoPlaySetting(VideoPlaySetting):
    def __init__(self, userAgent="", extraHeaders={}, downloadMode=False):
        super(CustomVideoPlaySetting, self).__init__()
        self.vpsp.setUserAgent(userAgent)
        self.vpsp.setExtraHeaders(extraHeaders)
        
class DefaultVideoPlaySetting(VideoPlaySetting):
    def __init__(self):
        super(DefaultVideoPlaySetting, self).__init__()
        self.vpsp.setUserAgent(USER_AGENT)
        self.vpsp.setExtraHeaders({})
