'''
Created on Feb 19, 2015

@author: marko

'''
import os
import re

from Components.FileList import FileEntryComponent
from Components.Harddisk import harddiskmanager
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox as OrigMessageBox
from Tools.Directories import fileExists

from enigma import eServiceReference, eListboxPythonMultiContent, eServiceCenter, gFont

from . import _

# taken from IPTVPlayer
class eConnectCallbackObj:
    def __init__(self, obj=None, connectHandler=None):
        self.connectHandler = connectHandler
        self.obj = obj
    
    def __del__(self):
        if 'connect' not in dir(self.obj):
            if 'get' in dir(self.obj):
                self.obj.get().remove(self.connectHandler)
            else:
                self.obj.remove(self.connectHandler)
        else:
            del self.connectHandler
        self.connectHandler = None
        self.obj = None

# taken from IPTVPlayer
def eConnectCallback(obj, callbackFun):
    if 'connect' in dir(obj):
        return eConnectCallbackObj(obj, obj.connect(callbackFun))
    else:
        if 'get' in dir(obj):
            obj.get().append(callbackFun)
        else:
            obj.append(callbackFun)
        return eConnectCallbackObj(obj, callbackFun)
    return eConnectCallbackObj()

# this function is not the same accross different images
def LanguageEntryComponent(file, name, index):
    from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
    from Tools.LoadPixmap import LoadPixmap
    png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, 'countries/' + index + '.png'))
    if png == None:
        png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, 'countries/' + file + '.png'))
        if png == None:
            png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, 'countries/missing.png'))
    res = (index, name, png)
    return res


# there is no simple MessageBox in DMM images
SimpleMessageBox = False
try:
    OrigMessageBox("", "", simple=True)
    SimpleMessageBox = True
except TypeError:
    pass

class MessageBox(OrigMessageBox):
    def __init__(self, *args, **kwargs):
        if kwargs.get('simple') is not None and not SimpleMessageBox:
            del kwargs['simple']
        OrigMessageBox.__init__(self, *args, **kwargs)

# FileList is sometimes changing -> subclasses stop to work
class FileList(MenuList):
    def __init__(self, directory, showDirectories=True, showFiles=True, showMountpoints=True, matchingPattern=None, useServiceRef=False, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=False, additionalExtensions=None):
        MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
        self.additional_extensions = additionalExtensions
        self.mountpoints = []
        self.current_directory = None
        self.current_mountpoint = None
        self.useServiceRef = useServiceRef
        self.showDirectories = showDirectories
        self.showMountpoints = showMountpoints
        self.showFiles = showFiles
        if isTop:
            self.topDirectory = directory
        else:
            self.topDirectory = "/"
        # example: matching .nfi and .ts files: "^.*\.(nfi|ts)"
        if matchingPattern:
            self.matchingPattern = re.compile(matchingPattern)
        else:
            self.matchingPattern = None
        self.inhibitDirs = inhibitDirs or []
        self.inhibitMounts = inhibitMounts or []

        self.refreshMountpoints()
        self.changeDir(directory)
        self.l.setFont(0, gFont("Regular", 18))
        self.l.setItemHeight(23)
        self.serviceHandler = eServiceCenter.getInstance()

    def refreshMountpoints(self):
        self.mountpoints = [os.path.join(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
        self.mountpoints.sort(reverse=True)

    def getMountpoint(self, file):
        file = os.path.join(os.path.realpath(file), "")
        for m in self.mountpoints:
            if file.startswith(m):
                return m
        return False

    def getMountpointLink(self, file):
        if os.path.realpath(file) == file:
            return self.getMountpoint(file)
        else:
            if file[-1] == "/":
                file = file[:-1]
            mp = self.getMountpoint(file)
            last = file
            file = os.path.dirname(file)
            while last != "/" and mp == self.getMountpoint(file):
                last = file
                file = os.path.dirname(file)
            return os.path.join(last, "")

    def getSelection(self):
        if self.l.getCurrentSelection() is None:
            return None
        return self.l.getCurrentSelection()[0]

    def getCurrentEvent(self):
        l = self.l.getCurrentSelection()
        if not l or l[0][1] == True:
            return None
        else:
            return self.serviceHandler.info(l[0][0]).getEvent(l[0][0])

    def getFileList(self):
        return self.list

    def inParentDirs(self, dir, parents):
        dir = os.path.realpath(dir)
        for p in parents:
            if dir.startswith(p):
                return True
        return False

    def changeDir(self, directory, select=None):
        self.list = []

        # if we are just entering from the list of mount points:
        if self.current_directory is None:
            if directory and self.showMountpoints:
                self.current_mountpoint = self.getMountpointLink(directory)
            else:
                self.current_mountpoint = None
        self.current_directory = directory
        directories = []
        files = []

        if directory is None and self.showMountpoints:  # present available mountpoints
            for p in harddiskmanager.getMountedPartitions():
                path = os.path.join(p.mountpoint, "")
                if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
                    self.list.append(FileEntryComponent(name=p.description, absolute=path, isDir=True))
            files = [ ]
            directories = [ ]
        elif directory is None:
            files = [ ]
            directories = [ ]
        elif self.useServiceRef:
            # we should not use the 'eServiceReference(string)' constructor, because it doesn't allow ':' in the directoryname
            root = eServiceReference(2, 0, directory)
            if self.additional_extensions:
                root.setName(self.additional_extensions)
            serviceHandler = eServiceCenter.getInstance()
            list = serviceHandler.list(root)

            while 1:
                s = list.getNext()
                if not s.valid():
                    del list
                    break
                if s.flags & s.mustDescent:
                    directories.append(s.getPath())
                else:
                    files.append(s)
            directories.sort()
            files.sort()
        else:
            if fileExists(directory):
                try:
                    files = os.listdir(directory)
                except:
                    files = []
                files.sort()
                tmpfiles = files[:]
                for x in tmpfiles:
                    if os.path.isdir(directory + x):
                        directories.append(directory + x + "/")
                        files.remove(x)

        if self.showDirectories:
            if directory:
                if self.showMountpoints and directory == self.current_mountpoint:
                    self.list.append(FileEntryComponent(name="<" + _("List of storage devices") + ">", absolute=None, isDir=True))
                elif (directory != self.topDirectory) and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
                    self.list.append(FileEntryComponent(name="<" + _("Parent directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))
            for x in directories:
                if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
                    name = x.split('/')[-2]
                    self.list.append(FileEntryComponent(name=name, absolute=x, isDir=True))

        if self.showFiles:
            for x in files:
                if self.useServiceRef:
                    path = x.getPath()
                    name = path.split('/')[-1]
                else:
                    path = directory + x
                    name = x

                if (self.matchingPattern is None) or self.matchingPattern.search(path):
                    self.list.append(FileEntryComponent(name=name, absolute=x , isDir=False))

        if self.showMountpoints and len(self.list) == 0:
            self.list.append(FileEntryComponent(name=_("nothing connected"), absolute=None, isDir=False))

        self.l.setList(self.list)

        if select is not None:
            i = 0
            self.moveToIndex(0)
            for x in self.list:
                p = x[0][0]

                if isinstance(p, eServiceReference):
                    p = p.getPath()

                if p == select:
                    self.moveToIndex(i)
                i += 1

    def getCurrentDirectory(self):
        return self.current_directory

    def canDescent(self):
        if self.getSelection() is None:
            return False
        return self.getSelection()[1]

    def descent(self):
        if self.getSelection() is None:
            return
        self.changeDir(self.getSelection()[0], select=self.current_directory)

    def getFilename(self):
        if self.getSelection() is None:
            return None
        x = self.getSelection()[0]
        if isinstance(x, eServiceReference):
            x = x.getPath()
        return x

    def getServiceRef(self):
        if self.getSelection() is None:
            return None
        x = self.getSelection()[0]
        if isinstance(x, eServiceReference):
            return x
        return None

    def execBegin(self):
        harddiskmanager.on_partition_list_change.append(self.partitionListChanged)

    def execEnd(self):
        harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)

    def refresh(self):
        self.changeDir(self.current_directory, self.getFilename())

    def partitionListChanged(self, action, device):
        self.refreshMountpoints()
        if self.current_directory is None:
            self.refresh()
