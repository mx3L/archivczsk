class PlayException(Exception):
    pass
        
class UrlNotExistError(PlayException):
    pass

class RTMPGWMissingError(PlayException):
    pass
