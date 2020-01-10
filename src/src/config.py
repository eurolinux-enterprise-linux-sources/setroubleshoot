# /usr/bin/python -E
# -*- mode: Python; -*-
#
# Copyright (C) 2006 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

__all__ = ['config_init',
           'get_config',
           'get_option',
           'set_config',
           'parse_config_setting',
           'config_has_section',
           'LOG_CATEGORIES',
          ]

import getopt
import sys
import os
import ConfigParser
import re

_cfg = None

CFG_FILE = os.path.join('/etc/setroubleshoot', "%s.conf" % 'setroubleshoot')

LOG_CATEGORIES = ['rpc','xml','cfg','alert','sig','plugin','avc',
	          'email','gui', 'gui_data', 'program','database','server','dbus',
                  'stats', 'communication', 'subprocess']

defaults = {
'general' : {
    'pid_file' : {
        'value'       : '/var/run/setroubleshootd.pid',
        'description' : '',
        'readOnly'    : False,
    },
    'pkg_name' : {
        'value'       : 'setroubleshoot',
        'description' : '',
        'readOnly'    : True,
    },
    'pkg_version' : {
        'value'       : '3.0.47',
        'description' : '',
        'readOnly'    : True,
    },
    'project_url' : {
        'value'       : 'http://hosted.fedoraproject.org/projects/setroubleshoot',
        'description' : 'URL of project website',
    },
    'rpc_version' : {
        'value'       : '1.1',
        'description' : '',
        'readOnly'    : True,
    },
    'i18n_text_domain' : {
        'value'       : 'setroubleshoot',
        'description' : 'internationalization (i18n) translation catalog',
        'readOnly'    : True,
    },
    'i18n_locale_dir' : {
        'value'       : '/usr/share/locale',
        'description' : 'internationalization (i18n) translation catalog directory',
        'readOnly'    : True,
    },
    'i18n_encoding' : {
        'value'       : 'utf-8',
        'description' : 'internationalization (i18n) encoding (codeset)',
        'readOnly'    : True,
    },
    'data_dir' : {
        'value'       : '/usr/share/setroubleshoot',
        'description' : '',
        'readOnly'    : True,
    },
    'config_dir' : {
        'value'       : '/etc/setroubleshoot',
        'description' : '',
        'readOnly'    : True,
    },
    'use_auparse' : {
        'value'       : False,
        'description' : '',
        'readOnly'    : False,
    },
    'icon_name' : {
        'value'       : 'setroubleshoot_icon',
        'description' : '',
        'readOnly'    : True,
    },
},
'helper_apps' : {
    'web_browser_launcher' : {
        'value'       : '/usr/bin/xdg-open',
        'description' : 'Helper application to launch web browser on a URL',
    },
},
'audit' : {
    'binary_protocol_socket_path' : {
        'value'       : '/var/run/audit_events',
        'description' : 'unix domain socket used to listen for audit messages (binary audit protocol)',
    },
    'text_protocol_socket_path' : {
        'value'       : '/var/run/audispd_events',
        'description' : 'unix domain socket used to listen for audit messages (textural audit protocol)',
    },
    'retry_interval' : {
        'value'       : 60,
        'description' : 'number of seconds to wait before trying to connect to audit socket again in the event of socket failure',
    },
},
'alert' : {
    'use_notification' : {
        'value'       : 'always',
        'description' : '''Control balloon notification. Possible values: always,never,browser_hidden "always" will
always display the notification. "never" disables notification completely. "browser_hidden" displays the notification
but only if the alert browser is not visible. Note: individual alerts can be flagged as silent disabling notification
for a specific alert, this parameter does not override that.''',
    },
},
'plugins' : {
    'plugin_dir' : {
        'value'       : '/usr/share/setroubleshoot/plugins',
        'description' : '',
    },
},
'session_dbus' : {
    'bus_name' : {
        'value'       : 'org.fedoraproject.Setroubleshootd',
        'description' : '',
        'readOnly'    : True,
    },
    'object_path' : {
        'value'       : '/org/fedoraproject/Setroubleshootd',
        'description' : '',
        'readOnly'    : True,
    },
    'interface' : {
        'value'       : 'org.fedoraproject.SetroubleshootdIface',
        'description' : '',
        'readOnly'    : True,
    },
},
'system_dbus' : {
    'bus_name' : {
        'value'       : 'org.fedoraproject.Setroubleshootd',
        'description' : '',
        'readOnly'    : True,
    },
    'object_path' : {
        'value'       : '/org/fedoraproject/Setroubleshootd',
        'description' : '',
        'readOnly'    : True,
    },
    'interface' : {
        'value'       : 'org.fedoraproject.SetroubleshootdIface',
        'description' : '',
        'readOnly'    : True,
    },
},
'database' : {
    'database_dir' : {
        'value'       : '/var/lib/setroubleshoot',
        'description' : '',
    },
    'filename' : {
        'value'       : 'setroubleshoot',
        'description' : '',
    },
    'max_alerts' : {
        'value'       : 50,
        'description' : '''
Keep no more than this many alerts in the database. Oldest alerts based on
the alert's last seen date will be purged first. Zero implies no limit''',
    },
    'max_alert_age' : {
        'value'       : '',
        'description' : '''
Purge any alerts whose age based on it's last seen date exceeds this threshold.
Age may be specified as a sequence of integer unit pairs. Units may be one of
year,month,week,day,hour,minute,second and may optionally be plural.
Example: '2 weeks 1 day' sets the threshold at 15 days.
An empty string implies no limit''',
    },
},
'connection' : {
    'default_port' : {
        'value'       : '69783',     # FIXME: figure out defined port,
        'description' : '',
    },
},
'listen_for_client' : {
    'path' : {
        'value'       : os.path.join('/var/run/setroubleshoot','setroubleshoot_server'),
        'description' : '',
        'readOnly'    : False,
    },
    'address_list' : {
        'value'       : '{unix}%(path)s',
        'description' : '''
List of socket addresses server should listen on for client
connections. Addresses should not contain any whitespace. Each address
is of the form "[{family}]address[:port]" where [] indicates the value
is optional. Valid values for family are inet or unix, if the family
is absent it defaults to inet. If the family is unix the address is
interpreted as a file path. If the family is inet the address is
interpreted as either a host name or IP address. As a special case if
the inet address is "hostname" the current hostname will be
substituted. If the family is inet the address may optionally be
followed by a colon (:) and a port number. If the port number is
absent in the address it defaults to the port specified in this config
section. Example, to listen on the local unix domain socket and
provide remote connections use this "{unix}%(path)s, hostname"
'''
    },
},
'client_connect_to' : {
    'path' : {
        'value'       : os.path.join('/var/run/setroubleshoot','setroubleshoot_server'),
        'description' : '',
        'readOnly'    : False,
    },
    'address_list' : {
        'value'       : '{unix}%(path)s hostname',
        'description' : '''
List of socket addresses server should listen on for client
connections. Addresses should not contain any whitespace. Each address
is of the form "[{family}]address[:port]" where [] indicates the value
is optional. Valid values for family are inet or unix, if the family
is absent it defaults to inet. If the family is unix the address is
interpreted as a file path. If the family is inet the address is
interpreted as either a host name or IP address. As a special case if
the inet address is "hostname" the current hostname will be
substituted. If the family is inet the address may optionally be
followed by a colon (:) and a port number. If the port number is
absent in the address it defaults to the port specified in this config
section. Example, to listen on the local unix domain socket and
provide remote connections use this "{unix}%(path)s, hostname"
'''
    },
},
'socket' : {
    'buf_size' : {
        'value'       : '2048',
        'description' : '',
        'readOnly'    : True,
    },
    'timeout' : {
        'value'       : '5',
        'description' : '',
        'readOnly'    : True,
    },
},
'setroubleshootd_log' : {
    'level' : {
        'value'       : 'warning',
        'description' : '''
Global logging level. Levels are the same as in the python logging
module, but are case insenstive. The level may also be specified as an
integer. The defined levels in severity order are:[CRITICAL, ERROR,
WARNING, INFO, DEBUG]''',
    },
    'categories' : {
        'value'       : '',
        'description' : '''
Comma seperated list of logging categories. Each categories may
optionally be followed by a colon(:) and a logging level, which either
may be one of the symbolic levels or numeric, e.g. ipc:info. If no
level is defined the default level is used. If the category name is
preceded by a tilde (~) the category is not logged at all.
The list of available categories is: [%s]''' % ', '.join(LOG_CATEGORIES),
    },
    'filename' : {
        'value'       : '/var/log/setroubleshoot/setroubleshootd.log',
        'description' : '',
    },
    'filemode' : {
        'value'       : 'w',
        'description' : 'should be "w" or "a" for write or append respectively'
    },
    'format' : {
        'value'       : '%(asctime)s [%(name)s.%(levelname)s] %(message)s',
        'description' : '',
    },
    'console' : {
        'value'       : 'False',
        'description' : 'True|False, also log to the console',
    },
    'profile' : {
        'value'       : 'False',
        'description' : 'True|False, gather statistics',
    },
},
'sealert_log' : {
    'level' : {
        'value'       : 'warning',
        'description' : '''
Global logging level. Levels are the same as in the python logging
module, but are case insenstive. The level may also be specified as an
integer. The defined levels in severity order are:[CRITICAL, ERROR,
WARNING, INFO, DEBUG]''',
    },
    'categories' : {
        'value'       : '',
        'description' : '''
Comma seperated list of logging categories. Each categories may
optionally be followed by a colon(:) and a logging level, which either
may be one of the symbolic levels or numeric, e.g. ipc:info. If no
level is defined the default level is used. If the category name is
preceded by a tilde (~) the category is not logged at all.
The list of available categories is: [%s]''' % ', '.join(LOG_CATEGORIES),
    },
    'filename' : {
        'value'       : '',
        'description' : ''
    },
    'filemode' : {
        'value'       : 'a',
        'description' : 'should be "w" or "a" for write or append respectively'
    },
    'format' : {
        'value'       : '%(asctime)s [%(name)s.%(levelname)s] %(message)s',
        'description' : '',
    },
    'console' : {
        'value'       : 'False',
        'description' : 'True|False, also log to the console',
    },
    'profile' : {
        'value'       : 'False',
        'description' : 'True|False, gather statistics',
    },
},
'access' : {
    'client_users' : {
	'value'	      : '*',
	'description' : '''
Comma-separated list of users allowed to run the client and connect to
the local fault server and therefore see security denials.
Also accepts '*' to allow all users to connect.'''
    },
    'fix_cmd_users' : {
	'value'	      : 'root',
	'description' : '''
Comma-separated list of users allowed to run the fix commands with
root privileges. Members of this list can execute the fix commands
specified in any alert. The command is executed with root privileges
so you should be very caeful who you add to this list as you are
granting them significant power to alter the security settings of this
system. The wildcard '*' is NOT allowed.'''

    },
},
'email' : {
    'smtp_host' : {
        'value'       : 'localhost',
        'description' : 'The SMTP server address',
    },
    'smtp_port' : {
        'value'       : '25',
        'description' : 'The SMTP server port',
    },
    'from_address' : {
        'value'       : 'SELinux_Troubleshoot',
        'description' : 'The From: email header',
    },
    'subject' : {
        'value'       : 'SELinux AVC Alert',
        'description' : 'The Subject: email header',
    },
    'recipients_filepath' : {
        'value'       : os.path.join('/var/lib/setroubleshoot', 'email_alert_recipients'),
        'description' : 'Path name of file with email recipients. One address per line, optionally followed by enable flag. Comment character is #. '
    },
},
'help' : {
    'help_url': {
        'value'       : 'http://hosted.fedoraproject.org/projects/setroubleshoot/wiki/SETroubleShoot%%20User%%20FAQ',
	'description' : 'URL to user help information',
     },
    'bug_report_url': {
        'value'       : 'http://bugzilla.redhat.com/bugzilla/enter_bug.cgi',
	'description' : 'URL used to report bugs',
     },
},
'test' : {
    'analyze' : {
        'value'       : 'False',
        'description' : 'Print plugin report',
        'readOnly'    : True,
    },
},
'fix_cmd' : {
    'run_fix_cmd_enable' : {
        'value'       : 'False',
        'description' : 'Permit running fix commands',
    },
},
}

def config_init():
    global _cfg
    _cfg = read_configuration(defaults)

def read_configuration(defaults):
    cfg = ConfigParser.SafeConfigParser()
    try:
        cfg.read(CFG_FILE)
    except Exception, e:
        # loggers have not been initialized yet, can't use log_cfg, use stderr instead
        print >> sys.stderr, "error parsing config file (%s): %s" % (CFG_FILE, e)
        return None

    default_sections = defaults.keys()
    for default_section in default_sections:
        if not cfg.has_section(default_section):
            cfg.add_section(default_section)
        for default_option,properties in defaults[default_section].items():
            value    = properties['value']
            readOnly = properties.get('readOnly', False)
            if not cfg.has_option(default_section, default_option):
                cfg.set(default_section,default_option,value)
            else:
                if readOnly:
                    # loggers have not been initialized yet, can't use log_cfg, use stderr instead
                    print >> sys.stderr, "error [%s] %s cannot be set in config file" %( default_section, default_option)
                    cfg.set(default_section, default_option, value)
                    
    return cfg

def convert_cfg_type(value, cfg_type=None):
    try:
        if cfg_type is None or cfg_type is str:
            return value
        elif cfg_type is int:
            return int(value)
        elif cfg_type is bool:
            if isinstance(value, bool): return value
            if isinstance(value, int): return bool(value)
            if value.lower() in ['true',  't', 'yes', 'y', 'on']:  return True
            if value.lower() in ['false', 'f', 'no',  'n', 'off']: return False
            raise ValueError("cannot convert %s to boolean" % value)
        elif cfg_type is float:
            return float(value)
        elif cfg_type == 'raw':
            return value
        else:
            try:
                # We can't import log in this modules scope because log imports us, thus loggers will not
                # have been created yet, Therefore we must import the logger in our function local scope
                from setroubleshoot.log import log_cfg 
                log_cfg.error("unknown type %s for option %s", cfg_type, value)
            except ImportError:
                print >> sys.stderr, "error unknown type %s for option %s" % (cfg_type, value)
    except Exception, e:
        try:
            # We can't import log in this modules scope because log imports us, thus loggers will not
            # have been created yet, Therefore we must import the logger in our function local scope
            from setroubleshoot.log import log_cfg 
            log_cfg.error("unknown type %s for option %s", cfg_type, value)
        except ImportError:
            print >> sys.stderr, "error unknown type %s for option %s" % (cfg_type, value)

def get_option(section, name, default_value=None, kwds=None, option_type=None):
    value = None
    if kwds is not None and kwds.has_key(name):
        value = convert_cfg_type(kwds[name])
    elif config_has_section(section):
        value = get_config(section, name, option_type)

    if value is None:
        value = default_value

    return value

def get_config(section, option, cfg_type=None):
    if _cfg is None: return None
    try:
        if cfg_type is None or cfg_type is str:
            return _cfg.get(section, option)
        elif cfg_type is int:
            return _cfg.getint(section, option)
        elif cfg_type is bool:
            return _cfg.getboolean(section, option)
        elif cfg_type is float:
            return _cfg.getfloat(section, option)
        elif cfg_type == 'raw':
            return _cfg.get(section, option, raw=True)
        else:
            try:
                # We can't import log in this modules scope because log imports us, thus loggers will not
                # have been created yet, Therefore we must import the logger in our function local scope
                from setroubleshoot.log import log_cfg 
                log_cfg.error("unknown type = %s getting %s option in %s section: %s", cfg_type, option, section)
            except ImportError:
                print >> sys.stderr, "error unknown type = %s getting %s option in %s section: %s" % (cfg_type, option, section)
            
    except Exception, e:
        try:
            # We can't import log in this modules scope because log imports us, thus loggers will not
            # have been created yet, Therefore we must import the logger in our function local scope
            from setroubleshoot.log import log_cfg
            log_cfg.error("cannot get %s option in %s section: %s", option, section, e)
        except ImportError:
            print >> sys.stderr, "error cannot get %s option in %s section: %s" % (option, section, e)
        return None
    

def set_config(section, option, value):
    try:
        if _cfg is None:
             return False
        if not _cfg.has_section(section):
            _cfg.add_section(section)
        _cfg.set(section, option, value)
    except Exception, e:
        log_program.exception("Cannot set config: section='%s' option='%s' value='%s'", section, option, value)
        return False
    return True
    
config_setting_re = re.compile("([^.=]+?)\s*\.\s*([^.=]+?)\s*=\s*(.*)")
def parse_config_setting(cfg_setting):
    match = config_setting_re.search(cfg_setting)
    if match:
        section = match.group(1)
        option  = match.group(2)
        value   = match.group(3)
    else:
        try:
            # We can't import log in this modules scope because log imports us, thus loggers will not
            # have been created yet, Therefore we must import the logger in our function local scope
            from setroubleshoot.log import log_cfg
            log_cfg.error("could not parse '%s', must be 'section.option=value'", cfg_setting)
        except ImportError:
            print >> sys.stderr, "error: could not parse '%s', must be 'section.option=value'" % (cfg_setting)
        return False

    try:
        # We can't import log in this modules scope because log imports us, thus loggers will not
        # have been created yet, Therefore we must import the logger in our function local scope
        from setroubleshoot.log import log_cfg
        log_cfg.debug("setting config: section='%s' option='%s' value='%s'", section, option, value)
    except ImportError:
        print >> sys.stderr, "setting config: section='%s' option='%s' value='%s'" % (section, option, value)

    set_config(section, option, value)
    return True

def config_has_section(section):
    if _cfg is None: return None
    try:
        return _cfg.has_section(section)
    except Exception, e:
        try:
            # We can't import log in this modules scope because log imports us, thus loggers will not
            # have been created yet, Therefore we must import the logger in our function local scope
            from setroubleshoot.log import log_cfg
            log_cfg.error("config_has_section(%s): %s", section, e)
        except ImportError:
            print >> sys.stderr, "error: config_has_section(%s): %s" % (section, e)
        return False
    

def dump_defaults(defaults, showReadOnly=False):
    import textwrap
    wrap = textwrap.TextWrapper(width=78,
                                initial_indent='# ', subsequent_indent='# ')

    sections = defaults.keys()
    sections.sort()
    for section in sections:
        visibleOptions = 0
        for option,properties in defaults[section].items():
            readOnly    = properties.get('readOnly', False)
            if showReadOnly or not readOnly:
                visibleOptions += 1
        if visibleOptions > 0:
            print "[%s]" % section
            for option,properties in defaults[section].items():
                value       = properties['value']
                readOnly    = properties.get('readOnly', False)
                description = properties.get('description', '')

                if readOnly and not showReadOnly:
                    continue

                if not description:
                    description = 'No Description Available'
                print wrap.fill('%s: ' % option + description)
                if readOnly:
                    print '# READ ONLY, default = "%s"' % (value)
                else:
                    print "%s = %s" % (option, value)
                print

def dump_configuration(cfg):
    sections = cfg.sections()
    sections.sort()
    for section in sections:
        options = cfg.options(section)
        options.sort()
        for option in options:
            value = get_config(section, option)
            print "[%s] %s = %s" % (section, option, value)
        print


# -----------------------------------------------------------------------------

if __name__ == '__main__':

    def usage():
	print '''
    -d generate default config file
    -h help
    '''
    try:
	opts, args = getopt.getopt(sys.argv[1:], "dh", ["defaults", "help"])
    except getopt.GetoptError:
	# print help information and exit:
	usage()
	sys.exit(2)

    do_dump_defaults = False
    for o, a in opts:
	if o in ("-d", "--defaults"):
            do_dump_defaults = True

	if o in ("-h", "--help"):
	    usage()
	    sys.exit()

    if do_dump_defaults:
        dump_defaults(defaults)

else:
    config_init()
