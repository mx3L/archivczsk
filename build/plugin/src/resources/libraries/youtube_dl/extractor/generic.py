# coding: utf-8

from __future__ import unicode_literals

import os
import re
import sys

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..compat import (
    compat_etree_fromstring,
    compat_str,
    compat_urllib_parse_unquote,
    compat_urlparse,
    compat_xml_parse_error,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    HEADRequest,
    is_html,
    js_to_json,
    KNOWN_EXTENSIONS,
    merge_dicts,
    mimetype2ext,
    orderedSet,
    sanitized_Request,
    smuggle_url,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    UnsupportedError,
    xpath_text,
)
from .commonprotocols import RtmpIE

class GenericIE(InfoExtractor):
    IE_DESC = 'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = 'generic'
    _TESTS = [
        # Direct link to a video
        {
            'url': 'http://media.w3.org/2010/05/sintel/trailer.mp4',
            'md5': '67d406c2bcb6af27fa886f31aa934bbe',
            'info_dict': {
                'id': 'trailer',
                'ext': 'mp4',
                'title': 'trailer',
                'upload_date': '20100513',
            }
        },
        # {
        #     # TODO: find another test
        #     # http://schema.org/VideoObject
        #     'url': 'https://flipagram.com/f/nyvTSJMKId',
        #     'md5': '888dcf08b7ea671381f00fab74692755',
        #     'info_dict': {
        #         'id': 'nyvTSJMKId',
        #         'ext': 'mp4',
        #         'title': 'Flipagram by sjuria101 featuring Midnight Memories by One Direction',
        #         'description': '#love for cats.',
        #         'timestamp': 1461244995,
        #         'upload_date': '20160421',
        #     },
        #     'params': {
        #         'force_generic_extractor': True,
        #     },
        # }
    ]

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen('[redirect] Following redirect to %s' % new_url)

    def _extract_rss(self, url, video_id, doc):
        playlist_title = doc.find('./channel/title').text
        playlist_desc_el = doc.find('./channel/description')
        playlist_desc = None if playlist_desc_el is None else playlist_desc_el.text

        entries = []
        for it in doc.findall('./channel/item'):
            next_url = None
            enclosure_nodes = it.findall('./enclosure')
            for e in enclosure_nodes:
                next_url = e.attrib.get('url')
                if next_url:
                    break

            if not next_url:
                next_url = xpath_text(it, 'link', fatal=False)

            if not next_url:
                continue

            entries.append({
                '_type': 'url_transparent',
                'url': next_url,
                'title': it.find('title').text,
            })

        return {
            '_type': 'playlist',
            'id': url,
            'title': playlist_title,
            'description': playlist_desc,
            'entries': entries,
        }

    def _extract_camtasia(self, url, video_id, webpage):
        """ Returns None if no camtasia video can be found. """

        camtasia_cfg = self._search_regex(
            r'fo\.addVariable\(\s*"csConfigFile",\s*"([^"]+)"\s*\);',
            webpage, 'camtasia configuration file', default=None)
        if camtasia_cfg is None:
            return None

        title = self._html_search_meta('DC.title', webpage, fatal=True)

        camtasia_url = compat_urlparse.urljoin(url, camtasia_cfg)
        camtasia_cfg = self._download_xml(
            camtasia_url, video_id,
            note='Downloading camtasia configuration',
            errnote='Failed to download camtasia configuration')
        fileset_node = camtasia_cfg.find('./playlist/array/fileset')

        entries = []
        for n in fileset_node.getchildren():
            url_n = n.find('./uri')
            if url_n is None:
                continue

            entries.append({
                'id': os.path.splitext(url_n.text.rpartition('/')[2])[0],
                'title': '%s - %s' % (title, n.tag),
                'url': compat_urlparse.urljoin(url, url_n.text),
                'duration': float_or_none(n.find('./duration').text),
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'title': title,
        }

    def _real_extract(self, url):
        if url.startswith('//'):
            return self.url_result(self.http_scheme() + url)

        parsed_url = compat_urlparse.urlparse(url)
        if not parsed_url.scheme:
            default_search = self._downloader.params.get('default_search')
            if default_search is None:
                default_search = 'fixup_error'

            if default_search in ('auto', 'auto_warning', 'fixup_error'):
                if re.match(r'^[^\s/]+\.[^\s/]+/', url):
                    self._downloader.report_warning('The url doesn\'t specify the protocol, trying with http')
                    return self.url_result('http://' + url)
                elif default_search != 'fixup_error':
                    if default_search == 'auto_warning':
                        if re.match(r'^(?:url|URL)$', url):
                            raise ExtractorError(
                                'Invalid URL:  %r . Call youtube-dlc like this:  youtube-dlc -v "https://www.youtube.com/watch?v=BaW_jenozKc"  ' % url,
                                expected=True)
                        else:
                            self._downloader.report_warning(
                                'Falling back to youtube search for  %s . Set --default-search "auto" to suppress this warning.' % url)
                    return self.url_result('ytsearch:' + url)

            if default_search in ('error', 'fixup_error'):
                raise ExtractorError(
                    '%r is not a valid URL. '
                    'Set --default-search "ytsearch" (or run  youtube-dlc "ytsearch:%s" ) to search YouTube'
                    % (url, url), expected=True)
            else:
                if ':' not in default_search:
                    default_search += ':'
                return self.url_result(default_search + url)

        url, smuggled_data = unsmuggle_url(url)
        force_videoid = None
        is_intentional = smuggled_data and smuggled_data.get('to_generic')
        if smuggled_data and 'force_videoid' in smuggled_data:
            force_videoid = smuggled_data['force_videoid']
            video_id = force_videoid
        else:
            video_id = self._generic_id(url)

        self.to_screen('%s: Requesting header' % video_id)

        head_req = HEADRequest(url)
        head_response = self._request_webpage(
            head_req, video_id,
            note=False, errnote='Could not send HEAD request to %s' % url,
            fatal=False)

        if head_response is not False:
            # Check for redirect
            new_url = head_response.geturl()
            if url != new_url:
                self.report_following_redirect(new_url)
                if force_videoid:
                    new_url = smuggle_url(
                        new_url, {'force_videoid': force_videoid})
                return self.url_result(new_url)

        full_response = None
        if head_response is False:
            request = sanitized_Request(url)
            request.add_header('Accept-Encoding', '*')
            full_response = self._request_webpage(request, video_id)
            head_response = full_response

        info_dict = {
            'id': video_id,
            'title': self._generic_title(url),
            'upload_date': unified_strdate(head_response.headers.get('Last-Modified'))
        }

        # Check for direct link to a video
        content_type = head_response.headers.get('Content-Type', '').lower()
        m = re.match(r'^(?P<type>audio|video|application(?=/(?:ogg$|(?:vnd\.apple\.|x-)?mpegurl)))/(?P<format_id>[^;\s]+)', content_type)
        if m:
            format_id = compat_str(m.group('format_id'))
            if format_id.endswith('mpegurl'):
                formats = self._extract_m3u8_formats(url, video_id, 'mp4')
            elif format_id == 'f4m':
                formats = self._extract_f4m_formats(url, video_id)
            else:
                formats = [{
                    'format_id': format_id,
                    'url': url,
                    'vcodec': 'none' if m.group('type') == 'audio' else None
                }]
                info_dict['direct'] = True
            self._sort_formats(formats)
            info_dict['formats'] = formats
            return info_dict

        if not self._downloader.params.get('test', False) and not is_intentional:
            force = self._downloader.params.get('force_generic_extractor', False)
            self._downloader.report_warning(
                '%s on generic information extractor.' % ('Forcing' if force else 'Falling back'))

        if not full_response:
            request = sanitized_Request(url)
            # Some webservers may serve compressed content of rather big size (e.g. gzipped flac)
            # making it impossible to download only chunk of the file (yet we need only 512kB to
            # test whether it's HTML or not). According to youtube-dlc default Accept-Encoding
            # that will always result in downloading the whole file that is not desirable.
            # Therefore for extraction pass we have to override Accept-Encoding to any in order
            # to accept raw bytes and being able to download only a chunk.
            # It may probably better to solve this by checking Content-Type for application/octet-stream
            # after HEAD request finishes, but not sure if we can rely on this.
            request.add_header('Accept-Encoding', '*')
            full_response = self._request_webpage(request, video_id)

        first_bytes = full_response.read(512)

        # Is it an M3U playlist?
        if first_bytes.startswith(b'#EXTM3U'):
            info_dict['formats'] = self._extract_m3u8_formats(url, video_id, 'mp4')
            self._sort_formats(info_dict['formats'])
            return info_dict

        # Maybe it's a direct link to a video?
        # Be careful not to download the whole thing!
        if not is_html(first_bytes):
            self._downloader.report_warning(
                'URL could be a direct video link, returning it as such.')
            info_dict.update({
                'direct': True,
                'url': url,
            })
            return info_dict

        webpage = self._webpage_read_content(
            full_response, url, video_id, prefix=first_bytes)

        self.report_extraction(video_id)

        # Is it an RSS feed, a SMIL file, an XSPF playlist or a MPD manifest?
        try:
            doc = compat_etree_fromstring(webpage.encode('utf-8'))
            if doc.tag == 'rss':
                return self._extract_rss(url, video_id, doc)
            elif doc.tag == 'SmoothStreamingMedia':
                info_dict['formats'] = self._parse_ism_formats(doc, url)
                self._sort_formats(info_dict['formats'])
                return info_dict
            elif re.match(r'^(?:{[^}]+})?smil$', doc.tag):
                smil = self._parse_smil(doc, url, video_id)
                self._sort_formats(smil['formats'])
                return smil
            elif doc.tag == '{http://xspf.org/ns/0/}playlist':
                return self.playlist_result(
                    self._parse_xspf(
                        doc, video_id, xspf_url=url,
                        xspf_base_url=full_response.geturl()),
                    video_id)
            elif re.match(r'(?i)^(?:{[^}]+})?MPD$', doc.tag):
                info_dict['formats'] = self._parse_mpd_formats(
                    doc,
                    mpd_base_url=full_response.geturl().rpartition('/')[0],
                    mpd_url=url)
                self._sort_formats(info_dict['formats'])
                return info_dict
            elif re.match(r'^{http://ns\.adobe\.com/f4m/[12]\.0}manifest$', doc.tag):
                info_dict['formats'] = self._parse_f4m_formats(doc, url, video_id)
                self._sort_formats(info_dict['formats'])
                return info_dict
        except compat_xml_parse_error:
            pass

        # Is it a Camtasia project?
        camtasia_res = self._extract_camtasia(url, video_id, webpage)
        if camtasia_res is not None:
            return camtasia_res

        # Sometimes embedded video player is hidden behind percent encoding
        # (e.g. https://github.com/ytdl-org/youtube-dl/issues/2448)
        # Unescaping the whole page allows to handle those cases in a generic way
        webpage = compat_urllib_parse_unquote(webpage)

        # Unescape squarespace embeds to be detected by generic extractor,
        # see https://github.com/ytdl-org/youtube-dl/issues/21294
        webpage = re.sub(
            r'<div[^>]+class=[^>]*?\bsqs-video-wrapper\b[^>]*>',
            lambda x: unescapeHTML(x.group(0)), webpage)

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._og_search_title(
            webpage, default=None) or self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title',
            default='video')

        # Try to detect age limit automatically
        age_limit = self._rta_search(webpage)
        # And then there are the jokers who advertise that they use RTA,
        # but actually don't.
        AGE_LIMIT_MARKERS = [
            r'Proudly Labeled <a href="http://www\.rtalabel\.org/" title="Restricted to Adults">RTA</a>',
        ]
        if any(re.search(marker, webpage) for marker in AGE_LIMIT_MARKERS):
            age_limit = 18

        # video uploader is domain name
        video_uploader = self._search_regex(
            r'^(?:https?://)?([^/]*)/.*', url, 'video uploader')

        video_description = self._og_search_description(webpage, default=None)
        video_thumbnail = self._og_search_thumbnail(webpage, default=None)

        info_dict.update({
            'title': video_title,
            'description': video_description,
            'thumbnail': video_thumbnail,
            'age_limit': age_limit,
        })

        # Look for YouTube embeds
        youtube_urls = YoutubeIE._extract_urls(webpage)
        if youtube_urls:
            return self.playlist_from_matches(
                youtube_urls, video_id, video_title, ie=YoutubeIE.ie_key())

        if not found:
            raise UnsupportedError(url)

        entries = []
        for video_url in orderedSet(found):
            video_url = unescapeHTML(video_url)
            video_url = video_url.replace('\\/', '/')
            video_url = compat_urlparse.urljoin(url, video_url)
            video_id = compat_urllib_parse_unquote(os.path.basename(video_url))

            # Sometimes, jwplayer extraction will result in a YouTube URL
            if YoutubeIE.suitable(video_url):
                entries.append(self.url_result(video_url, 'Youtube'))
                continue

            # here's a fun little line of code for you:
            video_id = os.path.splitext(video_id)[0]

            entry_info_dict = {
                'id': video_id,
                'uploader': video_uploader,
                'title': video_title,
                'age_limit': age_limit,
            }

            if RtmpIE.suitable(video_url):
                entry_info_dict.update({
                    '_type': 'url_transparent',
                    'ie_key': RtmpIE.ie_key(),
                    'url': video_url,
                })
                entries.append(entry_info_dict)
                continue

            ext = determine_ext(video_url)
            if ext == 'smil':
                entry_info_dict['formats'] = self._extract_smil_formats(video_url, video_id)
            elif ext == 'xspf':
                return self.playlist_result(self._extract_xspf_playlist(video_url, video_id), video_id)
            elif ext == 'm3u8':
                entry_info_dict['formats'] = self._extract_m3u8_formats(video_url, video_id, ext='mp4')
            elif ext == 'mpd':
                entry_info_dict['formats'] = self._extract_mpd_formats(video_url, video_id)
            elif ext == 'f4m':
                entry_info_dict['formats'] = self._extract_f4m_formats(video_url, video_id)
            elif re.search(r'(?i)\.(?:ism|smil)/manifest', video_url) and video_url != url:
                # Just matching .ism/manifest is not enough to be reliably sure
                # whether it's actually an ISM manifest or some other streaming
                # manifest since there are various streaming URL formats
                # possible (see [1]) as well as some other shenanigans like
                # .smil/manifest URLs that actually serve an ISM (see [2]) and
                # so on.
                # Thus the most reasonable way to solve this is to delegate
                # to generic extractor in order to look into the contents of
                # the manifest itself.
                # 1. https://azure.microsoft.com/en-us/documentation/articles/media-services-deliver-content-overview/#streaming-url-formats
                # 2. https://svs.itworkscdn.net/lbcivod/smil:itwfcdn/lbci/170976.smil/Manifest
                entry_info_dict = self.url_result(
                    smuggle_url(video_url, {'to_generic': True}),
                    GenericIE.ie_key())
            else:
                entry_info_dict['url'] = video_url

            if entry_info_dict.get('formats'):
                self._sort_formats(entry_info_dict['formats'])

            entries.append(entry_info_dict)

        if len(entries) == 1:
            return entries[0]
        else:
            for num, e in enumerate(entries, start=1):
                # 'url' results don't have a title
                if e.get('title') is not None:
                    e['title'] = '%s (%d)' % (e['title'], num)
            return {
                '_type': 'playlist',
                'entries': entries,
            }
