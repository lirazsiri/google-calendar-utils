#!/usr/bin/env python
"""Convert a dump stream of calendar json events into a filesystem
"""
import os
import os.path
import sys
import simplejson

from utils import lines2records

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)
    print >> sys.stderr, "syntax: %s path/to/output/dir" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def main():

    args = sys.argv[1:]
    if not args:
        usage()

    outputdir = args[0]

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    for event in lines2records(sys.stdin):
        event = simplejson.loads(event)
        path = os.path.join(outputdir, event['id'])
        assert os.path.dirname(path) == outputdir

        print >> file(path, 'w'), simplejson.dumps(event, indent=True)

if __name__ == "__main__":
    main()
