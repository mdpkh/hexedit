# Geeda's Simple Hex Editor (G-SHE)

A basic hex editor with a visual style inspired by decades-old memories of the DOS utility called LIST.

Primary author is Maggie&#8239;David P.&#8239;K. Haynes, a.k.a. Geeda. This project was started April 19, 2018, and the Git repository was created February 7, 2019. Code is written for Python 2.7. Geeda makes no promises of devoting time to continued development.

## Usage

As of version 1.a.1909 there's not really much to do besides watch text appear on the screen and lines rebalance as more text appears at the end. Attempting to close the graphical window will introduce a quit confirmation dialog with basic keyboard navigation.

## Dependencies

### SDL2

G-SHE uses the `sdl2` and `sdl2.ext` modules from [PySDL2](https://pysdl2.readthedocs.io/en/rel_0_9_4/install.html).

## Files

### hexedit.py

The main G-SHE program file.

### scrbuf.py

80&#215;25 text mode screen buffer class using SDL2 surfaces for the screen buffer and character graphics, a baked-in default character glyph set, and a simple demo program.

### temoro.srcf

Temoro, a Smoothed Raster Cell Font reminiscent of IBM's EGA-mode font in 10&#215;24-pixel character cells. Supports ASCII, CP-437, and Windows-1252 character sets, plus optional non-lining figures, and optional control pictures or backslash-escape symbols for C0 control characters.

### temosa.srcf

Temosa, a sans-serif version of the Temoro font.

### version.py

This module stores the version and copyright strings for G-SHE. Run `version.py update` to automatically increment the version number and update copyright year before a commit.

### fontsrc

#### fontsrc/flags.txt

Minimal documentation for the `sflags` and `cflags` lines in `*.srcfdef.txt` files to be read by `packfont.py`.

#### fontsrc/packfont.py

A utility for compiling SRCF files.

#### fontsrc/srcfinfo.py

A crude tool for displaying metadata in SRCF files. Will probably be moved to project root in the future to support GUI font selection in `hexedit.py`.
