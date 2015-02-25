from cStringIO import StringIO

def lines2records(fh, isnewrecord=lambda l: l.startswith("{")):
    """Parse stream of lines into stream of records.
    A new record starts when isnewrecord returns True"""

    sio = StringIO()

    def fmt(sio):
        return sio.getvalue().strip()

    for line in fh.readlines():
        if isnewrecord(line):
            record = fmt(sio)
            if record:
                yield record
                sio.reset()
                sio.truncate()

        sio.write(line)

    yield fmt(sio)

