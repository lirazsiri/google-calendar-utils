#!/usr/bin/python
#
# Copyright (c) 2015 Liraz Siri <liraz@turnkeylinux.org>
#
# Ths program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
"""
Read list of events from stdin and insert those that don't already exist

Options:

    --simulate          Show which events would have been inserted, but don't insert
    --creds=PATH        Where to load/save OAuth2 credentials
                        Defaults: ~/.config/google-calendar-dump.dat

Example usage:


    cat calendar-dump | google-calendar-insert --simulate myemail@gmail.com
    cat calendar-dump | google-calendar-insert myemail@gmail.com

"""

import os.path
import sys
import getopt

from api import Calendars
from utils import lines2records

import datetime
import dateutil.parser

import simplejson

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s <calendarId>"  % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

class Error(Exception):
    pass

class Options:
    credsfile = None
    simulate = False

    def __repr__(self):
        return `self.__dict__`

def parse_cli_args(args):
    options = Options()

    try:
        opts, args = getopt.gnu_getopt(args, 'h',
                                       ['simulate', 'creds='])
    except getopt.GetoptError, e:
        usage(e)

    for opt, val in opts:
        if opt == '-h':
            usage()

        elif opt == '--creds':
            if not os.path.isfile(val):
                fatal("credentials file '%s' does not exist" % val)

            options.credsfile = val

        elif opt == '--simulate':
            options.simulate = True

    if len(args) < 1:
        usage()

    return options, args

def calendar_get_all_events(cal, calendar_id, timeMin, timeMax):

    return all_events

class Events:
    @staticmethod
    def _gettime(event):
        def _get(t):
            return t.get('dateTime', t.get('date'))

        event_start = event.get('start')
        event_end = event.get('end')

        if event_start and event_end:
            return "%s:%s" % (_get(event_start), _get(event_end))
        else:
            return None

    def __init__(self, events):
        self.byid = { event['id']: event for event in events }
        self.bytimes = {}

        for event in events:
            time = self._gettime(event)
            if not time:
                continue
            d = self.bytimes.setdefault(time, {})
            d[event['id']] = event

    def exists(self, event):
        if event['id'] in self.byid:
            return True

        event_time = self._gettime(event)
        if event_time not in self.bytimes:
            return False

        for other in self.bytimes[event_time].values():
            if other['summary'] == event['summary']:
                return True

        return False

def filter_duplicates(all_events, events):
    all_events = Events(all_events)
    for event in events:
        if all_events.exists(event):
            continue
        yield event

def parse_input(fh):
    return [ simplejson.loads(record) for record in lines2records(fh) ]

def getstartdate(event):
    event_start = event.get('start')
    if not event_start:
        return None

    time = event_start.get('dateTime', event_start.get('date'))
    return dateutil.parser.parse(time).date()

def get_events_timerange(events):
    dates = [ getstartdate(event) for event in events if getstartdate(event) ]
    date_min = min(dates)
    date_max = max(dates)

    oneday = datetime.timedelta(days=1)
    return (date_min - oneday, date_max + oneday)

def main():
    options, args = parse_cli_args(sys.argv[1:])

    if len(args) < 1:
        usage()

    calendar_id = args[0]

    inserted_events = parse_input(sys.stdin)
    timeMin, timeMax = get_events_timerange(inserted_events)

    cal = Calendars(options.credsfile)
    all_events = list(cal.iter_events(calendar_id,
                                      timeMin=timeMin,
                                      timeMax=timeMax,
                                      singleEvents=True,
                                      showDeleted=False,
                                      orderBy='startTime'))

    filtered_events = filter_duplicates(all_events, inserted_events)
    if options.simulate:
        for event in filtered_events:
            print simplejson.dumps(event, indent=True)
    else:
        for event in cal.insert_events(calendar_id, filter_duplicates(all_events, filtered_events)):
            print simplejson.dumps(event, indent=True)

if __name__=="__main__":
    main()

