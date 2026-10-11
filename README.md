# Food Product Scanner

Scan or type a food barcode to see ingredients, possible allergens, vegetarian status (Indian convention: egg is non-veg), Nutri-Score (2023 algorithm) and NOVA group. Works on the web (Flask, deployed on Vercel) and from the Flutter app in `food_scanner_mobile/`.

- **Barcodes** are looked up in [Open Food Facts](https://world.openfoodfacts.org) (free, ODbL).
- **Photos** are checked for a barcode on the server (zxing-cpp). If `GEMINI_API_KEY` is set and there's no barcode, Gemini reads the label text. Without a key the site runs with no AI at all.
- **Nothing is faked.** Unknown products, missing ingredients and unconfirmed veg status are shown as such.
- **No accounts, no cookies, no server-side storage.** History and saved products live in the visitor's browser.

## Run locally

```bash
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                  # optional: add GEMINI_API_KEY
FLASK_DEBUG=1 python app.py           # http://127.0.0.1:5000
pytest -q                             # run the tests
```

## Deploy on Vercel

1. Import the repo in Vercel (it uses `vercel.json`).
2. In **Project → Settings → Environment Variables**, add what you need from `.env.example`. `GEMINI_API_KEY` is optional; `CONTACT_EMAIL` and `SITE_OWNER` are recommended (shown in the footer and policies).
3. For rate limits that hold across Vercel's instances, add an Upstash Redis URL as `RATELIMIT_STORAGE_URI`.
4. In Google Cloud, set a daily quota on the Gemini API as a hard spending limit.

Docker / Cloud Run: `docker compose up` or `./deploy_gcp.sh` (listens on port 8080).

## API (used by the mobile app)

`POST /scan` with JSON `{"barcode": "8901058000290"}` or a multipart `image` file. Returns `{success, dashboard, result, open_food_facts, ...}`; errors return `{success: false, error}` with a 4xx/5xx status.

## Security

- No secrets in code; the Gemini key is read from the environment and sent in a request header, never in a URL.
- Same-origin check on POST requests, rate limits (30 scans/min, 8 photos/min, 60 photos/day per IP) and a daily AI cap.
- Uploads limited to 4 MB and verified as real JPEG/PNG/WebP images; never written to disk.
- Strict Content-Security-Policy, HSTS, `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`.
- All product data is rendered as text (no `innerHTML`), so it can't inject scripts.
- Debug mode is off unless `FLASK_DEBUG=1`.

## Licences

MIT (this project, see `LICENSE`). Bundled: html5-qrcode (Apache-2.0, `static/vendor`), Outfit and Inter fonts (SIL OFL 1.1, `static/fonts`). Data: Open Food Facts (ODbL).
