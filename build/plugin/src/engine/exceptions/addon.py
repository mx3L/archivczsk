from exceptions import Exception

class AddonException(Exception):
    pass

class AddonThreadException(AddonException):
    pass
        
class AddonInfoError(AddonException):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AddonError(AddonException):
    def __init__(self, value):
        self.value = value 
    def __str__(self):
        return repr(self.value) 		

class AddonWarningError(AddonException):
    def __init__(self, value):
        self.value = value 
    def __str__(self):
        return repr(self.value)
    
class AddonSettingError(AddonException):
    def __init__(self, value,setting,session):
        self.value = value 
    def __str__(self):
        return repr(self.value)