'''Read a Smoothed Raster Cell Font definition file and glyph graphics;
   process data and pack into a file for Geeda's SHE'''

import array
import itertools
import pickle
import os
import sys
import zlib

import png


class _CaptureEq:
    def __init__(self, obj):
        self.obj = obj
        self.match = obj

    def __eq__(self, other):
        result = (self.obj == other)
        if result:
            self.match = other
        return result

    def __getattr__(self, name):
        return getattr(self.obj, name)



def common_object(item):
    global common_strings
    global common_tuples
    if isinstance(item, str):
        item = item.decode('ascii', 'replace')
        try:
            container = common_strings
            #print "Selecting existing common strings set"
        except NameError:
            common_strings = {item}
            #print "Initializing common strings set with this item"
            return item
    elif isinstance(item, unicode):
        try:
            container = common_strings
            #print "Selecting existing common strings set"
        except NameError:
            common_strings = {item}
            #print "Initializing common strings set with this item"
            return item
    elif isinstance(item, tuple):
        try:
            container = common_tuples
            #print "Selecting existing common tuples set"
        except NameError:
            common_tuples = {item}
            #print "Initializing common tuples set with this item"
            return item
    else:
        #print "This item is not a string or a tuple."
        return item
    t = _CaptureEq(item)
    try:
        if t in container:
            #print "Item found in selected set."
            return t.match
    except TypeError:
        #print "This item contains unhashable elements."
        return item
    container |= {item}
    #print "Item added to selected set."
    return item


def dedundify(item):
    if isinstance(item, list):
        #print "Dedundifying a list..."
        newlist = []
        for subitem in item:
            newlist.append(dedundify(subitem))
            subitem = None
        #print "End of list."
        return item
    elif isinstance(item, set):
        #print "Dedundifying a set..."
        newset = set()
        for subitem in item:
            newset |= {dedundify(subitem)}
            subitem = None
        #print "End of set."
        return newset
    elif isinstance(item, dict):
        #print "Dedundifying a dict..."
        newdict = {}
        for key in item:
            #print "Key " + str(key) + ":"
            newdict[common_object(key)] = dedundify(item[key])
            item[key] = None
        #print "End of dict."
        return newdict
    elif isinstance(item, tuple):
        #print "Dedundifying a tuple..."
        tlist = []
        for subitem in item:
            subitem = dedundify(subitem)
            tlist.append(subitem)
            subitem = None
        #print "End of tuple."
        return common_object(tuple(tlist))
    #print "Singleton " + str(item)
    return common_object(item)


def rspecdecode(rspec):
    ss, h, es = rspec.partition('-')
    if h == '-':
        s = int(ss, 16)
        e = int(es, 16) + 1
        return xrange(s, e)
    if ss.endswith('*'):
        s = int(ss.rstrip('*'), 16)
        return itertools.repeat(s)
    s = int(ss, 16)
    return (s, )


def tryopen(filename, filemode, extlist):
    for ext in extlist:
        try:
            return open(filename + ext, filemode)
        except IOError:
            continue
    else:
        raise IOError(
            '[Errno 2] No such file or directory: \'{:s}\''.format(filename))


arraykeys = {'ucp',
             'cflags',
             }
numkeys = {'cellwidth',
           'cellheight',
           'sflags',
           }
dictkeys = {'preset',
            'defaultpreset',
            }
multivalkeys = {'bases',
                'preset',
                'defaultpreset',
                }
defaultfkeys = ('name',
                'author',
                'license',
                'cellwidth',
                'cellheight',
                'preset',
                'defaultpreset')
defaultfvals = ('Untitled',
                '',
                '',
                8,
                16,
                {},
                None)
defaultskeys = ('name',
                'ref',
                'sflags',
                'ucp',
                'cflags',
                'graphics')
defaultsvals = ('Untitled',
                '',
                0,
                array.array('L', itertools.repeat(0, 256)),
                array.array('L', itertools.repeat(0, 256)),
                None)
srcfdefexts = ('',
               '.txt',
               '.srcfdef',
               '.srcfdef.txt')
gfxexts = ('',
           '.png')
packedsig = 'SRCF binary v1860\r\n'

progname = os.path.basename(sys.argv[0])
try:
    deffilename = sys.argv[1]
except IndexError:
    print 'Usage: {:s} deffile [outfile [-noext]]'.format(progname)
    sys.exit(1)
checkext = True
try:
    outfilename = sys.argv[2]
    if outfilename == '-noext':
        outfilename = None
        checkext = False
    elif outfilename.startswith('-'):
        print 'Warning: command line argument {:s} not understood;' \
              .format(outfilename)
        print '\tinterpreting as output file name'
except IndexError:
    outfilename = None
try:
    if sys.argv[3] == '-noext':
        checkext = False
        if '.' in outfilename:
            print 'Warning: switch -noext ignored'
            print '\t(specified output name {:s} already has an extension' \
                  .format(outfilename)
        if len(sys.argv) > 4:
            print 'Warning: command line argument(s) not understood: {:s}' \
                  .format(' '.join(sys.argv[4 : ]))
    else:
        print 'Warning: command line argument(s) not understood: {:s}' \
              .format(' '.join(sys.argv[3 : ]))
except IndexError:
    pass
try:
  with tryopen(deffilename, 'rU', srcfdefexts) as df:
    print 'Reading definition file {:s}...'.format(df.name)
    defbasepath = os.path.dirname(deffilename)
    fsig = df.readline().rstrip()
    if fsig != 'SRCF Def':
        print 'Error: SRCF Definition signature missing.'
        sys.exit(2)
    fver = int(df.readline())
    if fver > 1855:
        print 'Error: This definition file requires a newer version of {:s}' \
              .format(progname)
        sys.exit(2)
    rootdict = {}
    basesets = {}
    extsets = {}
    gpages = {}
    dictcontext = rootdict
    for asg in df:
        key, sep, valstruct = asg.rstrip().partition('=')
        if key.strip() == '':
            continue
        if key == 'END' and sep == '':
            break
        if key == 'BASESET':
            basesets[valstruct] = {}
            dictcontext = basesets[valstruct]
            dictcontext['name'] = valstruct
            continue
        if key == 'EXTSET':
            extsets[valstruct] = {}
            dictcontext = extsets[valstruct]
            dictcontext['name'] = valstruct
            continue
        if key == 'graphics':
            gpages[valstruct] = [None] * 256
        if key in arraykeys:
            if key not in dictcontext:
                dictcontext[key] = array.array('L', itertools.repeat(0, 256))
            for rangepair in valstruct.split(';'):
                kranges, sep, vranges = rangepair.partition(':')
                krange = itertools.chain(*(
                    rspecdecode(rspec)
                    for rspec in kranges.strip().split(' ')
                    ))
                vrange = itertools.chain(*(
                    rspecdecode(rspec)
                    for rspec in vranges.strip().split(' ')
                    ))
                while True:
                    try:
                        i = next(krange)
                    except StopIteration:
                        break
                    try:
                        v = next(vrange)
                    except StopIteration:
                        print 'Warning: insufficient values supplied:'
                        print '\tKeys: \'{:s}\''.format(kranges)
                        print '\tValues: \'{{:s}\''.format(vranges)
                        break
                    dictcontext[key][i] = v
        elif key in dictkeys:
            if key not in dictcontext:
                dictcontext[key] = {}
            for kvpair in valstruct.split(';'):
                k, sep, v = kvpair.partition(':')
                if key in multivalkeys:
                    v = tuple(v.strip().split(' '))
                dictcontext[key][k] = v
        elif key in numkeys:
            if key in multivalkeys:
                v = tuple(int(h, 16)
                          for h in valstruct.strip().split(' '))
            else:
                v = int(valstruct.strip(), 16)
            dictcontext[key] = v
        elif key in multivalkeys:
            dictcontext[key] = tuple(valstruct.strip().split(' '))
        else:
            dictcontext[key] = valstruct
except IOError:
    print 'Error: Failed to open definition file: {:s}'.format(deffilename)
    sys.exit(2)
fdp = None
for k in rootdict['defaultpreset']:
    fdp = rootdict['defaultpreset'][k]
    break
if 'preset' not in rootdict:
    rootdict['preset'] = {}
try:
    rootdict['preset'].update(rootdict['defaultpreset'])
    del rootdict['defaultpreset']
except KeyError:
    pass
rootdict['defaultpreset'] = fdp
rootdict[0] = tuple(rootdict.get(k, v)
                    for k, v in itertools.izip(
                        defaultfkeys, defaultfvals))
for k in defaultfkeys:
    try:
        del rootdict[k]
    except KeyError:
        pass
basesets = {basesets[k]['ref']: basesets[k]
            for k in basesets}
extsets = {extsets[k]['ref']: extsets[k]
           for k in extsets}
for k in basesets:
    s = basesets[k]
    s[0] = tuple(s.get(k, v)
                 for k, v in itertools.izip(
                     defaultskeys, defaultsvals))
    for k in defaultskeys:
        try:
            del s[k]
        except KeyError:
            pass
for k in extsets:
    s = extsets[k]
    s[0] = tuple(s.get(k, v)
                 for k, v in itertools.izip(
                     defaultskeys, defaultsvals))
    for k in defaultskeys:
        try:
            del s[k]
        except KeyError:
            pass
rootdict = dedundify(rootdict)
basesets = dedundify(basesets)
extsets = dedundify(extsets)
gpages = dedundify(gpages)
fcw = rootdict[0][3] * 3
fch = rootdict[0][4]
dskernel = [((x - 2, 1),
             (x - 1, 2),
             (x,     3),
             (x + 1, 2),
             (x + 2, 1))
            for x in xrange(fcw)]
dskernel[0] = ((0, 5),
               (1, 3),
               (2, 1))
dskernel[1] = ((0, 3),
               (1, 3),
               (2, 2),
               (3, 1))
dskernel[fcw - 2] = ((fcw - 4, 1),
                     (fcw - 3, 2),
                     (fcw - 2, 3),
                     (fcw - 1, 3))
dskernel[fcw - 1] = ((fcw - 3, 1),
                     (fcw - 2, 3),
                     (fcw - 1, 5))
for s in (  [basesets[k] for k in basesets]
          + [extsets[k] for k in extsets]):
    gp = gpages[s[0][5]]
    for c in xrange(256):
        if s[0][4][c] & 0x10:
            gp[c] = s[0][4][c] & 0x7ffff00
warnsonienable = True
for gsource in gpages:
  gfxfilename = os.path.join(defbasepath, gsource)
  gp = gpages[gsource]
  try:
   with tryopen(gfxfilename, 'rb', gfxexts) as gf:
    print 'Loading graphics file {:s}...'.format(gf.name)
    gfw, gfh, gfp, gfm = png.Reader(file=gf).read()
    gfp = iter(gfp)
    gfncol = gfw // fcw
    c = 0
    gfc = 0
    while c < 256:
        try:
            pix = [[1 if p > 0 else 0
                    for p in next(gfp)]
                   for y in xrange(fch)]
        except StopIteration:
            print 'Warning: too few rows in graphics source file'
            break
        while c < 256:
            gfsc = gfc * fcw
            if gp[c] is not None:
                if gp[c] & 0x1000000 and warnsonienable:
                    print 'Warning: smoothing override not implemented.'
                    warnsonienable = False
                gp[c] = array.array('B', itertools.repeat(0, fcw * fch))
                cp = 0
                for y in xrange(fch):
                    for x in xrange(fcw):
                        v = 0
                        for sx, m in dskernel[x]:
                            v += pix[y][sx + gfsc] * m
                        gp[c][cp] = v
                        cp += 1
            c += 1
            gfc += 1
            if gfc >= gfncol:
                gfc = 0
                break
    del pix
    del gfp
  except IOError:
    print 'Warning: failed to open graphics file {:s}'.format(gsource)
  except png.FormatError:
    print 'Warning: graphics file {:s} is not a valid PNG image file' \
          .format(gsource)
    gp[ : ] = [None] * 256
#print rootdict
#print basesets
#print extsets
#print gpages
if outfilename is None:
    outfilename = rootdict[0][0].lower() \
                  + ('.srcf' if checkext else '')
    checkext = False
if checkext and (not '.' in os.path.basename(outfilename.lower())):
    outfilename = outfilename + '.srcf'
try:
    with open(outfilename, 'wb') as ff:
        print 'Writing {:s}...'.format(outfilename)
        ff.write(packedsig)
        ff.write(
            zlib.compress(
                pickle.dumps(
                    (rootdict,
                     basesets,
                     extsets,
                     gpages),
                    -1),
                9))
except IOError:
    print 'Error: Failed to write to file {:s}'.format(outfilename)
    sys.exit(2)
