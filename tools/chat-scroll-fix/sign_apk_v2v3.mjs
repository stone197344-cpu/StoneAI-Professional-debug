#!/usr/bin/env node
/**
 * Minimal, layout-preserving APK signer for Android APK Signature Scheme v2 + v3.
 *
 * Unlike a full re-zip "sign and align" pipeline this:
 *   - keeps every existing zip entry exactly where it was (no re-compression,
 *     no member reordering, no META-INF/* files dropped),
 *   - only appends an APK Signing Block right before the central directory and
 *     patches the EOCD's central-directory offset.
 *
 * Prereqs: `npm install apk_sign_ts` somewhere; point --pkg at that package dir
 * (default /tmp/work/sign/node_modules/apk_sign_ts or $APK_SIGN_TS_DIR).
 *
 * Usage:
 *   node sign_apk_v2v3.mjs <in.apk> <key.pem> <cert.pem> <out.apk> [pkgdir]
 */

import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [inApk, keyPem, certPem, outApk, pkgArg] = process.argv.slice(2);
if (!inApk || !keyPem || !certPem || !outApk) {
  console.error(
    "usage: node sign_apk_v2v3.mjs <in.apk> <key.pem> <cert.pem> <out.apk> [apk_sign_ts-pkg-dir]"
  );
  process.exit(2);
}
const pkgDir =
  pkgArg || process.env.APK_SIGN_TS_DIR || "/tmp/work/sign/node_modules/apk_sign_ts";
const mod = (name) => pathToFileURL(path.join(pkgDir, "dist", name)).href;

const { SigningKey } = await import(mod("SigningKey.js"));
const { V2Signer } = await import(mod("V2Signer.js"));
const { V3Signer } = await import(mod("V3Signer.js"));
const { createSigningBlock, createV2SignaturePair, createV3SignaturePair } =
  await import(mod("ApkSigningBlock.js"));
const { findEndOfCentralDirectory } = await import(mod("ZipUtils.js"));

const apk = new Uint8Array(fs.readFileSync(inApk));
const signingKey = SigningKey.fromPEM(
  fs.readFileSync(keyPem, "utf8"),
  fs.readFileSync(certPem, "utf8"),
  process.env.KEY_PASSWORD
);

const eocd = findEndOfCentralDirectory(apk);
if (!eocd) throw new Error("EOCD not found - not a zip/apk");
const cdOffset = eocd.centralDirectoryOffset;
const eocdOffset = eocd.recordOffset;
console.log(
  "input %d bytes, EOCD@%d, centralDirectory@%d, %d entries",
  apk.length, eocdOffset, cdOffset, eocd.entryCount
);

// Refuse to sign an apk that already has a signing block: the caller must
// rebuild it after changing entries anyway (stale signatures must be dropped).
const magic = Buffer.from("APK Sig Block 42");
if (cdOffset - 16 >= 0 &&
    Buffer.compare(Buffer.from(apk.subarray(cdOffset - 16, cdOffset)), magic) === 0) {
  throw new Error("input already contains an APK Signing Block; strip it first");
}

const digestAlgorithm = "SHA-256";
const schemes = (process.env.SIGN_SCHEMES || "v2,v3").split(",").map((s) => s.trim());
const { v2Value } = await new V2Signer({ signingKey, digestAlgorithm }).sign(
  apk, cdOffset, eocdOffset
);
const pairs = [createV2SignaturePair(v2Value)];
let v3Value = { length: 0 };
if (schemes.includes("v3")) {
  ({ v3Value } = await new V3Signer({
    signingKey,
    digestAlgorithm,
    minSdkVersion: 26, // manifest minSdkVersion of the app
    maxSdkVersion: 0x7fffffff,
  }).sign(apk, cdOffset, eocdOffset));
  pairs.push(createV3SignaturePair(v3Value));
}
console.log("schemes: %s", schemes.join("+"));

const signingBlock = createSigningBlock(pairs);
console.log("signing block: %d bytes (v2 %d, v3 %d)", signingBlock.length,
            v2Value.length, v3Value.length);

const out = Buffer.concat([
  Buffer.from(apk.subarray(0, cdOffset)),
  Buffer.from(signingBlock),
  Buffer.from(apk.subarray(cdOffset, eocdOffset)),
  (() => {
    const tail = Buffer.from(apk.subarray(eocdOffset));
    tail.writeUInt32LE(cdOffset + signingBlock.length, 16); // EOCD cd offset
    return tail;
  })(),
]);
fs.writeFileSync(outApk, out);
console.log("wrote %s (%d bytes, +%d)", outApk, out.length, out.length - apk.length);
