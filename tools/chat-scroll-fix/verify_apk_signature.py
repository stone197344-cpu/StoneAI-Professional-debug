#!/usr/bin/env python3
"""
Independently verify an APK's APK Signature Scheme v2/v3 blocks.

Implements the published Android scheme (chunked content digest 0xa5/0x5a,
RSA PKCS#1 v1.5 signatures) from scratch with the `cryptography` package, so it
cross-checks whatever signing tool produced the file.

  python3 verify_apk_signature.py <apk> [--dump]

Exit code 0 only if every present scheme verifies.
"""

import hashlib
import struct
import sys

from cryptography.x509 import load_der_x509_certificate
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

V2_ID = 0x7109871A
V3_ID = 0xF05368C0
MAGIC = b"APK Sig Block 42"
# IDs as emitted by Android build-tools apksigner (0x0103 == RSA PKCS#1 v1.5 / SHA-256,
# empirically confirmed against a real apksigner-signed APK) plus the small
# ContentDigestAlgorithm enum values some tools use.
CONTENT_DIGEST_IDS = {
    0x0101: "SHA-256", 0x0102: "SHA-512", 0x0103: "SHA-256", 0x0104: "SHA-512",
    1: "SHA-256", 2: "SHA-512",
}
SIG_IDS = {0x0103: ("SHA-256", hashes.SHA256), 0x0104: ("SHA-512", hashes.SHA512)}


def u32(buf, off=0):
    return struct.unpack_from("<I", buf, off)[0]


def u64(buf, off=0):
    return struct.unpack_from("<Q", buf, off)[0]


def find_eocd(raw):
    for i in range(len(raw) - 22, max(-1, len(raw) - 22 - 65535), -1):
        if raw[i:i + 4] == b"PK\x05\x06":
            if i + 22 + struct.unpack_from("<H", raw, i + 20)[0] == len(raw):
                return i
    raise SystemExit("EOCD not found")


def read_lp(buf, off, what):
    """Read a uint32-length-prefixed blob, return (blob, next_offset)."""
    n = u32(buf, off)
    off += 4
    if off + n > len(buf):
        raise SystemExit("truncated %s (need %d, have %d)" % (what, n, len(buf) - off))
    return buf[off:off + n], off + n


def chunk_digest(section, algo):
    """APK content chunk digest: 1 MiB chunks, 0xa5 || len || chunk, then 0x5a || n || digests."""
    h = hashlib.new(algo)
    chunk_digests = []
    for i in range(0, len(section), 1024 * 1024):
        chunk = section[i:i + 1024 * 1024]
        ch = hashlib.new(algo)
        ch.update(b"\xa5")
        ch.update(struct.pack("<I", len(chunk)))
        ch.update(chunk)
        chunk_digests.append(ch.digest())
    h.update(b"\x5a")
    h.update(struct.pack("<I", len(chunk_digests)))
    for d in chunk_digests:
        h.update(d)
    return h.digest()


def content_digest(raw, block_start, cd_start, eocd_start, algo):
    """Digest sections 1..3; section 3 is the EOCD with its cd-offset field = block_start."""
    eocd = bytearray(raw[eocd_start:])
    struct.pack_into("<I", eocd, 16, block_start)
    chunks = []
    for section in (raw[:block_start], raw[cd_start:eocd_start], bytes(eocd)):
        chunks.append(section)
    # digest is over all three sections' chunk digests, numbered globally
    digests = []
    for section in chunks:
        for i in range(0, len(section), 1024 * 1024):
            chunk = section[i:i + 1024 * 1024]
            ch = hashlib.new(algo)
            ch.update(b"\xa5")
            ch.update(struct.pack("<I", len(chunk)))
            ch.update(chunk)
            digests.append(ch.digest())
    h = hashlib.new(algo)
    h.update(b"\x5a")
    h.update(struct.pack("<I", len(digests)))
    for d in digests:
        h.update(d)
    return h.digest()


def parse_digest_records(buf):
    out = []
    off = 0
    while off < len(buf):
        rec, off = read_lp(buf, off, "digest")
        alg = u32(rec, 0)
        dlen = u32(rec, 4)
        out.append((alg, rec[8:8 + dlen]))
    return out


def parse_sig_records(buf):
    out = []
    off = 0
    while off < len(buf):
        rec, off = read_lp(buf, off, "signature")
        alg = u32(rec, 0)
        slen = u32(rec, 4)
        out.append((alg, rec[8:8 + slen]))
    return out


def parse_seq(buf):
    """length-prefixed sequence -> list of length-prefixed items as raw bytes."""
    items = []
    off = 0
    while off < len(buf):
        item, off = read_lp(buf, off, "sequence item")
        items.append(item)
    return items


def parse_value(value):
    """APK Signing Block pair value -> list of signers (raw bytes)."""
    # value is a length-prefixed sequence of length-prefixed signers
    seq_content, _ = read_lp(value, 0, "signers sequence")
    return parse_seq(seq_content)


def verify(apk_path, dump=False):
    raw = open(apk_path, "rb").read()
    eocd_start = find_eocd(raw)
    cd_start = u32(raw, eocd_start + 16)
    block_end = cd_start
    if raw[block_end - 16:block_end] != MAGIC:
        raise SystemExit("no APK Signing Block (not v2/v3 signed)")
    block_size = u64(raw, block_end - 24)          # trailing size field
    block_start = block_end - 8 - block_size
    if u64(raw, block_start) != block_size:
        raise SystemExit("signing block size fields disagree")
    print("APK %d bytes | signing block [%d, %d) = %d bytes | CD @%d | EOCD @%d"
          % (len(raw), block_start, block_end, block_size + 8, cd_start, eocd_start))

    pairs = {}
    off = block_start + 8
    while off < block_end - 24:
        plen = u64(raw, off)
        pid = u32(raw, off + 8)
        value = raw[off + 12:off + 8 + plen]
        pairs[pid] = value
        if dump:
            print("  pair 0x%08x len=%d" % (pid, plen))
        off += 8 + plen

    ok = True
    for pid, name in ((V2_ID, "v2"), (V3_ID, "v3")):
        if pid not in pairs:
            print("  [%s] absent" % name)
            continue
        signers = parse_value(pairs[pid])
        for si, signer in enumerate(signers):
            so = 0
            signed_data, so = read_lp(signer, so, "signed data")
            p = 0
            digests_raw, p = read_lp(signed_data, p, "digests")
            certs_raw, p = read_lp(signed_data, p, "certs")
            if name == "v3":
                minsdk, maxsdk = u32(signed_data, p), u32(signed_data, p + 4)
                p += 8
            attrs, p = read_lp(signed_data, p, "attrs")
            if p != len(signed_data):
                extra = signed_data[p:]
                print("        note: %d trailing signed-data byte(s): %s"
                      % (len(extra), extra.hex()))
                assert extra == b"\0" * len(extra), "unexpected signed-data tail"
            if name == "v3":
                assert so + 8 <= len(signer)
                so += 8
            sigs_raw, so = read_lp(signer, so, "signatures")
            pubkey, so = read_lp(signer, so, "public key")
            assert so == len(signer), "trailing signer bytes"
            if name == "v3":
                assert u32(signer, 4 + len(signed_data)) == minsdk
                assert u32(signer, 8 + len(signed_data)) == maxsdk

            certs = [load_der_x509_certificate(c) for c in parse_seq(certs_raw)]
            digests = parse_digest_records(digests_raw)
            sigs = parse_sig_records(sigs_raw)
            cert = certs[0]
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
            cert_spki = cert.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
            if cert_spki != pubkey:
                print("        public key MISMATCH between certificate and signer record")
                ok = False
            print("  [%s] signer %d: %d cert(s), %d digest(s), %d signature(s)%s"
                  % (name, si, len(certs), len(digests), len(sigs),
                     " minSdk=%d maxSdk=%d" % (minsdk, maxsdk) if name == "v3" else ""))
            print("        cert: %s" % cert.subject.rfc4514_string())
            print("        cert sha256: %s" % cert.fingerprint(hashes.SHA256()).hex())

            for d_alg, d_val in digests:
                algo = CONTENT_DIGEST_IDS.get(d_alg)
                if algo is None:
                    print("        digest alg 0x%04x unknown" % d_alg)
                    ok = False
                    continue
                expected = content_digest(raw, block_start, cd_start, eocd_start, algo)
                good = expected == d_val
                ok &= good
                print("        content digest %s: %s (%s)"
                      % (algo, d_val.hex()[:32] + "...", "MATCH" if good else
                         "MISMATCH expected " + expected.hex()[:32] + "..."))
            for s_alg, s_val in sigs:
                if s_alg not in SIG_IDS:
                    print("        signature alg 0x%04x unknown" % s_alg)
                    ok = False
                    continue
                s_name, h_fn = SIG_IDS[s_alg]
                try:
                    cert.public_key().verify(
                        s_val, signed_data, padding.PKCS1v15(), h_fn())
                    print("        signature %s over signed data: VALID" % s_name)
                except Exception as exc:  # noqa: BLE001
                    ok = False
                    print("        signature %s over signed data: INVALID (%s)"
                          % (s_name, exc))
    return ok


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    sys.exit(0 if verify(args[0], dump="--dump" in sys.argv) else 1)
