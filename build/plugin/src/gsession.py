'''
Created on 11.3.2013

@author: marko
To set/get global session
'''

class GlobalSession(object):
    session = None
        
    @staticmethod
    def setSession(session):
        GlobalSession.session = session

    @staticmethod
    def getSession():
        return GlobalSession.session
