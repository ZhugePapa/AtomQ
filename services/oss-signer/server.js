import express from "express";
import OSS from "ali-oss";
import dotenv from "dotenv";

dotenv.config();

const required = [
  "OSS_ACCESS_KEY_ID",
  "OSS_ACCESS_KEY_SECRET",
  "OSS_REGION",
  "OSS_BUCKET",
  "OSS_PREFIX"
];

for (const key of required) {
  if (!process.env[key] || !process.env[key].trim()) {
    throw new Error(`Missing required env: ${key}`);
  }
}

const app = express();
const port = Number(process.env.PORT || 3000);
const prefix = normalizePrefix(process.env.OSS_PREFIX);
const expiresIn = Number(process.env.SIGN_EXPIRES_SECONDS || 180);
const forceHttps = String(process.env.OSS_SIGN_FORCE_HTTPS || "true").toLowerCase() !== "false";

const client = new OSS({
  region: process.env.OSS_REGION,
  bucket: process.env.OSS_BUCKET,
  accessKeyId: process.env.OSS_ACCESS_KEY_ID,
  accessKeySecret: process.env.OSS_ACCESS_KEY_SECRET
});

app.get("/health", (_req, res) => {
  res.json({ ok: true, prefix, expiresIn });
});

app.get("/api/oss/sign", (req, res) => {
  try {
    const raw = String(req.query.path || "");
    if (!raw) {
      return res.status(400).json({ error: "path is required" });
    }

    const objectKey = sanitizeObjectPath(raw);
    if (!objectKey.startsWith(prefix)) {
      return res.status(403).json({ error: "path not allowed by prefix" });
    }

    let url = client.signatureUrl(objectKey, {
      method: "GET",
      expires: expiresIn,
      secure: forceHttps
    });
    if (forceHttps && url.startsWith("http://")) {
      url = "https://" + url.slice("http://".length);
    }

    return res.json({
      url,
      expiresIn,
      objectKey
    });
  } catch (err) {
    return res.status(500).json({
      error: "sign failed",
      detail: err instanceof Error ? err.message : String(err)
    });
  }
});

app.listen(port, () => {
  console.log(`atomq-oss-signer listening on :${port}`);
});

function normalizePrefix(value) {
  let p = String(value || "").trim();
  while (p.startsWith("/")) p = p.slice(1);
  if (!p.endsWith("/")) p += "/";
  return p;
}

function sanitizeObjectPath(value) {
  let path = String(value).trim();
  while (path.startsWith("/")) path = path.slice(1);
  if (!path || path.includes("..")) {
    throw new Error("invalid object path");
  }
  return path;
}
