#!/usr/bin/env python3
"""Dump the interesting attributes of a binary AndroidManifest.xml (AOSP binary XML)."""
import struct
import sys
import zipfile

RES_XML_TYPE = 0x0003
RES_STRING_POOL_TYPE = 0x0001
RES_XML_START_ELEMENT_TYPE = 0x0102


def parse_string_pool(data, off):
    (_type, header_size, size) = struct.unpack_from("<HHI", data, off)
    (string_count, style_count, flags, strings_start, styles_start) = struct.unpack_from("<IIIII", data, off + 8)
    offsets = struct.unpack_from("<%dI" % string_count, data, off + header_size)
    utf8 = bool(flags & (1 << 8))
    base = off + strings_start
    out = []
    for o in offsets:
        p = base + o
        if utf8:
            # u16 len (possibly 2 words), u8 len2, bytes, 0
            n = data[p]
            if n & 0x80:
                n = ((n & 0x7F) << 8) | data[p + 1]
                p += 2
            else:
                p += 1
            m = data[p]
            if m & 0x80:
                m = ((m & 0x7F) << 8) | data[p + 1]
                p += 2
            else:
                p += 1
            out.append(data[p:p + m].decode("utf-8", "replace"))
        else:
            n = struct.unpack_from("<H", data, p)[0]
            p += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", data, p)[0]
                p += 2
            out.append(data[p:p + n * 2].decode("utf-16-le", "replace"))
    return out, size


def main(path):
    if path.endswith(".apk"):
        with zipfile.ZipFile(path) as z:
            data = z.read("AndroidManifest.xml")
    else:
        data = open(path, "rb").read()

    off = 8  # skip the outer XML chunk header
    strings = []
    while off < len(data):
        (_type, _hs, size) = struct.unpack_from("<HHI", data, off)
        if size == 0:
            break
        if _type == RES_STRING_POOL_TYPE:
            strings, _ = parse_string_pool(data, off)
        elif _type == RES_XML_START_ELEMENT_TYPE:
            (_t, _h, _s, line, _c) = struct.unpack_from("<HHIIi", data, off)
            ns, name = struct.unpack_from("<iI", data, off + 16)
            attr_count = struct.unpack_from("<H", data, off + 28)[0]
            elem = strings[name]
            attrs = []
            for i in range(attr_count):
                a = off + 36 + i * 20
                ans, aname, araw = struct.unpack_from("<iiI", data, a)
                size_v, res0, dtype, ddata = struct.unpack_from("<HBBI", data, a + 12)
                if dtype == 0x03:      # string
                    val = strings[ddata] if araw == 0xFFFFFFFF else strings[araw]
                elif dtype == 0x12:    # boolean
                    val = bool(ddata)
                elif dtype == 0x10:    # int dec
                    val = ddata
                elif dtype == 0x11:    # int hex
                    val = hex(ddata)
                elif dtype == 0x01:    # reference
                    val = "@0x%08x" % ddata
                else:
                    val = "type=0x%02x data=0x%x" % (dtype, ddata)
                attrs.append("%s=%s" % (strings[aname], val))
            print("%-16s %s" % (elem, " ".join(attrs)))
        off += size


if __name__ == "__main__":
    main(sys.argv[1])
