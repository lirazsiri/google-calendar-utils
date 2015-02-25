#!/usr/bin/env python
"""Convert an old pydump stream into a json stream of events"""
import sys
import simplejson
from utils import lines2records

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)
    print >> sys.stderr, "syntax: %s" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def main():

    args = sys.argv[1:]
    if args:
        usage()

    for event in lines2records(sys.stdin):
        event = eval(event)
        print simplejson.dumps(event, indent=True) + "\n"

if __name__ == "__main__":
    main()
