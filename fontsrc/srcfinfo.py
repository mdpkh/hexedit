import pickle, zlib


def getmeta(partialdata, allstrings=False):
    #insert newer signature check blocks at top
    if partialdata.startswith('SRCF binary v1860\r\n'):
        s = []
        expectedlen = None
        for f in zlib.decompressobj() \
                    .decompress(partialdata[19 :]) \
                    .split('\x00\x00\x00'):
            if expectedlen is not None:
                s.append(f[: expectedlen])
                if 'K\n' in f[expectedlen :] and not allstrings:
                    break
            expectedlen = ord(f[-1])
    return s


if __name__ == '__main__':
    import sys
    try:
        fname = sys.argv[1]
    except IndexError:
        print 'Please name a file to scan.'
        sys.exit(1)
    try:
        loadlen = sys.argv[2]
    except IndexError:
        loadlen = '512'
    try:
        loadlen = int(loadlen)
    except ValueError:
        print  'Scan length not understood as integer.'
        sys.exit(1)
    if loadlen < 122:
        print 'At least 122 bytes must be scanned to extract any metadata.'
        sys.exit(1)
    allstrings = True
    try:
        maxcount = sys.argv[3]
    except IndexError:
        maxcount = '3'
        allstrings = False
    try:
        maxcount = int(maxcount)
    except ValueError:
        print  'Max string count not understood as integer.'
        sys.exit(1)
    if maxcount < 1:
        print 'Surely you must want at least one metadata string.'
        maxcount = loadlen
    with open(fname, 'rb') as f:
        d = f.read(loadlen)
    d = getmeta(d, allstrings)
    if len(d) == 0:
        print 'No metadata recovered.'
        sys.exit(0)
    for s in d[: maxcount]:
        print s
    sys.exit(1)
