import urllib2
import os

def load(subpath):
    if subpath.startswith('http'):
        req = urllib2.Request(subpath)
        try:
            response = urllib2.urlopen(req)
            text = response.read()
        except Exception:
            raise
        finally:
            if 'response' in locals():
                response.close()
        return text
    else:
        with open(subpath, 'r') as f:
            return f.read()


def decode(text, encodings, current_encoding=None, decode_from_start=False):
    utext = None
    used_encoding = None
    current_encoding_idx = -1
    current_idx = 0

    if decode_from_start:
        current_encoding = None

    if current_encoding is not None:
        current_encoding_idx = encodings.index(current_encoding)
        current_idx = current_encoding_idx + 1
        if current_idx >= len(encodings):
            current_idx = 0

    while current_idx != current_encoding_idx:
        enc = encodings[current_idx]
        try:
            print '[decode] trying enconding', enc,'...'
            utext = unicode(text, enc)
            print '[decode] decoded with', enc, 'encoding.'
            used_encoding = enc
            return utext, used_encoding
        except Exception:
            if enc == encodings[-1] and current_encoding_idx == -1:
                raise Exception("[decode] cannot decode, try to use different encodings")
            elif enc == encodings[-1] and current_encoding_idx != -1:
                current_idx = 0
                continue
            else:
                current_idx += 1
                continue

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None
