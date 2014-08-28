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

    --max-results=NUM   Set maximum number of results to return
                        Defaults to None (uses API default)

Example usage:

    google-calendar-dump myemail@gmail.com 2014-1-1

"""

import os
from os.path import *

import sys
import getopt

from fixedmap import FixedMap

# credentials for consumer app, not end-user

class API:
    CLIENT_ID = '202930974095-vds3f7krnef053ibmhojl2ivsqcg3n41.apps.googleusercontent.com'
    CLIENT_SECRET = 'urPmLmos5dw6wekTMfZV2O0z'

    HOME_CREDSFILE = '.config/google-calendar-dump.dat'

    @classmethod
    def _get_credentials(cls, credsfile=None):
        """get credentials stored in credsfile, or get credentials via OAuth and store in PATH"""

        from oauth2client.client import OAuth2WebServerFlow
        from oauth2client import tools
        from oauth2client.file import Storage

        if credsfile is None:
            credsfile = join(os.environ['HOME'], cls.HOME_CREDSFILE)

        flow = OAuth2WebServerFlow(client_id=cls.CLIENT_ID,
                                   client_secret=cls.CLIENT_SECRET,
                                   scope='https://www.googleapis.com/auth/calendar')

        storage = Storage(credsfile)
        credentials = storage.get()

        # workaround because we don't use argparse
        class cmd_flags:
            def __init__(self):
                self.short_url = True 
                self.noauth_local_webserver = False
                self.logging_level = 'ERROR' 
                self.auth_host_name = 'localhost'
                self.auth_host_port = [8080, 9090]

        if credentials is None or credentials.invalid == True:
            credentials = tools.run_flow(flow, storage, flags=cmd_flags())

        return credentials

    @classmethod
    def get_service(cls, credsfile=None):
        """return service API"""

        import httplib2
        from apiclient.discovery import build

        # Create an httplib2.Http object to handle our HTTP requests and authorize it
        # with our good Credentials.
        credentials = cls._get_credentials(credsfile)

        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build(serviceName='calendar', version='v3', http=http)

        return service
    
class Map(FixedMap):
    """Like Map except it allows missing values in kws"""

    def __init__(self, **kws):

        defaults = dict([ (field, None) for field in self.FIELDS ])
        defaults.update(kws)

        FixedMap.__init__(self, **defaults)

class Calendars:

    class Calendar(Map):
        FIELDS = ['id', 'summary', 'description', 'accessRole']

        def __init___(self, **kws):

            for field in FIELDS:
                self[field] = None

            FixedMap.__init__(self, *args, **kws)

    def __init__(self, credsfile=None):
        self.service = API.get_service(credsfile)

    def iter_calendars(self):

        cl = self.service.calendarList()

        nextpage = None
        while True:

            request = cl.list(fields='items(accessRole,description,id,summary,summaryOverride),nextPageToken', 
                              showDeleted=False,
                              pageToken=nextpage)

            response = request.execute()

            items = response.get('items')
            if items:
                for item in response['items']:
                    yield self.Calendar(**item)

            nextpage = response.get('nextPageToken')
            if not nextpage:
                break

    @property
    def calendars(self):
        return list(self.iter_calendars())
    
def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s --list-calendars" % sys.argv[0]
    print >> sys.stderr, "List calendar Ids\n"

    print >> sys.stderr, "Syntax: %s <calendarId> [ <since-date> <until-date> ]" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def _dump_calendar(calendar, credsfile, max_results=None):
    

    service = get_service(credsfile)
    events = service.events()

    request = events.list(
        calendarId='liraz.siri2@gmail.com', 
        timeMin='2014-08-21T00:00:00Z',
        timeMax='2014-08-22T00:00:00Z',
        singleEvents=True, 
        orderBy='startTime', 
        fields='nextPageToken,items(colorId,start,end,start,summary)')

    print request.execute()

def dump_calendar(calendar, credsfile, since=None, until=None, max_results=None):
    print `(calendar, credsfile, since, until, max_results)`

def parse_date(s):
    pass

def main():
    max_results = None
    credsfile = None

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h', 
                                       ['list-calendars', 'creds=', 'max-results='])
    except getopt.GetoptError, e:
        usage(e)

    opt_list_calendars = False

    for opt, val in opts:
        if opt == '-h':
            usage()

        elif opt == '--creds':
            if not isfile(val):
                fatal("credentials file '%s' does not exist" % val)

            credsfile = val

        elif opt == '--max-results':
            try:
                max_results = int(val)
            except ValueError:
                fatal("illegal max-results value '%s'" % val)

        if opt == '--list-calendars':
            opt_list_calendars = True

    if opt_list_calendars:
        if args:
            usage('--list-calendars accepts no arguments')

        for calendar in Calendars(credsfile).calendars:
            print "%-65s %s" % (calendar.id, calendar.summary)

        sys.exit(0)
            
    if len(args) < 1:
        usage()

    calendar = args[0]

    try:
        if len(args) > 1:
            since = parse_date(args[1])

        if len(args) > 2:
            until = parse_date(args[2])

    except Error, e:
        fatal(e)

    api = API(credsfile)
    dump_calendar(api, calendar, since=since, until=until, max_results=max_results)

if __name__=="__main__":
    main()

