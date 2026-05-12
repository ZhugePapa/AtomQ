# AtomQ OSS Signer

## 1. Setup

```bash
cd /Users/leiwang/Documents/AtomQ/services/oss-signer
cp .env.example .env
```

Fill `.env` with your RAM user AK/SK.
Make sure `OSS_SIGN_FORCE_HTTPS=true` (default) so iOS ATS accepts download URLs.

## 2. Install & Run

```bash
npm install
npm run dev
```

Health check:

```bash
curl http://127.0.0.1:3000/health
```

Sign URL:

```bash
curl "http://127.0.0.1:3000/api/oss/sign?path=atomq/content_package/public/manifest.json"
```

## 3. iOS config

Set `ATOMQ_OSS_SIGN_URL` in app `Info.plist`:

`http://127.0.0.1:3000/api/oss/sign`

`ATOMQ_OSS_OBJECT_PREFIX` should be:

`atomq/content_package/public/`
