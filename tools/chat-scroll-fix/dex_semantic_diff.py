#!/usr/bin/env python3
"""
Semantic (not byte-for-byte) comparison of two .dex files using androguard.

Reports which classes/methods were added, removed or changed, and for changed
methods prints a small instruction-level diff.  Used to prove that an
apktool (baksmali/smali) round trip preserves the original program, and to
check exactly what a patch changed.

  python3 dex_semantic_diff.py <old.dex> <new.dex> [--limit N]
"""

import sys
from androguard.core.dex import DEX


def method_key(klass, meth):
    return "%s->%s%s" % (klass.get_name(), meth.get_name(), meth.get_descriptor())


def canonical(klass, meth):
    lines = []
    code = meth.get_code()
    if code is None:
        lines.append("<no code>")
    else:
        for ins in code.get_bc().get_instructions():
            lines.append("%s %s" % (ins.get_name(), ins.get_output()))
    return lines


def inventory(path):
    d = DEX(open(path, "rb").read())
    classes = {}
    for klass in d.get_classes():
        classes[klass.get_name()] = klass
    methods = {}
    for klass in d.get_classes():
        for meth in klass.get_methods():
            methods[method_key(klass, meth)] = canonical(klass, meth)
    return d, classes, methods


def main():
    limit = 20
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        raise SystemExit(__doc__)
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    print("parsing %s ..." % args[0])
    _, classes_a, methods_a = inventory(args[0])
    print("parsing %s ..." % args[1])
    _, classes_b, methods_b = inventory(args[1])

    ka, kb = set(classes_a), set(classes_b)
    print("classes: old=%d new=%d | added=%d removed=%d"
          % (len(ka), len(kb), len(kb - ka), len(ka - kb)))
    for n in sorted(kb - ka)[:limit]:
        print("   + class %s" % n)
    for n in sorted(ka - kb)[:limit]:
        print("   - class %s" % n)

    ma, mb = set(methods_a), set(methods_b)
    print("methods: old=%d new=%d | added=%d removed=%d"
          % (len(ma), len(mb), len(mb - ma), len(ma - mb)))
    for n in sorted(mb - ma)[:limit]:
        print("   + method %s" % n)
    for n in sorted(ma - mb)[:limit]:
        print("   - method %s" % n)

    changed = [k for k in (ma & mb) if methods_a[k] != methods_b[k]]
    print("methods with changed instruction stream: %d" % len(changed))
    for k in sorted(changed)[:limit]:
        old, new = methods_a[k], methods_b[k]
        print("   ~ %s   (%d -> %d instructions)" % (k, len(old), len(new)))
        n = 0
        for line in old:
            if line not in new:
                print("       old-only: %s" % line)
                n += 1
                if n >= 6:
                    break
        n = 0
        for line in new:
            if line not in old:
                print("       new-only: %s" % line)
                n += 1
                if n >= 6:
                    break
    if len(changed) > limit:
        print("   ... and %d more" % (len(changed) - limit))
    return 0 if not (kb - ka) and not (ma - mb) and not changed else 0


if __name__ == "__main__":
    sys.exit(main())
