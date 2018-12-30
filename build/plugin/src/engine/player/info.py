'''
Created on 22.12.2012

@author: marko
'''
import os
from Plugins.Extensions.archivCZSK import log

GSTREAMER_PATH = '/usr/lib/gstreamer-0.10'
GSTREAMER10_PATH = '/usr/lib/gstreamer-1.0'
LIB_PATH = '/usr/lib'
EPLAYER2_PATH = '/lib/libeplayer2.so'
EPLAYER3_PATH = '/lib/libeplayer3.so'


class VideoPlayerInfo(object):
    def __init__(self):
        self.type = 'gstreamer'
        self.version = 0
        if os.path.isdir(GSTREAMER10_PATH):
            print 'found gstreamer'
            log.logDebug('Found gstreamer 1.0')
            self.type = 'gstreamer'
            self.version = '1.0'
        elif os.path.isdir(GSTREAMER_PATH):
            print 'found gstreamer'
            log.logDebug('Found gstreamer 0.10')
            self.type = 'gstreamer'
            self.version = '0.10'
        elif os.path.isfile(EPLAYER3_PATH):
            log.logDebug('Found eplayer3')
            print 'found eplayer3'
            self.type = 'eplayer3'
        elif os.path.isfile(EPLAYER2_PATH):
            log.logDebug('Found eplayer2')
            print 'found eplayer2'
            self.type = 'eplayer2'
            

    def getName(self):
        if self.type == 'gstreamer':
            if self.version == '1.0':
                return 'Gstreamer 1.0'
            return 'GStreamer 0.10'
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
            rtmplib2 = os.path.join(GSTREAMER10_PATH, 'libgstrtmp.so')
            
            librtmp = os.path.join(LIB_PATH, 'librtmp.so.0')
            librtmp2 = os.path.join(LIB_PATH, 'librtmp.so.1')
            
            # flv is file container used in rtmp
            flvlib = os.path.join(GSTREAMER_PATH, 'libgstflv.so')
            flvlib2 = os.path.join(GSTREAMER10_PATH, 'libgstflv.so')
            if (os.path.isfile(rtmplib) or os.path.isfile(rtmplib2)) and (os.path.isfile(librtmp) or os.path.isfile(librtmp2)) and (os.path.isfile(flvlib) or os.path.isfile(flvlib2)):
                log.logDebug("RTMP supported for 100%...")
                return True

            msg = ""
            if not (os.path.isfile(rtmplib) or os.path.isfile(rtmplib2)):
                msg+= "\n'libgstrtmp.so' is missing..."
            if not (os.path.isfile(librtmp) or os.path.isfile(librtmp2)):
                msg+= "\n'%s' or '%s' is missing..."%(librtmp, librtmp2)
            if not (os.path.isfile(flvlib) or os.path.isfile(flvlib2)):
                msg+= "\n'libgstflv.so' is missing..."

            log.logDebug("RTMP not supported (some file missing '/usr/lib/gstreamer-*')...%s"%msg)
            return False
            
        elif self.type == 'eplayer2':
            # dont know any eplayer2 which supports rtmp
            # also not used anymore so setting to false
            log.logDebug("RTMP may be supported (eplayer2)...")
            return False
        elif self.type == 'eplayer3':
            rtmplib = '/usr/lib/librtmp.so'
            log.logDebug("RTMP may be supported (eplayer3)...")
            if os.path.isfile(rtmplib):
                log.logDebug("RTMP may be supported (eplayer3)...\n%s"%rtmplib)
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
            mmslib2 = os.path.join(GSTREAMER10_PATH, 'libgstmms.so')
            if os.path.isfile(mmslib) or os.path.isfile(mmslib2):
                log.logDebug("MMS supported")
                return True
            log.logDebug("MMS not supported, missing file '/usr/lib/gstreamer-*/libgstmms.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("MMS may be supported (eplayer3)")
            return None
                
        elif self.type == 'eplayer2':
            log.logDebug("MMS may be supported (eplayer2)")
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
            rtsplib2 = os.path.join(GSTREAMER10_PATH, 'libgstrtsp.so')
            rtplib2 = os.path.join(GSTREAMER10_PATH, 'libgstrtp.so')
            rtpmanager2 = os.path.join(GSTREAMER10_PATH, 'libgstrtpmanager.so')
            if ((os.path.isfile(rtsplib) and os.path.isfile(rtplib) and os.path.isfile(rtpmanager)) or
                (os.path.isfile(rtsplib2) and os.path.isfile(rtplib2) and os.path.isfile(rtpmanager2))):
                log.logDebug("RTSP supported for 100%...")
                return True

            msg = ""
            if not (os.path.isfile(rtsplib) or os.path.isfile(rtsplib2)):
                msg+= "\n'libgstrtsp.so' is missing..."
            if not (os.path.isfile(rtplib) or os.path.isfile(rtplib2)):
                msg+= "\n'libgstrtp.so' is missing..."
            if not (os.path.isfile(rtpmanager2) or os.path.isfile(rtpmanager)):
                msg+= "\n'libgstrtpmanager.so' is missing..."

            log.logDebug("RTSP may be supported (some file missing '/usr/lib/gstreamer-*')...%s"%msg)
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("RTSP may be supported (eplayer3)")
            return None
                
        elif self.type == 'eplayer2':
            log.logDebug("RTSP may be supported (eplayer2)")
            return None
        
    def isHTTPSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            httplib = os.path.join(GSTREAMER_PATH, 'libgstsouphttpsrc.so')
            httplib2 = os.path.join(GSTREAMER10_PATH, 'libgstsouphttpsrc.so')
            if not os.path.isfile(httplib2):
                httplib2 = os.path.join(GSTREAMER10_PATH, 'libgstsoup.so')
            if os.path.isfile(httplib) or os.path.isfile(httplib2):
                log.logDebug("HTTP supported")
                return True
            log.logDebug("HTTP not supported, missing file '/usr/lib/gstreamer-*/libgstsouphttpsrc.so' or '/usr/lib/gstreamer-*/libgstsoup.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("HTTP may be supported (eplayer3)")
            return True
                
        elif self.type == 'eplayer2':
            log.logDebug("HTTP may be supported (eplayer2)")
            return True
        
    def isHLSSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            fragmentedlib = os.path.join(GSTREAMER_PATH, 'libgstfragmented.so')
            fragmentedlib2 = os.path.join(GSTREAMER10_PATH, 'libgstfragmented.so')
            if not os.path.isfile(fragmentedlib2):
                fragmentedlib2 = os.path.join(GSTREAMER10_PATH, 'libgsthls.so')
            if os.path.isfile(fragmentedlib) or os.path.isfile(fragmentedlib2):
                log.logDebug("HLS supported")
                return True
            log.logDebug("HLS not supported, missing file '/usr/lib/gstreamer-*/libgstfragmented.so' or '/usr/lib/gstreamer-*/libgsthls.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("HLS may be supported (eplayer3)")
            return None
                
        elif self.type == 'eplayer2':
            log.logDebug("HLS may be supported (eplayer2)")
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
            asflib2 = os.path.join(GSTREAMER10_PATH, 'libgstasf.so')
            if os.path.isfile(asflib) or os.path.isfile(asflib2):
                log.logDebug("ASF supported")
                return True
            log.logDebug("ASF not supported, missing file '/usr/lib/gstreamer-*/libgstasf.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("ASF may be supported (eplayer3)")
            return None
                
        elif self.type == 'eplayer2':
            log.logDebug("ASF may be supported (eplayer2)")
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
            flvlib2 = os.path.join(GSTREAMER10_PATH, 'libgstflv.so')
            if os.path.isfile(flvlib) or os.path.isfile(flvlib2):
                log.logDebug("FLV supported")
                return True
            log.logDebug("FLV not supported, missing file '/usr/lib/gstreamer-*/libgstflv.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("FLV  supported (eplayer3)")
            return True
                
        elif self.type == 'eplayer2':
            log.logDebug("FLV may be supported (eplayer2)")
            return None
        
    def isMKVSupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            mkvlib = os.path.join(GSTREAMER_PATH, 'libgstmatroska.so')
            mkvlib2 = os.path.join(GSTREAMER10_PATH, 'libgstmatroska.so')
            if os.path.isfile(mkvlib) or os.path.isfile(mkvlib2):
                log.logDebug("MKV supported")
                return True
            log.logDebug("MKV not supported, missing file '/usr/lib/gstreamer-*/libgstmatroska.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("MKV supported (eplayer3)")
            return True
                
        elif self.type == 'eplayer2':
            log.logDebug("MKV supported (eplayer2)")
            return True
        
    def isAVISupported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            avilib = os.path.join(GSTREAMER_PATH, 'libgstavi.so')
            avilib2 = os.path.join(GSTREAMER10_PATH, 'libgstavi.so')
            if os.path.isfile(avilib) or os.path.isfile(avilib2):
                log.logDebug("AVI supported")
                return True
            log.logDebug("AVI not supported, missing file '/usr/lib/gstreamer-*/libgstavi.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("AVI supported (eplayer3)")
            return True
                
        elif self.type == 'eplayer2':
            log.logDebug("AVI supported (eplayer2)")
            return True
        
    def isMP4Supported(self):
        """
        @return: True if its 100% supported
        @return: None may be supported
        @return: False not supported
        """
        if self.type == 'gstreamer':
            isomp4lib = os.path.join(GSTREAMER_PATH, 'libgstisomp4.so')
            isomp4lib2 = os.path.join(GSTREAMER10_PATH, 'libgstisomp4.so')
            if os.path.isfile(isomp4lib) or os.path.isfile(isomp4lib2):
                log.logDebug("MP4 supported")
                return True
            log.logDebug("MP4 not supported, missing file '/usr/lib/gstreamer-*/libgstisomp4.so'")
            return False
            
        elif self.type == 'eplayer3':
            log.logDebug("MP4 supported (eplayer3)")
            return True
                
        elif self.type == 'eplayer2':
            log.logDebug("MP4 supported (eplayer2)")
            return True
        
    def is3GPPSupported(self):
        if self.type == 'gstreamer':
            return self.isMP4Supported()
        
        elif self.type == 'eplayer3':
            log.logDebug("3GPP may be supported (eplayer3)")
            return None
                
        elif self.type == 'eplayer2':
            log.logDebug("3GPP may be supported (eplayer2)")
            return None
        
    

#########################################################################
        
videoPlayerInfo = VideoPlayerInfo()
            
            
