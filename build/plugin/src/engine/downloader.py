'''
Created on 8.5.2012

@author: marko
'''
import os, time, mimetypes
from urlparse import urlsplit
from twisted.python import failure
from twisted.web import client
from twisted.internet import reactor
import urlparse, urllib2
from tools import util
from exceptions.download import NotSupportedProtocolError

try:
    from enigma import eConsoleAppContainer
    from Plugins.Extensions.archivCZSK import _
except ImportError:
    pass


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
    return os.path.basename(urlsplit(url)[2])

def getFileInfo(url, localFileName=None, headers={}):    
    resetUrllib2Opener()
    
    localName = url2name(url)
    req = urllib2.Request(url, headers=headers)
    resp = urllib2.urlopen(req)
    exttype = resp.info().get('Content-Type')
    length = resp.info().get('Content-Length')
    if resp.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        localName = resp.info()['Content-Disposition'].split('filename=')[1]
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
        
    localName = localName.replace(' ', '_')
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
        if not download.url in [down.url for down in self.download_lst]:
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
            if not isinstance(download, HTTPDownloadTwisted):
                download.pp.appClosed.append(download.remove)
            else:
                download.defer.addCallback(download.remove)
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

        if url[0:4] == 'rtmp':
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
                
            # always download rtmp stream as live,
            # this way we should slowly but correctly download every video
            live = True

            d = RTMPDownloadE2(url=url, name=name, destDir=destination, live=live, quiet=quiet)
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
            # only for EPLAYER3(ffmpeg demux)
            # When playing and downloading avi/mkv container then use HTTPTwistedDownload instead of wget
            # Reason is that when we use wget download, downloading file is progressively increasing its size, and ffmpeg isnt updating size of file accordingly
            # so when video gets to place what ffmpeg read in start, playing prematurely stops because of EOF. 
            # When we use HTTPDownloadTwisted, we firstly create the file of length of the downloading file, and then download to it, so ffmpeg reads
            # full length filesize.
            # Its not nice fix but its working ...
            if mode == "":
                if os.path.splitext(filename)[1] in ('.avi', '.mkv') and playDownload:
                    d = HTTPDownloadTwisted(name=filename, url=url, filename=filename, destDir=destination, quiet=quiet, headers=headers, fullLengthFile=True)
                else:
                    d = HTTPDownloadE2(name=filename, url=url, filename=filename, destDir=destination, quiet=quiet, headers=headers)
                    
            elif mode == "wget":
                d = HTTPDownloadE2(name=filename, url=url, filename=filename, destDir=destination, quiet=quiet, headers=headers)
            else:
                d = HTTPDownloadTwisted(name=filename, url=url, filename=filename, destDir=destination, quiet=quiet, headers=headers)
                
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
    def __init__(self, name, url, destDir, filename=None, live=False, quiet=False):
        if not filename:
            filename = name + '.flv'
            filename = filename.replace(' ', '_')
            filename = filename.replace('/', '')
            filename = filename.replace('(', '')
            filename = filename.replace(')', '')
        Download.__init__(self, name, url, destDir, filename, quiet)
        self.pp = eConsoleAppContainer()
        #self.pp.dataAvail.append(self.__startCB)
        self.pp.appClosed.append(self.__finishCB)
        self.pp.stderrAvail.append(self.__outputCB)
        self.live = live

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
        print cmd
        if self.quiet:
            cmd += ' -q '
        if self.live:
            cmd += ' -v'
        print '[RTMPDownloadE2] starting downloading', self.url, 'to', self.local
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
        print cmd
        if self.quiet:
            cmd += ' -q'
        print '[HTTPDownloadE2] starting downloading', self.url
        self.__startCB()
        self.pp.execute(cmd)

    def cancel(self):
        if self.pp.running():
            self.killed = True
            self.pp.sendCtrlC()
        
class HTTPProgressDownloader(client.HTTPDownloader):
    
    def __init__(self, url, fileOrName, updateCurrentLength, writeToEmptyFile=False, outputCB=None, headers={}, *args, **kwargs):
        self.writeToEmptyFile = writeToEmptyFile
        self.outputCB = outputCB
        self.updateCurrentLength = updateCurrentLength
        self.totalLength = 0
        self.currentLength = 0
        client.HTTPDownloader.__init__(self, url, fileOrName, headers=headers, agent=USER_AGENT, *args, **kwargs)
        

    def gotHeaders(self, headers):
        print 'gotHeaders'
        if self.status == '200': # page data is on the way
            if headers.has_key('content-length'):
                self.totalLength = int(headers['content-length'][0])
                print self.totalLength
            else:
                self.totalLength = 0
            self.currentLength = 0.0
            print ''
        return client.HTTPDownloader.gotHeaders(self, headers)
    
    def pageStart(self, partialContent):
        """Called on page download start.

        @param partialContent: tells us if the download is partial download we requested.
        """
        if partialContent and not self.requestedPartial:
            raise ValueError, "we shouldn't get partial content response if we didn't want it!"
        if self.waiting:
            try:
                if not self.file:
                    self.file = self.openFile(partialContent)
            except IOError:
                #raise
                self.deferred.errback(failure.Failure())

    def pagePart(self, data):
        if self.status == '200':
            self.currentLength += len(data)
            self.updateCurrentLength(self.currentLength)
            if self.totalLength:
                percent = "%i%%" % ((self.currentLength / self.totalLength) * 100)
                outputstr = "%.3f/%.3f MB %s percent" % (float(self.currentLength / (1024 * 1024)), float(self.totalLength / (1024 * 1024)), percent)
                self.outputCB(outputstr)
            else:
                percent = '%dK' % (self.currentLength / 1000)
                outputstr = "%d/%i MB %d percent" % (self.currentLength, percent)
                self.outputCB(outputstr)
        return client.HTTPDownloader.pagePart(self, data)
    
    def createEmptyFile(self, size):
        f = open(self.fileName, "wb")
        f.seek((size) - 1)
        f.write("\0")
        f.close()

    
    def openFile(self, partialContent):
        #download avi files to existing file with full length of file which will be downloaded
        if self.writeToEmptyFile:
            self.createEmptyFile(self.totalLength)
            file = open(self.fileName, 'rb+')
            return file
        else:
            return client.HTTPDownloader.openFile(self, partialContent)



class HTTPDownloadTwisted(Download):
    def __init__(self, name, url, destDir, filename=None, quiet=False, headers={}, fullLengthFile=False):
        if filename is None:
            path = urlparse.urlparse(url).path
            filename = os.path.basename(path)
        Download.__init__(self, name, url, destDir, filename, quiet)
        self.connector = None
        self.currentLength = 0
        self.headers = headers
        self.fullLengthFile = fullLengthFile

    def __startCB(self):
        self.running = True
        if self.startCB is not None:
            self.startCB(self)

    def __finishCB(self, retval):
        self.running = False
        self.finish_time = time.time()
        if not self.killed:
            self.downloaded = True
        else:
            self.downloaded = False
        if self.finishCB is not None:
            self.finishCB(self)

    def __outputCB(self, data):
        if self.showOutput and self.outputCB is not None:
            self.outputCB(data)
    
    def updateCurrentLength(self, currentLength):
        self.currentLength = currentLength
        
    def getCurrentLength(self):
        return self.currentLength
    
    def start(self):
        self.__startCB()
        self.defer = self.downloadWithProgress(self.url, self.local, writeToEmptyFile=self.fullLengthFile, outputCB=self.__outputCB, headers=self.headers).addCallback(self.__finishCB).addErrback(self.downloadError)

    def cancel(self):
        if self.running and self.connector is not None:
            self.downloaded = False
            self.running = False
            self.killed = True
            self.connector.disconnect()
    
    def downloadWithProgress(self, url, file, contextFactory=None, *args, **kwargs):
        scheme, host, port, path = client._parse(url)
        factory = HTTPProgressDownloader(url, file, self.updateCurrentLength, *args, **kwargs)
        if scheme == 'https':
            from twisted.internet import ssl
            if contextFactory is None:
                contextFactory = ssl.ClientContextFactory()
            self.connector = reactor.connectSSL(host, port, factory, contextFactory)
        else:
            self.connector = reactor.connectTCP(host, port, factory)
        return factory.deferred
    
    def downloadError(self, failure):
        self.downloaded = False
        self.running = False
        print "Error:", failure.getErrorMessage()
        self.__finishCB(None)
        
        
        
class GStreamerDownload():
    def __init__(self, path, preBufferPercent=0, preBufferSeconds=0):
        self.path = path
        self.preBufferPercent = 0
        self.preBufferSeconds = 0
