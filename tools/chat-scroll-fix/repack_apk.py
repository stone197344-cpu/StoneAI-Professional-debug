#!/usr/bin/env python3
"""
Replace a single entry inside an APK (zip) while preserving everything else.

The output keeps the original's entry order, compression methods, alignment
padding, inter-entry junk and central directory records; only the replaced
entry's bytes (and its crc/sizes) change, and the old APK Signing Block (if the
apk was signed) is dropped so the apk can be re-signed.

Usage:
    python3 repack_apk.py original.apk new_classes3.dex output.apk classes3.dex
"""

import struct
import sys
import zlib

LFH = 0x04034B50
CDH = 0x02014B50
EOCD = 0x06054B50
SIG_BLOCK_MAGIC = b"APK Sig Block 42"


def raw_deflate(data, level=9):
    """Compress to a raw deflate stream (what zip entries contain)."""
    c = zlib.compressobj(level, zlib.DEFLATED, -15)
    return c.compress(data) + c.flush()


def parse_central_directory(raw):
    i = raw.rfind(b"PK\x05\x06")
    if i < 0:
        raise SystemExit("no EOCD found")
    (_sig, _disk, _cddisk, nrec, nrec_tot, _cdsize, cdoff, _clen) = struct.unpack(
        "<IHHHHIIH", raw[i:i + 22])
    if nrec != nrec_tot:
        raise SystemExit("multi-disk zip is not supported")
    entries = []
    off = cdoff
    for _ in range(nrec):
        (sig, vmade, vneed, flags, method, mtime, mdate, crc, csize, usize,
         fnl, efl, clen, dstart, iattr, eattr, lho) = struct.unpack(
             "<IHHHHHHIIIHHHHHII", raw[off:off + 46])
        if sig != CDH:
            raise SystemExit("bad central directory record at %d" % off)
        name = raw[off + 46:off + 46 + fnl].decode("utf-8")
        extra = raw[off + 46 + fnl:off + 46 + fnl + efl]
        comment = raw[off + 46 + fnl + efl:off + 46 + fnl + efl + clen]
        entries.append(dict(name=name, vmade=vmade, vneed=vneed, flags=flags,
                            method=method, mtime=mtime, mdate=mdate, crc=crc,
                            csize=csize, usize=usize, extra_cd=extra,
                            comment=comment, dstart=dstart, iattr=iattr,
                            eattr=eattr, lho=lho))
        off += 46 + fnl + efl + clen
    return cdoff, entries


def local_region(raw, lho):
    (sig, vneed, flags, method, mtime, mdate, crc, csize, usize,
     fnl, efl) = struct.unpack("<IHHHHHIIIHH", raw[lho:lho + 30])
    if sig != LFH:
        raise SystemExit("bad local header at %d" % lho)
    if flags & 0x08:
        raise SystemExit("data descriptor used; unsupported")
    name = raw[lho + 30:lho + 30 + fnl]
    return name, vneed, flags, method, mtime, mdate, crc, csize, usize, fnl, efl


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    src, new_entry_path, dst, target = sys.argv[1:5]

    raw = open(src, "rb").read()
    new_bytes = open(new_entry_path, "rb").read()
    cdoff, entries = parse_central_directory(raw)

    physical = sorted(entries, key=lambda e: e["lho"])
    if [e["name"] for e in physical] != [e["name"] for e in entries]:
        raise SystemExit("central directory is not in physical order; unsupported")

    out = bytearray()
    offsets = {}
    cursor = 0
    replaced = False
    for e in entries:
        name, vneed, flags, method, mtime, mdate, crc, csize, usize, fnl, efl = \
            local_region(raw, e["lho"])
        end = e["lho"] + 30 + fnl + efl + csize
        out += raw[cursor:cursor + (e["lho"] - cursor)]      # keep inter-entry junk
        offsets[e["name"]] = len(out)
        if e["name"] == target:
            body = raw_deflate(new_bytes) if method == 8 else new_bytes
            crc = zlib.crc32(new_bytes) & 0xFFFFFFFF
            csize = len(body)
            usize = len(new_bytes)
            replaced = True
        else:
            body = raw[e["lho"] + 30 + fnl + efl:end]
        out += struct.pack("<IHHHHHIIIHH", LFH, vneed, flags, method, mtime,
                           mdate, crc, csize, usize, fnl, efl)
        out += name + raw[e["lho"] + 30 + fnl:e["lho"] + 30 + fnl + efl] + body
        cursor = end
    if not replaced:
        raise SystemExit("entry %r not found" % target)

    trailing = raw[cursor:cdoff]
    if SIG_BLOCK_MAGIC in trailing[-32:]:
        trailing = b""                                        # drop the old signature
    out += trailing

    cd_off = len(out)
    for e in entries:
        name = e["name"].encode("utf-8")
        crc, csize, usize = e["crc"], e["csize"], e["usize"]
        if e["name"] == target:
            crc = zlib.crc32(new_bytes) & 0xFFFFFFFF
            usize = len(new_bytes)
            csize = len(raw_deflate(new_bytes)) if e["method"] == 8 else usize
        out += struct.pack("<IHHHHHHIIIHHHHHII", CDH, e["vmade"], e["vneed"],
                           e["flags"], e["method"], e["mtime"], e["mdate"], crc,
                           csize, usize, len(name), len(e["extra_cd"]),
                           len(e["comment"]), e["dstart"], e["iattr"],
                           e["eattr"], offsets[e["name"]])
        out += name + e["extra_cd"] + e["comment"]

    cd_size = len(out) - cd_off
    out += struct.pack("<IHHHHIIH", EOCD, 0, 0, len(entries), len(entries),
                       cd_size, cd_off, 0)

    open(dst, "wb").write(out)
    print("wrote %s (%d bytes, %d entries, replaced %s)" %
          (dst, len(out), len(entries), target))


if __name__ == "__main__":
    main()
