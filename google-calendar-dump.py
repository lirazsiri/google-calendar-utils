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
import gflags

FLAGS = gflags.FLAGS

# credentials for consumer app, not end-user
__API_CLIENT_ID__ = '202930974095-vds3f7krnef053ibmhojl2ivsqcg3n41.apps.googleusercontent.com'
__API_CLIENT_SECRET__ = 'urPmLmos5dw6wekTMfZV2O0z'

def get_credentials(path):
    """get credentials stored in path, or get credentials via OAuth and store in PATH"""

    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client.tools import run
    from oauth2client.file import Storage

    flow = OAuth2WebServerFlow(client_id=__API_CLIENT_ID__,
        client_secret=__API_CLIENT_SECRET__,
        scope='https://www.googleapis.com/auth/calendar')

    storage = Storage(path)
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
        credentials = run(flow, storage)

    return credentials

def get_service(credentials):
    """return service API"""

    import httplib2
    from apiclient.discovery import build

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build(serviceName='calendar', version='v3', http=http)

    return service
    
def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s <calendarId> [ <since-date> <until-date> ]" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def __main():
    creds = get_credentials('calendar.dat')
    service = get_service(creds)
    events = service.events()

    request = events.list(
        calendarId='liraz.siri2@gmail.com', 
        timeMin='2014-08-21T00:00:00Z',
        timeMax='2014-08-22T00:00:00Z',
        singleEvents=True, 
        orderBy='startTime', 
        fields='nextPageToken,items(colorId,start,end,start,summary)')

    print request.execute()

def main():

    max_results = None
    credsfile = join(os.environ['HOME'], '.config/google-calendar.dat')

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h', ['creds=', 'max-results='])
    except getopt.GetoptError, e:
        usage(e)

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

    if len(args) < 1:
        usage()

    calendar = args[0]

    if len(args) > 1:
        sincedate = args[1]

    if len(args) > 2:
        untildate = args[2]

    print "args: " + `args`
        
    print

    print `calendar`
    print `credsfile`
    print `max_results`

if __name__=="__main__":
    main()

