#!/usr/bin/python

import os
import sys
import traceback
from xml.etree.cElementTree import ElementTree

TMP_PATH = "/tmp/repo_archivczsk"
PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/"
REPOSITORIES_PATH = os.path.join(PLUGIN_PATH,"resources/repositories")


def load_xml(xml_file):
    xml = None
    try:
        xml = open(xml_file, "r+")

    # trying to set encoding utf-8 in xml file with not defined encoding
        if 'encoding' not in xml.readline():
            xml.seek(0)
            xml_string = xml.read()
            xml_string = xml_string.decode('utf-8')
            xml.seek(0)
            xml.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
            xml.write(xml_string.encode('utf-8'))
            xml.flush()
    except IOError, e:
        print "I/O error(%d): %s" % (e.errno, e.strerror)
    finally:
        if xml:xml.close()


    el = ElementTree()
    try:
        el.parse(xml_file)
    except IOError, e:
        print "cannot load %s file I/O error(%d): %s" % (xml_file, e.errno, e.strerror)
        raise
    else:
        return el

class XMLParser():
    def __init__(self, xml_file):
        xml = load_xml(xml_file)
        self.xml = xml.getroot()

    def parse(self):
        pass

class XBMCSettingsXMLParser(XMLParser):

    def parse(self):
        categories = []
        settings = self.xml

        main_category = {'label':'general', 'subentries':[]}
        for setting in settings.findall('setting'):
            main_category['subentries'].append(self.get_setting_entry(setting))
        categories.append(main_category)

        for category in settings.findall('category'):
            category_entry = self.get_category_entry(category)
            categories.append(category_entry)

        return categories


    def get_category_entry(self, category):
        entry = {'label':category.attrib.get('label'), 'subentries':[]}
        for setting in category.findall('setting'):
            entry['subentries'].append(self.get_setting_entry(setting))
        return entry


    def get_setting_entry(self, setting):
        entry = {}
        entry['label'] = setting.attrib.get('label')
        entry['id'] = setting.attrib.get('id')
        entry['type'] = setting.attrib.get('type')
        entry['default'] = setting.attrib.get('default')
        entry['visible'] = setting.attrib.get('visible') or 'true'
        if entry['type'] == 'text':
            entry['option'] = setting.attrib.get('option') or 'false'
        if entry['type'] == 'enum':
            entry['lvalues'] = setting.attrib.get('lvalues')
        elif entry['type'] == 'labelenum':
            entry['values'] = setting.attrib.get('values')
        return entry


class XBMCAddonXMLParser(XMLParser):

    addon_types = {
                   "xbmc.python.pluginsource":"content",
                   "xbmc.addon.repository":"repository",
                   "xbmc.python.module":"tools"
                   }

    def get_addon_id(self, addon):
        id_addon = addon.attrib.get('id')#.replace('-', '')
        #id_addon = id_addon.split('.')[-2] if id_addon.split('.')[-1] == 'cz' else id_addon.split('.')[-1]
        return id_addon


    def parse(self):
        return self.parse_addon(self.xml)

    def parse_addon(self, addon):

        id = self.get_addon_id(addon)
        if id is None:
            raise Exception("Parse error: Mandatory atrribute 'id' is missing")
        name = addon.attrib.get('name')
        if name is None:
            raise Exception("Parse error: Mandatory atrribute 'name' is missing")
        author = addon.attrib.get('provider-name')
        if author is None:
            raise Exception("Parse error: Mandatory atrribute 'author' is missing")
        version = addon.attrib.get('version')
        if version is None:
            raise Exception("Parse error: Mandatory atrribute 'version' is missing")

        type = 'unknown'
        description = {}
        broken = None
        repo_datadir_url = u''
        repo_addons_url = u''
        requires = []
        library = 'lib'
        script = 'default.py'

        req = addon.find('requires')
        for imp in req.findall('import'):
            requires.append({'addon':imp.attrib.get('addon'),
                             'version':imp.attrib.get('version'),
                             'optional':imp.attrib.get('optional')})


        for info in addon.findall('extension'):
            if info.attrib.get('point') in self.addon_types:
                ad_type = self.addon_types[info.attrib.get('point')]
                if ad_type == 'repository':
                    type = ad_type
                    repo_datadir_url = info.find('datadir').text
                    repo_addons_url = info.find('info').text
                elif ad_type == 'tools':
                    type = ad_type
                    library = info.attrib.get('library')
                elif ad_type == 'content':
                    provides = None
                    if info.findtext('provides'):
                        provides = info.findtext('provides')
                    if info.attrib.get('provides'):
                        provides = info.attrib.get('provides')
                    if provides is not None and provides == 'video':
                        type = 'video'
                        script = info.attrib.get('library')


            if info.attrib.get('point') == 'xbmc.addon.metadata':
                if info.findtext('broken'):
                    broken = info.findtext('broken')
                for desc in info.findall('description'):
                    if desc.attrib.get('lang') is None:
                        description['en'] = desc.text
                    else:
                        description[desc.attrib.get('lang')] = desc.text

        return {"id":id,
                "name":name,
                "author":author,
                "type":type ,
                "version":version,
                "description":description,
                "broken":broken,
                "repo_addons_url":repo_addons_url,
                "repo_datadir_url":repo_datadir_url,
                "requires":requires,
                "library":library,
                "script":script}


class XBMCMultiAddonXMLParser(XBMCAddonXMLParser):

    def parse_addons(self):
        addons = {}
        for addon in self.xml.findall('addon'):
            addon_dict = self.parse_addon(addon)
            addon_id = addon_dict['id']
            addons[addon_id] = addon_dict
        return addons

    def find_addon(self, id):
        for addon in self.xml.findall('addon'):
            if id == self.get_addon_id(addon):
                return self.parse_addon(addon)




def download_addons(repository, base, commit=None):
    repository_path = base + REPOSITORIES_PATH + '/' + repository + '/addon.xml'
    if not os.path.isfile(repository_path):
        print "ERROR: repository - %s doesn't exist"%repository
        print "ERROR: invalid repository path: %s"%repository_path
        return
    try:
        repo = XBMCAddonXMLParser(repository_path).parse()
    except Exception:
        traceback.print_exc()
        print "ERROR: cannot parse - %s repository"%repository
        return
    addons_xml_path = os.path.join(TMP_PATH, "addons.xml")
    os.system("find %s -mindepth 1 -type d -exec rm -rf {} \;"% os.path.split(repository_path)[0])
    os.system("find %s -type l -exec rm -rf {} \;"% os.path.split(repository_path)[0])
    os.system("mkdir -p %s" % TMP_PATH)
    repo_addons_url = repo["repo_addons_url"]
    if repo_addons_url.find('{commit}') != -1 and commit:
        repo_addons_url = repo_addons_url.replace('{commit}', commit)
    os.system("wget -O %s %s" % (addons_xml_path, repo_addons_url))
    remote_addons = XBMCMultiAddonXMLParser(addons_xml_path).parse_addons()
    for addon_id in remote_addons.keys():
        remote_addon = remote_addons[addon_id]
        zip_filename = "%s-%s.zip" % (addon_id, remote_addon['version'])
        remote_base = repo['repo_datadir_url'] + '/' + addon_id
        if remote_base.find('{commit}') != -1 and commit:
            remote_base = remote_base.replace('{commit}', commit)
        local_file = os.path.join(TMP_PATH, zip_filename)
        remote_file = remote_base + '/' + zip_filename
        print "downloading %s..." % addon_id
        os.system("wget -O %s %s" % (local_file, remote_file))
        os.system("unzip %s -d %s" % (local_file, os.path.dirname(repository_path)))
    os.system("rm -r %s" % TMP_PATH)




if __name__=='__main__':
    print sys.argv
    if len(sys.argv) < 2:
        print "You need to provide repository name"
    else:
        repository = sys.argv[1]
        base=''
        commit = None
        if len(sys.argv) == 3:
            base = sys.argv[2]
        if len(sys.argv) == 4:
            commit = sys.argv[3]
        print "downloading addons from [%s] repository to %s" % (repository, base)
        download_addons(repository, base, commit)
