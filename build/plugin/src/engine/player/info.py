'''
Created on 22.12.2012

@author: marko
'''
import os

GSTREAMER_PATH = '/usr/lib/gstreamer-0.10'
LIB_PATH = '/usr/lib'
EPLAYER2_PATH = '/lib/libeplayer2.so'
EPLAYER3_PATH = '/lib/libeplayer3.so'


class VideoPlayerInfo(object):
    def __init__(self):
        self.type = 'gstreamer'
        self.version = 0
        if os.path.isdir(GSTREAMER_PATH):
            print 'found gstreamer'
            self.type = 'gstreamer'
        elif os.path.isfile(EPLAYER3_PATH):
            print 'found eplayer3'
            self.type = 'eplayer3'
        elif os.path.isfile(EPLAYER2_PATH):
            print 'found eplayer2'
            self.type = 'eplayer2'
            
            
    def getName(self):
        if self.type == 'gstreamer':
            return 'GStreamer'
        if self.type == 'eplayer3':
            return 'EPlayer3'
        if self.type == 'eplayer2':
            return 'Eplayer2'
    
######################### Supported protocols ##################################
 
    def isRTMPSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        
        if self.type == 'gstreamer':
            rtmplib = os.path.join(GSTREAMER_PATH, 'libgstrtmp.so')
            
            librtmp = os.path.join(LIB_PATH, 'librtmp.so.0')
            librtmp2 = os.path.join(LIB_PATH, 'librtmp.so.1')
            
            # flv is file container used in rtmp
            flvlib = os.path.join(GSTREAMER_PATH, 'libgstflv.so')
            if os.path.isfile(rtmplib) and (os.path.isfile(librtmp) or os.path.isfile(librtmp2)) and os.path.isfile(flvlib):
                    return True
            return False
            
        elif self.type == 'eplayer2':
            # dont know any eplayer2 which supports rtmp
            # also not used anymore so setting to false
            return False
        elif self.type == 'eplayer3':
            rtmplib = '/usr/lib/librtmp.so'
            if os.path.isfile(rtmplib):
                # some older e2 images not support rtmp
                # even if there is this library(missing support in servicemp3)
                return None
            
    def isMMSSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            mmslib = os.path.join(GSTREAMER_PATH, 'libgstmms.so')
            if os.path.isfile(mmslib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return None
                
        elif self.type == 'eplayer2':
            return None
        
    def isRTSPSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            rtsplib = os.path.join(GSTREAMER_PATH, 'libgstrtsp.so')
            rtplib = os.path.join(GSTREAMER_PATH, 'libgstrtp.so')
            rtpmanager = os.path.join(GSTREAMER_PATH, 'libgstrtpmanager.so')
            if os.path.isfile(rtsplib) and os.path.isfile(rtplib) and os.path.isfile(rtpmanager):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return None
                
        elif self.type == 'eplayer2':
            return None
        
    def isHTTPSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            httplib = os.path.join(GSTREAMER_PATH, 'libgstsouphttpsrc.so')
            if os.path.isfile(httplib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return True
                
        elif self.type == 'eplayer2':
            return True
        
    def isHLSSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            fragmentedlib = os.path.join(GSTREAMER_PATH, 'libgstfragmented.so')
            if os.path.isfile(fragmentedlib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return None
                
        elif self.type == 'eplayer2':
            return None
        
##########################################################################

########################### Supported Video Formats ######################

    def isASFSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            asflib = os.path.join(GSTREAMER_PATH, 'libgstasf.so')
            if os.path.isfile(asflib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return None
                
        elif self.type == 'eplayer2':
            return None
        
    def isWMVSupported(self):
        return self.isASFSupported()
        
    def isFLVSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            flvlib = os.path.join(GSTREAMER_PATH, 'libgstflv.so')
            if os.path.isfile(flvlib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return True
                
        elif self.type == 'eplayer2':
            return None
        
    def isMKVSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            mkvlib = os.path.join(GSTREAMER_PATH, 'libgstmatroska.so')
            if os.path.isfile(mkvlib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return True
                
        elif self.type == 'eplayer2':
            return True
        
    def isAVISupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            avilib = os.path.join(GSTREAMER_PATH, 'libgstavi.so')
            if os.path.isfile(avilib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return True
                
        elif self.type == 'eplayer2':
            return True
        
    def isMP4Supported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            isomp4lib = os.path.join(GSTREAMER_PATH, 'libgstisomp4.so')
            if os.path.isfile(isomp4lib):
                return True
            return False
            
        elif self.type == 'eplayer3':
            return True
                
        elif self.type == 'eplayer2':
            return True
        
    def is3GPPSupported(self):
        if self.type == 'gstreamer':
            return self.isMP4Supported()
        
        elif self.type == 'eplayer3':
            return None
                
        elif self.type == 'eplayer2':
            return None
        
    

#########################################################################
        
videoPlayerInfo = VideoPlayerInfo()
            
            
