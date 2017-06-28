#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU GPL v3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# https://github.com/sz-blacky/nagios-plugins
# check_burp_backup_ages
# check_burp_backup_ages: Local check, Check freshness of last backups on
# a burp server

# Based on check_burp_backup_age by Régi Leroy (regilero)
# https://github.com/regilero/check_burp_backup_age

import sys
import os
import argparse
import time
import datetime


class CheckBurp(object):

    def __init__(self):
        self._program = "check_burp_backup_ages"
        self._version = "1.0"
        self._author = "Márton Szigeti (sz-blacky)"
        self._nick = "BURP"
        self._ok = 0
        self._warning = 1
        self._critical = 2
        self._unknown = 3
        self._pending = 4
        self.args = None
        self.diff_min = None
        self.criticals = []
        self.warnings = []
        self.unknowns = []
        self.oks = []

    def critical_bail(self, msg):
        print '{0} CRITICAL - {1}'.format(self._nick, msg)
        sys.exit(self._critical)

    def critical(self, msg, sort_key):
	    self.criticals.append(Message('{0} CRITICAL - {1}'.format(self._nick, msg), sort_key))

    def warning(self, msg, sort_key):
	    self.warnings.append(Message('{0} WARNING - {1}'.format(self._nick, msg), sort_key))

    def unknown(self, msg, sort_key):
	    self.unknowns.append(Message('{0} UNKNOWN - {1}'.format(self._nick, msg), sort_key))
        
    def ok(self, msg, sort_key):
	    self.oks.append(Message('{0} OK - {1}'.format(self._nick, msg), sort_key))

    def opt_parser(self):
        parser = argparse.ArgumentParser(
            prog=self._program,
            description=("Local check, Check freshness of last backups.\n\n"
                         "Running on the backup server "
                         "this program will check the timestamp file of the "
                         "last backups for all hosts and get the age of these"
                         " last successful runs. These ages are then compared to "
                         "thresolds to generate alerts."),
            epilog=("Note that this is a local check, running on the backup "
                    "server.\nSo the hostname argument is not used to perform"
                    " any distant connection.\n"))
        parser.add_argument('-v', '--version',
                            version='%(prog)s {0}'.format(self._version),
                            action='version', help='show program version')
        parser.add_argument('-d', '--directory', default='/backups', nargs='?',
                            help=('base directory path for backups (where are '
                                  'the backups?) [default: %(default)s]'))
        parser.add_argument('-w', '--warning', default=1560, const=1560,
                            type=int, nargs='?',
                            help=('Warning thresold, time in minutes before '
                                  'going to warning [default: %(default)s]'))
        parser.add_argument('-c', '--critical', default=1800, const=1800,
                            type=int, nargs='?',
                            help=('Critical thresold, time in minutes before '
                                  'going to critical [default: %(default)s]'))

        self.args = vars(parser.parse_args())

        if self.args['warning'] >= self.args['critical']:
            self.unknown(('Warning thresold ({0}) should be lower than the '
                          'critical one ({1})').format(self.args['warning'],
                                                       self.args['critical']))

    def test_backup_dir(self):
        if not os.path.isdir(self.args['directory']):
            self.critical_bail(('Base backup directory {0}'
                           ' does not exists').format(self.args['directory']))

    def check_backup_timestamp(self, hostname):
        bckpdir = self.args['directory'] + '/' + hostname
        bckpdircur = bckpdir + '/current'
        ftimestamp = bckpdircur + '/timestamp'
        if not os.path.isdir(bckpdir):
            self.critical(('Host backup directory {0}'
                           ' does not exists').format(bckpdir), sys.maxint)
            return
        if not os.path.isdir(bckpdircur):
            self.critical(('Current Host backup directory {0}'
                           ' does not exists').format(bckpdircur), sys.maxint)
            return
        if not os.path.isfile(ftimestamp):
            self.critical(('timestamp file '
                           'does not exists ({0})').format(ftimestamp), sys.maxint)
            return
        lines = []
        with open(ftimestamp) as f:
            lines = f.readlines()

        if not len(lines):
            self.critical(('timestamp file seems'
                           ' to be empty ({0})').format(ftimestamp), sys.maxint)

        tline = lines.pop()
        parts = tline.split()
        if not 3 == len(parts):
            self.critical(('invalid syntax in '
                           'timestamp file ({0})').format(ftimestamp), sys.maxint)

        btime = time.strptime(parts[1] + ' ' + parts[2], "%Y-%m-%d %H:%M:%S")
        btime = datetime.datetime(*btime[:6])
        ctime = time.localtime()
        ctime = datetime.datetime(*ctime[:6])
        diff = ctime-btime
        diff_min = int((diff.seconds + (diff.days * 24 * 3600))/60)
        diff_human = ('{0} day(s) {1:02d} hour(s) {2:02d} '
                           'minute(s)').format(diff.days,
                                               diff.seconds//3600,
                                               (diff.seconds//60) % 60)
        if diff_min >= self.args['warning']:
            if diff_min >= self.args['critical']:
                self.critical(('Last backup of {0} is too old: '
                               '{1} ({2}>={3})').format(hostname,
                                                        diff_human,
                                                        diff_min,
                                                        self.args['critical']), diff.total_seconds())
            else:
                self.warning(('Last backup of {0} starts to get old: '
                              '{1} ({2}>={3})').format(hostname,
                                                       diff_human,
                                                       diff_min,
                                                       self.args['warning']), diff.total_seconds())
        else:
            self.ok(('Last backup of {0} is fresh enough: '
                     '{1} ({2}<{3})').format(hostname,
                                             diff_human,
                                             diff_min,
                                             self.args['warning']), diff.total_seconds())

    def run(self):
        self.opt_parser()
        self.test_backup_dir()
        dirs = os.listdir(self.args['directory'])
        if len(dirs) > 0:
            for hostname in dirs:
                self.check_backup_timestamp(hostname)
        else:
            self.unknown('No backup directories found')
        for collection in [self.criticals, self.warnings, self.unknowns, self.oks]:
            collection.sort(key = lambda message: message.key, reverse = True)
            for message in collection:
                print message.message
        if len(self.criticals) > 0:
            sys.exit(self._critical)
        if len(self.warnings) > 0:
            sys.exit(self._warning)
        if len(self.unknowns) > 0:
            sys.exit(self._unknown)
        sys.exit(self._ok)

class Message:
    def __init__(self, message, sort_key):
        self.message = message
        self.key = sort_key

def main():
    try:
        check_burp = CheckBurp()
        check_burp.run()
    except Exception, e:
        print 'Unknown error UNKNOWN - {0}'.format(e)
        sys.exit(3)


if __name__ == "__main__":
    main()
