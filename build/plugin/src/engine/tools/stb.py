'''
Source from Project-Valerie
http://code.google.com/p/project-valerie/source/browse/trunk/ValerieMediaCenter/__common__.py
'''
import sys
from os.path import isfile


gBoxType = None

def getBoxtype():
        global gBoxType

        if gBoxType is not None:
                return gBoxType
        else:
                _setBoxtype()
                return gBoxType

def _setBoxtype():
        global gBoxType
        box = 'Unknown'
        fPath1 = "/proc/stb/info/model"
        fPath2 = "/hdd/model"
        fPath = isfile(fPath1) and fPath1 or isfile(fPath2) and fPath2 or ''
        try:
            with open(fPath,'r') as f:
                box = f.readline().strip()
        except IOError:
            box = "PC"
        
        manu = 'Unknown'
        model = box
        arch = "sh4"
        version = ""
        
        if box == "PC":
            manu = "PC"
            model = "PC"
            arch = "sh4"
    
        elif box == "ufs910":
                manu = "Kathrein"
                model = "UFS-910"
                arch = "sh4"
        elif box == "ufs912":
                manu = "Kathrein"
                model = "UFS-912"
                arch = "sh4"
        elif box == "ufs922":
                manu = "Kathrein"
                model = "UFS-922"
                arch = "sh4"
        elif box == "tf7700hdpvr":
                manu = "Topfield"
                model = "HDPVR-7700"
                arch = "sh4"
        elif box == "dm800":
                manu = "Dreambox"
                model = "800"
                arch = "mipsel"
        elif box == "dm800se":
                manu = "Dreambox"
                model = "800se"
                arch = "mipsel"
        elif box == "dm8000":
                manu = "Dreambox"
                model = "8000"
                arch = "mipsel"
        elif box == "dm500hd":
                manu = "Dreambox"
                model = "500hd"
                arch = "mipsel"
        elif box == "dm7025":
                manu = "Dreambox"
                model = "7025"
                arch = "mipsel"  
        elif box == "dm7020hd":
                manu = "Dreambox"
                model = "7020hd"
                arch = "mipsel"
        elif box == "elite":
                manu = "Azbox"
                model = "Elite"
                arch = "mipsel"
        elif box == "premium":
                manu = "Azbox"
                model = "Premium"
                arch = "mipsel"
        elif box == "premium+":
                manu = "Azbox"
                model = "Premium+"
                arch = "mipsel"
        elif box == "cuberevo-mini":
                manu = "Cubarevo"
                model = "Mini"
                arch = "sh4"
        elif box == "hdbox":
                manu = "Fortis"
                model = "HdBox"
                arch = "sh4"
       
        if arch == "mipsel":
                version = getBoxArch()
        else:
                version = "duckbox"
       
        gBoxType = (manu, model, arch, version)
        
def getBoxArch():
        ARCH = "unknown"
       
        if (sys.version_info < (2, 6, 8) and sys.version_info > (2, 6, 6)):
                ARCH = "oe16"
                       
        if (sys.version_info < (2, 7, 4) and sys.version_info > (2, 7, 0)):
                ARCH = "oe20"

        return ARCH