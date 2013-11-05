from Components.Converter.ServicePosition import ServicePosition
from Components.Element import cached

class ServicePositionAdj(ServicePosition):
    """
    Like ServicePosition converter but also provides ability to
    dynamically alter service length/position -
    i.e. to fix incorrect position in some RTMP streams
    """
    
    basePts = 0
    baseLengthPts = 0
    
    @staticmethod
    def setBasePts(basePts):
        ServicePositionAdj.basePts = basePts
    
    @staticmethod  
    def setBaseLength(baseLengthPts):
        ServicePositionAdj.baseLengthPts = baseLengthPts
        
    @cached
    def getPosition(self):
        seek = self.getSeek()
        if seek is None:
            return None
        pos = seek.getPlayPosition()
        if pos[0]:
            return 0
        return pos[1] + ServicePositionAdj.basePts
    
    @cached
    def getLength(self):
        seek = self.getSeek()
        if seek is None:
            return None
        length = seek.getLength()
        if length[0]:
            return 0
        return length[1] + ServicePositionAdj.baseLengthPts
    
    position = property(getPosition)
    length = property(getLength)
    
    def destroy(self):
        super(ServicePositionAdj, self).destroy()
        ServicePositionAdj.basePts = 0
        ServicePositionAdj.baseLengthPts = 0
        
    
    
