'''
Created on 10.3.2013

@author: marko
'''
class DownloadException(Exception):
    pass

class NotSupportedProtocolError(DownloadException):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)