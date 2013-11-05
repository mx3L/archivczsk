'''
Created on 16.5.2013

@author: marko

'''
from twisted.internet import defer
from enigma import eTimer

bufferServicemp4 = True

def setBufferSize(iStreamed, size):
    """
    set buffer size in (B)
    """
    if iStreamed:
        iStreamed.setBufferSize(size)
    

def getBufferInfo(iStreamed):
    """
    @return:{ percentage: buffer percent,
              avg_in_rate: average input rate (B),
              avg_out_rate: average output rate (B),
              space: buffer space (s),
              size: buffer size (B),
              downloading: bool,
              download_path: download path,
              download_percent: download percent (B)
            }
    """
                   
    
    bufferDict = {'percentage':0,
                  'space':0,
                  'size':0,
                  'avg_in_rate':0,
                  'avg_out_rate':0,
                  # servicemp4 download stuff
                  'downloading':False,
                  'download_path':'',
                  'downloa_percent':0
                  }
    
    if iStreamed:
        bufferInfo = iStreamed.getBufferCharge()
        bufferDict['percentage'] = bufferInfo[0]
        bufferDict['avg_in_rate'] = bufferInfo[1]
        bufferDict['avg_out_rate'] = bufferInfo[2]
        bufferDict['space'] = bufferInfo[3]
        bufferDict['size'] = bufferInfo[4]
        if bufferServicemp4:
            try:
                # servicemp4 download
                bufferDict['downloading'] = bufferInfo[5]
                bufferDict['download_path'] = bufferInfo[6]
                bufferDict['download_percent'] = bufferInfo[7]
            except IndexError:
                global bufferServicemp4
                bufferServicemp4 = False
    return bufferDict



class Video(object):
    def __init__(self, session, serviceTryLimit=25):
        self.session = session
        self.service = None
        self.__serviceTimer = eTimer()
        self.__serviceTimerTryDelay = 500 #ms
        self.__serviceTryTime = 0
        self.__serviceTryLimit = serviceTryLimit * 1000
        self.__deferred = None
        
    def restartService(self):
        self.service = None
        self.__deferred = defer.Deferred()
        

    def startService(self):
        """
        Get real start of service
        @return: deferred, fires success when gets service or errback when dont get service in time limit
        """
        
        def fireDeferred():
            self.__serviceTimer.callback.remove(setService)
            self.__deferred.callback(None)
            self.__deferred = None
            
        def fireDeferredErr():
            self.__serviceTimer.callback.remove(setService)
            self.__deferred.errback(defer.failure.Failure(Exception("")))
            self.__deferred = None
            
        def getService():
            if self.__deferred is None:
                return
            
            if self.service is None:
                if self.__serviceTryTime < self.__serviceTryLimit:
                    self.__serviceTimer.start(self.__serviceTimerTryDelay, True)
                else:
                    fireDeferredErr()
            else:
                fireDeferred()
                
        def setService():
            self.__serviceTryTime += self.__serviceTimerTryDelay
            self.service = self.session.nav.getCurrentService()
            getService()
        
        self.__deferred = defer.Deferred()
        self.__serviceTimer.callback.append(setService)
        getService()
        return self.__deferred    
        
    

    def __getSeekable(self):
        if self.service is None:
            return None
        return self.service.seek()
    
    def getCurrentPosition(self):
        seek = self.__getSeekable()
        if seek is None:
            return None
        r = seek.getPlayPosition()
        if r[0]:
            return None
        return long(r[1])

    def getCurrentLength(self):
        seek = self.__getSeekable()
        if seek is None:
            return None
        r = seek.getLength()
        if r[0]:
            return None
        return long(r[1])
    
    def getName(self):
        if self.service is None:
            return ''
        return self.session.nav.getCurrentlyPlayingServiceReference().getName()
