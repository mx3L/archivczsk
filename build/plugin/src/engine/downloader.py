'''
Created on 8.5.2012

@author: marko
'''
import os, time, mimetypes
import urlparse, urllib2, urllib
from player.info import videoPlayerInfo
from exceptions.download import NotSupportedProtocolError

try:
    from enigma import eConsoleAppContainer
    from Plugins.Extensions.archivCZSK import _
except ImportError:
    pass

GST_LAUNCH = None
if videoPlayerInfo.type == 'gstreamer' and videoPlayerInfo.version == '1.0':
    GST_LAUNCH = 'gst-launch-1.0'
elif videoPlayerInfo.type =='gstreamer' and videoPlayerInfo.version == '0.10':
    GST_LAUNCH = 'gst-launch-0.10'


RTMP_DUMP_PATH = '/usr/bin/rtmpdump'
WGET_PATH = 'wget'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'

VIDEO_EXTENSIONS = ('.3gp', '3g2', '.asf', '.avi', '.flv', '.mp4', '.mkv', '.mpeg', '.mov' '.mpg', '.wmv', '.divx', '.vob', '.iso', '.ts')
AUDIO_EXTENSIONS = ('.mp2', '.mp3', '.wma', '.ogg', '.dts', '.flac', '.wave')
PLAYLIST_EXTENSIONS = ('.m3u', '.m3u8')
ARCHIVE_EXTENSIONS = ('.rar', '.zip', '.7zip')
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS + ARCHIVE_EXTENSIONS + PLAYLIST_EXTENSIONS

def toUTF8(text):
    if isinstance(text, unicode):
        text = text.encode('utf-8', 'ignore')
    return text

def resetUrllib2Opener():
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)

def url2name(url):
    fname = os.path.basename(urlparse.urlparse(url).path.split('/')[-1])
    if url.startswith('rtmp'):
        url_split = url.split()
        if len(url_split) > 1:
            for i in url_split:
                if i.find('playpath=') == 0:
                    fname = urlparse.urlparse(i[len('playpath='):]).path.split('/')[-1]
                    break
    elif url.startswith('http') and urlparse.urlparse(url).path.endswith('.m3u8'):
        fname = urlparse.urlparse(url).path.split('/')[-2]
    return sanitizeFilename(fname)

def sanitizeFilename(s):
    """Sanitizes a string so it could be used as part of a filename."""
    def replace_insane(char):
        if char == '?' or ord(char) < 32 or ord(char) == 127:
            return ''
        elif char == '"':
            return '\''
        elif char == ':':
            return ' -'
        elif char in '\\/|*<>':
            return '-'
        return char

    result = u''.join(map(replace_insane, s))
    while '--' in result:
        result = result.replace('--', '-')
    return result.strip('-')

def getFileInfo(url, localFileName=None, headers={}):
    resetUrllib2Opener()

    localName = url2name(url)
    req = urllib2.Request(url, headers=headers)
    resp = urllib2.urlopen(req)
    exttype = resp.info().get('Content-Type')
    length = resp.info().get('Content-Length')
    if resp.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        # http://stackoverflow.com/questions/93551/how-to-encode-the-filename-parameter-of-content-disposition-header-in-http
        try:
            localName = resp.info()['Content-Disposition'].split('filename=')[1]
        except:
            localName = urllib.unquote(resp.info()['Content-Disposition'].split("filename*=UTF-8''")[1])
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif resp.url != url:
        # if we were redirected, the real file name we take from the final URL
        localName = url2name(resp.url)

    # we can force to save the file as specified name
    if localFileName:
        # if our filename doesnt have extensions, then add identified extension from localName
        if os.path.splitext(localFileName)[1] == "":
            ext = os.path.splitext(localName)[1]
            if ext in VIDEO_EXTENSIONS:
                localFileName = os.path.splitext(localFileName)[0] + ext

        localName = localFileName
    resp.close()

    if os.path.splitext(localName)[1] == "":
        ext = mimetypes.guess_extension(exttype)
        if ext is not None:
            localName = localName + ext
        else:
            url_ext = '.' + url.split('.')[-1]
            localName = localName + url_ext

    # we didnt get valid extensions so we add one
    if os.path.splitext(localName)[1] not in MEDIA_EXTENSIONS:
        localName = os.path.splitext(localName)[0] + '.mp4'

    localName = sanitizeFilename(localName)
    #localName = util.removeDiacritics(localName)
    return localName, length


class DownloadManager(object):
    instance = None

    @staticmethod
    def getInstance():
        return DownloadManager.instance

    def __init__(self, download_lst):
        print 'initializing downloadManager'
        DownloadManager.instance = self
        self.download_lst = download_lst
        self.count = len(download_lst)
        self.on_change = []

    def addDownload(self, download, overrideCB=None):
        #check if we didn't download from this url already
        c1 = download.url in [d.url for d in self.download_lst]
        # check if filename already exists
        c2 = os.path.isfile(download.local)
        if not c1 and not c2:
            self.download_lst.append(download)
            download.start()
        else:
            if overrideCB is not None:
                overrideCB(download)

    def cancelDownload(self, download):
        if download.running:
            download.cancel()

    def removeDownload(self, download):
        if download.running:
            download.pp.appClosed.append(download.remove)
            download.cancel()
            self.download_lst.remove(download)
        else:
            download.remove()
            self.download_lst.remove(download)

    def findDownloadByIT(self, it):
        for download in self.download_lst:
            if it.url == download.local:
                return download
        return None

    def createDownload(self, name, url, destination, filename=None, live=False, startCB=None, finishCB=None, quiet=False, stream=None, playDownload=False, headers={}, mode=""):
        d = None
        url = toUTF8(url)
        if not os.path.exists(destination):
            os.makedirs(destination)

        if (((url[0:4] == 'rtmp' and mode in ('auto', 'gstreamer')) or
              (url[0:4] == 'http' and mode  in ('auto', 'gstreamer') and urlparse.urlparse(url).path.endswith('.m3u8')) or
              (url[0:4] == 'http' and mode in ('auto', 'gstreamer') and playDownload) or
              (url[0:4] == 'http' and mode in ('gstreamer',))) and GST_LAUNCH):
            d = GstDownload(url = url, name = name, destDir = destination)
            d.onStartCB.append(startCB)
            d.onFinishCB.append(finishCB)
            d.status = DownloadStatus(d)

        elif url[0:4]  == 'rtmp' and mode in ('auto', 'rtmpdump'):
            if stream is not None:
                url = stream.getRtmpgwUrl()
            else:
                urlList = url.split()
                rtmp_url = []
                for url in urlList[1:]:
                    rtmp = url.split('=', 1)
                    rtmp_url.append(' --' + rtmp[0])
                    rtmp_url.append("'%s'" % rtmp[1])
                url = "'%s'" % urlList[0] + ' '.join(rtmp_url)

            if not live:
                realtime = True
            else:
                realtime = False

            d = RTMPDownloadE2(url=url, name=name, destDir=destination, live=live, quiet=quiet, realtime=realtime)
            d.onStartCB.append(startCB)
            d.onFinishCB.append(finishCB)
            d.status = DownloadStatus(d)

        elif url[0:4] == 'http':
            try:
                filename, length = getFileInfo(url, filename, headers)
            except (urllib2.HTTPError, urllib2.URLError) as e:
                print "[Downloader] cannot create download %s - %s error" % (toUTF8(filename), str(e))
                raise
            # for now we cannot download hls streams
            if filename.endswith('m3u8'):
                raise NotSupportedProtocolError('HLS')
            d = HTTPDownloadE2(name=filename, url=url, filename=filename, destDir=destination, quiet=quiet, headers=headers)
            d.onStartCB.append(startCB)
            d.onFinishCB.append(finishCB)
            d.length = long(length)
            d.status = DownloadStatus(d)

        else:
            print '[Downloader] cannot create download %s - not supported protocol' % toUTF8(filename)
            protocol = filename.split('://')[0].upper()
            raise NotSupportedProtocolError(protocol)

        d.playMode = playDownload
        return d

class DownloadStatus():
    def __init__(self, download):
        self.download = download
        self.totalLength = download.length
        self.currentLength = 0
        self.speed = 0
        self.percent = -1
        self.eta = -1
        self.ignoreFirstUpdate = True


    def update(self, refreshTime):

        totalLength = self.totalLength
        tempLength = self.currentLength
        speedB = 0

        if os.path.isfile(self.download.local):
            currentLength = self.download.getCurrentLength()

            # download just started
            if tempLength == 0:
                if not self.ignoreFirstUpdate:
                    speedB = long(float(currentLength) / float(refreshTime))

            elif tempLength > 0:
                speedB = long(float(currentLength - tempLength) / float(refreshTime))

            self.speed = speedB
            if totalLength > 0:
                if speedB > 0:
                    self.eta = int(float(totalLength - currentLength) / float(speedB))
                self.percent = float(totalLength - currentLength) / float(totalLength) * 100
            self.currentLength = currentLength

            #print '[DownloadStatus] update: speed %s' % self.speed

        else:
            print "[Downloader] status: cannot update, file doesnt exist"

    def dumpInfo(self):
        return "Name=%s  downloaded: [%d MB/ %d MB] remaining time %dh:%dm:%ds"\
            % (self.download.name, self.currentLength, self.totalLength, self.etaHMS[0], self.etaHMS[1], self.etaHMS[2])



class Download(object):
    def __init__(self, name, url, destDir, filename, quiet):
        self.start_time = time.time()
        self.finish_time = None
        self.url = url
        self.name = name
        self.filename = filename.encode('ascii', 'ignore')
        self.destDir = destDir.encode('ascii', 'ignore')
        self.local = os.path.join(destDir, filename).encode('ascii', 'ignore')
        self.length = 0
        self.quiet = quiet
        self.playMode = False
        self.running = False
        self.killed = False
        self.paused = False
        self.downloaded = False
        self.showOutput = False
        self.outputCB = self.__runOutputCB
        self.onOutputCB = []
        self.startCB = self.__runStartCB
        self.onStartCB = []
        self.finishCB = self.__runFinishCB
        self.onFinishCB = []
        self.pp = None
        self.state = 'unknown'
        self.textState = _('unknown')

    def __runFinishCB(self, download):
        self.__updateState()
        for f in self.onFinishCB:
            f(self)

    def __runStartCB(self, download):
        self.__updateState()
        for f in self.onStartCB:
            f(self)

    def __runOutputCB(self, data):
        for f in self.onOutputCB:
            f(data)

    def __updateState(self):
        if not self.running and self.downloaded:
            self.state = 'success_finished'
            self.textState = _('succesfully finished')
        elif not self.running and not self.downloaded:
            self.state = 'error_finished'
            self.textState = _('not succesfully finished')
        elif self.running and not self.downloaded:
            self.state = 'downloading'
            self.textState = _('downloading')
        else:
            self.state = 'unknown'
            self.textState = _("unknown")


    def remove(self, callback=None):
        """removes download"""
        if not self.running and os.path.isfile(self.local):
            print 'removing', self.filename
            os.remove(self.local)

    def getLength(self):
        pass

    def getCurrentLength(self):
        currentLength = 0
        if os.path.isfile(self.local):
            currentLength = long(os.path.getsize(self.local))
            #print "Name=%s  downloaded: [%lu B/ %lu B]" % (self.name, currentLength, self.length)
        return currentLength


    def start(self):
        """Starts downloading file"""
        pass

    def stop(self):
        """Stops downloading file"""
        pass

    def resume(self):
        """Resumes downloading file"""
        pass

    def cancel(self):
        """Kills downloading process"""
        pass


class RTMPDownloadE2(Download):
    def __init__(self, name, url, destDir, filename=None, live=False, quiet=False, realtime=True):
        if not filename:
            filename = name + '.flv'
            filename = sanitizeFilename(filename)
        Download.__init__(self, name, url, destDir, filename, quiet)
        self.pp = eConsoleAppContainer()
        #self.pp.dataAvail.append(self.__startCB)
        self.pp.appClosed.append(self.__finishCB)
        self.pp.stderrAvail.append(self.__outputCB)
        self.live = live
        self.realtime = realtime

    def __startCB(self):
        self.running = True
        if self.startCB is not None:
            self.startCB(self)

    def __finishCB(self, retval):
        print 'e2rtmpdownload finished with', str(retval)
        self.running = False
        self.finish_time = time.time()
        if retval == 1 and not self.killed:
            if os.path.getsize(self.local) > (0.95 * self.length):
                self.downloaded = True
            else:
                self.downloaded = False
        elif retval == 0 and not self.killed:
            self.downloaded = True
        else:
            self.downloaded = False
        if self.finishCB is not None:
            self.finishCB(self)


    def __outputCB(self, data):
        if self.showOutput and self.outputCB is not None:
            self.outputCB(data)

    def start(self):
        cmd = RTMP_DUMP_PATH + ' -r ' + self.url + ' -o ' + '"' + self.local + '"'
        cmd = cmd.encode('utf-8')
        if self.quiet:
            cmd += ' -q '
        if self.live:
            cmd += ' -v'
        if self.realtime:
            cmd += ' -R'
        print '[cmd]',cmd
        self.__startCB()
        self.pp.execute(cmd)

    def cancel(self):
        if self.pp.running():
            self.killed = True
            self.downloaded = False
            self.pp.sendCtrlC()


class HTTPDownloadE2(Download):
    """Downloads file with wget"""
    def __init__(self, name, url, destDir, filename=None, quiet=False, headers={}):
        if filename is None:
            path = urlparse.urlparse(url).path
            filename = os.path.basename(path)
        Download.__init__(self, name, url, destDir, filename, quiet)
        self.pp = eConsoleAppContainer()
        #self.pp.dataAvail.append(self.__startCB)
        self.pp.stderrAvail.append(self.__outputCB)
        self.pp.appClosed.append(self.__finishCB)
        if len(headers) > 0:
            self.headers = '--header ' + ' --header '.join([("'" + key + ': ' + value + "'") for key, value in headers.iteritems()])
        else: self.headers = ""

    def __startCB(self):
        self.running = True
        if self.startCB is not None:
            self.startCB(self)

    def __finishCB(self, retval):
        print 'e2httpdownload finished with', str(retval)
        self.running = False
        self.finish_time = time.time()
        if retval == 0 and not self.killed:
            self.downloaded = True
        else:
            self.downloaded = False
        if self.finishCB is not None:
            self.finishCB(self)

    def __outputCB(self, data):
        if self.showOutput and self.outputCB is not None:
            self.outputCB(data)

    def kill(self):
        if self.pp.running():
            self.pp.kill()

    def start(self):
        cmd = WGET_PATH + ' "' + self.url + '"' + ' -O ' + '"' + self.local + '"' ' -U ' + '"' + USER_AGENT + '" ' + self.headers
        cmd = cmd.encode('utf-8')
        if self.quiet:
            cmd += ' -q'
        print '[cmd]',cmd
        self.__startCB()
        self.pp.execute(cmd)

    def cancel(self):
        if self.pp.running():
            self.killed = True
            self.pp.sendCtrlC()


class GstDownload(Download):
    """Downloads file with gstreamer"""
    def __init__(self, name, url, destDir, filename=None, quiet=False, headers={}):
        if filename is None:
            filename = url2name(url)
        if not filename.endswith(VIDEO_EXTENSIONS):
            filename = os.path.splitext(filename)[0] +'.mp4'
        Download.__init__(self, name, url, destDir, filename, quiet)
        self.pp = eConsoleAppContainer()
        #self.pp.dataAvail.append(self.__startCB)
        self.pp.stderrAvail.append(self.__outputCB)
        self.pp.appClosed.append(self.__finishCB)

    def __startCB(self):
        self.running = True
        if self.startCB is not None:
            self.startCB(self)

    def __finishCB(self, retval):
        print 'gstdownload finished with', str(retval)
        self.running = False
        self.finish_time = time.time()
        if retval == 0 and not self.killed:
            self.downloaded = True
        else:
            self.downloaded = False
        if self.finishCB is not None:
            self.finishCB(self)

    def __outputCB(self, data):
        if self.showOutput and self.outputCB is not None:
            self.outputCB(data)

    def kill(self):
        if self.pp.running():
            self.pp.kill()

    def start(self):
        if self.url.startswith('rtmp'):
            cmd = "%s rtmpsrc location='%s' ! filesink location='%s'"%(GST_LAUNCH, self.url, self.local)
        elif self.url.startswith('http') and urlparse.urlparse(self.url).path.endswith('.m3u8'):
            cmd = "%s souphttpsrc location='%s' ! hlsdemux ! filesink location='%s'"%(GST_LAUNCH, self.url, self.local)
        elif self.url.startswith('http'):
            cmd = "%s souphttpsrc location='%s' ! filesink location='%s'"%(GST_LAUNCH, self.url, self.local)
        cmd = cmd.encode('utf-8')
        print '[cmd]',cmd
        self.__startCB()
        self.pp.execute(cmd)

    def cancel(self):
        if self.pp.running():
            self.killed = True
            self.pp.sendCtrlC()

class GStreamerDownload():
    def __init__(self, path, preBufferPercent=0, preBufferSeconds=0):
        self.path = path
        self.preBufferPercent = 0
        self.preBufferSeconds = 0
