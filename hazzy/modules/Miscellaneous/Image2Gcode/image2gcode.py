#!/usr/bin/env python

# image-to-gcode is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  image-to-gcode is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with image-to-gcode;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301 USA.
#
# image-to-gcode.py is Copyright (C) 2005 Chris Radek
# chris@timeguy.com
# image-to-gcode.py is Copyright (C) 2006 Jeff Epler
# jepler@unpy.net
# image-to-gcode.py is Copyright (C) 2018 TurBoss
# j.l.toledano.l@gmail.com

import sys
import os
import gettext

from PIL import Image

import numpy.core

plus_inf = numpy.core.Inf

from rs274.author import Gcode
import rs274.options

from math import *
import operator

epsilon = 1e-5

progress_msg = True


def tobytes(img):
    if hasattr(img, 'tobytes'):
        return img.tobytes()
    return img.tostring()


def ball_tool(r, rad):
    s = -sqrt(rad ** 2 - r ** 2)
    return s


def endmill(r, dia):
    return 0


def vee_common(angle):
    slope = tan(angle * pi / 180)

    def f(r, dia):
        return r * slope

    return f


tool_makers = [ball_tool, endmill, vee_common(30), vee_common(45), vee_common(60)]


def make_tool_shape(f, wdia, resp):
    res = 1. / resp
    dia = int(wdia * res + .5)
    wrad = wdia / 2.
    if dia < 2: dia = 2
    n = numpy.array([[plus_inf] * dia] * dia, dtype=numpy.float32)
    hdia = dia / 2.
    l = []
    for x in range(dia):
        for y in range(dia):
            r = hypot(x - hdia, y - hdia) * resp
            if r < wrad:
                z = f(r, wrad)
                l.append(z)
                n[x, y] = z
    n = n - n.min()
    return n


def amax(seq):
    res = 0
    for i in seq:
        if abs(i) > abs(res): res = i
    return res


def group_by_sign(seq, slop=sin(pi / 18), key=lambda x: x):
    sign = None
    subseq = []
    for i in seq:
        ki = key(i)
        if sign is None:
            subseq.append(i)
            if ki != 0:
                sign = ki / abs(ki)
        else:
            subseq.append(i)
            if sign * ki < -slop:
                sign = ki / abs(ki)
                yield subseq
                subseq = [i]
    if subseq: yield subseq


class ConvertScanAlternating:
    def __init__(self):
        self.st = 0

    def __call__(self, primary, items):
        st = self.st = self.st + 1
        if st % 2: items.reverse()
        if st == 1:
            yield True, items
        else:
            yield False, items

    def reset(self):
        self.st = 0


class ConvertScanIncreasing:
    def __call__(self, primary, items):
        yield True, items

    def reset(self):
        pass


class ConvertScanDecreasing:
    def __call__(self, primary, items):
        items.reverse()
        yield True, items

    def reset(self):
        pass


class ConvertScanUpmill:
    def __init__(self, slop=sin(pi / 18)):
        self.slop = slop

    def __call__(self, primary, items):
        for span in group_by_sign(items, self.slop, operator.itemgetter(2)):
            if amax([it[2] for it in span]) < 0:
                span.reverse()
            yield True, span

    def reset(self):
        pass


class ConvertScanDownmill:
    def __init__(self, slop=sin(pi / 18)):
        self.slop = slop

    def __call__(self, primary, items):
        for span in group_by_sign(items, self.slop, operator.itemgetter(2)):
            if amax([it[2] for it in span]) > 0:
                span.reverse()
            yield True, span

    def reset(self):
        pass


class ReduceScanLace:
    def __init__(self, converter, slope, keep):
        self.converter = converter
        self.slope = slope
        self.keep = keep

    def __call__(self, primary, items):
        slope = self.slope
        keep = self.keep
        if primary:
            idx = 3
            test = operator.le
        else:
            idx = 2
            test = operator.ge

        def bos(j):
            return j - j % keep

        def eos(j):
            if j % keep == 0: return j
            return j + keep - j % keep

        for i, (flag, span) in enumerate(self.converter(primary, items)):
            subspan = []
            a = None
            for i, si in enumerate(span):
                ki = si[idx]
                if a is None:
                    if test(abs(ki), slope):
                        a = b = i
                else:
                    if test(abs(ki), slope):
                        b = i
                    else:
                        if i - b < keep: continue
                        yield True, span[bos(a):eos(b + 1)]
                        a = None
            if a is not None:
                yield True, span[a:]

    def reset(self):
        self.converter.reset()


unitcodes = ['G20', 'G21']
convert_makers = [ConvertScanIncreasing, ConvertScanDecreasing, ConvertScanAlternating, ConvertScanUpmill,
                  ConvertScanDownmill]


def progress(a, b):
    if progress_msg:
        print("PROGRESS = {0:.2f}%".format(a * 100. / b + .5))


class Converter:
    def __init__(self,
                 image,
                 units,
                 tool_shape,
                 pixelsize,
                 pixelstep,
                 safetyheight,
                 tolerance,
                 feed,
                 convert_rows,
                 convert_cols,
                 cols_first_flag,
                 entry_cut,
                 spindle_speed,
                 roughing_offset,
                 roughing_delta,
                 roughing_feed,
                 output):

        self.image = image
        self.units = units
        self.tool = tool_shape
        self.pixelsize = pixelsize
        self.pixelstep = pixelstep
        self.safetyheight = safetyheight
        self.tolerance = tolerance
        self.base_feed = feed
        self.convert_rows = convert_rows
        self.convert_cols = convert_cols
        self.cols_first_flag = cols_first_flag
        self.entry_cut = entry_cut
        self.spindle_speed = spindle_speed
        self.roughing_offset = roughing_offset
        self.roughing_delta = roughing_delta
        self.roughing_feed = roughing_feed
        self.output = output

        self.target = None

        self.cache = {}

        w, h = self.w, self.h = image.shape
        ts = self.ts = tool_shape.shape[0]

        self.h1 = h - ts
        self.w1 = w - ts

        self.tool_shape = tool_shape * self.pixelsize * ts / 2

        self.g = None
        self.feed = None
        self.ro = None
        self.rd = None

    def one_pass(self):
        g = self.g
        g.set_feed(self.feed)

        if self.convert_cols and self.cols_first_flag:
            self.g.set_plane(19)
            self.mill_cols(self.convert_cols, True)
            if self.convert_rows: g.safety()
        if self.convert_rows:
            self.g.set_plane(18)
            self.mill_rows(self.convert_rows, not self.cols_first_flag)
        if self.convert_cols and not self.cols_first_flag:
            self.g.set_plane(19)
            if self.convert_rows: g.safety()
            self.mill_cols(self.convert_cols, not self.convert_rows)
        if self.convert_cols:
            self.convert_cols.reset()
        if self.convert_rows:
            self.convert_rows.reset()
        g.safety()

    def convert(self):

        file = open(self.output, "wb")
        self.target = lambda x: file.write(str(x) + "\n")

        self.g = Gcode(safetyheight=self.safetyheight,
                       tolerance=self.tolerance,
                       spindle_speed=self.spindle_speed,
                       units=self.units,
                       target=self.target
                       )
        g = self.g

        g.begin()
        g.continuous(self.tolerance)
        g.safety()
        if self.roughing_delta and self.roughing_offset:
            base_image = self.image
            rough = make_tool_shape(ball_tool, 2 * self.roughing_offset, self.pixelsize)
            w, h = base_image.shape
            tw, th = rough.shape
            w1 = w + tw
            h1 = h + th
            nim1 = numpy.zeros((w1, h1), dtype=numpy.float32) + base_image.min()
            nim1[tw / 2:tw / 2 + w, th / 2:th / 2 + h] = base_image
            self.image = numpy.zeros((w, h), dtype=numpy.float32)

            for j in range(0, w):
                progress(j, w)
                for i in range(0, h):
                    self.image[j, i] = (nim1[j:j + tw, i:i + th] - rough).max()

            self.feed = self.roughing_feed
            r = -self.roughing_delta
            m = self.image.min()
            self.ro = self.roughing_offset

            while r > m:
                self.rd = r
                self.one_pass()
                r = r - self.roughing_delta

            if r < m + epsilon:
                self.rd = m
                self.one_pass()

            self.image = base_image
            self.cache.clear()

        self.feed = self.base_feed
        self.ro = 0
        self.rd = self.image.min()
        self.one_pass()
        g.end()

    def get_z(self, x, y):
        try:
            return min(0, max(self.rd, self.cache[x, y]) + self.ro)
        except KeyError:
            m1 = self.image[y:y + self.ts, x:x + self.ts]
            self.cache[x, y] = d = (m1 - self.tool).max()
            return min(0, max(self.rd, d) + self.ro)

    def get_dz_dy(self, x, y):
        y1 = max(0, y - 1)
        y2 = min(self.image.shape[0] - 1, y + 1)
        dy = self.pixelsize * (y2 - y1)
        return (self.get_z(x, y2) - self.get_z(x, y1)) / dy

    def get_dz_dx(self, x, y):
        x1 = max(0, x - 1)
        x2 = min(self.image.shape[1] - 1, x + 1)
        dx = self.pixelsize * (x2 - x1)
        return (self.get_z(x2, y) - self.get_z(x1, y)) / dx

    def mill_rows(self, convert_scan, primary):
        w1 = self.w1
        h1 = self.h1
        pixelsize = self.pixelsize
        pixelstep = self.pixelstep
        jrange = range(0, w1, 1)
        if w1 - 1 not in jrange:
            jrange.append(w1 - 1)
        irange = range(h1)

        for j in jrange:
            progress(jrange.index(j), len(jrange))
            y = (w1 - j) * pixelsize
            scan = []
            for i in irange:
                x = i * pixelsize
                milldata = (i, (x, y, self.get_z(i, j)),
                            self.get_dz_dx(i, j), self.get_dz_dy(i, j))
                scan.append(milldata)
            for flag, points in convert_scan(primary, scan):
                if flag:
                    self.entry_cut(self, points[0][0], j, points)
                for p in points:
                    self.g.cut(*p[1])
            self.g.flush()

    def mill_cols(self, convert_scan, primary):
        w1 = self.w1
        h1 = self.h1
        pixelsize = self.pixelsize
        pixelstep = self.pixelstep
        jrange = range(0, h1, pixelstep)
        irange = range(w1)
        if h1 - 1 not in jrange: jrange.append(h1 - 1)
        jrange.reverse()

        for j in jrange:
            progress(jrange.index(j), len(jrange))
            x = j * pixelsize
            scan = []
            for i in irange:
                y = (w1 - i) * pixelsize
                milldata = (i, (x, y, self.get_z(j, i)),
                            self.get_dz_dy(j, i), self.get_dz_dx(j, i))
                scan.append(milldata)
            for flag, points in convert_scan(primary, scan):
                if flag:
                    self.entry_cut(self, j, points[0][0], points)
                for p in points:
                    self.g.cut(*p[1])
            self.g.flush()


class SimpleEntryCut:
    def __init__(self, feed):
        self.feed = feed

    def __call__(self, conv, i0, j0, points):
        p = points[0][1]
        if self.feed:
            conv.g.set_feed(self.feed)
        conv.g.safety()
        conv.g.rapid(p[0], p[1])
        if self.feed:
            conv.g.set_feed(conv.feed)


def circ(r, b):
    """
    Calculate the portion of the arc to do so that none is above the
    safety height (that's just silly)
    """

    z = r ** 2 - (r - b) ** 2
    if z < 0:
        z = 0
    return z ** .5


class ArcEntryCut:
    def __init__(self, feed, max_radius):
        self.feed = feed
        self.max_radius = max_radius

    def __call__(self, conv, i0, j0, points):

        if len(points) < 2:
            p = points[0][1]
            if self.feed:
                conv.g.set_feed(self.feed)
            conv.g.safety()
            conv.g.rapid(p[0], p[1])
            if self.feed:
                conv.g.set_feed(conv.feed)
            return

        p1 = points[0][1]
        p2 = points[1][1]
        z0 = p1[2]

        lim = int(ceil(self.max_radius / conv.pixelsize))
        r = range(1, lim)

        if self.feed:
            conv.g.set_feed(self.feed)

        conv.g.safety()

        x, y, z = p1

        pixelsize = conv.pixelsize

        cx = cmp(p1[0], p2[0])
        cy = cmp(p1[1], p2[1])

        radius = self.max_radius

        if cx != 0:
            h1 = conv.h1
            for di in r:
                dx = di * pixelsize
                i = i0 + cx * di
                if i < 0 or i >= h1: break
                z1 = conv.get_z(i, j0)
                dz = (z1 - z0)
                if dz <= 0: continue
                if dz > dx:
                    conv.g.write("(case 1)")
                    radius = dx
                    break
                rad1 = (dx * dx / dz + dz) / 2
                if rad1 < radius:
                    radius = rad1
                if dx > radius:
                    break

            z1 = min(p1[2] + radius, conv.safetyheight)
            x1 = p1[0] + cx * circ(radius, z1 - p1[2])
            conv.g.rapid(x1, p1[1])
            conv.g.cut(z=z1)

            conv.g.flush()
            conv.g.lastgcode = None

            if cx > 0:
                conv.g.write("G3 X{0} Z{1} R{2}".format(p1[0], p1[2], radius))
            else:
                conv.g.write("G2 X{0} Z{1} R{2}".format(p1[0], p1[2], radius))

            conv.g.lastx = p1[0]
            conv.g.lasty = p1[1]
            conv.g.lastz = p1[2]

        else:
            w1 = conv.w1
            for dj in r:
                dy = dj * pixelsize
                j = j0 - cy * dj
                if j < 0 or j >= w1:
                    break
                z1 = conv.get_z(i0, j)
                dz = (z1 - z0)
                if dz <= 0:
                    continue
                if dz > dy:
                    radius = dy
                    break
                rad1 = (dy * dy / dz + dz) / 2
                if rad1 < radius:
                    radius = rad1
                if dy > radius:
                    break

            z1 = min(p1[2] + radius, conv.safetyheight)
            y1 = p1[1] + cy * circ(radius, z1 - p1[2])
            conv.g.rapid(p1[0], y1)
            conv.g.cut(z=z1)

            conv.g.flush()
            conv.g.lastgcode = None
            if cy > 0:
                conv.g.write("G2 Y%f Z%f R%f" % (p1[1], p1[2], radius))
            else:
                conv.g.write("G3 Y%f Z%f R%f" % (p1[1], p1[2], radius))
            conv.g.lastx = p1[0]
            conv.g.lasty = p1[1]
            conv.g.lastz = p1[2]

        if self.feed:
            conv.g.set_feed(conv.feed)


def main():
    file_name = "/home/turboss/Projects/i2gTest/A.tif"
    image_file = Image.open(file_name)

    size = image_file.size
    dpi_w, dpi_h = image_file.info['dpi']
    bit_depth = image_file.mode

    w, h = size

    numpy_image = None

    if bit_depth == "I;16":
        # print("16 BIT BW {0} {1} dpi".format(dpi_w, dpi_h))
        numpy_image = numpy.fromstring(
            tobytes(image_file),
            dtype=numpy.uint16).reshape((h, w)).astype(numpy.float32)
        numpy_image = numpy_image / int(0xffff)

    elif bit_depth == "L":
        # print("8 BIT BW {0} {1} dpi".format(dpi_w, dpi_h))
        numpy_image = numpy.fromstring(
            tobytes(image_file),
            dtype=numpy.uint8).reshape((h, w)).astype(numpy.float32)
        numpy_image = numpy_image / int(0xff)

    maker = tool_makers[0]
    tool_diameter = 1.5
    pixel_size = 0.08
    tool = make_tool_shape(maker, tool_diameter, pixel_size)
    step = w / float(dpi_w)

    depth = 2

    numpy_image = numpy_image * depth
    numpy_image = numpy_image - depth

    rows = 1
    columns = 0
    columns_first = 3
    spindle_speed = 24000

    if rows:
        convert_rows = convert_makers[0]()
    else:
        convert_rows = None
    if columns:
        convert_cols = convert_makers[0]()
    else:
        convert_cols = None

    if 0 and rows and columns:
        slope = tan(45 * pi / 180)
        if columns_first:
            convert_rows = ReduceScanLace(convert_rows, slope, step + 1)
        else:
            convert_cols = ReduceScanLace(convert_cols, slope, step + 1)
        if 0 > 1:
            if columns_first:
                convert_cols = ReduceScanLace(convert_cols, slope, step + 1)
            else:
                convert_rows = ReduceScanLace(convert_rows, slope, step + 1)

    units = "G21"
    tolerance = 0.0001
    feed = 2000
    plunge = 600

    output = "/home/turboss/Projects/i2gTest/test.ngc"

    i2g = Converter(numpy_image,
                    units,
                    tool,
                    pixel_size,
                    step,
                    depth,
                    tolerance,
                    feed,
                    convert_rows,
                    convert_cols,
                    columns_first,
                    ArcEntryCut(plunge, .125),
                    spindle_speed,
                    0,
                    0,
                    feed,
                    output
                    )

    i2g.convert()


if __name__ == "__main__":
    main()
