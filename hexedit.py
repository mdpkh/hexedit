'''                     Geeda's Simple Hex Editor
Copyright Maggie David P.K. Haynes
A simple hex editor with a visual style inspired by the MS-DOS utility LIST.
'''

import array
import collections
import ctypes
from heapq import heapify, heappop, heappush, heappushpop, heapreplace
import itertools
import os, os.path
import pickle
import sys
import time
import zlib

import sdl2, sdl2.ext

import scrbuf
from version import aboutstring


fallbacks = {u'\xa0':   (u' ',),
             u'\xa9':   (u'(c)',),
             u'\u2009': (u' ',),
             u'\u2026': (u'...',),
             u'\u202f': (u'\u2009', u'\xa0', u' '),
             u'\u2190': (u'<',),
             u'\u2192': (u'>',),
             u'\u25ba': (u'\u2192',u'>'),
             u'\u25b2': (u'\u2191',),
             u'\u25bc': (u'\u2193',),
             u'\u25c4': (u'\u2190',u'<'),
             }
namedencodings = {}
cellcolors = {0x00: (0, ( 7,  6,  3,  2,  8)),
              0x10: (0, (15, 14, 11, 10,  7)),
              0x20: (0, ( 8,  8,  8,  8,  8)),
              0x01: (1, ( 7,  6,  3,  2,  9)),
              0x11: (1, (15, 14, 11, 10,  9)),
              0x21: (1, ( 9,  9,  9,  9,  9)),
              0x03: (3, ( 0,  6,  1,  5,  8)),
              0x23: (3, ( 8,  8,  8,  8,  8)),
              0x04: (4, ( 7,  2,  9,  3, 12)),
              0x14: (4, (15, 10,  9, 11,  7)),
              0x24: (4, (12, 12, 12, 12, 12)),
              0x06: (6, ( 0,  1,  4,  1,  8)),
              0x26: (6, ( 8,  8,  8,  8,  8)),
              0x07: (7, ( 0,  6,  1,  5,  8)),
              0x27: (7, ( 8,  8,  8,  8,  8)),
              }
attalias = [ 0,  1,  3,  3,  4,  4,  6,  7, 32, 33,  3,  3, 20, 20,  6, 16,
            16, 17,  3,  3, 20, 20,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
             0,  1,  3,  3,  4,  4,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            16, 17,  3,  3, 20, 20,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
             0,  1,  3,  3,  4,  4,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            16, 17,  3,  3, 20, 20,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
             0,  1,  3,  3,  4,  4,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            16, 17,  3,  3, 20, 20,  6,  7, 16, 17,  3,  3, 20, 20,  6,  7,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39,
            32, 33, 35, 35, 36, 36, 38, 39, 32, 33, 35, 35, 36, 36, 38, 39]
ibmcolors = [0x00, 0x02, 0x08, 0x0a,
             0x20, 0x22, 0x24, 0x2a,
             0x15, 0x17, 0x1d, 0x1f,
             0x35, 0x37, 0x3d, 0x3f]
colormix = (((  0,   0,   0,   0,   0,   0,   0,   0,   0,   0),
             (  0,  26,  39,  49,  57,  63,  70,  75,  80,  85),
             (  0,  60,  84, 102, 117, 130, 141, 152, 161, 170),
             (  0,  94, 130, 156, 178, 197, 213, 228, 242, 255)),
            (( 85,  80,  75,  70,  63,  57,  49,  39,  26,   0),
             ( 85,  85,  85,  85,  85,  85,  85,  85,  85,  85),
             ( 85,  99, 111, 122, 132, 140, 148, 156, 163, 170),
             ( 85, 121, 147, 168, 187, 203, 217, 231, 243, 255)),
            ((170, 161, 152, 141, 130, 117, 102,  84,  60,   0),
             (170, 163, 156, 148, 140, 132, 122, 111,  99,  85),
             (170, 170, 170, 170, 170, 170, 170, 170, 170, 170),
             (170, 182, 193, 204, 213, 223, 231, 239, 247, 255)),
            ((255, 242, 228, 213, 197, 178, 156, 130,  94,   0),
             (255, 243, 231, 217, 203, 187, 168, 147, 121,  85),
             (255, 247, 239, 231, 223, 213, 204, 193, 182, 170),
             (255, 255, 255, 255, 255, 255, 255, 255, 255, 255)))
ALIGN_CENTER = 'Align Center'
ALIGN_LEFT = 'Align Left'
ALIGN_RIGHT = 'Align Right'
CTRL_BUTTON = 'Button Control'
CTRL_LABEL = 'Control Label'
LDIR_LEFT = 'Label Direction Left'
LDIR_RIGHT = 'Label Direction Right'
URESP_NO = 'User Response: No'
URESP_YES = 'User Response: Yes'
SDLX_KEYPRESS = sdl2.SDL_USEREVENT | sdl2.SDL_KEYUP | 0xF0
SDLX_MOD_KEYS = (sdl2.SDLK_LCTRL,
                 sdl2.SDLK_LSHIFT,
                 sdl2.SDLK_LALT,
                 sdl2.SDLK_LGUI,
                 sdl2.SDLK_RCTRL,
                 sdl2.SDLK_RSHIFT,
                 sdl2.SDLK_RALT,
                 sdl2.SDLK_RGUI,)
SDLX_TIMERTICK = sdl2.SDL_USEREVENT | 0xC10


class Control(object):
    def __init__(self, spanc, spanr, type, **props):
        #default properties
        self.enabled = True
        self.labeldir = None
        self.caption = unicode(type)
        if type is CTRL_BUTTON:
            self.capalign = ALIGN_CENTER
        elif type is CTRL_LABEL:
            self.capalign = ALIGN_LEFT
        else:
            self.capalign = None
        self.hotkey = None
        self.action = None
        #properties specified in keyword args
        self.__dict__.update(props)
        #properties which override keyword args
        self.type = type
        self.spanc = spanc
        self.spanr = spanr
        if isinstance(self.spanc, tuple):
            self.spanc = slice(*self.spanc)
        elif isinstance(self.spanc, int):
            self.spanc = slice(self.spanc, self.spanc + 1)
        if isinstance(self.spanr, tuple):
            self.spanr = slice(*self.spanr)
        elif isinstance(self.spanr, int):
            self.spanr = slice(self.spanr, self.spanr + 1)
        self.skipfocus = self.type in (CTRL_LABEL,
                                       )
        self.focus = False
        self.label = None
        self.rlabel = None

    def drawFocus(self, refreshscreen=True):
        if self.type is CTRL_BUTTON:
            lpad = self.lpadf if self.focus else self.lpadn
            rpad = self.rpadf if self.focus else self.rpadn
            screen.cbuf[self.spanc.start, self.spanr.start] = lpad
            screen.cbuf[self.spanc.stop - 1, self.spanr.stop - 1] = rpad
            if self.focus:
                screen.abuf[self.spanc, self.spanr] = 17
            elif self.enabled:
                screen.abuf[self.spanc, self.spanr] = 3
            else:
                screen.abuf[self.spanc, self.spanr] = 35
        elif self.type is CTRL_LABEL:
            lpad = self.lpadf if self.focus else self.lpadn
            rpad = self.rpadf if self.focus else self.rpadn
            screen.cbuf[self.spanc.start, self.spanr.start] = lpad
            screen.cbuf[self.spanc.stop - 1, self.spanr.stop - 1] = rpad
        if refreshscreen:
            screen.refresh((self.spanc, self.spanr))
            

    def drawFull(self, refreshscreen=False):
        #caption = altencode(self.caption, screen.encoding)
        if self.type is CTRL_BUTTON:
            self.lpadf = altencode(u'\u25ba'
                                   if self.labeldir is not LDIR_RIGHT
                                   else u' ', screen.encoding)
            self.lpadn = altencode(u' ', screen.encoding)
            self.rpadf = altencode(u'\u25c4'
                                   if self.labeldir is not LDIR_RIGHT
                                   else u' ', screen.encoding)
            self.rpadn = altencode(u' ', screen.encoding)
            lpad = self.lpadf if self.focus else self.lpadn
            rpad = self.rpadf if self.focus else self.rpadn
            midr = (self.spanr.start + self.spanr.stop - 1) >> 1
            xm0 = self.spanc.start + len(lpad)
            xm1 = self.spanc.stop - len(rpad)
            screen.cbuf[self.spanc.start : xm0, midr] = lpad
            screen.cbuf[xm1 : self.spanc.stop, midr] = rpad
            wraptext(self.caption, (xm0, xm1), self.spanr, self.capalign)
            if self.focus:
                screen.abuf[self.spanc, self.spanr] = 17
            elif self.enabled:
                screen.abuf[self.spanc, self.spanr] = 3
            else:
                screen.abuf[self.spanc, self.spanr] = 35
        elif self.type is CTRL_LABEL:
            self.lpadf = altencode(u'\u25ba'
                                   if self.labeldir is not LDIR_RIGHT
                                   else u' ', screen.encoding)
            self.lpadn = altencode(u' ', screen.encoding)
            self.rpadf = altencode(u'\u25c4'
                                   if self.labeldir is not LDIR_RIGHT
                                   else u' ', screen.encoding)
            self.rpadn = altencode(u' ', screen.encoding)
            lpad = self.lpadf if self.focus else self.lpadn
            rpad = self.rpadf if self.focus else self.rpadn
            mpad = altencode(u' ', screen.encoding) \
                   * ((self.spanc.stop - self.spanc.start)
                      * (self.spanr.stop - self.spanr.start)
                      - len(caption) - 2)
            lpad = altencode(lpad, screen.encoding)
            rpad = altencode(rpad, screen.encoding)
            mpad = altencode(mpad, screen.encoding)
            screen.cbuf[self.spanc, self.spanr] = (
                lpad + caption + mpad + rpad)
            screen.abuf[self.spanc, self.spanr] = 7 if self.enabled \
                                                  else 39
        if refreshscreen:
            screen.refresh((self.spanc, self.spanr))


class Form(object):
    def __init__(self, controls, inittabidx=None):
        self.controls = controls
        if inittabidx is None:
            if self.controls[0].type is CTRL_LABEL:
                self.controls[0].focus = True
                self.tabidx = 1
            else:
                self.tabidx = 0
        else:
            self.tabidx = inittabidx
        self.controls[self.tabidx].focus = True
        label = None
        for c in self.controls:
            if c.type is CTRL_LABEL:
                label = c
            elif label is not None:
                c.label = label
                label.rlabel = c
        for c in self.controls:
            c.drawFull(True)

    def ctrlActionAt(self, pos):
        tc, tr = pos
        for c in self.controls:
            if         tc in xrange(*c.spanc.indices(80)) \
                   and tr in xrange(*c.spanr.indices(25)):
                return c.action
        return None

    def ctrlActionByHotkey(self, hotkey):
        for c in self.controls:
            if c.hotkey == hotkey:
                return c.action
        return None

    def ctrlAt(self, pos):
        tc, tr = pos
        for c in self.controls:
            if         tc in xrange(*c.spanc.indices(80)) \
                   and tr in xrange(*c.spanr.indices(25)):
                return c
        return None

    def ctrlByHotkey(self, hotkey):
        for c in self.controls:
            if c.hotkey == hotkey:
                return c
        return None

    def ctrlIdxAt(self, pos):
        newtabidx = 0
        tc, tr = pos
        for c in self.controls:
            if         tc in xrange(*c.spanc.indices(80)) \
                   and tr in xrange(*c.spanr.indices(25)):
                return newtabidx
            newtabidx += 1
        return None

    def ctrlIdxByHotkey(self, hotkey):
        newtabidx = 0
        for c in self.controls:
            if c.hotkey == hotkey:
                return newtabidx
            newtabidx += 1
        return None

    def focusedAction(self):
        return self.controls[self.tabidx].action

    def focusedControl(self):
        return self.controls[self.tabidx]

    def focusNext(self):
        self.controls[self.tabidx].focus = False
        self.controls[self.tabidx].drawFocus()
        while True:
            self.tabidx += 1
            if self.tabidx >= len(self.controls):
                self.tabidx = 0
            if not self.controls[self.tabidx].skipfocus:
                break
        self.controls[self.tabidx].focus = True
        self.controls[self.tabidx].drawFocus()

    def focusPrev(self):
        self.controls[self.tabidx].focus = False
        self.controls[self.tabidx].drawFocus()
        while True:
            if self.tabidx == 0:
                self.tabidx = len(self.controls)
            self.tabidx -= 1
            if not self.controls[self.tabidx].skipfocus:
                break
        self.controls[self.tabidx].focus = True
        self.controls[self.tabidx].drawFocus()

    def setFocus(self, newtabidx):
        while self.controls[newtabidx].skipfocus:
            newtabidx += 1
            if newtabidx >= len(self.controls):
                newtabidx = 0
        if self.tabidx == newtabidx:
            return
        self.controls[self.tabidx].focus = False
        self.controls[self.tabidx].drawFocus()
        self.tabidx = newtabidx
        self.controls[self.tabidx].focus = True
        self.controls[self.tabidx].drawFocus()


KeypressEvent = collections.namedtuple('KeypressEvent',
                                       ['type',
                                        'modkeys',
                                        'keycombo'])
TimerEvent = collections.namedtuple('TimerEvent',
                                       ['type',])


def altencode(u, tenc):
    global namedencodings
    if isinstance(u, str):
        u = u.decode('ascii', 'replace')
    if isinstance(tenc, str):
        try:
            return u.encode(tenc, 'strict')
        except UnicodeEncodeError:
            pass
        if tenc not in namedencodings:
            namedencodings[tenc] = [chr(c).decode(tenc, 'replace')
                                    for c in xrange(256)]
        tenc = namedencodings[tenc]
    for f in fallbacks:
        if f not in u:
            continue
        if f in tenc:
            continue
        for r in fallbacks[f]:
            rq = True
            for c in r:
                if c not in tenc:
                    rq = False
                    break
            if rq:
                u = u.replace(f, r)
                break
    b = bytearray(itertools.repeat(0, len(u)))
    p = 0
    try:
        rc = tenc.index(u'\ufffd')
    except ValueError:
        rc = 63
    for c in u:
        try:
            b[p] = tenc.index(c)
        except ValueError:
            b[p] = rc
        p += 1
    return str(b)


def countback(start=0x7fffffff):
    x = start
    while True:
        yield x
        x -= 1

def drawdlg(spanc, spanr):
    if isinstance(spanc, int):
        x0 = spanc
        x1 = spanc + 1
    elif isinstance(spanc, tuple):
        x0, x1 = spanc
    elif isinstance(spanc, slice):
        x0, x1, step = spanc.indices(80)
    if isinstance(spanr, int):
        y0 = spanr
        y1 = spanr + 1
    elif isinstance(spanr, tuple):
        y0, y1 = spanr
    elif isinstance(spanr, slice):
        y0, y1, step = spanr.indices(80)
    x2 = x0 + 2
    x3 = x1 + 2
    y2 = y0 + 1
    y3 = y1 + 1
    area = (slice(x0, x3), slice(y0, y3))
    ra = screen.abuf[area]
    rc = screen.cbuf[area]
    screen.abuf[slice(x0, x1), slice(y0, y1)] = 7
    screen.cbuf[slice(x0, x1), slice(y0, y1)] = 32
    screen.abuf[slice(x1, x3), slice(y2, y1)] = 32
    screen.abuf[slice(x2, x3), slice(y1, y3)] = 32
    return (area, ra, rc)


def eventloop(**kwargs):
    tenable = 'tinterval' in kwargs
    if tenable:
        lastt = time.clock()
    while True:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_EXPOSED:
                    screen.refresh(((0, 0), (0, 0)))
                    continue
            elif event.type == sdl2.SDL_QUIT:
                if 'quitconfirm' in kwargs:
                    if isinstance(kwargs['quitconfirm'], tuple):
                        uresponse = kwargs['quitconfirm'][0](
                            **(kwargs['quitconfirm'][1:]))
                    else:
                        uresponse = kwargs['quitconfirm'](event)
                    if uresponse is URESP_NO:
                        continue
                yield event
                return
            yield event
        time.sleep(0.001)
        t = time.clock()
        if tenable and t > lastt + kwargs['tinterval']:
            lastt = t
            yield TimerEvent(SDLX_TIMERTICK)


def keypressfilter(events):
    modstate = 0
    keycombo = set()
    armkeyup = False
    for e in events:
        yield e
        if e.type == sdl2.SDL_KEYDOWN:
            armkeyup = True
            if e.key.keysym.sym in SDLX_MOD_KEYS:
                modstate |= e.key.keysym.sym
            else:
                if not modstate:
                    armkeyup = False
                    yield KeypressEvent(SDLX_KEYPRESS,
                                        0,
                                        {e.key.keysym.sym})
                keycombo.add(e.key.keysym.sym)
        elif e.type == sdl2.SDL_KEYUP:
            if armkeyup:
                armkeyup = False
                yield KeypressEvent(SDLX_KEYPRESS,
                                    modstate,
                                    keycombo)
            if e.key.keysym.sym in SDLX_MOD_KEYS:
                modstate &= ~e.key.keysym.sym
            else:
                keycombo.discard(e.key.keysym.sym)


def loadfont(infilename=None, sets=None):
    global screen
    global loadedfontpack
    if infilename is False and loadedfontpack is not None:
        fdata = loadedfontpack
    else:
        if not isinstance(infilename, (str, unicode)):
            infilename = prefs['font.file']
        with open(infilename, 'rb') as f:
            fdata = f.read(32)
            #insert newer version read blocks here
            if fdata.startswith('SRCF binary v1860\r\n'):
                fdata = fdata[19 :] + f.read()
                try:
                    fdata = zlib.decompress(fdata)
                except zlib.error:
                    print 'Decompression error reading {:s}'.format(infilename)
                    return
                try:
                    fdata = pickle.loads(fdata)
                except Exception:
                    print 'Error interpreting {:s}'.format(infilename)
                    return
                #perform transformation to newer version srcf data here
            else:
                print 'Signature check failed reading {:s}'.format(infilename)
                return
        #assume fdata is in up-to-data srcf format
        loadedfontpack = fdata
    rootdict, basesets, extsets, gpages = fdata
    del fdata
    #print rootdict
    if sets is None or sets == '(default)':
        sets = rootdict[0][6]
        if isinstance(sets, unicode):
            try:
                sets = rootdict[0][5][sets]
            except KeyError:
                for k in rootdict[0][5]:
                    sets = rootdict[0][5][k]
                    break
    elif isinstance(sets, (str, unicode)):
        sets = unicode(sets).split(u' ')
    #populate data with base set
    baseset = sets[0]
    sets = sets[1 :]
    try:
        baseset = basesets[baseset]
    except KeyError:
        print 'First element in charset selection is not a baseset'
        return
    cflags = baseset[0][4]
    cucp = baseset[0][3]
    if baseset[0][5] not in gpages:
        print 'Missing graphics set from font file'
        return
    gsrc = [baseset[0][5]] * 256
    #add in selected extension sets
    #TODO
    #save codepoint table
    screen.encoding = [unichr(c) for c in cucp]
    #begin drawing characters
    fcw = rootdict[0][3]
    fch = rootdict[0][4]
    pagesize = 1024 * fcw * fch
    #allocate font memory area and create surface objects if necessary
    freesurf = []
    freedsurfrepr = set()
    for a in cellcolors:
        if a not in fontmemory:
            fontmemory[a] = (ctypes.c_ulong * pagesize)()
            if screen.charsurf[a] is not None:
                freesurf.append(screen.charsurf[a])
            screen.charsurf[a] = sdl2.SDL_CreateRGBSurfaceFrom(
                ctypes.byref(fontmemory[a]),
                fcw, fch << 8,
                32,
                fcw << 2,
                0xff0000,
                0xff00,
                0xff,
                0x0)
    for s in freesurf:
        r = repr(s)
        if r in freedsurfrepr:
            continue
        sdl2.SDL_FreeSurface(s)
        freedsurfrepr.add(r)
    del freesurf
    del freedsurfrepr
    for a in xrange(256):
        if a not in cellcolors:
            screen.charsurf[a] = screen.charsurf[attalias[a]]
    if prefs['font.subpixel'] == 'rgb':
        offsetr = 0
        offsetg = 1
        offsetb = 2
    elif prefs['font.subpixel'] == 'bgr':
        offsetr = 2
        offsetg = 1
        offsetb = 0
    else:
        offsetr = 1
        offsetg = 1
        offsetb = 1
    for c in xrange(256):
        colorclass = cflags[c] & 7
        gp = gpages[gsrc[c]][c]
        for a in cellcolors:
            try:
                backcolor = ibmcolors[cellcolors[a][0]]
            except IndexError:
                backcolor = 0x00
            try:
                forecolor = ibmcolors[cellcolors[a][1][colorclass]]
            except IndexError:
                forecolor = 0x2a
            backr = (backcolor & 0x30) >> 4
            backg = (backcolor & 0xc) >> 2
            backb = backcolor & 0x3
            forer = (forecolor & 0x30) >> 4
            foreg = (forecolor & 0xc) >> 2
            foreb = forecolor & 0x3
            aptr = 0
            mptr = fcw * fch * c
            for y in xrange(fch):
                for x in xrange(fcw):
                    try:
                        r = colormix[backr][forer][gp[aptr + offsetr]]
                        g = colormix[backg][foreg][gp[aptr + offsetg]]
                        b = colormix[backb][foreb][gp[aptr + offsetb]]
                    except IndexError:
                        r = colormix[backr][forer][9]
                        g = colormix[backg][foreg][9]
                        b = colormix[backb][foreb][9]
                    fontmemory[a][mptr] = r << 16 | g << 8 | b
                    aptr += 3
                    mptr += 1
        yield None
    screen.cellwidth = fcw
    screen.cellheight = fch
    screen.refresh()

def loadprefs(infilename=None):
    global prefs
    if infilename is None:
        infilename = os.path.join(
            os.path.expanduser('~'),
            '.g-she')
    try:
        with open(infilename, 'r') as f:
            for d in f:
                if d.startswith('#'):
                    continue
                k, s, v = d.partition('=')
                if len(s) == 0:
                    continue
                prefs[k] = v
        return None
    except IOError:
        prefs.update({
            'font.file': 'temoro.srcf',
            'font.sets': '(default)',
            'font.subpixel': 'rgb',
            'font.encoding': 'ascii',
            })
        return None


def main():
    global fontmemory
    global loadedfontpack
    global prefs
    global screen
    global window
    consoleenc = sys.stdout.encoding
    print altencode(aboutstring['title'], consoleenc)
    print altencode(aboutstring['version'], consoleenc)
    print altencode(aboutstring['copyright'], consoleenc)
    print altencode(aboutstring['license'], consoleenc)
    print '\nLoading user preferences...'
    prefs = {}
    loadprefs()
    print 'Initializing SDL...'
    sdl2.ext.init()
    print 'Initializing screen buffer...'
    window = sdl2.ext.Window(aboutstring['title'], size=(800, 600))
    charcells = [None] * 256
    basicfont, basicfontdata = scrbuf.defaultfont(0xaaaaaa, 0x0, 10, 24)
    for a in cellcolors:
        charcells[a] = basicfont
    winsurf = window.get_surface()
    screen = scrbuf.ScrBuf(winsurf,
                           charcells,
                           10, 24,
                           window.refresh,
                           ())
    screen.encoding = prefs['font.encoding']
    if ' ' in screen.encoding:
        try:
            screen.encoding = [int(h, 16)
                               for h in screen.encoding.split(' ')]
        except ValueError:
            pass
    screen.cbuf[ : , : ] = (' *  ' * 20 + '   *' * 20) * 13
    screen.abuf[ : , : ] = 0x21
    boxcolor = int(time.time()) & 7
    screen.abuf[20 : 60, 7 : 13] = 0x20 | boxcolor
    screen.cbuf[20 : 60, 7 : 13] = 0x20
    screen.refresh()
    s = altencode(aboutstring['title'], screen.encoding)
    x = (80 - len(s)) // 2
    screen.cursorTo((x, 8))
    screen.setColor(0x10 | boxcolor)
    screen.printText(s)
    s = altencode(aboutstring['version'], screen.encoding)
    x = (80 - len(s)) // 2
    screen.cursorTo((x, 9))
    screen.setColor(0x00 | boxcolor)
    screen.printText(s)
    s = altencode(aboutstring['copyright'], screen.encoding)
    x = (80 - len(s)) // 2
    screen.cursorTo((x, 10))
    screen.printText(s)
    ss = altencode(aboutstring['crhilite'], screen.encoding)
    hidx = s.lower().find(ss)
    if hidx >= 0:
        screen.abuf[x + hidx : x + hidx + len(ss),
                    screen.crow] = 0x10 | boxcolor
    s = altencode(aboutstring['license'], screen.encoding)
    x = (80 - len(s)) // 2
    screen.cursorTo((x, 11))
    screen.setColor(0x20 | boxcolor)
    screen.printText(s)
    screen.cursorTo((0, 0))
    screen.setColor(0x10)
    print 'Displaying main window...'
    window.show()
    screen.refresh()
    print 'Loading font...'
    fontmemory = {}
    loadedfontpack = None
    lastrefresh = time.clock()
    for discard in loadfont():
        if time.clock() - lastrefresh > 1.0:
            screen.refresh()
            lastrefresh = time.clock()
    print 'Starting application loop...'
    scnWrapdemo()
    for event in eventloop(quitconfirm=scnQuitconfirm):
        pass
    print 'Quitting SDL...'
    window.hide()
    del window
    sdl2.ext.quit()
    del screen
    del basicfontdata
    del fontmemory
    return 0


def scnQuitconfirm(*args):
    restoreinfo = drawdlg((21, 59), (10, 15))
    wraptext('Exit G-SHE?',
             (22, 58), (11, 13), ALIGN_CENTER)
    f = Form([Control((27, 37), 13, CTRL_BUTTON,
                      caption=u'Yes', hotkey = sdl2.SDLK_y, action=URESP_YES),
              Control((43, 53), 13, CTRL_BUTTON,
                      caption=u'No', hotkey = sdl2.SDLK_n, action=URESP_NO),
              ])
    screen.refresh(restoreinfo[0])
    for event in keypressfilter(eventloop(
                quitconfirm=(lambda x: URESP_YES))):
        if event.type == SDLX_KEYPRESS:
            if sdl2.SDLK_y in event.keycombo:
                return URESP_YES
            if sdl2.SDLK_n in event.keycombo:
                undrawdlg(restoreinfo)
                return URESP_NO
            if sdl2.SDLK_TAB in event.keycombo:
                if event.modkeys & (sdl2.KMOD_LSHIFT | sdl2.KMOD_RSHIFT):
                    f.focusPrev()
                else:
                    f.focusNext()
            elif sdl2.SDLK_RETURN in event.keycombo \
                 or sdl2.SDLK_SPACE in event.keycombo:
                c = f.focusedControl()
                if c.type is CTRL_BUTTON:
                    if c.action is URESP_NO:
                        undrawdlg(restoreinfo)
                    return c.action


def scnWrapdemo(*args):
    restoretitle = window.title
    restoreabuf = screen.abuf[ : , : ]
    restorecbuf = screen.cbuf[ : , : ]
    window.title = 'Word-wrap demo'
    teststring = u'Here is a very long run of text, with some short words, ' +\
                 u'and some very long words like extraordinary, ' +\
                 u'Mississippi, and canteloupe. Let\'s also throw in some ' +\
                 u'hyphenated words, like lactose-intolerant, Put-In-Bay, ' +\
                 u'merry-go-round, state-of-the-art, and ground-breaking. ' +\
                 u'This run of words is also a bit repetitive. '
    teststring *= 3
    i = 1
    screen.abuf[ 9 : 75, 4 : 23] = 32
    screen.abuf[ 7 : 73, 3 : 22] = 3
    screen.abuf[12 : 68, 5 : 20] = 1
    screen.cbuf[ 7 : 73, 3 : 22] = 32
    screen.refresh()
    for event in eventloop(tinterval=0.33):
        if event.type == sdl2.SDL_KEYDOWN or event.type == SDLX_TIMERTICK:
            wraptext(teststring[: i], (12, 68), (5, 20), ALIGN_CENTER)
            i += 1
        if i > len(teststring):
            break
    window.title = restoretitle
    screen.abuf[ : , : ] = restoreabuf
    screen.cbuf[ : , : ] = restorecbuf
    screen.refresh()


def srcfnamefromfile(f):
    buf = f.read(32)
    #insert newer signature check blocks here
    if buf.startswith('SRCF binary v1860\r\n'):
        buf = buf[19 :]
        sidx = -1
        while sidx == -1:
            r = f.read(32)
            if len(r) == 0:
                return None
            buf += r
            sidx = buf.find('\0\0\0')
        nlen = ord(buf[sidx - 1])
        sidx += 3
        return buf[sidx : sidx + nlen].decode('utf8', 'replace')


def undrawdlg(restoreinfo):
    area, abuf, cbuf = restoreinfo
    screen.abuf[area] = abuf
    screen.cbuf[area] = cbuf
    screen.refresh(area)


def wraptext(text, spanc, spanr, alignment=None, breakchars=None):
    if alignment is None:
        alignment = ALIGN_LEFT
    if isinstance(spanc, int):
        x0 = spanc
        x1 = spanc + 1
    elif isinstance(spanc, tuple):
        x0, x1 = spanc
    elif isinstance(spanc, slice):
        x0, x1, step = spanc.indices(80)
    if isinstance(spanr, int):
        y0 = spanr
        y1 = spanr + 1
    elif isinstance(spanr, tuple):
        y0, y1 = spanr
    elif isinstance(spanr, slice):
        y0, y1, step = spanr.indices(25)
    maxw = x1 - x0
    maxh = y1 - y0
    text = altencode(text, screen.encoding)[: maxw * maxh]
    if breakchars is None:
        breakchars = {(c, False) for c in altencode(u'-/\\', screen.encoding)} \
                     | {(c, True) for c in altencode(u' ', screen.encoding)}
    else:
        breakchars = {(c if isinstance(c, tuple)
                       else (c, True))
                      for c in breakchars}
    padchar = altencode(u' ', screen.encoding)
    q = []
    tlen = len(text)
    h = lambda x: (tlen - x) // maxw
    ll = lambda n0, n1: (n1[0] - n0[0]
                         + (1 if n0[1] < 1 else 0)
                         - (1 if n1[1] <= 1 else 0))
    d = lambda n0, n1: (maxw - ll(n0, n1)) ** 2 + 1
    breakpenalty = maxw * maxw + maxw
    ec = countback()
    start = [h(0), (0, 0), next(ec), 0x7fffffff, h(0), [], 0]
    q.append(start)
    ebc = []
    for idx in xrange(len(text)):
        c = text[idx]
        if (c, True) in breakchars:
            q.append([0x7fffffff, (idx, 1), None, 0x7fffffff, h(idx), [], None])
        elif (c, False) in breakchars:
            q.append([0x7fffffff, (idx, 2), None, 0x7fffffff, h(idx), [], None])
        else:
            ebc.append([0x7fffffff, (idx, 2, True), None, 0x7fffffff, h(idx), [], None])
    b0 = q[0]
    eb = []
    for b1 in itertools.islice(q, 1, None):
        idx0 = b0[1][0] + (1 if b0[1] >= 1 else 0)
        idx1 = b1[1][0] + (1 if b1[1] > 1 else 0)
        if idx1 - idx0 > maxw:
            print idx0, idx1
            for b2 in ebc:
                if idx0 + 3 < b2[1][0] < idx1 - 3:
                    eb.append(b2)
        b0 = b1
    del ebc
    q += eb
    del eb
    goal = [0x7fffffff, (tlen, 0), next(ec), 0x7fffffff, 0, [], None]
    q.append(goal)
    backtrace = {}
    for i in xrange(len(q) - 1):
        for j in xrange(i + 1, len(q)):
            n0 = q[i][1]
            n1 = q[j][1]
            if ll(n0, n1) <= maxw:
                if len(n0) > 2 or len(n1) > 2:
                    q[i][5].append((q[j], d(n0, n1) + breakpenalty))
                else:
                    q[i][5].append((q[j], d(n0, n1)))
##    for i in q:
##        if len(i[1]) <= 2:
##            print i[0], i[1], i[2], i[3], i[4], '; '.join(
##                '({:d}, {:d})'.format(j[0][1][0], j[1])
##                for j in i[5]
##                if len(j[0][1]) <= 2)
    heapify(q)
    searching = True
    while len(q) > 0 and searching:
        cnode = heappop(q)
        if cnode is goal:
            searching = False
            break
        if cnode[2] is None:
            continue
        lc1 = cnode[6] + 1
        if lc1 > maxh:
            continue
        cnode[2] = None
        g0 = cnode[0]
        for edge in cnode[5]:
            g1 = g0 + edge[1]
            g1h = g1 + edge[0][4]
            if g1 < edge[0][0]:
                backtrace[edge[0][1]] = cnode[1]
                edge[0][0] = g1
                edge[0][3] = g1h
                edge[0][6] = lc1
                if edge[0][2] is None:
                    edge[0][2] = next(ec)
                    q.append(edge[0])
                heapify(q)
    if goal[6] is None:
        bestscore = (0, -0x80000000)
        bestreach = start
        for e in q:
            escore = (e[1][0], e[0] ^ -1)
            if escore > bestscore:
                bestscore = escore
                bestreach = e
        goal = bestreach
    tnode = goal[1]
    linebreaks = [tnode]
    while tnode != start[1]:
        tnode = backtrace[tnode]
        linebreaks.append(tnode)
    linebreaks.reverse()
    b0 = linebreaks[0]
    trimset = ''.join(c[0]
                      for c in breakchars
                      if c[1])
    r = y0
    for b1 in itertools.islice(linebreaks, 1, None):
        idx0 = b0[0] + (1 if b0[1] >= 1 else 0)
        idx1 = b1[0] + (1 if b1[1] > 1 else 0)
        line = text[idx0 : idx1].strip(trimset)
        excess = maxw - len(line)
        #if alignment is ALIGN_LEFT: #see else suite
        if alignment is ALIGN_CENTER:
            padl = excess >> 1
            padr = excess - padl
        elif alignment is ALIGN_RIGHT:
            padl = excess
            padr = 0
        else: #ALIGN_LEFT or unknown
            padl = 0
            padr = excess
        screen.cbuf[x0 : x1, r] = padchar * padl + line + padchar * padr
        screen.crow = r
        screen.ccol = x1 - padr
        r += 1
        if r >= y1:
            break
        b0 = b1
    screen.refresh((spanc, spanr))


if __name__ == '__main__':
    sys.exit(main())

