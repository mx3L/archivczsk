'''
Created on Feb 10, 2014

@author: marko
'''
import os
import zipfile
import threading

SUBTITLES_SEEKERS = []

from seekers.utilities import regex_tvshow, regex_movie, languageTranslate, langToCountry
from seekers import TitulkyComSeeker, EdnaSeeker, OpenSubtitlesSeeker
from seekers import SubtitlesCaptchaError, SubtitlesDownloadError, SubtitlesSearchError

if TitulkyComSeeker.module:
    SUBTITLES_SEEKERS.append(TitulkyComSeeker)
if EdnaSeeker.module:
    SUBTITLES_SEEKERS.append(EdnaSeeker)
if OpenSubtitlesSeeker.module:
    SUBTITLES_SEEKERS.append(OpenSubtitlesSeeker)


class SubsSeeker(object):
    SUBTILES_EXTENSIONS= ['.srt','.sub']

    def __init__(self,  download_path, tmp_path, captcha_cb, delay_cb, message_cb, settings=None, settings_provider_cls=None):
        self.download_path = download_path
        self.tmp_path = tmp_path
        self.seekers = []
        for seeker in SUBTITLES_SEEKERS:
            provider_name = seeker.provider_name
            default_settings = seeker.default_settings
            default_settings['enabled'] = {'type':'yesno','default':True,'label':'Enabled','pos':-1}
            if settings_provider_cls is not None:
                settings=None
                settings_provider = settings_provider_cls(provider_name, default_settings)
                self.seekers.append(seeker(tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
            elif settings is not None and provider_name in settings:
                settings_provider = None
                self.seekers.append(seeker(tmp_path, download_path, settings[provider_name], settings_provider, captcha_cb, delay_cb, message_cb))
            else:
                settings = None
                settings_provider = None
                self.seekers.append(seeker(tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))

    def getSubtitles(self, updateCB=None, title=None, filepath=None, langs=None):
        print '[SubsSeeker] getting subtitles list', title, filepath, langs
        if not title:
            title = os.path.splitext(os.path.basename(filepath))[0]
        subtitlesDict= {}
        threads = []
        lock = threading.Lock()

        def searchSubtitles(seeker, subtitlesList, title, filepath, langs, season, episode, tvshow, year):
            subtitles = seeker.search(title, filepath, langs, season, episode, tvshow, year)
            with lock:
                subtitlesDict[seeker.__class__.__name__] = subtitles
                if updateCB:
                    updateCB(subtitlesDict)

        season=episode=tvshow=year=""

        titlemovie, year = regex_movie(title)
        if titlemovie:
            title = titlemovie

        # from xbmc-subtitles
        if year == "":                                            # If we have a year, assume no tv show
            if str(year) == "":                                          # Still no year: *could* be a tvshow
                titleshow, season, episode = regex_tvshow(False, title)
                if titleshow != "" and season != "" and episode != "":
                    season = str(int(season))
                    episode = str(int(episode))
                    tvshow = titleshow
                else:
                    season = ""                                              # Reset variables: could contain garbage from tvshow regex above
                    episode = ""
                    tvshow = ""
            else:
                year = ""
        print title, filepath, langs, season, episode, tvshow, year

        for seeker in self.seekers:
            if seeker.settings_provider.getSetting('enabled'):
                for lang in seeker.supported_langs:
                    if lang in langs:
                        threads.append(threading.Thread(target=searchSubtitles, args=(seeker, subtitlesDict, title, filepath, langs, season, episode, tvshow, year)))
                        break
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return subtitlesDict

    def getSubtitlesList(self, subtitles_dict, provider=None, langs=None, synced=False, nonsynced=False):
        subtitles_list = []
        if provider and provider in subtitles_dict:
            subtitles_list = subtitles_dict[provider]['list']
            for sub in subtitles_list:
                if 'provider' not in sub:
                    sub['provider'] = subtitles_dict[provider]['provider'].provider_name
                if 'country' not in sub:
                    sub['country'] = langToCountry(languageTranslate(sub['language_name'],0,2))
        else:
            for provider in subtitles_dict:
                provider_list = subtitles_dict[provider]['list']
                subtitles_list+= provider_list
                for sub in provider_list:
                    if 'provider' not in sub:
                        sub['provider'] = subtitles_dict[provider]['provider'].provider_name
                    if 'country' not in sub:
                        sub['country'] = langToCountry(languageTranslate(sub['language_name'],0,2))
        if synced:
            subtitles_list = filter(lambda x:x['sync'], subtitles_list)
        elif nonsynced:
            subtitles_list = filter(lambda x:not x['sync'], subtitles_list)
        if langs:
            subtitles_list = filter(lambda x:x['language_name'] in [languageTranslate(lang, 0, 2) for lang in langs])
        return subtitles_list

    def sortSubtitlesList(self, subtitles_list, langs=None, sort_langs=False, sort_rank=False, sort_sync=False, sort_provider=False ):
        def sortLangs(x):
            for idx, lang in enumerate(langs):
                if languageTranslate(x['language_name'],0,2) == lang:
                    return idx
            return len(langs)
        if langs and sort_langs:
            return sorted(subtitles_list, key = sortLangs)
        if sort_provider:
            return sorted(subtitles_list, key= lambda x:x['provider'])
        if sort_rank:
            return subtitles_list
        if sort_sync:
            return sorted(subtitles_list, key=lambda x:x['sync'],reverse=True)
        return subtitles_list

    def downloadSubtitle(self, selected_subtitle, subtitles_dict):
        print '[SubsSeeker] downloading subtitle', selected_subtitle
        seeker = None
        for provider in subtitles_dict.keys():
            if selected_subtitle in subtitles_dict[provider]['list']:
                seeker = subtitles_dict[provider]['provider']
                break
        if seeker:
            compressed, filepath= seeker.download(subtitles_dict[provider], selected_subtitle)
            if compressed:
                if compressed == 'zip':
                    return self._unpack_zipsub(filepath, self.download_path)
                elif compressed == 'rar':
                    return self._unpack_rarsub(filepath, self.download_path)
                else:
                    print '[SubsSeeker] unsupported archive', compressed
                    raise Exception(_("unsupported archive %s"%compressed))
            else:
                return [filepath]

    def _unpack_zipsub(self, zip_path, dest_dir):
        zf = zipfile.ZipFile(zip_path)
        namelist =zf.namelist()
        subsfiles = []
        for subsfn in namelist:
            if os.path.splitext(subsfn)[1] in self.SUBTILES_EXTENSIONS:
                outfile = open(os.path.join(dest_dir, subsfn) , 'wb')
                outfile.write(zf.read(subsfn))
                outfile.flush()
                outfile.close()
                subsfiles.append(os.path.join(dest_dir, subsfn))
        return subsfiles

    def _unpack_rarsub(self, rar_path, dest_dir):
        raise NotImplementedError()

