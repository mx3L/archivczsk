'''
Created on 21.10.2012

@author: marko
'''
import os, traceback, sys
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigText, ConfigNumber, ConfigIP, ConfigPassword, ConfigDirectory, configfile, getConfigListEntry

from tools import util, parser
from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK import settings
from Plugins.Extensions.archivCZSK.resources.repositories import config as addon_config
from Plugins.Extensions.archivCZSK.gui import menu
from Plugins.Extensions.archivCZSK.gui import info
from Plugins.Extensions.archivCZSK.gui import shortcuts
from Plugins.Extensions.archivCZSK.gui import download
from contentprovider import VideoAddonContentProvider

class Addon(object):

    def __init__(self, info, repository):
        self.repository = repository
        self.info = info

        self.id = info.id
        self.name = info.name
        self.version = info.version
        self.author = info.author
        self.description = info.description
        self.changelog = info.changelog
        self.path = info.path
        self.relative_path = os.path.relpath(self.path, repository.path)

        log.info("%s - initializing", self)

        self._updater = repository._updater
        self.__need_update = False

        # load languages
        self.language = AddonLanguage(self, os.path.join(self.path, self.repository.addon_languages_relpath))
        if self.language.has_language(settings.LANGUAGE_SETTINGS_ID):
            self.language.set_language(settings.LANGUAGE_SETTINGS_ID)
        else:
            #fix to use czech language instead of slovak language when slovak is not available
            if settings.LANGUAGE_SETTINGS_ID == 'sk' and self.language.has_language('cs'):
                self.language.set_language('cs')
            else:
                self.language.set_language('en')

        # load settings
        self.settings = AddonSettings(self, os.path.join(self.path, self.repository.addon_settings_relpath))

        # loader to handle addon imports
        self.loader = AddonLoader(self)

    def __repr__(self):
        return "%s(%s-%s)" % (self.__class__.__name__, self.name, self.version)


    def update(self):
        if self.__need_update:
            ret = self._updater.update_addon(self)
            if ret:
                self.__need_update = False
            return ret
        else:
            return False

    def check_update(self, load_xml=True):
        self.__need_update, self.info.broken = self._updater.check_addon(self, load_xml)
        return self.__need_update

    def need_update(self):
        return self.__need_update


    def get_localized_string(self, id_language):
        return self.language.get_localized_string(id_language)

    def setting_exist(self, setting_id):
        return self.settings.setting_exist(setting_id)

    def get_setting(self, setting_id):
        return self.settings.get_setting(setting_id)

    def set_setting(self, setting_id, value):
        return self.settings.set_setting(setting_id, value)

    def get_info(self, info):
        try:
            atr = getattr(self.info, '%s' % info)
        except Exception as e:
            #traceback.print_exc()
            log.error("%s get_info cannot retrieve info - %s" % (self, str(e)))
            return None
        else:
            return atr

    def open_settings(self, session, cb=None):
        menu.openAddonMenu(session, self, cb)

    def open_changelog(self, session):
        info.showChangelog(session, self.name, self.changelog)


    def include(self):
        self.loader.add_importer()

    def deinclude(self):
        self.loader.remove_importer()

    def close(self):
        self.loader.close()
        self.info = None
        self.loader = None
        self._updater = None
        self.repository = None



class XBMCAddon(object):
    def __init__(self, addon):
        self._addon = addon

    def __getattr__(self, attr):
        return getattr(self._addon, attr)

    def getLocalizedString(self, id_language):
        return self._addon.get_localized_string(id_language)

    def getAddonInfo(self, info):
        return self._addon.get_info(info)

    def getSetting(self, setting):
            val = self._addon.get_setting(setting)
            if isinstance(val, bool):
                if val:
                    return 'true'
                else:
                    return 'false'
            return val

    def setSetting(self, setting, value):
        return self._addon.set_setting(setting, value)



class ToolsAddon(Addon):
    def __init__(self, info, repository):
        Addon.__init__(self, info, repository)
        self.library = self.info.library

        lib_path = os.path.join(self.path, self.library)
        self.loader.add_path(lib_path)

class VideoAddon(Addon):
    ignore_requires = [
                       "xbmc.python",
                       "script.module.simplejson",
                       "script.usage.tracker"
                       ]

    def __init__(self, info, repository):
        Addon.__init__(self, info, repository)
        self.script = info.script
        self.requires = [require for require in info.requires if require['addon'] not in VideoAddon.ignore_requires]
        if self.script == '':
            raise Exception("%s entry point missing in addon.xml" % self)
        # content provider
        self.downloads_path = self.get_setting('download_path')
        self.shortcuts_path = os.path.join(config.plugins.archivCZSK.dataPath.getValue(), self.id)
        self.provider = VideoAddonContentProvider(self, self.downloads_path, self.shortcuts_path)

    def refresh_provider_paths(self, *args, **kwargs):
        self.downloads_path = self.get_setting('download_path')
        self.shortcuts_path = os.path.join(config.plugins.archivCZSK.dataPath.getValue(), self.id)
        self.provider.downloads_path = self.downloads_path
        self.provider.shortcuts_path = self.shortcuts_path

    def open_shortcuts(self, session, cb):
        def callback(*args, **kwargs):
            self.refresh_provider_paths()
            cb and cb(*args, **kwargs)
        shortcuts.openShortcuts(session, self, callback)

    def open_downloads(self, session, cb):
        def callback(*args, **kwargs):
            self.refresh_provider_paths()
            cb and cb(*args, **kwargs)
        download.openAddonDownloads(session, self, callback)

    def close(self):
        Addon.close(self)
        self.provider.close()
        self.provider = None



class AddonLanguage(object):
    """Loading xml language file"""
    language_map = {
                    'en':'English',
                    'sk':'Slovak',
                    'cs':'Czech',
                    }

    def __init__(self, addon, languages_dir):

        self.addon = addon
        self._languages_dir = languages_dir
        self._language_filename = 'strings.xml'
        self.current_language = {}
        self.default_language_id = 'en'
        self.current_language_id = 'en'
        self.languages = {}
        log.debug("initializing %s - languages", addon)

        if not os.path.isdir(languages_dir):
            log.error("%s cannot load languages, missing %s directory", self, os.path.basename(languages_dir))
            return

        for language_dir in os.listdir(languages_dir):
            language_id = self.get_language_id(language_dir)
            if language_id is None:
                log.error("%s unknown language %s, you need to update Language map to use it, skipping..", self, language_dir)
                continue
            language_dir_path = os.path.join(languages_dir, language_dir)
            language_file_path = os.path.join(language_dir_path, self._language_filename)
            if os.path.isfile(language_file_path):
                self.languages[language_id] = None
            else:
                log.error("%s cannot find language file %s, skipping %s language..", self, language_file_path, language_dir)

    def __repr__(self):
        return "%s[language]" % self.addon


    def load_language(self, language_id):
        language_dir_path = os.path.join(self._languages_dir, self.get_language_name(language_id))
        language_file_path = os.path.join(language_dir_path, self._language_filename)
        try:
            el = util.load_xml(language_file_path)
        except Exception:
            log.error("%s skipping language %s"%(self, language_id))
        else:
            language = {}
            strings = el.getroot()
            for string in strings.findall('string'):
                string_id = int(string.attrib.get('id'))
                text = string.text
                language[string_id] = text
            self.languages[language_id] = language
            log.debug("%s language %s was successfully loaded", (self, language_id))


    def get_language_id(self, language_name):
        revert_langs = dict(map(lambda item: (item[1], item[0]), self.language_map.items()))
        if language_name in revert_langs:
            return revert_langs[language_name]
        else:
            return None

    def get_language_name(self, language_id):
        if language_id in self.language_map:
            return self.language_map[language_id]
        else:
            return None

    def get_localized_string(self, string_id):
        if string_id in self.current_language:
            return self.current_language[string_id]
        else:
            log.error("%s cannot find language id %s in %s language, returning id of language", self, string_id, self.current_language_id)
            return str(string_id)

    def has_language(self, language_id):
        return language_id in self.languages

    def set_language(self, language_id):
        if self.has_language(language_id):
            if self.languages[language_id] is None:
                self.load_language(language_id)
            log.info("%s setting current language %s to %s", self, self.current_language_id, language_id)
            self.current_language_id = language_id
            self.current_language = self.languages[language_id]
        else:
            log.error("%s cannot set language %s, language is not available", self, language_id)

    def get_language(self):
        return self.current_language_id

    def close(self):
        self.addon = None



class AddonSettings(object):

    def __init__(self, addon, settings_file):
        log.debug("%s - initializing settings", addon)


        # remove dots from addon.id to resolve issue with load/save config of addon
        addon_id = addon.id.replace('.', '_')

        setattr(config.plugins.archivCZSK.archives, addon_id, ConfigSubsection())
        self.main = getattr(config.plugins.archivCZSK.archives, addon_id)
        addon_config.add_global_addon_settings(addon, self.main)

        self.main.enabled = ConfigYesNo(default=True)

        self.addon = addon
        self.categories = []
        # not every addon has settings
        try:
            settings_parser = parser.XBMCSettingsXMLParser(settings_file)
        except IOError:
            pass
        else:
            self.category_entries = settings_parser.parse()
            #hard code addon order for each addon
            try:
                #list.append(getConfigListEntry(_("Show movie info"), config.plugins.archivCZSK.showVideoInfo))
                labelInfo = _("Show movie info")
                obj = {'option': 'false', 'default': 'true', 'label': labelInfo, 'visible': 'true', 'type': 'bool', 'id': 'auto_show_video_info'}
                self.category_entries[0]['subentries'].append(obj)

                #todo check if exist already
                labelorder = _("Addon order")
                obj = {'option': 'false', 'default': '99999', 'label': labelorder, 'visible': 'true', 'type': 'text', 'id': 'auto_addon_order'}
                self.category_entries[0]['subentries'].append(obj)
                #if 'auto_addon_order' in self.category_entries[0]['subentries']:
                #    log.logInfo("############auto_addon_order already exist")
            except:
                log.logError("Add addon order (%s) failed.\n%s" % (self.addon, traceback.format_exc()))
            self.initialize_settings()


    def __repr__(self):
        return "%s[settings]" % self.addon


    def initialize_settings(self):
        for entry in self.category_entries:
            if entry['label'] == 'general':
                if len(entry['subentries']) == 0 :
                    continue
                else:
                    category = {'label':_('general'), 'subentries':[]}
            else:
                category = {'label':self._get_label(entry['label']), 'subentries':[]}

            for subentry in entry['subentries']:
                self.initialize_entry(self.main, subentry)
                if subentry['visible'] == 'true':
                    category['subentries'].append(getConfigListEntry(self._get_label(subentry['label']).encode('utf-8'), subentry['setting_id']))
            log.debug("%s initialized category %s", self, str(category))
            self.categories.append(category)


    def get_configlist_categories(self):
        return self.categories

    def setting_exist(self, setting_id):
        try:
            getattr(self.main, '%s' % setting_id)
            return True
        except:
            return False

    def get_setting(self, setting_id):
        try:
            setting = getattr(self.main, '%s' % setting_id)
        except (ValueError, KeyError, AttributeError):
            log.error('%s cannot retrieve setting %s,  Invalid setting id', self, setting_id)
            log.logDebug("Cannot retrieve setting '%s' - %s" % (setting_id, self.addon))
            return ""
        else:
            if isinstance(setting, ConfigIP):
                return setting.getText()
            return setting.getValue()

    def set_setting(self, setting_id, value):
        try:
            setting = getattr(self.main, '%s' % setting_id)
        except ValueError:
            log.error('%s cannot retrieve setting %s,  Invalid setting id', self, setting_id)
            return False
        else:
            setting.setValue(value)
            setting.save()
            return True

    def _get_label(self, label):
        log.debug('%s resolving label: %s', self, label)
        try:
            string_id = int(label)
        except ValueError:
            if isinstance(label, unicode):
                return label
            else:
                label = util.decode_string(label)
                return label
        else:
            label = self.addon.get_localized_string(string_id)
            return label


    def initialize_entry(self, setting, entry):
        # fix dotted id
        entry['id'] = entry['id'].replace('.', '_')

        if entry['type'] == 'bool':
            setattr(setting, entry['id'], ConfigYesNo(default=(entry['default'] == 'true')))
            entry['setting_id'] = getattr(setting, entry['id'])

        elif entry['type'] == 'text':
            if entry['option'] == 'true':
                setattr(setting, entry['id'], ConfigPassword(default=entry['default'], fixed_size=False))
            else:
                setattr(setting, entry['id'], ConfigText(default=entry['default'], fixed_size=False))
            entry['setting_id'] = getattr(setting, entry['id'])

        elif entry['type'] == 'enum':
            choicelist = [(str(idx), self._get_label(e).encode('utf-8')) for idx, e in enumerate(entry['lvalues'].split("|"))]
            setattr(setting, entry['id'], ConfigSelection(default=entry['default'], choices=choicelist))
            entry['setting_id'] = getattr(setting, entry['id'])

        elif entry['type'] == 'labelenum':
            choicelist = [(self._get_label(e).encode('utf-8'), self._get_label(e).encode('utf-8')) for e in entry['values'].split("|")]
            setattr(setting, entry['id'], ConfigSelection(default=entry['default'], choices=choicelist))
            entry['setting_id'] = getattr(setting, entry['id'])

        elif entry['type'] == 'ipaddress':
            setattr(setting, entry['id'], ConfigIP(default=map(int, entry['default'].split('.')), auto_jump=True))
            entry['setting_id'] = getattr(setting, entry['id'])

        elif entry['type'] == 'number':
            setattr(setting, entry['id'], ConfigNumber(default=int(entry['default'])))
            entry['setting_id'] = getattr(setting, entry['id'])
        else:
            log.error('%s cannot initialize unknown entry %s', self, entry['type'])

    def close(self):
        self.addon = None


class AddonInfo(object):

    def __init__(self, info_file):
        log.info("AddonInfo(%s) initializing.." , '/'.join(info_file.split('/')[-3:]))

        pars = parser.XBMCAddonXMLParser(info_file)
        addon_dict = pars.parse()
        
        self.id = addon_dict['id']
        self.name = addon_dict['name']
        self.version = addon_dict['version']
        self.author = addon_dict['author']
        self.type = addon_dict['type']
        self.broken = addon_dict['broken']
        self.path = os.path.dirname(info_file)
        self.library = addon_dict['library']
        self.script = addon_dict['script']
        self.tmp_path = config.plugins.archivCZSK.tmpPath.value
        self.data_path = os.path.join(config.plugins.archivCZSK.dataPath.getValue(), self.id)
        self.profile = self.data_path

        # create data_path(profile folder)
        util.make_path(self.data_path)

        if settings.LANGUAGE_SETTINGS_ID in addon_dict['description']:
            self.description = addon_dict['description'][settings.LANGUAGE_SETTINGS_ID]
        elif settings.LANGUAGE_SETTINGS_ID == 'sk' and 'cs' in addon_dict['description']:
            self.description = addon_dict['description']['cs']
        else:
            if not 'en' in addon_dict['description']:
                self.description = u''
            else:
                self.description = addon_dict['description']['en']

        self.requires = addon_dict['requires']
        self.image = os.path.join(self.path, 'icon.png')

        #changelog
        changelog_path = None
        if os.path.isfile(os.path.join(self.path, 'changelog.txt')):
            changelog_path = os.path.join(self.path, 'changelog.txt')

        elif os.path.isfile(os.path.join(self.path, 'Changelog.txt')):
            changelog_path = os.path.join(self.path, 'Changelog.txt')

        else:
            changelog_path = None

        if changelog_path is not None:
            with open(changelog_path, 'r') as f:
                text = f.read()
            try:
                self.changelog = text
            except Exception:
                log.error('%s c[C]angleog.txt cannot be decoded', self)
                self.changelog = u''
                pass
        else:
            log.error('%s c[C]hangelog.txt file is missing', self)
            self.changelog = u''


    def __repr__(self):
        return "AddonInfo(%s)" % ('/'.join(self.path.split('/')[-2:]))


    def get_changelog(self):
        return self.changelog

    def close(self):
        self.addon = None


class AddonLoader():
    def __init__(self, addon):
        self.addon = addon
        self.__importer = util.CustomImporter(addon.id,log=log.debug)

    def add_path(self, path):
        self.__importer.add_path(path)

    def add_importer(self):
        log.debug("%s adding importer" , self.addon)
        if self.__importer in sys.meta_path:
            log.debug("%s importer is already in meta_path" % self.addon)
        else:
            sys.meta_path.append(self.__importer)

    def remove_importer(self):
        log.debug("%s removing importer" , self.addon)
        sys.meta_path.remove(self.__importer)

    def close(self):
        self.addon = None
        self.__importer.release_modules()
        self.__importer = None
