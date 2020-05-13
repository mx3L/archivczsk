from htmlentitydefs import name2codepoint as n2cp
import htmlentitydefs
import httplib
import imp
import marshal
import md5
import mimetypes
import os.path
import re
import stat
import sys
import socket
import traceback
import urllib
import urllib2
from urlparse import urlsplit, urlparse
from xml.etree.cElementTree import ElementTree, fromstring


from twisted.internet import reactor
from twisted.web.client import Agent, BrowserLikeRedirectAgent, readBody
from twisted.web.http_headers import Headers

try:
    from Plugins.Extensions.archivCZSK import log, removeDiac
except ImportError:
    from logger import log

supported_video_extensions = ('.avi', '.mp4', '.mkv', '.mpeg', '.mpg')

def is_hls_url(url):
    return url.startswith('http') and urlparse(url).path.endswith('.m3u8')

def load_module(code_path):
    try:
        try:
            code_dir = os.path.dirname(code_path)
            code_file = os.path.basename(code_path)

            fin = open(code_path, 'rb')

            return  imp.load_source(md5.new(code_path).hexdigest(), code_path, fin)
        finally:
            try: fin.close()
            except: pass
    except ImportError, x:
        log.logError("ImportError load_module(code_path) failed.\n%s"%traceback.format_exc())
        traceback.print_exc(file=sys.stderr)
        raise
    except:
        log.logError("Exception load_module(code_path) failed.\n%s"%traceback.format_exc())
        traceback.print_exc(file=sys.stderr)
        raise


def load_xml_string(xml_string):
    try:
        root = fromstring(xml_string)
    except Exception, er:
        print "cannot parse xml string", er
        raise
    else:
        return root


def load_xml(xml_file):
    xml = None
    try:
        xml = open(xml_file, "r+")

    # trying to set encoding utf-8 in xml file with not defined encoding
        if 'encoding' not in xml.readline():
            xml.seek(0)
            xml_string = xml.read()
            xml_string = xml_string.decode('utf-8')
            xml.seek(0)
            xml.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            xml.write(xml_string.encode('utf-8'))
            xml.flush()
    except IOError, e:
        print "I/O error(%d): %s" % (e.errno, e.strerror)
    finally:
        if xml:xml.close()


    el = ElementTree()
    try:
        el.parse(xml_file)
    except IOError, e:
        print "cannot load %s file I/O error(%d): %s" % (xml_file, e.errno, e.strerror)
        raise
    else:
        return el

# source from xbmc_doplnky
def decode_html(data):
    try:
        if not type(data) == unicode:
            data = unicode(data, 'utf-8', errors='ignore')
            entity_re = re.compile(r'&(#?)(x?)(\w+);')
            return entity_re.subn(_substitute_entity, data)[0]
    except:
        traceback.print_exc()
        return data

def decode_string(string):
    if isinstance(string, unicode):
        return string
    encodings = ['utf-8', 'windows-1250', 'iso-8859-2']
    for encoding in encodings:
        try:
            return string.decode(encoding)
        except Exception:
            if encoding == encodings[-1]:
                return u'cannot_decode'
            else:
                continue

def toUnicode(text):
    if isinstance(text, basestring):
        if isinstance(text, unicode):
            return text
        if isinstance(text, str):
            return unicode(text, 'utf-8', 'ignore')
    return unicode(str(text), 'utf-8', 'ignore')

def toString(text):
    if text is None:
        return None
    if isinstance(text, basestring):
        if isinstance(text, unicode):
            return text.encode('utf-8')
        return text
    return str(text)

def check_version(local, remote):
    local = local.split('.')
    remote = remote.split('.')
    if len(local) < len(remote):
        for i in range(len(local)):
            if int(local[i]) == int(remote[i]):
                continue
            return int(local[i]) < int(remote[i])
        return True
    else:
        for i in range(len(remote)):
            if int(local[i]) == int(remote[i]):
                continue
            return int(local[i]) < int(remote[i])
        return False


def make_path(p):
    '''Makes sure directory components of p exist.'''
    try:
        os.makedirs(p)
    except OSError:
        pass

def download_to_file(remote, local, mode='wb', debugfnc=None):
    f, localFile = None, None
    try:
        if debugfnc:
            debugfnc("downloading %s to %s", remote, local)
        else:
            print  "downloading %s to %s", (remote, local)
        try:
            import ssl
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            f = urllib2.urlopen(remote, context = context, timeout=10)
        except Exception:
            f = urllib2.urlopen(remote, timeout = 10)
        make_path(os.path.dirname(local))
        localFile = open(local, mode)
        localFile.write(f.read())
    except urllib2.HTTPError, e:
        if debugfnc:
            debugfnc("HTTP Error: %s %s", e.code, remote)
        else:
            print "HTTP Error: %s %s" % (e.code, remote)
        raise
    except urllib2.URLError, e:
        if debugfnc:
            debugfnc("URL Error: %s %s", e.reason, remote)
        else:
            print "URL Error: %s %s" % (e.reason, remote)
        raise
    except IOError, e:
        if debugfnc:
            debugfnc("I/O error(%d): %s", (e.errno, e.strerror))
        else:
            print "I/O error(%d): %s" % (e.errno, e.strerror)
        raise
    else:
        if debugfnc:
            debugfnc('%s succesfully downloaded', local)
        else:
            print local, 'succesfully downloaded'
    finally:
        if f:f.close()
        if localFile:localFile.close()
    print "download finished"

def download_web_file(remote, local, mode='wb', debugfnc=None, headers={}):
    f, localFile = None, None
    try:
        if debugfnc:
            debugfnc("downloading %s to %s", remote, local)
        else:
            print  "downloading %s to %s", (remote, local)
        req = urllib2.Request(remote, headers=headers)
        from Plugins.Extensions.archivCZSK.settings import USER_AGENT
        req.add_header('User-Agent', USER_AGENT)
        f = urllib2.urlopen(req)
        make_path(os.path.dirname(local))
        localFile = open(local, mode)
        localFile.write(f.read())
    except urllib2.HTTPError, e:
        if debugfnc:
            debugfnc("HTTP Error: %s %s", e.code, remote)
        else:
            print "HTTP Error: %s %s" % (e.code, remote)
        raise
    except urllib2.URLError, e:
        if debugfnc:
            debugfnc("URL Error: %s %s", e.reason, remote)
        else:
            print "URL Error: %s %s" % (e.reason, remote)
        raise
    except IOError, e:
        if debugfnc:
            debugfnc("I/O error(%d): %s", (e.errno, e.strerror))
        else:
            print "I/O error(%d): %s" % (e.errno, e.strerror)
        raise
    else:
        if debugfnc:
            debugfnc('%s succesfully downloaded', local)
        else:
            print local, 'succesfully downloaded'
    finally:
        if f:f.close()
        if localFile:localFile.close()


# source from xbmc_doplnky
def _substitute_entity(match):
        ent = match.group(3)
        if match.group(1) == '#':
            # decoding by number
            if match.group(2) == '':
                # number is in decimal
                return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x' + ent, 16))
        else:
            # they were using a name
            cp = n2cp.get(ent)
            if cp: return unichr(cp)
            else: return match.group()



def isSupportedVideo(url):
    if url.startswith('rtmp'):
        return True
    if os.path.splitext(url)[1] != '':
        if os.path.splitext(url)[1] in supported_video_extensions:
            return True
        else:
            return False
    else:
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
        exttype = resp.info().get('Content-Type')
        resp.close()
        ext = mimetypes.guess_extension(exttype)
        if ext in supported_video_extensions:
            return True
        else:
            return False
    return True


def BtoKB(byte):
        return int(byte / float(1024))

def BtoMB(byte):
        return int(byte / float(1024 * 1024))

def BtoGB(byte):
    return int(byte / float(1024 * 1024 * 1024))

def sToHMS(self, sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return h, m, s

def unescapeHTML(s):
    """
    @param s a string (of type unicode)
    """
    assert type(s) == type(u'')

    result = re.sub(ur'(?u)&(.+?);', htmlentity_transform, s)
    return result

def clean_html(html):
    """Clean an HTML snippet into a readable string"""
    # Newline vs <br />
    html = html.replace('\n', ' ')
    html = re.sub('\s*<\s*br\s*/?\s*>\s*', '\n', html)
    # Strip html tags
    html = re.sub('<.*?>', '', html)
    # Replace html entities
    html = unescapeHTML(html)
    return html

def encodeFilename(s):
    """
    @param s The name of the file (of type unicode)
    """

    assert type(s) == type(u'')

    if sys.platform == 'win32' and sys.getwindowsversion()[0] >= 5:
        # Pass u'' directly to use Unicode APIs on Windows 2000 and up
        # (Detecting Windows NT 4 is tricky because 'major >= 4' would
        # match Windows 9x series as well. Besides, NT 4 is obsolete.)
        return s
    else:
        return s.encode(sys.getfilesystemencoding(), 'ignore')

def sanitize_filename(value):
    from Plugins.Extensions.archivCZSK import removeDiac
    tmp = removeDiac(value)
    tmp = unicode(re.sub(r'(?u)[^\w\s.-]', '', tmp).strip().lower())
    return re.sub(r'(?u)[-\s]+', '-', tmp)
    #import unicodedata
    #value = toUnicode(value)
    #value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    #value = unicode(re.sub(r'(?u)[^\w\s.-]', '', value).strip().lower())
    #value = re.sub(r'(?u)[-\s]+', '-', value)
    #return value

def htmlentity_transform(matchobj):
    """Transforms an HTML entity to a Unicode character.

    This function receives a match object and is intended to be used with
    the re.sub() function.
    """
    entity = matchobj.group(1)

    # Known non-numeric HTML entity
    if entity in htmlentitydefs.name2codepoint:
        return unichr(htmlentitydefs.name2codepoint[entity])

    # Unicode character
    mobj = re.match(ur'(?u)#(x?\d+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith(u'x'):
            base = 16
            numstr = u'0%s' % numstr
        else:
            base = 10
        return unichr(long(numstr, base))

    # Unknown entity in name, return its literal representation
    return (u'&%s;' % entity)



class Language(object):
    language_map = {
                'en':'English',
                'sk':'Slovak',
                'cz':'Czech',
                }
    @staticmethod
    def get_language_id(language_name):
        revert_langs = dict(map(lambda item: (item[1], item[0]), Language.language_map.items()))
        if language_name in revert_langs:
            return revert_langs[language_name]
        else:
            return None

    @staticmethod
    def get_language_name(language_id):
        if language_id in Language.language_map:
            return Language.language_map[language_id]
        else:
            return None

def get_streams_from_manifest(url, manifest_data):
    manifest_data_str = toString(manifest_data)
    for m in re.finditer(r'^#EXT-X-STREAM-INF:(?P<info>.+)\n(?P<chunk>.+)', manifest_data_str, re.MULTILINE):
        stream_info = {}
        for info in re.split(r''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', m.group('info')):
            key, val = info.split('=', 1)
            stream_info[key.lower()] = val
        stream_info['url'] = url[:url.rfind('/') + 1] + m.group('chunk')
        yield stream_info

def url_get_data_async(url, callback=None, data=None, headers=None, timeout=60):
    def handle_failure(failure):
        failure.printTraceback()
        callback(None)
    def handle_result(data):
        callback(data)

    assert data is None, "sorry data is currently not supported"
    if headers is not None:
        headers = {k:[v] for k,v in headers.items()}
    agent = BrowserLikeRedirectAgent(Agent(reactor, connectTimeout=timeout))
    d = agent.request('GET', url, Headers(headers))
    d.addCallback(readBody)
    if callback is not None:
        d.addCallbacks(handle_result, handle_failure)
    return d

def url_get_data(url, data=None, headers=None, timeout=30):
    if headers is None:
        headers = {}
    request = urllib2.Request(url, data, headers)
    try:
        response = urllib2.urlopen(request, timeout=timeout)
        return response.read()
    except (urllib2.URLError, urllib2.HTTPError, socket.timeout):
        traceback.print_exc()

def url_get_response_headers(url, headers=None, timeout=5, max_redirects=3):
    purl = urlparse(url)
    if  headers is None:
        headers = {}
    if purl.scheme.startswith("http"):
        if purl.path:
            if purl.query:
                path = purl.path + "?" + purl.query
            else:
                path = purl.path
        else:
            path = "/"
        conn = None
        try:
            if purl.scheme == "http":
                conn = httplib.HTTPConnection(purl.netloc, timeout=timeout)
            if purl.scheme == "https":
                conn = httplib.HTTPSConnection(purl.netloc, timeout=timeout)
            if conn is not None:
                conn.request("HEAD", path, headers=headers)
                response = conn.getresponse()
                if response.status == 200:
                    return dict(response.getheaders())
                if (response.status in range(300, 309) and max_redirects):
                    max_redirects -= 1
                    return url_get_response_headers(
                            response.getheader("Location"), headers,
                            timeout, max_redirects)
        except Exception:
            traceback.print_exc()
        finally:
            conn and conn.close()

def url_get_content_length(url, headers=None, timeout=5, max_redirects=5):
    resp_headers = url_get_response_headers(url, headers, timeout, max_redirects)
    if resp_headers:
        length = resp_headers.get('content-length')
        if length: return int(length)

def url_get_file_info(url, headers=None, timeout=3):
    purl = urlparse(url)
    filename = purl.path.split('/')[-1]
    length = None
    if url.startswith('rtmp'):
        url_split = url.split()
        if len(url_split) > 1:
            for i in url_split:
                if i.find('playpath=') == 0:
                    filename = urlparse(i[len('playpath='):]).path.split('/')[-1]

    elif url.startswith('http') and purl.path.endswith('.m3u8'):
            filename = purl.path.split('/')[-2]

    elif url.startswith('http'):
        if headers is None:
            headers = {}
        resp_headers = url_get_response_headers(url, headers, timeout=timeout)
        if resp_headers:
            content_length = resp_headers.get('content-length')
            if content_length is not None:
                length = int(content_length)
            content_disposition = resp_headers.get('content-disposition')
            if content_disposition is not None:
                filename_match = re.search(r'''filename=(?:\*=UTF-8'')?['"]?([^'"]+)''', content_disposition)
                if filename_match is not None:
                    filename = toString(urllib.unquote_plus(filename_match.group(1)))
            content_type = resp_headers.get('content-type')
            if content_type is not None:
                extension = mimetypes.guess_extension(content_type, False)
                if extension is not None:
                    if not os.path.splitext(filename)[1]:
                        filename += extension
    return {'filename':sanitize_filename(filename), 'length':length}

def download_to_file_async(url, dest, callback=None, data=None, headers=None, timeout=60):
    def got_data(data):
        if data:
            try:
                with open(dest, "wb") as f:
                    f.write(data)
            except Exception as e:
                log.logError("download_to_file_async: %s"% toString(e))
                callback(None, None)
            else:
                callback(url, dest)
        else:
            callback(None, None)
    log.logDebug("download_to_file_async: %s -> %s"% (toString(url), toString(dest)))
    return url_get_data_async(url, got_data, data, headers, timeout)

def get_free_space(location):
    try:
        s = os.statvfs(location)
        return s.f_bavail * s.f_bsize
    except Exception:
        traceback.print_exc()

def check_program(program):

    def is_file(fpath):
        return os.path.isfile(fpath)

    def is_exe(fpath):
        return os.access(fpath, os.X_OK)

    def set_executable(program):
        mode = os.stat(program).st_mode
        os.chmod(program, mode | stat.S_IXUSR)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_file(program):
            if not is_exe(program):
                set_executable(program)
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_file(exe_file):
                if not is_exe(exe_file):
                    set_executable(exe_file)
                return exe_file
    return None


def convert_png_to_8bit(png_path, pngquant_path='pngquant'):
    pngquant = check_program(pngquant_path)
    if pngquant is None:
        print 'cannot decode png %s, pngquant not found' % png_path
        return png_path

    png_path_8bit = os.path.splitext(png_path)[0] + '-fs8.png'
    cmd = '%s --force 32 %s' % (pngquant, png_path)
    cmd = cmd.split()

    if os.path.isfile(png_path_8bit):
        os.remove(png_path_8bit)

    eConsoleAppContainer().execute(*cmd)
    if os.path.isfile(png_path_8bit):
        print 'png %s was successfully converted' % os.path.basename(png_path)
        return png_path_8bit
    return png_path



class CustomImporter:
    """Used to avoid name collisions in sys.modules"""
    def __init__(self, name, lib_path='', log=None):
        self.name = name
        self.__path = [lib_path]
        if log:
            self.log = log
        else:
            self.log = lambda *args:None
        self.__modules = {}
        self.__filehandle = None

    def add_path(self, path):
        if not path in self.__path:
            self.__path.append(path)

    def add_module(self, mod_name, mod):
        self.__modules[mod_name] = mod

    def release_modules(self):
        """ lose reference to evaluated modules,
              so python GC can collect them and free memory"""
        self.__modules.clear()

    def __repr__(self):
        return "[%s-importer] " % self.name

    def find_module(self, fullname, path):
        self.log("%s import '%s'" , self, fullname)

        if fullname in sys.modules:
            self.log("%s found '%s' in sys.modules\nUsing python standard importer" , self, fullname)
            return None

        if fullname in self.__modules:
            self.log("%s found '%s' in modules" , self, fullname)
            return self
        try:
            path = self.__path
            self.log("%s finding modul '%s' in %s" , self, fullname, path)
            self.__filehandle, self.filename, self.description = imp.find_module(fullname, path)
            self.log("%s found modul '%s' <filename:%s description:%s>" , self, fullname, self.filename, self.description)
        except ImportError:
            self.log("%s cannot found modul %s" , self, fullname)
            if self.__filehandle:
                self.__filehandle.close()
                self.__filehandle = None
            return None
        if self.__filehandle is None:
            self.log("%s cannot import package '%s', try to append it to sys.path" , self, fullname)
            raise ImportError
        self.log("%s trying to load module '%s'" , self, fullname)
        return self

    def load_module(self, fullname):
        if fullname in self.__modules:
            return self.__modules[fullname]
        try:
            code = self.__filehandle.read()
        except Exception:
            return
        finally:
            if self.__filehandle:
                self.__filehandle.close()
                self.__filehandle = None
        self.log("%s importing modul '%s'" , self, fullname)
        bytecode = os.path.splitext(self.filename)[1] in ['.pyo', '.pyc']
        mod = self.__modules[fullname] = imp.new_module(fullname)
        mod.__file__ = self.filename
        mod.__loader__ = self
        del self.filename
        del self.description
        try:
            if bytecode:
                # magic = code[:4]
                # assert magic == imp.get_magic()
                code_bytes = code[8:]
                code = marshal.loads(code_bytes)
            exec code in mod.__dict__
            self.log("%s imported modul '%s'", self, fullname)
        except Exception:
            log.logError("Load module failed %s '%s'.\n%s"%(self,fullname,traceback.format_exc()))
            del self.__modules[fullname]
            raise
        return mod

