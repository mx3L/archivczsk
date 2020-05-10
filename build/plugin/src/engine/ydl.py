from twisted.internet.defer import Deferred

from Plugins.Extensions.archivCZSK import settings
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.engine.tools.e2util import PythonProcess

class YoutubeDl(PythonProcess):
    def __init__(self):
        PythonProcess.__init__(self, settings.YDL_SCRIPT_PATH)

        self.version = ""
        self.initialized = False
        self.available = None
        self.resolving = False
        self.lastResolvingUrl = ""

    def init(self):
        if self.initialized:
            d = Deferred()
            d.callback(True)
            return d

        callbacks = {}
        callbacks['messageCB'] = self.gotResponse
        callbacks['finishedCB'] = self.processExited
        self.start(callbacks)

        self.d = Deferred()
        return self.d

    def resolveUrl(self, url):
        log.info("YoutubeDL::resolveUrl '%s'" % (url,))

        if not self.initialized:
            log.info("YoutubeDL::resolveUrl not initialized...")
            d = Deferred()
            d.callback(None)
            return d
        if self.resolving:
            log.info("YoutubeDL::resolveUrl already resolving url...")
            d = Deferred()
            d.callback(None)
            return d

        self.resolving = True
        self.lastResolvingUrl = url
        self.write({'url': url})

        self.d = Deferred()
        return self.d

    def getVideoLinks(self, url):
        def gotExtractedData(data):
            print "gotExtractedData"
            h264_formats = []
            if data:
                formats = data.get('formats')
                for f in formats:
                    #print "format id", f['format_id'], f['vcodec'], f['acodec'] 
                    if int(f['format_id']) in (18, 22):
                        h264_formats.append(f)
                return sorted(h264_formats, key=lambda f: int(f['format_id']))

        d = self.resolveUrl(url)
        d.addCallback(gotExtractedData)
        return d

    def gotResponse(self, response):
        if response['type'] == 'info':
            if response['status']:
                self.initialized = True
                self.available = True
                log.info("YoutubeDL::gotResponse: initialized")
                self.d.callback(True)
            else:
                log.info("YoutubeDL::gotResponse: failed to initialize: %s" % (response['exception'], ))
                self.available = False
                self.d.callback(False)
        elif response['type'] == 'request':
            self.resolving = False
            self.lastResolvingUrl = None
            if response['status']:
                log.info("YoutubeDL::getResponse: url resolved")
                self.d.callback(response['result'])
            else:
                self.d.errback(response['exception'])

    def getVersion(self):
        return self.version

    def isInitialized(self):
        return self.initialized

    def isAvailable(self):
        return self.available

    def processExited(self, retval):
        log.info("YoutubeDL::processExited: process exited %d" %(retval))

ydl = YoutubeDl()
