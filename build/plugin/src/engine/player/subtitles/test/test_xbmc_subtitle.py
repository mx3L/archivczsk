'''
Created on Feb 6, 2014

@author: marko
'''
import os, sys
import time
import unittest
filename = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join (filename, '..'))


class TestXBMCSubtitleProvider(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.settings = {}
        cls.tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'subcache')
        cls.download_path = cls.tmp_path
        cls.provider_class = None

    def captcha_cb(self, url):
        return raw_input('visit url:%s\ntype captcha:'%url)

    def message_cb(self, text):
        print text

    def delay_cb(self, seconds):
        for i in xrange(seconds):
            print i,'second'
            time.sleep(1)

    def setUp(self):
        self.search_list = []
        self.tvshow_list = []
        self.download_list = []
        self.download_tvshow_list = []

    def testSearchSimple(self):
        for title in self.search_list:
            result = self.provider.search(title)
            print result
            self.assertTrue(len(result) > 0, 'There should be at least 1 subtitle found')

    def testTVShowTitle(self):
        for tvshow in self.tvshow_list:
            result = self.provider.search(title=tvshow[0], tvshow=tvshow[0])
            self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')

    def testTVShowTitleSeason(self):
        for tvshow in self.tvshow_list:
            result = self.provider.search(title=tvshow[0], tvshow=tvshow[0], season=tvshow[1])
            self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')

    def testTVShowTitleSeasonEpisode(self):
        for tvshow in self.tvshow_list:
            result = self.provider.search(title=tvshow[0], tvshow=tvshow[0], season=tvshow[1], episode=tvshow[2])
            self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')

    def testDownloadSimple(self):
        for title in self.download_list:
            subtitles = self.provider.search(title)
            self.assertTrue(len(subtitles['list']) > 0, 'There should be at least 1 subtitle found')
            self.provider.download(subtitles, subtitles['list'][-1])

    def testDownloadTVShow(self):
        for title, season, episode in self.download_tvshow_list:
            result = self.provider.search(title=title, tvshow=title, season=season, episode=episode)
            self.provider.download(result, result['list'][-1])


from seekers.xbmc_subtitles import TitulkyComSeeker
class TestTitulkycom(TestXBMCSubtitleProvider):
    def setUp(self):
        self.settings = {'Titulkyuser':'',
                                    'Titulkypass':''}
        self.search_list = ['Alias']
        self.download_list= []
        self.tvshow_list = []
        self.download_tvshow_list = []
        self.provider= TitulkyComSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import EdnaSeeker
class TestEdna(TestXBMCSubtitleProvider):
    def setUp(self):
        self.settings = {}
        self.search_list = []
        self.download_list = []
        self.tvshow_list = [('True Detective','1','1')]
        self.download_tvshow_list = [('True Detective','1','1'), ('True Detective','1','6')]
        self.provider= EdnaSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import OpenSubtitlesSeeker
class TestOpenSubtitles(TestXBMCSubtitleProvider):
    def setUp(self):
        self.settings = {}
        self.search_list = ['Dark Knight']
        self.download_list= ['Dark Knight']
        self.tvshow_list = []
        self.download_tvshow_list = []
        self.provider= OpenSubtitlesSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)




if __name__ == "__main__":
    unittest.main()
