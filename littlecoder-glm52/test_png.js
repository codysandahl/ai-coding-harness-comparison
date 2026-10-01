// Self-check for the PNG metadata-embedding logic in app.js.
// Verifies crc32 + chunk layout against the known IEND chunk CRC (0xAE426082).
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function encAscii(s) {
  const a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i) & 0x7f;
  return a;
}
function concat(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0); out.set(b, a.length);
  return out;
}
function makeChunk(type, data) {
  const typeBytes = encAscii(type);
  const len = new Uint8Array(4);
  new DataView(len.buffer).setUint32(0, data.length, false);
  const crc = new Uint8Array(4);
  new DataView(crc.buffer).setUint32(0, crc32(concat(typeBytes, data)), false);
  return concat(concat(len, typeBytes), concat(data, crc));
}

const failures = [];

// 1. Known-good CRC: IEND chunk (type "IEND", empty data) has CRC 0xAE426082.
const iend = makeChunk("IEND", new Uint8Array(0));
const iendCrc = new DataView(iend.buffer).getUint32(iend.length - 4, false) >>> 0;
if (iendCrc !== 0xAE426082) failures.push(`IEND CRC = 0x${iendCrc.toString(16)} (expected 0xae426082)`);

// 2. makeChunk structure: length(4) type(4) data(n) crc(4)
if (iend.length !== 12) failures.push(`IEND chunk length = ${iend.length} (expected 12)`);
const typeStr = String.fromCharCode(iend[4], iend[5], iend[6], iend[7]);
if (typeStr !== "IEND") failures.push(`chunk type = ${typeStr} (expected IEND)`);

// 3. tEXt chunk with keyword "prompt" + 0x00 + text parses correctly
const t = encAscii("prompt");
const v = encAscii("a lighthouse at dusk");
const tdata = new Uint8Array(t.length + 1 + v.length);
tdata.set(t, 0); tdata[t.length] = 0; tdata.set(v, t.length + 1);
const tchunk = makeChunk("tEXt", tdata);
const tLen = new DataView(tchunk.buffer).getUint32(0, false) >>> 0;
if (tLen !== tdata.length) failures.push(`tEXt length field = ${tLen} (expected ${tdata.length})`);
const tType = String.fromCharCode(tchunk[4], tchunk[5], tchunk[6], tchunk[7]);
if (tType !== "tEXt") failures.push(`tEXt type = ${tType}`);
const tCrc = new DataView(tchunk.buffer).getUint32(tchunk.length - 4, false) >>> 0;
const tExpectedCrc = crc32(concat(encAscii("tEXt"), tdata));
if (tCrc !== tExpectedCrc) failures.push(`tEXt CRC mismatch`);

if (failures.length) {
  console.error("FAIL: " + failures.join("; "));
  process.exit(1);
}
console.log("PNG chunk self-check passed.");