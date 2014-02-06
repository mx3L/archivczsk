from utilities import langToCountry,  languageTranslate

class SubtitlesSearchError(Exception):
    pass

class SubtitlesDownloadError(Exception):
    pass

class SubtitlesCaptchaError(SubtitlesDownloadError):
    pass

class SettingsProvider(object):
    def __init__(self, default_settings, settings=None):
        self.settings = default_settings
        if settings:
            self.settings.update(settings)

    def getSetting(self, key):
        if isinstance(self.settings[key],dict):
            if not 'value' in self.settings[key]:
                if not 'default' in self.settings[key]:
                    raise Exception("Invalid settings provided, missing 'value/default' entry")
                return self.settings[key]['default']
            return self.settings[key]['value']
        return self.settings[key]

    def setSetting(self, key, value):
        if not isinstance(self.settings[key], dict):
            self.settings[key] = {}
        self.settings[key]['value'] = value


class BaseSeeker(object):
    provider_name = 'base'
    supported_langs= []
    default_settings = {}

    def __init__(self, tmp_path, download_path, settings=None, settings_provider=None, logo=None):
        self.tmp_path = tmp_path
        self.download_path = download_path
        if settings_provider is not None:
            print str(self), 'using custom settings_provider - %s'%repr(settings_provider)
            self.settings_provider = settings_provider
        elif settings is not None:
            print str(self), 'using default settings_provider with custom settings'
            self.settings_provider = SettingsProvider(self.default_settings,settings)
        else:
            print str(self), 'using default settings_provider with default settings'
            self.settings_provider = SettingsProvider(self.default_settings)

    def __str__(self):
        return "["+self.__class__.__name__ +"]"

    def search(self, title=None, filepath=None, langs=None, season=None, episode=None, tvshow=None, year=None):
        """
        returns subtitles dict
        """
        assert title is not None or filepath is not None,'title or filepath needs to be provided'
        subtitles = self._search(title, filepath, langs, season, episode, tvshow, year)
        subtitles['provider'] = self
        for sub in subtitles['list']:
            if not 'country' in sub:
                sub['country'] = langToCountry(languageTranslate(sub['language_name'],0,2))
        return subtitles


    def _search(self, title, filepath, langs, season, episode, tvshow, year):
        return {'list':[{'filename':'','language_name':'','size':'','sync':''},]}


    def download(self, subtitles, selected_subtitle, path = None):
        """
        downloads and returns path to subtitles file(can be compressed)
        """
        return self._download(subtitles, selected_subtitle, path)


    def _download(self, subtitles, selected_subtitle, path):
        pass
