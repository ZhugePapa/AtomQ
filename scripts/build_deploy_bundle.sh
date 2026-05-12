#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/leiwang/Documents/AtomQ"
BUNDLE_DIR="$ROOT/deploy/AtomQ-DeployBundle"

rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

mkdir -p "$BUNDLE_DIR/app"
cp "$ROOT/ios-homepage/project.yml" "$BUNDLE_DIR/app/"
cp -R "$ROOT/ios-homepage/AtomQ.xcodeproj" "$BUNDLE_DIR/app/"
cp -R "$ROOT/ios-homepage/AtomQ" "$BUNDLE_DIR/app/"

mkdir -p "$BUNDLE_DIR/signer"
cp "$ROOT/services/oss-signer/package.json" "$BUNDLE_DIR/signer/"
cp "$ROOT/services/oss-signer/server.js" "$BUNDLE_DIR/signer/"
cp "$ROOT/services/oss-signer/.env.example" "$BUNDLE_DIR/signer/"
cp "$ROOT/services/oss-signer/.gitignore" "$BUNDLE_DIR/signer/"
cp "$ROOT/services/oss-signer/README.md" "$BUNDLE_DIR/signer/"

cat > "$BUNDLE_DIR/README.md" <<'EOF'
# AtomQ Deploy Bundle

This folder is a self-contained deployment package for AtomQ.

## Structure

- `app/`: iOS app project (`AtomQ.xcodeproj` + source files)
- `signer/`: OSS sign service used by app for private bucket access

## 1) Run signer service

```bash
cd signer
cp .env.example .env
# Fill OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET in .env
npm install
npm run dev
```

## 2) Run iOS app

Open:

`app/AtomQ.xcodeproj`

Build scheme:

`AtomQ`

The app will request signed URLs from:

`http://127.0.0.1:3000/api/oss/sign`

## Notes

- Do not commit real `.env` credentials.
- If signer uses a different host/port, update `app/AtomQ/Info.plist`:
  - `ATOMQ_OSS_SIGN_URL`
EOF

echo "Deploy bundle generated at: $BUNDLE_DIR"
