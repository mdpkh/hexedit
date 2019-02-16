major = '1'
minor = 'a'
#the following two lines are updated programmatically
#to update, run this file with 'update' as its command line argument
build = '1912'
cryear = '19'

if __name__ != '__main__':
    aboutstring = {
        'title': u'Geeda\'s Simple Hex Editor',
        'version': u'{:s}.{:s}.{:s}'
            .format(major, minor, build),
        'copyright': u'\xa92018-{:s} Maggie\u202fDavid P.\u202fK. Haynes'
            .format(cryear),
        'crhilite': u'gie da',
        'license': u'all rights reserved (for now\u2026)'}
else:
    import sys
    if len(sys.argv) <= 1 or sys.argv[1] != 'update':
        print 'Import this module or run it with argument \'update\'.'
        sys.exit(0)
    import datetime
    now = datetime.datetime.utcnow()
    if now.year < 2000:
        print 'Stop messing around with the system time!'
        sys.exit(1)
    if now.year > 2099:
        print 'Date code is defined only for 21st century.'
        sys.exit(1)
    cryear = '{:02d}'.format(now.year - 2000)
    dc = '{:s}{:02d}'.format(cryear, ((now.month - 1) << 3) | (now.day >> 2))
    bpd, dot, bpm = build.partition('.')
    if dc > bpd:
        bpd = dc
        dot = ''
        bpm = ''
    else:
        dot = '.'
        try:
            m = int(bpm)
        except ValueError:
            m = 0
        bpm = '{:d}'.format(m + 1)
    build = bpd + dot + bpm

    outcode = []
    if not __file__.endswith('.py'):
        print 'Expect my own filename to end in .py; aborting!'
        sys.exit(8)
    try:
        code = list(open(__file__, 'r'))
    except IOError:
        print 'Failed to open source code file!'
        sys.exit(2)
    nlines = len(code)
    bline = None
    status = 192
    for i in xrange(nlines):
        if code[i].startswith('build'):
            code[i] = 'build = {:s}\n'.format(repr(build))
            status &= ~64
            break
    for i in xrange(i, nlines):
        if code[i].startswith('cryear'):
            code[i] = 'cryear = {:s}\n'.format(repr(cryear))
            status &= ~128
            break
    try:
        open(__file__, 'w').writelines(code)
    except IOError:
        print 'Failed to rewrite source code file!'
        sys.exit(4)
    if status & 64:
        print 'Warning: did not find build variable assignment line!'
    if status & 128:
        print 'Warning: did not find cryear variable assignment line!'
    sys.exit(status)
