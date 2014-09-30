#!/usr/bin/python
#
# Copyright (c) 2014 Liraz Siri <liraz@turnkeylinux.org>
#
# Ths program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
"""Options:

    --simulate          Show which changes would be made, but don't edit
    --edit              Edit events that have changed

    --creds=PATH        Where to load/save OAuth2 credentials
                        Defaults: ~/.config/google-calendar-dump.dat

Example usage:

    google-calendar-events myemail@gmail.com 2014-1-1 2014-1-8 > events.txt
    sed -i 's/foo/bar/' events.txt
    cat events.txt | google-calendar-events --edit myemail@gmail.com 2014-1-1 2014-1-8

"""

import os.path
import sys
import getopt
import re

import dateutil.parser

from api import Calendars
from StringIO import StringIO

from fixedmap import FixedMap
import string

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s <calendarId> --edit <calendarId> <since-date> <until-date>"  % sys.argv[0]
    print >> sys.stderr, "Read list of events from stdin and edit those that have changed"
    print >> sys.stderr

    print >> sys.stderr, "Syntax: %s <calendarId> <since-date> <until-date>" % sys.argv[0]
    print >> sys.stderr, "Print list of events for manual editing"
    print >> sys.stderr
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def parse_date(s):
    return dateutil.parser.parse(s).date()

def fmt_date(date):
    return date.isoformat() + "T00:00:00Z"

class Error(Exception):
    pass

class EventLog:
    class Tuple(FixedMap):
        FIELDS = ['id', 'colorId', 'summary']

        @classmethod
        def from_resource(cls, res):
            summary = filter(lambda c: c in string.printable, res['summary']).strip()
            return cls(res['id'], res.get('colorId', '0'), summary)

        def to_resource(self):
            d = self.copy()
            d['colorId'] = self.colorId if self.colorId != '0' else None
            return d

    @staticmethod
    def fmt(arg):
        def fmt_event(resource):
            elt = EventLog.Tuple.from_resource(resource)

            args = elt.copy()
            args['start'] = resource['start'].get('dateTime') or resource['start'].get('date')

            return "%(id)s %(start)s :: C=%(colorId)s S=%(summary)s" % args

        if isinstance(arg, dict):
            return fmt_event(arg)

        sio = StringIO()
        for resource in arg:
            print >> sio, fmt_event(resource)
        return sio.getvalue()

    @staticmethod
    def parse(log):
        for line in log.splitlines():
            m = re.match(r'(\S+)\s.*:: C=(\S+) S=(.*)', line)
            if not m:
                continue

            id, colorId, summary = m.groups()
            yield EventLog.Tuple(id, colorId, summary)

    @staticmethod
    def changed(orig, edited):
        orig = dict([ (elt.id, elt) for elt in orig ])
        changed = []
        for edit in edited:
            if edit.id not in orig or edit != orig[edit.id]:
                changed.append(edit)

        return changed

class Options:
    credsfile = None
    simulate = False
    edit = False

    def __repr__(self):
        return `self.__dict__`

def parse_cli_args(args):
    options = Options()

    try:
        opts, args = getopt.gnu_getopt(args, 'h',
                                       ['simulate', 'edit', 'creds='])
    except getopt.GetoptError, e:
        usage(e)

    for opt, val in opts:
        if opt == '-h':
            usage()

        elif opt == '--edit':
            options.edit = True

        elif opt == '--creds':
            if not os.path.isfile(val):
                fatal("credentials file '%s' does not exist" % val)

            options.credsfile = val

        elif opt == '--simulate':
            options.simulate = True

    if len(args) < 3:
        usage()

    return options, args

def main():
    options, args = parse_cli_args(sys.argv[1:])

    if len(args) < 3:
        usage()

    calendar_id = args[0]
    since = parse_date(args[1])
    until = parse_date(args[2])

    cal = Calendars(options.credsfile)
    cal_events = list(cal.iter_events(calendar_id, timeMin=since,
                                                   timeMax=until,
                                                   singleEvents=True,
                                                   showDeleted=False,
                                                   orderBy='startTime'))

    if options.edit:
        edited_events = EventLog.parse(sys.stdin.read())
        orig_events = [ EventLog.Tuple.from_resource(cal_event) for cal_event in cal_events ]

        changed = EventLog.changed(orig_events, edited_events)

        if options.simulate:
            for change in changed:
                print change
        else:
            edited = cal.patch_events(calendar_id, [ change.to_resource() for change in changed ])
            for edit in edited:
                print EventLog.fmt(edit)

    else:
        print EventLog.fmt(cal_events)

if __name__=="__main__":
    main()

