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

from collections import namedtuple

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
    Tuple = namedtuple('Event', ['id', 'colorId', 'summary'])
    Tuple.from_resource = classmethod(lambda cls, res: cls(res['id'],
                                                           res.get('colorId', '0'),
                                                           res['summary']))

    @staticmethod
    def fmt(resources):
        def fmt_event(resource):
            elt = EventLog.Tuple.from_resource(resource)

            args = elt.__dict__.copy()
            args['start'] = resource['start'].get('dateTime') or resource['start'].get('date')

            return "%(id)s %(start)s :: C=%(colorId)s S=%(summary)s" % args

        sio = StringIO()
        for resource in resources:
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

def main():
    credsfile = None
    opt_edit = False

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h',
                                       ['edit', 'creds='])
    except getopt.GetoptError, e:
        usage(e)

    for opt, val in opts:
        if opt == '-h':
            usage()

        elif opt == '--edit':
            opt_edit = True

        elif opt == '--creds':
            if not os.path.isfile(val):
                fatal("credentials file '%s' does not exist" % val)

            credsfile = val

    if len(args) < 3:
        usage()

    calendar_id = args[0]

    since = until = None
    try:
        if len(args) > 1:
            since = parse_date(args[1])

        if len(args) > 2:
            until = parse_date(args[2])

    except Error, e:
        fatal(e)

    cal = Calendars(credsfile)

    events = list(cal.iter_events(calendar_id, timeMin=since,
                                  timeMax=until,
                                  singleEvents=True,
                                  showDeleted=False,
                                  orderBy='startTime'))

    if opt_edit:
        print list(EventLog.parse(sys.stdin.read()))
    else:
        print EventLog.fmt(events)

if __name__=="__main__":
    main()

