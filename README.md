# Geeda's Simple Hex Editor (G-SHE)

A basic hex editor with a visual style inspired by decades-old memories of the DOS utility called LIST.

Primary author is Maggie&#8239;David P.&#8239;K. Haynes, a.k.a. Geeda. This project was started April 19, 2018, and the Git repository was created February 7, 2019. Code is written for Python 2.7. Geeda makes no promises of devoting time to continued development.

## Usage

As of version 1.a.1909 there's not really much to do besides watch text appear on the screen and lines rebalance as more text appears at the end. Attempting to close the graphical window will introduce a quit confirmation dialog with basic keyboard navigation.

## Files

### hexedit.py

The main G-SHE program file.

### scrbuf.py

80&#215;25 text mode screen buffer class using SDL2 surfaces for the screen buffer and character graphics, a baked-in default character glyph set, and a simple demo program.

### temoro.srcf

Temoro, a Smoothed Raster Cell Font reminiscent of IBM's EGA-mode font in 10&#215;24-pixel character cells. Supports ASCII, CP-437, and Windows-1252 character sets, plus optional non-lining figures, and optional control pictures or backslash-escape symbols for C0 control characters.

### fontsrc

#### fontsrc/packfont.py

A utility for compiling SRCF files.

#### fontsrc/srcfinfo.py

A crude tool for displaying metadata in SRCF files.
