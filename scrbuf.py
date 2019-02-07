'''
80x25 text mode screen buffer class using SDL2 surfaces for the screen buffer
and character graphics
'''

import array, ctypes, itertools, zlib

import sdl2


class ScrBuf(object):

    def __init__(self, scrsurf, charsurf, cellwidth, cellheight,
                 refreshfn, rfnparams):
        self.NCOLS = 80
        self.NROWS = 25
        self.blankchar = 32
        self.tabs = range(0, self.NCOLS, 5)
        self.cellwidth = cellwidth
        self.cellheight = cellheight
        self.scrsurf = scrsurf
        self.charsurf = charsurf
        try:
            len(self.charsurf)
        except TypeError:
            self.charsurf = (self.charsurf, )
        except IndexError:
            raise ValueError('charsurf must be indexable using integers beginning with 0')
        for a in self.charsurf:
            sdl2.SDL_SetSurfaceBlendMode(a, sdl2.SDL_BLENDMODE_NONE)
        self.refreshfn = refreshfn
        self.rfnparams = rfnparams
        self.cbuf = ByteBuf2D(self.NCOLS, self.NROWS, self.blankchar)
        self.catt = 7 if (len(self.charsurf) >= 8) else 0
        self.ccol = 0
        self.crow = 0
        self.abuf = ByteBuf2D(self.NCOLS, self.NROWS, self.catt)
        self.refresh()
        return

    def cls(self):
        self.cbuf[:, :] = self.blankchar
        self.abuf[:, :] = self.catt
        self.ccol = 0
        self.crow = 0
        self.refresh()
        return

    def cursorDown(self):
        self.crow += 1
        if self.crow >= self.NROWS:
            self.scroll(1)
            return True
        return False

    def cursorHome(self):
        self.ccol = 0
        return

    def cursorLeft(self):
        self.ccol -= 1
        if self.ccol < 0:
            self.ccol = 0
        return

    def cursorRight(self):
        self.ccol += 1
        if self.ccol > self.NCOLS:
            self.cursorDown()
            self.ccol -= self.NCOLS
        return

    def cursorTab(self, tabidx=None):
        if tabidx is not None:
            if self.ccol <= self.tabs[tabidx]:
                self.cursorDown()
            self.ccol = self.tabs[tabidx]
            return
        for tab in self.tabs:
            if tab > self.ccol:
                self.ccol = tab
                return
        self.cursorDown()
        self.ccol = self.tabs[0]
        return

    def cursorTo(self, pos):
        self.ccol, self.crow = pos
        if self.crow >= self.NROWS:
            self.scroll(self.crow - self.NROWS + 1)
            return True
        return False

    def cursorUp(self):
        self.crow -= 1
        if self.crow < 0:
            self.crow = 0
        return

    def getColor(self, pos=None):
        if pos is None:
            return self.catt
        return self.abuf[pos]

    def getText(self, pos=None):
        if pos is None:
            return chr(self.cbuf[ccol, crow])
        rcols, rrows = pos
        if isinstance(rcols, int):
            rcols = slice(rcols, rcols + 1)
        if isinstance(rrows, int):
            rrows = slice(rrows, rrows + 1)
        rcols = rcols.indices(self.NCOLS)
        rrows = rrows.indices(self.NROWS)
        return '\n'.join(
            [self.cbuf[slice(*rcols), r].tostring()
             for r in xrange(*rrows)])

    def printChar(self, c, refresh=True):
        scrolled = False
        if self.ccol >= self.NCOLS:
            self.ccol = 0
            scrolled = self.cursorDown()
        if not isinstance(c, int):
            if len(c) < 1:
                c = 0
            elif isinstance(c, str):
                c = ord(c[0])
            elif isinstance(c, unicode):
                c = ord(c[0]) & 255
            else:
                c = int(c) & 255
        self.cbuf[self.ccol, self.crow] = c
        self.abuf[self.ccol, self.crow] = self.catt
        if refresh:
            self.refresh((self.ccol, self.crow))
        self.ccol += 1
        return scrolled

    def printText(self, text):
        text = str(text)
        minrow = self.crow
        mincol = self.ccol
        maxrow = self.crow - 1
        maxcol = self.ccol - 1
        enablelf = True
        for c in text:
            c = ord(c)
            if c == 10 and enablelf:
                self.cursorHome()
                if self.cursorDown():
                    minrow = self.NROWS - 1
                    maxrow = minrow - 1
                    mincol = 0
                    maxcol = -1
                enablelf = True
                continue
            enablelf = True
            if c == 0:
                break
            if c == 7:
                print 'Beep!\a'
                continue
            if c == 8:
                self.cursorLeft()
                self.cbuf[self.ccol, self.crow] = self.blankchar
                if minrow > self.crow:
                    minrow = self.crow
                elif maxrow < self.crow:
                    maxrow = self.crow
                if mincol > self.ccol:
                    mincol = self.ccol
                elif maxcol < self.ccol:
                    maxcol = self.ccol
                continue
            if c == 9:
                self.cursorTab()
                continue
            if c == 12:
                self.cls()
                continue
            if c == 13:
                self.cursorHome()
                if self.cursorDown():
                    minrow = self.NROWS - 1
                    maxrow = minrow - 1
                    mincol = 0
                    maxcol = -1
                enablelf = False
                continue
            if minrow > self.crow:
                minrow = self.crow
            elif maxrow < self.crow:
                maxrow = self.crow
            if mincol > self.ccol:
                mincol = self.ccol
            elif maxcol < self.ccol:
                maxcol = self.ccol
            if self.printChar(c, False):
                minrow = self.NROWS - 1
                maxrow = minrow - 1
                mincol = 0
                maxcol = -1
            if maxrow < self.crow:
                maxrow = self.crow
                mincol = 0
        self.refresh((slice(mincol, maxcol + 1),
                      slice(minrow, maxrow + 1)))

    def refresh(self, area=None):
        if area is None:
            area = ((0, self.NCOLS, 1),
                    (0, self.NROWS, 1))
        rcols, rrows = area
        if isinstance(rcols, tuple):
            rcols = slice(*rcols).indices(self.NCOLS)
        elif isinstance(rcols, slice):
            rcols = rcols.indices(self.NCOLS)
        else:
            rcols = int(rcols)
            rcols = (rcols, rcols + 1, 1)
        if isinstance(rrows, tuple):
            rrows = slice(*rrows).indices(self.NROWS)
        elif isinstance(rrows, slice):
            rrows = rrows.indices(self.NROWS)
        else:
            rrows = int(rrows)
            rrows = (rrows, rrows + 1, 1)
        rrows = xrange(*rrows)
        rcols = range(*rcols)
        for r in rrows:
            y = r * self.cellheight
            for c in rcols:
                x = c * self.cellwidth
                sdl2.SDL_BlitSurface(
                    self.charsurf[self.abuf[c, r]],
                    sdl2.SDL_Rect(
                        0,
                        self.cellheight * self.cbuf[c, r],
                        self.cellwidth,
                        self.cellheight),
                    self.scrsurf,
                    sdl2.SDL_Rect(
                        self.cellwidth * c,
                        self.cellheight * r,
                        0, 0))
        self.refreshfn(*self.rfnparams)
        return

    def scroll(self, n):
        if n >= self.NROWS:
            self.cls()
            return
        nn = self.NROWS - n
        self.cbuf[:, :nn] = self.cbuf[:, n:]
        self.abuf[:, :nn] = self.abuf[:, n:]
        self.cbuf[:, nn:] = self.blankchar
        self.abuf[:, nn:] = self.catt
        self.crow -= n
        self.refresh()
        return

    def setColor(self, a, pos=None):
        if pos is None:
            self.catt = a
            return
        self.abuf[pos] = a
        self.refreshfn[pos]
        return


class ByteBuf2D(array.array):

    def __new__(cls, ncols, nrows, default=0):
        return array.array.__new__(cls, 'B', [default] * (ncols * nrows))

    def __init__(self, ncols, nrows, default=0):
        #array.array.__init__(self, 'B', [default] * (ncols * nrows))
        self.ncols = ncols
        self.nrows = nrows

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            return array.array.__getitem__(self, key)
        if len(key) != 2:
            raise TypeError('2D array index must be integer or tuple of length 2')
        ckey, rkey = key
        if isinstance(ckey, int) and isinstance(rkey, int):
            if ckey < 0:
                ckey += self.ncols
            if rkey < 0:
                rkey += self.nrows
            return array.array.__getitem__(self, ckey + self.ncols * rkey)
        if isinstance(ckey, int):
            if ckey < 0:
                ckey += self.ncols
            ckey = slice(ckey, ckey + 1)
        cki = ckey.indices(self.ncols)
        cn = len(xrange(*cki))
        if isinstance(rkey, int):
            if rkey < -1:
                rkey += self.nrows
            rkey = slice(rkey, rkey + 1)
        rki = rkey.indices(self.nrows)
        rn = len(xrange(*rki))
        gather = ByteBuf2D(cn, rn)
        dr = 0
        for sr in xrange(*rki):
            offset = sr * self.ncols
            gather[:, dr] = array.array.__getitem__(
                self, slice(cki[0] + offset, cki[1] + offset, cki[2]))
            dr += 1
        return gather

    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            if isinstance(value, float):
                value = int(value) & 255
            elif isinstance(value, str):
                value = ord(value)
            elif isinstance(value, unicode):
                value = ord(value) & 255
            return array.array.__setitem__(self, key, value)
        if len(key) != 2:
            raise TypeError('2D array index must be integer or tuple of length 2')
        ckey, rkey = key
        if isinstance(ckey, int) and isinstance(rkey, int):
            if ckey < 0:
                ckey += self.ncols
            if rkey < 0:
                rkey += self.nrows
            if isinstance(value, float):
                value = int(value) & 255
            elif isinstance(value, str):
                value = ord(value)
            elif isinstance(value, unicode):
                value = ord(value) & 255
            return array.array.__setitem__(self, ckey + self.ncols * rkey, value)
        try:
            src = iter(value)
        except TypeError:
            src = itertools.repeat(value)
        if isinstance(ckey, int):
            if ckey < 0:
                ckey += self.ncols
            ckey = slice(ckey, ckey + 1)
        cki = ckey.indices(self.ncols)
        cn = len(xrange(*cki))
        if isinstance(rkey, int):
            if rkey < -1:
                rkey += self.nrows
            rkey = slice(rkey, rkey + 1)
        rki = rkey.indices(self.nrows)
        rn = len(xrange(*rki))
        for dr in xrange(*rki):
            offset = dr * self.ncols
            for dc in xrange(*cki):
                try:
                    c = next(src)
                except StopIteration:
                    return
                if isinstance(c, float):
                    c = int(c) & 255
                elif isinstance(c, str):
                    c = ord(c)
                elif isinstance(c, unicode):
                    c = ord(c) & 255
                array.array.__setitem__(self, dc + offset, c)

    def __iter__(self):
        self.iteridx = 0
        return self

    def next(self):
        if self.iteridx >= array.array.__len__(self):
            raise StopIteration
        r = array.array.__getitem__(self, self.iteridx)
        self.iteridx += 1
        return r

    def __len__(self):
        return (ncols, nrows)

    def __repr__(self):
        return ('<ByteBuf2D {:d}x{:d}> '.format(self.ncols, self.nrows)
                + array.array.__repr__(self))

    def __str__(self):
        return '[' + ',  '.join([
            '[' + ' '.join([
                '{:3d}'.format(self[c, r])
                for c in xrange(self.ncols)]) + ']'
            for r in xrange(self.nrows)]) + ']'


def defaultfont(forergb, backrgb, cwidth=8, cheight=16):
    '''
    Given 32-bit foreground and background colors, create a SDL_Surface
    containing a default character font with 256 character cells of size
    8x16, arranged vertically (so entire surface size is 8x4096).
    Return a pointer to this SDL_Surface and a data array which must not be
    freed until the surface is freed.
    '''
    pixdata = (ctypes.c_ulong * int(1024 * cwidth * cheight))()
    charset = sdl2.SDL_CreateRGBSurfaceFrom(ctypes.byref(pixdata),
                                            cwidth, cheight << 8,
                                            32,
                                            cwidth << 2,
                                            0xff0000,
                                            0xff00,
                                            0xff,
                                            0x0)
    charsrc = array.array('B')
    charsrc.fromstring(zlib.decompress(
        'x\x9cuW\xcfk\x1bG\x14^\xc5\xb0\xa1 d\xfb\xb6\xc6\xc6F\xb4\x17\xdf\xb6\x18\x94\xdd\xb2\xb6.\xfd\x17z\xe9i\te\xc9a(:\xa9*,j\x82\xc0>\xf6\xa0C\xd0!\xd5)\x97\xfe\x15\xc2jG=,\xceM\x08\xac\x8a\x94\x82s\t\x8e\x83\xc0q\xc0]\xf5\xbd\x997\xb33\xab\xe4\xd3\n\xef\xa7\xf7f\xde\x8fy\xf3f\xbcZ\xadzaX\xaf\xd7\xbfl\xf6V\x02\xef&\xfd0\xac\x84\x00\xc97\x06\x83A\x0f\xbe\x83\r\xc9\xc7\x83\xe3&\xe0x0\x96\xfca\x7f \xd0\x7f(ye\xf0\xe2\xf9\xd9\xf3\xe1\x8bA\xc5\xe2\xc3\xe1\xa61\xbe\x1e\x86\x83?%GK\xc2\x1c\xd9\x1b\xbf!\xd0\xfc\xff,\x11GGGg\x92\xef\x80\xa9\xb330\xba#\xf9\xe6P@\xdb\x0b\xb7+\x95Cc\xbep\xe7\x8bJ\xfd\xeb\x82\xf7BB\xcf\x88oX\xf8G\xf2\xc3zo\xf9^\xcb1\xc6\x1d-\x1fN\x96\x1f\xf5\xf8g\xcf^Z\xfe\x86\xa5\xf9\x89\xf5\'\xef\n~xxX\xd9\xee+\xde\xefM&\xbd\xbe\xf2\x0fs96\xe6\xab\x84?/\xdf\xbc\x1a\x1e\x87\x14\xdf\xf8\x15\x81\xe4\xab_\x9a\x07\xbfN\xfe}\xff\xf1?\x92/\tc\xb5\x9a\xab\xcf\xc1\x81g\r^\x14E\x9e\xe79\xf0 \x92$\xf9\xcaV`,g\xe2+\xb4\xbd\x94\x9f\x8fR\xd7=\xe5)\x8dp\xcey\xd5\xf3c~*Y\xc0X\xd0\x9egY\xd6\x16\xd4\xf7\xfd\xd8\x9a\x0et\x05\xbc\xaa\xe4\xf0"\xe0\xf9Z%\x89VQb\xba\xe8u\x95-\xe37c\x80\x93\x7f".=\xe2\x81\x8b\xfe\x8d\x9e*\xff8\x9fN9g\x01\xe9\x05\x1dO\xa0+y\xca\xa5:\xcf5w#\xd7uyJ\xfe\xefE,\xcb\xc1\xe1}2=\x1a\x8d\xee\ry\x10\x03\xe7\x00\xe29\x8c\x971\xab\xf9@d\xc8\xf1\xbd\x0b\xe3\xab\x1d\xcbs#`\xe2*\\\xe1\x1ed\xcd\xd5\n]\xf1(\x08\x19\xea\xe8\xf9\xab\xc6\xfa\x8a\x1f\x16\x8b\xc5|D\xf6\xb70!9:$\xf9=T@\n\xdf\xe4^\xf2(9\x87\x08G\xe7I$\xf9\x1dK\x04\xd8\x1d\xc5\x97<~\xd2y\x12?Nr\x8b\xc7\xf1\x8d1~\xc1y\xf2\x8d\xe4hI\x98#{\x91G\xa0\xf9\xf7E5@\xfdP>\xae\xc0T\xa7\x03F\xaf$\xbf\x89\x05\xb4=~\x9d\xe7Sc>~u\x9b/.\n.rm\xe4[\xc4\x17\x17\xfe\x91|\xbaH\xab5-\xc7\x18\xaf\xb4<\x0e\xaa\xae\x1e\xdf\xed~o\xf9\xcbK\xf3\x13c\xc1V\xc1\xa7\xd3i~\xcd\x14gi\x10\xa4L\xf9\x87\xb9\x8c\x8c\xf9r~\x8a\x8bw\xae\xea/\xf2\t$w\x9e\x8e^\xb7\x82\xbd\x9a\xfb\x80\xe4UB\xa4V\xd3\xf9\x1cV\xb8\x1d\xcb\x1b\t\xd0\xa9\xa6z\xbf:\xaf\xe3\xb8#\x968\xd5\xf2\x94C\x01\xa8\xf8\xf6\xc0\x12\xcb\n}!\xcf\x0by\xc0~\x88o\x8c\xfc\x02\xda\xa8\x9e\xa5U\xb1\xa40?k\'E~\xa1.\x033\x9f\xae\xeb\xd4\\\x81D\x94\x1c\xe8\xcb\x02 \xfd\xa0T/\x80\xb79$xZ\xc4=\x97\x15j\xf8g\xac\x8f\x96\xa7\xdaE\xe5\x9f\xda\xd2\xf3vb\xf9\x9fb\x05\xa8\xf1[\xbe\x7f\x8f\xcb\xd1\xd8\xd3r1\xdc\xc8G"\xd7TsY\x00\xac\xe0,\x08\xccu\x92\x15\xd3u\xabjKe\xd8Oi\xfdk\x10j\x0b\xe3\xad\xa9|\x89\xcd\xec\xa9\xfd\x8c2\xd4\xf1Z\x14\xcc\xdc)A\xecp5\x1d\xedg\xd8\xceUWD\x94\xd9\xfec\x1f6\xd7\x13\x06\xdb\xf5\x91\xd9\xf5\x02\xdd\xc6\xe2\x01\xf4UK\x1f-\xc2\x12\x829U\xa0v\xbdp\xbb~p>K\x9e8V}xp2\x98\x1c\xf5M\xce\x8b\x86\xa6\xdc19\xb6\xc5<\x89a\xed\x93\xe2\xcc\xc8\xda\x8d\xeel\xf6\xa3$\'P\xdc9\xe6\xe3B\xc7o\xd5\x0f\xb7\xebI\xfa[p\xbf\x93Y\xf9D\xb9U\x1f\xdcX\xef\x0eR\xd5\xa0R\x12\xdb\xfd\x04\xe2\xc2b\xc4\x16A\xf9\xa5\xeduE\xfd\x19+\xad\x8b\x07\xa4\x94\xdfe\xd9\xdd\x1f\xd9\x02\xec\xc9\xfa\xaa\xedz\xe2\xf8\x04\xccZ\x94\x00s}p\xbd\xad\xfc\x82\xdc\x8c\x07\xb9\xe5?\xd4\x97\xb1\xbf\x80\xe9\x86+\x17\x9b\xb1\x13\xf34\xc2\xeb\x80Sl=\xec@\xf0\xc0\xf1j\xecGq\x86\x8e\x0c\x9d\x1c\xb7\xbf|\x85R\xe5\xb8\x1d\xe6\xd0\x15O\n\x9e\\\xfcv"U\xe4n\xc0K\x8c\x1e\xde`3\xd60\xa6\x03\xc6f\xf2u\xfb[\xfb\xf3\xdd\xef\xf6\xe7\xef\x9f\xec\x8f\xf7i\xdc\x95\x98\xe6\r\x89[\xfa\xab\xbc\xc8-^\xd6\xbfu\xb5~\x19\x94\x0e[~\xeb\xea\xda\xa5_4W\xfe86l\x7f=\xef\xc0\xd2\xf7\xbc\xf2\xbdpU\xd6W/J^\x1e_\xd2\xd6\xfa\xe4\xdf#\xcb\xffG~\xd3\xb2\xd6\xf4m\xf9\x07\xc7\xf6g\xe5|(\x8d\xd7\xfa$\xd7\xfa4^\xebSt\xb6\xbc\xd1(\xcf\xbf*\xc7WZ\x06\xed\xaf\x8a\xcf\x1a\x7f\xb0\x96\x9ffi\xbc\x9e\x8f\xb2U\xceoy\xbd\xf4|kWx\xf2O\xe1\xa6\x84\xcd\x12\xeca\x84\xf6|6\x9b\xcdi?w`k\xcf2\xd8\xbe\x99\xe4\xd0)G\x12J\x1d\xaf\xff\x08E9\xf4\xb4\xe2|\x02@\xf3\x04\xb4\x14U\xa7\xab\x9a\xa0=\xb7r\xd3\x85\x8e&\x9a\x16qj\xcf\xea>.\x0e+4w-\xf9>\\gO\xc4\x81Z\xd8\xbb\xbc\xbc,Z\xcc\x86\x0b|\xd9U\xe6\xf6\xfc\x18\xdb{\xec\xab\xf3Y_\x00u<\xea!\xd0\xbf\x17*It}\xd6M\x8c\xae\xdb\x8a\xd7vw\xbdu\x98\xf1\xc3d]\xf3\xfe\x8eMR\x9f\xca\xa2\x1f\xaea\xfd\xdf\x1b\xf5\xb2)\xeevo\x19\x8bd<3s)\x00\xad\x99\x1f\xffe\x97O*\xb1n\x05\xf0?\x93\x8d\xb5\xab'
        ))
    for y in xrange(4096):
        #offset = y << 3
        offset = ((y >> 4) * cheight + (y & 15)) * cwidth
        #print y, offset
        pixdata[offset    ] = forergb if charsrc[y] & 128 else backrgb
        pixdata[offset + 1] = forergb if charsrc[y] &  64 else backrgb
        pixdata[offset + 2] = forergb if charsrc[y] &  32 else backrgb
        pixdata[offset + 3] = forergb if charsrc[y] &  16 else backrgb
        pixdata[offset + 4] = forergb if charsrc[y] &   8 else backrgb
        pixdata[offset + 5] = forergb if charsrc[y] &   4 else backrgb
        pixdata[offset + 6] = forergb if charsrc[y] &   2 else backrgb
        pixdata[offset + 7] = forergb if charsrc[y] &   1 else backrgb
        for oo in xrange(offset + 8, offset + cwidth):
            pixdata[oo] = pixdata[offset + 7]
        if (y & 15) == 15:
            for oo in xrange(((y >> 4) * cheight + 16) * cwidth,
                             (((y >> 4) + 1) * cheight) * cwidth):
                pixdata[oo] = pixdata[oo - cwidth]
    return charset, pixdata


if __name__ == '__main__':
    import ctypes, sys, time, zlib
    print 'Initializing SDL...'
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    print 'Preparing colors...'
    color = [  (((a & 1)) * 0xaa)
             | (((a & 2) >> 1) * 0xaa00)
             | (((a & 4) >> 2) * 0xaa0000)
             | (((a & 8) >> 3) * 0x555555)
             | 0xff000000
             for a in xrange(16)]
    color[6] = 0xffaa5500
    contrastindices = [0.0, 0.15033995248574766, 0.627200577963303, 0.654297272982142, 0.3273606690819785, 0.3911240242592479, 0.45604669228450495, 0.7231380482709482, 0.34015634957805657, 0.4658184709735542, 0.9069946712247097, 0.9331775229499149, 0.6239085016547736, 0.6828218212911674, 0.9787963437153111, 1.0]
    cpairs = [(a & 15, a >> 4) for a in xrange(128)]
    poorcontrast = [(
        -0.39 <=
        (contrastindices[cpairs[p][0]] - contrastindices[cpairs[p][1]])
        <= 0.34
        ) for p in xrange(128)]
    charsets = [None] * 128
    charsetdata = [None] * 128
    #print 'Preparing default font in attributes 7 and 8...'.format(a)
    charsets[7], charsetdata[7] = defaultfont(color[7], color[0])
    charsets[8], charsetdata[8] = defaultfont(color[8], color[0])
    print 'Creating window...'
    window = sdl2.SDL_CreateWindow(b'Hello World',
                                   sdl2.SDL_WINDOWPOS_UNDEFINED,
                                   sdl2.SDL_WINDOWPOS_UNDEFINED,
                                   640, 400,
                                   sdl2.SDL_WINDOW_SHOWN)
    windowsurface = sdl2.SDL_GetWindowSurface(window)
    print 'Initializing screen buffer...'
    screenbuffer = ScrBuf(windowsurface,
                          charsets,
                          8, 16,
                          sdl2.SDL_UpdateWindowSurface,
                          (window,)
                          )
    print 'Writing to screen buffer...'
    screenbuffer.cbuf[:, :] = [32] * 2000
    screenbuffer.abuf[:, :] = [7] * 2000
    screenbuffer.refresh()
    running = True
    event = sdl2.SDL_Event()
    print 'Starting event loop...'
    a = 7
    displaymsg = True
    lastcolorchange = time.clock()
    introhint = True
    lastclick = time.clock()
    while running:
        while sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_MOUSEBUTTONUP:
                displaymsg = True
                introhint = False
                lastclick = time.clock()
                continue
        introhint = introhint or (time.clock() - lastclick > 300.0)
        if displaymsg:
            if (time.clock() - lastcolorchange) > 2.0:
                a += 1
                while poorcontrast[a]:
                    a += 1
                    a &= 127
                lastcolorchange = time.clock()
            if charsets[a] is None:
                #print 'Preparing default font in attribute {:d}...'.format(a)
                screenbuffer.cbuf[
                    screenbuffer.ccol:,
                    screenbuffer.crow
                    ] = 'working... '
                screenbuffer.refresh((slice(None),
                                      screenbuffer.crow))
                charsets[a], charsetdata[a] = defaultfont(
                    color[a & 15],
                    color[a >> 4]
                    )
            screenbuffer.setColor(a)
            screenbuffer.printText('Hello, world! ')
            displaymsg = False
        if introhint:
            screenbuffer.cbuf[
                screenbuffer.ccol:,
                screenbuffer.crow
                ] = '(Hint: click me!)'
            ha = (((a & 112) >> 4) * 17) | 8
            if charsets[ha] is None:
                #print 'Preparing default font in attribute {:d}...'.format(a)
                charsets[ha], charsetdata[ha] = defaultfont(
                    color[ha & 15],
                    color[ha >> 4]
                    )
            screenbuffer.abuf[
                screenbuffer.ccol:,
                screenbuffer.crow
                ] = [ha] * 17
            screenbuffer.refresh((slice(None),
                                  screenbuffer.crow))
            introhint = False
            lastclick = time.clock()
        time.sleep(0.008333333333333)
    sdl2.SDL_DestroyWindow(window)
    del screenbuffer
    for charset in charsets:
        sdl2.SDL_FreeSurface(charset)
    sdl2.SDL_Quit()
    sys.exit(0)
