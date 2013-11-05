'''
Created on 2.2.2013

@author: marko
'''
from Components.config import config, ConfigInteger, ConfigSubsection, ConfigYesNo, ConfigText, NoSave
from Plugins.Extensions.archivCZSK import log
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'

if not hasattr(config,'mediaplayer'):
    config.mediaplayer = ConfigSubsection()
config.mediaplayer.useAlternateUserAgent = ConfigYesNo(default=True)
config.mediaplayer.alternateUserAgent = ConfigText(default="")
config.mediaplayer.extraHeaders = NoSave(ConfigText(default=""))

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
        
    def setHTTPTimeout(self, timeout):
        self.__config.httpTimeout.setValue(str(timeout))
    
    def setExtraHeaders(self, dictHeaders):
        if not self.__config.servicemp4.getValue():
            headersString = '|'.join([(key + ':' + value) for key, value in dictHeaders.iteritems()])
            config.mediaplayer.extraHeaders.setValue(headersString)
        else:
            headersString = '#'.join([(key + ':' + value) for key, value in dictHeaders.iteritems()])
            self.__config.extraHeaders.setValue(headersString)
        
    def setUserAgent(self, agent=""):
        if self.__config.servicemp4.getValue():
            if agent != "":
                self.__config.userAgent.setValue(agent)
        else:
            if agent != "":
                config.mediaplayer.useAlternateUserAgent.setValue(True)
                config.mediaplayer.alternateUserAgent.setValue(agent)
            else:
                config.mediaplayer.useAlternateUserAgent.setValue(False)
        
    def setDownloadMode(self, mode=False):
        if mode:
            self.__config.download.setValue("True")
        else:
            self.__config.download.setValue("False")


class VideoPlaySetting(object):
    def __init__(self):
        self.vpsp = VideoPlaySettingsProvider()
        log.info("Loading %s", self.__class__.__name__)
        
class CustomVideoPlaySetting(VideoPlaySetting):
    def __init__(self, userAgent="", extraHeaders={}, downloadMode=False):
        super(CustomVideoPlaySetting, self).__init__()
        self.vpsp.setUserAgent(userAgent)
        self.vpsp.setExtraHeaders(extraHeaders)
        if downloadMode:
            self.vpsp.setDownloadMode(downloadMode)
        
class DefaultVideoPlaySetting(VideoPlaySetting):
    def __init__(self):
        super(DefaultVideoPlaySetting, self).__init__()
        self.vpsp.setUserAgent(USER_AGENT)
        self.vpsp.setExtraHeaders({})
        self.vpsp.setDownloadMode(False)