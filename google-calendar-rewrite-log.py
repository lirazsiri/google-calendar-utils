#!/usr/bin/python
#
# Copyright (c) 2014 Liraz Siri <liraz@turnkeylinux.org>
#
# Ths program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
"""Dump a google calendar
Options:

    --creds=PATH        Where to load/save OAuth2 credentials
                        Defaults: ~/.config/google-calendar-dump.dat

Example usage:

    google-calendar-rewrite-log myemail@gmail.com 2014-1-1

"""

import os.path
import sys
import getopt

import pprint
import dateutil.parser

from api import Calendars

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s" % sys.argv[0]
    print >> sys.stderr, "List calendar Ids\n"

    print >> sys.stderr, "Syntax: %s <calendarId> [ <since-date> <until-date> ]" % sys.argv[0]
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

def fmt_event(event):
    args = {}
    for key in ('id', 'summary'):
        args[key] = event[key]

    args['colorId'] = event.get('colorId', '0')

    start = event['start']
    args['start'] = start.get('dateTime') or start.get('date')

    return "%(id)s %(start)s :: C=%(colorId)s S=%(summary)s" % args

def main():
    credsfile = None

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h',
                                       ['creds='])
    except getopt.GetoptError, e:
        usage(e)

    for opt, val in opts:
        if opt == '-h':
            usage()

        elif opt == '--creds':
            if not os.path.isfile(val):
                fatal("credentials file '%s' does not exist" % val)

            credsfile = val

    if len(args) < 1:
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

    for event in Calendars(credsfile).iter_events(calendar_id,
                                                  timeMin=since,
                                                  timeMax=until,
                                                  singleEvents=True,
                                                  showDeleted=False,
                                                  orderBy='startTime'):

        print fmt_event(event)

if __name__=="__main__":
    main()

