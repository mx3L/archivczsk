import os
import time
import mimetypes
import urlparse
import urllib
import urllib2

from enigma import eConsoleAppContainer

from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK.compat import eConnectCallback
from Plugins.Extensions.archivCZSK.engine.exceptions.download import NotSupportedProtocolError
from Plugins.Extensions.archivCZSK.engine.player.info import videoPlayerInfo
from Plugins.Extensions.archivCZSK.engine.tools.util import toString, url_get_file_info, sanitize_filename

GST_LAUNCH = None
if videoPlayerInfo.type == 'gstreamer' and videoPlayerInfo.version == '1.0':
    GST_LAUNCH = 'gst-launch-1.0'
elif videoPlayerInfo.type =='gstreamer' and videoPlayerInfo.version == '0.10':
    GST_LAUNCH = 'gst-launch-0.10'

RTMP_DUMP_PATH      = '/usr/bin/rtmpdump'
WGET_PATH           = 'wget'
USER_AGENT          = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'

VIDEO_EXTENSIONS    = ('.3gp', '3g2', '.asf', '.avi', '.flv', '.mp4', '.mkv', '.mpeg', '.mov' '.mpg', '.wmv', '.divx', '.vob', '.iso', '.ts')
AUDIO_EXTENSIONS    = ('.mp2', '.mp3', '.wma', '.ogg', '.dts', '.flac', '.wave')
PLAYLIST_EXTENSIONS = ('.m3u', '.m3u8')
ARCHIVE_EXTENSIONS  = ('.rar', '.zip', '.7zip')
MEDIA_EXTENSIONS    = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS + ARCHIVE_EXTENSIONS + PLAYLIST_EXTENSIONS

def isHLSUrl(url):
    return url.startswith('http') and urlparse.urlparse(url).path.endswith('.m3u8')

def getFilenameAndLength(url=None, headers=None, filename=None):
    length = None
    if url is not None:
        info_dict = url_get_file_info(url, headers, timeout=3)
        if filename is None:
            filename = info_dict['filename']
        length = info_dict['length']
    if filename is not None:
        filename = sanitize_filename(filename)
        filename_tmp, extension = os.path.splitext(filename)
        if extension not in VIDEO_EXTENSIONS + AUDIO_EXTENSIONS:
            filename = filename_tmp + ".mp4"
    return filename, length

class DownloadManager(object):
    instance = None

    @staticmethod
    def getInstance():
        return DownloadManager.instance

    def __init__(self, download_lst):
        DownloadManager.instance = self
        self.download_lst = download_lst
        self.count = len(download_lst)
        self.on_change = []

    def addDownload(self, download, overrideCB=None):
        log.info("DownloadManager.addDownload(%s,%s)"%(download, str(overrideCB)))
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
            download.onFinishCB.append(download.remove)
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

    def createDownload(self, name, url, destination, filename=None, live=False, startCB=None, finishCB=None, stream=None, quiet=False, playDownload=False, headers=None, mode=""):
        log.info("Downloader.createDownload(url=%s,mode=%s"%(toString(url), mode))
        d = None
        filename, length = getFilenameAndLength(url, headers, filename)
        log.info("Downloader.createDownload() filename=%s, length=%s", toString(filename), length)
        if (((url[0:4] == 'rtmp' and mode in ('auto', 'gstreamer')) or
              (url[0:4] == 'http' and mode  in ('auto', 'gstreamer') and isHLSUrl(url)) or
              (url[0:4] == 'http' and mode in ('auto', 'gstreamer') and playDownload) or
              (url[0:4] == 'http' and mode in ('gstreamer',))) and GST_LAUNCH is not None):
            d = GstDownload(url = url, name = name, destDir = destination, filename=filename)
        elif url[0:4]  == 'rtmp' and mode in ('auto', 'rtmpdump'):
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
            d = RTMPDownloadE2(url=url, name=name, destDir=destination, 
                    filename=filename, live=live, quiet=quiet, realtime=realtime)
        elif url[0:4] == 'http':
            if isHLSUrl(url):
                raise NotSupportedProtocolError('HLS')
            d = HTTPDownloadE2(name=name, url=url, filename=filename, 
                    destDir=destination, quiet=quiet, headers=headers)
        else:
            protocol = url.split('://')[0].upper()
            log.error('Downloader.createDownload() - not supported protocol %s' % toString(protocol))
            raise NotSupportedProtocolError(protocol)

        if startCB is not None:
            d.onStartCB.append(startCB)
        if finishCB is not None:
            d.onFinishCB.append(finishCB)
        d.status = DownloadStatus(d)
        d.length = length or 0
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
        self.url = url
        self.name = name
        self.filename = toString(filename)
        self.destDir = destDir
        self.local = os.path.join(destDir, filename).encode('ascii', 'ignore')
        self.length = 0
        self.quiet = quiet
        self.start_time = time.time()
        self.finish_time = None
        self.running = False
        self.paused = False
        self.downloaded = False
        self.outputCB = self.__runOutputCB
        self.onOutputCB = []
        self.startCB = self.__runStartCB
        self.onStartCB = []
        self.finishCB = self.__runFinishCB
        self.onFinishCB = []
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
        if not self.running and os.path.isfile(self.local):
            os.remove(self.local)

    def getLength(self):
        pass

    def getCurrentLength(self):
        currentLength = 0
        if os.path.isfile(self.local):
            currentLength = long(os.path.getsize(self.local))
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

class DownloadProcessMixin(object):
    def __init__(self):
        self.killed = False
        self.showOutput = False

        self.pp = eConsoleAppContainer()
        self.appClosed_conn = eConnectCallback(self.pp.appClosed, self._finishCB)
        self.stderrAvail_conn = eConnectCallback(self.pp.stderrAvail, self._outputCB)

    def start(self):
        if not os.path.exists(self.destDir):
            os.makedirs(self.destDir)
        self._startCB()
        cmd = toString(self._buildCmd())
        log.info("Download.start \"%s\"" % cmd)
        self.pp.execute(cmd)

    def kill(self):
        if self.pp.running():
            self.pp.kill()

    def cancel(self):
        if self.pp.running():
            self.killed = True
            self.downloaded = False
            self.pp.sendCtrlC()

    def _startCB(self):
        self.running = True
        if self.startCB is not None:
            self.startCB(self)

    def _outputCB(self, data):
        if self.showOutput and self.outputCB is not None:
            self.outputCB(data)

    def _finishCB(self, retval):
        log.info("Download._finishCB(%d)"%(retval))
        self.running = False
        self.finish_time = time.time()
        if retval == 0 and not self.killed:
            self.downloaded = True
        else:
            self.downloaded = False
        if self.finishCB is not None:
            self.finishCB(self)


class RTMPDownloadE2(DownloadProcessMixin, Download):
    def __init__(self, name, url, destDir, filename, live=False, quiet=False, realtime=True):
        self.live = live
        self.realtime = realtime
        Download.__init__(self, name, url, destDir, filename, quiet)
        DownloadProcessMixin.__init__(self)

    def _buildCmd(self):
        cmd = RTMP_DUMP_PATH + ' -r ' + self.url + ' -o ' + '"' + self.local + '"'
        if self.quiet:
            cmd += ' -q '
        if self.live:
            cmd += ' -v'
        if self.realtime:
            cmd += ' -R'
        return cmd

    def _finishCB(self, retval):
        log.info("Download._finishCB(%d)"%(retval))
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


class HTTPDownloadE2(DownloadProcessMixin, Download):
    def __init__(self, name, url, destDir, filename, quiet=False, headers=None):
        Download.__init__(self, name, url, destDir, filename, quiet)
        DownloadProcessMixin.__init__(self)
        self.headers = headers
        if headers:
            self.headers = '--header ' + ' --header '.join([("'" + key + ': ' + value + "'") for key, value in headers.iteritems()])
        else: self.headers = ""

    def _buildCmd(self):
        cmd = WGET_PATH + ' "' + self.url + '"' + ' -O ' + '"' + self.local + '"' ' -U ' + '"' + USER_AGENT + '" ' + self.headers
        cmd = cmd.encode('utf-8')
        if self.quiet:
            cmd += ' -q'
        return cmd


class GstDownload(DownloadProcessMixin, Download):
    def __init__(self, name, url, destDir, filename, quiet=False, headers={}):
        Download.__init__(self, name, url, destDir, filename, quiet)
        DownloadProcessMixin.__init__(self)

    def _buildCmd(self):
        if self.url.startswith('rtmp'):
            cmd = "%s rtmpsrc location='%s' ! filesink location='%s'"%(GST_LAUNCH, self.url, self.local)
        elif self.url.startswith('http') and isHLSUrl(self.url):
            cmd = "%s souphttpsrc location='%s' ! hlsdemux ! filesink location='%s'"%(GST_LAUNCH, self.url, self.local)
        elif self.url.startswith('http'):
            cmd = "%s souphttpsrc location='%s' ! filesink location='%s'"%(GST_LAUNCH, self.url, self.local)
        return cmd

