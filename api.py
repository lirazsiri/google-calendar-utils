import os
from os.path import join
from fixedmap import FixedMap
import datetime

# credentials for consumer app, not end-user

class Map(FixedMap):
    """Like Map except it allows missing values in kws"""

    def __init__(self, **kws):

        defaults = dict([ (field, None) for field in self.FIELDS ])
        defaults.update(kws)

        FixedMap.__init__(self, **defaults)

class Calendars:
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

    class Calendar(Map):
        FIELDS = ['id', 'summary', 'description', 'accessRole']

    def __init__(self, credsfile=None):
        self.service = self.API.get_service(credsfile)

    @property
    def calendars(self):
        return list(self.iter_calendars())

    @staticmethod
    def fmt_values(keywords):
        keywords = keywords.copy()

        for k, v in keywords.items():
            if v is None:
                del keywords[k]

            if isinstance(v, datetime.date):
                keywords[k] = v.isoformat() + 'T00:00:00Z'

        return keywords

    @staticmethod
    def _iter_items(callback, **kwargs):
        nextPageToken = None
        while True:

            request = callback(pageToken=nextPageToken, **kwargs)
            response = request.execute()

            items = response.get('items')
            if items:
                for item in response['items']:
                    yield item

            nextPageToken = response.get('nextPageToken')
            if not nextPageToken:
                break

    def iter_events(self, calendar_id, **kws):

        events = self.service.events() # pylint: disable=E1101
        kws = self.fmt_values(kws)

        if 'maxResults' not in kws:
            kws['maxResults'] = 2500

        return self._iter_items(events.list,
                                calendarId=calendar_id, **kws)

    def iter_calendars(self):
        cl = self.service.calendarList() # pylint: disable=E1101

        for item in self._iter_items(cl.list,
                                     fields='items(accessRole,description,id,summary,summaryOverride),nextPageToken',
                                     showDeleted=False):
            yield self.Calendar(**item)


