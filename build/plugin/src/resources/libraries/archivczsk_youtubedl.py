import json
import sys
import os

from sys import stdin, stdout

def getRequest():
    return json.loads(stdin.read(int(stdin.read(7))))

def sendResponse(response):
    dump = json.dumps(response)
    dump = "%07d%s" % (len(dump)+7, dump)
    stdout.write(dump)
    stdout.flush()

def mainLoop():
    info = {'type': 'info', 'status':True, 'version': '', 'exception': None}
    try:
        import youtube_dl
        options = {'quiet': True}
        ydl = youtube_dl.YoutubeDL(options)
        sendResponse(info)
    except Exception as e:
        info['status'] = False
        info['exception'] = str(e)
        sendResponse(info)
        exit(1)

    while True:
        request = getRequest()
        if request:
            response = {'type':'request', 'status':False, 'result':None, 'exception':None}
            try:
                result = ydl.extract_info(request['url'], False)
                response['status'] = True
                response['result'] = result
            except Exception as e:
                response['exception'] = str(e)
            sendResponse(response)

if __name__ == "__main__":
    ydl_lib = os.path.join(os.path.dirname(os.path.realpath(__file__)),'youtube_dl')
    sys.path.append(ydl_lib)
    mainLoop()
