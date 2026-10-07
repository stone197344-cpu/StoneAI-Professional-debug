# Chat scroll fix — StoneAI Professional 1.0.0 (`com.leestone.stoneai`)

## The bug

While the AI streams a reply, the `LaunchedEffect` in `ChatScreen` was keyed on
`messages.size` **and** the last message's content, so it restarted for *every
streamed token* and unconditionally ran
`LazyListState.animateScrollToItem(lastIndex)`.  Any attempt to scroll up was
undone immediately and the never-settling animation kept fighting the user —
the chat could not be scrolled until generation finished.

## The fix

Auto-scroll now runs **only when the user is already at the bottom**; otherwise
nothing touches the scroll position:

| File (smali) | Change |
|---|---|
| `com/leestone/stoneai/ui/ChatScrollSupport.smali` | **new** — `createChatScrollEffect(state, listState, cont)` samples `listState.canScrollForward` at composition time (before the new token is laid out) and builds the effect lambda with `atBottom = !canScrollForward`. |
| `ChatScreenKt$ChatScreen$1$1.smali` | new `$atBottom:Z` field threaded through the constructor/`create()`; `invokeSuspend` bails out of the scroll when `$atBottom == false`; `animateScrollToItem` → `scrollToItem` (instant, no per-token animation restart). |
| `ChatScreenKt.smali` | the lambda is now built by `ChatScrollSupport.createChatScrollEffect(...)` instead of `new-instance` (the only call site). |

The effect key is unchanged, so a user pinned to the bottom still follows the
streaming answer token by token; a user who scrolled up stays where they are,
and auto-follow resumes on its own once they scroll back to the bottom.

## Deliverable

```
release/StoneAI-Professional-1.0.0-chat-scroll-fix.apk               (42,370,368 B)
    sha256 d45912ffdc6279968f19a0c617c75c1cdd2fac54deed09b155fc56c900f1a43e
    APK Signature Scheme v2 + v3   (targetSdk 35 requirement covered)

release/StoneAI-Professional-1.0.0-chat-scroll-fix-v2-only.apk       (42,368,906 B)
    sha256 e5f3edb204888bc6911b418f444505bd291f5b3a52ec3835e7ffb62ff31bcc0a
    v2 only — same scheme as the original build, use only if the first is refused
```

### Installation

The original build's signing key is not available, so Android will **not**
accept this file as an update of the installed app — uninstall first:

```sh
adb uninstall com.leestone.stoneai        # or uninstall from the phone's app list
adb install release/StoneAI-Professional-1.0.0-chat-scroll-fix.apk
```

Uninstalling clears app data: the GGUF models live in
`/data/data/com.leestone.stoneai/files/models` and have to be downloaded again
(if installing from a file manager, allow "install unknown apps" first).

## What was verified (and how)

* **Only the patched code changed.** 939 entries in both APKs, same order, and
  all 938 non-`classes3.dex` entries are byte-identical to the original APK;
  the new `classes3.dex` (377,896 B, dex 038) is the one built from the patched
  smali.  `unzip -t` clean; manifest still parses (minSdk 26 / targetSdk 35,
  `com.leestone.stoneai`, versionName 1.0.0); `META-INF/*` — including
  `META-INF/services/kotlinx.coroutines.*` — is untouched, because the signer
  only appends a signing block instead of re-zipping the archive.
* **The rebuild itself is faithful.**  A control build of the *unpatched*
  decoded tree was compared instruction-by-instruction with the original
  `classes3.dex` (`dex_semantic_diff.py`, androguard): no added/removed classes
  or methods, **0** changed instruction streams.  The patched shard differs
  from the original by exactly the intended delta: +1 class
  (`ChatScrollSupport`), +1 method (`createChatScrollEffect`), +1 overloaded
  lambda constructor / −1 old one, and instruction changes confined to
  `ChatScreenKt$ChatScreen$1$1.create`, `.invokeSuspend` and
  `ChatScreenKt.ChatScreen` (the `$atBottom` guard and
  `animateScrollToItem` → `scrollToItem`).
* **The signature is cryptographically valid.**  `verify_apk_signature.py`
  (spec implementation on top of `cryptography`) recomputes the chunked
  SHA-256 content digest and checks the RSA PKCS#1 v1.5 signature over the
  signed data: v2 *and* v3 MATCH/VALID, certificate consistent.  The same
  script reproduced the digest that real apksigner wrote into the original APK,
  which validates the digest algorithm itself.  androguard 4.1.4 independently
  reports `is_signed_v2=True`, `is_signed_v3=True` and parses the patched dex
  (141 classes).

Signing certificate (this build): `CN=Android Debug,O=Android,C=US`,
sha256 `99b9ae7e2217e9c3a1478346fc90f1e880aa92e1771f40464ebdf4b531647b84`,
keystore alias `androiddebugkey`, store/key password `android`
(`signing/stoneai-chatscrollfix.jks`, also as PKCS12 + PEM).  Keep that
keystore: rebuilds signed with it can update each other.

Not verified: on-device behaviour (no Android runtime here).  If auto-follow
ever misbehaves, the gate in `ChatScrollSupport` is a two-instruction change —
alternatives are `listState.isScrollInProgress` or
`firstVisibleItemIndex + visibleItemsCount >= totalItemsCount`.

## Layout

```
release/                                signed APKs (the deliverable)
tools/chat-scroll-fix/
  apply_patch.py                        patches a decoded apktool tree (3 files)
  repack_apk.py <orig.apk> <new.dex> <out.apk> classes3.dex
                                        swaps one zip entry, keeps every other
                                        entry (and inter-entry layout) intact
  sign_apk_v2v3.mjs <in.apk> <key.pem> <cert.pem> <out.apk> [apk_sign_ts pkg]
                                        adds a v2 (+v3) signing block
                                        (SIGN_SCHEMES=v2 for v2-only)
  verify_apk_signature.py <apk>         independent v2/v3 verifier
  dex_semantic_diff.py <old.dex> <new.dex>
                                        androguard class/method/instruction diff
  dump_manifest.py <apk>                binary AndroidManifest dumper
  artifacts/classes3.dex                the patched dex (already inside the APK)
  smali-patch/                          patched smali of the 3 files + unified diff
  signing/                              keystore + PEMs used for signing
  toolchain/apktool_2.4.1.jar           apktool used for decode/build
```

## Rebuild from scratch

```sh
# 1. original APK out of the split archive in the repo root
cat StoneAI-Professional-debug.7z.00{1,2,3,4} > /tmp/stone.7z
python3 -m pip install py7zr --break-system-packages
python3 -c "import py7zr; py7zr.SevenZipFile('/tmp/stone.7z').extractall('/tmp/stone')"
# -> /tmp/stone/StoneAI-Professional-debug.apk

# 2. decode, patch, rebuild only the smali shard that holds the fix
JAVA_HOME=/path/to/jdk java -jar tools/chat-scroll-fix/toolchain/apktool_2.4.1.jar d -r -f \
    /tmp/stone/StoneAI-Professional-debug.apk -o /tmp/dec
python3 tools/chat-scroll-fix/apply_patch.py /tmp/dec
mkdir -p /tmp/build && cd /tmp/build
cp -r /tmp/dec/res /tmp/dec/resources.arsc /tmp/dec/AndroidManifest.xml /tmp/dec/apktool.yml .
cp -r /tmp/dec/smali_classes3 smali
#   edit apktool.yml: sdkInfo: {minSdkVersion: 26, targetSdkVersion: 35}   (decoded file has null)
JAVA_HOME=/path/to/jdk java -jar ../chat-scroll-fix/toolchain/apktool_2.4.1.jar b . -o /tmp/out.apk
#   (a FileNotFoundException for unknown/DebugProbesKt.bin in the log is harmless)
unzip -p /tmp/out.apk classes.dex > /tmp/classes3.dex

# 3. swap the dex into the original archive and sign it
python3 tools/chat-scroll-fix/repack_apk.py \
    /tmp/stone/StoneAI-Professional-debug.apk /tmp/classes3.dex /tmp/unsigned.apk classes3.dex
npm install apk_sign_ts                 # node 18+; use the matching package dir below
node tools/chat-scroll-fix/sign_apk_v2v3.mjs /tmp/unsigned.apk \
    tools/chat-scroll-fix/signing/key.pem tools/chat-scroll-fix/signing/cert.pem \
    /tmp/signed.apk ./node_modules/apk_sign_ts
python3 tools/chat-scroll-fix/verify_apk_signature.py /tmp/signed.apk   # must exit 0
```

The keystore can be regenerated with
`keytool -genkeypair -keystore signing/stoneai-chatscrollfix.jks -storetype JKS
-storepass android -keypass android -alias androiddebugkey -keyalg RSA -keysize 2048
-validity 10000 -dname "CN=Android Debug,O=Android,C=US"` (keeping the existing
keystore is preferable: APKs signed with it can update each other).
