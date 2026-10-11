# Social Caption Generator for Odoo 17

An Odoo app that turns a **topic + tone** into **3 short, ready-to-post social media captions** (sensory · moment · call to action) with hashtags, in Arabic, English, or both.

- Works immediately after install with a **built-in generator**: no AI service, no API key, no internet needed.
- Writes the captions with **Claude** automatically once an Anthropic API key is added (Settings → Social Captions, or the `ANTHROPIC_API_KEY` environment variable). If Claude can't be reached, it falls back to the built-in generator and says why.
- Opens with 3 example requests already generated, so the demo is never empty.

## Easiest start (Windows): double-click RUN-DEMO.bat

1. Right-click `social_caption_studio.zip` → **Properties** → tick **Unblock** (if shown) → OK. Then right-click → **Extract All**.
2. Open the extracted folder and double-click **`RUN-DEMO.bat`**. If a blue "Windows protected your PC" screen appears: **More info → Run anyway**.
3. Press **1** (or just wait 10 seconds). The browser opens the demo. Log in with **admin / admin**.

`RUN-DEMO.bat` handles the usual problems by itself:

| Problem | What the file does |
|---|---|
| Docker Desktop not installed | Offers to install it (winget), or opens the download page |
| Docker installed but not running | Starts Docker Desktop and waits up to 3 minutes |
| Docker won't start | Explains the cause and offers to install / update WSL |
| Port 8069 already used | Picks the next free port (8070-8099) automatically |
| Already running | Reuses it and just opens the browser |
| Odoo slow or stuck | Shows the log and offers wait / reset fresh |
| Download failed | Explains (internet, disk space) and offers retry |
| Run from inside the zip | Tells you to extract first |

Its menu also has **2 = Stop**, **3 = Reset (fresh start)**, **4 = Show logs**.

macOS / Linux: run `./start-demo.sh` and `./stop-demo.sh`.

The first start needs internet to download Odoo (about 1 GB); later starts work offline.

## Run the demo (one command)

Requirements: Docker Desktop (Windows / macOS) or Docker Engine (Linux).

```bash
cd social_caption_studio
docker compose up -d
```

Wait about 30–60 seconds on the first start, then open **http://localhost:8069** and log in with **admin / admin**. Open the **Social Captions** app.

Optional, for AI-written captions:

```bash
ANTHROPIC_API_KEY=sk-ant-... docker compose up -d
```

(or paste the key later in **Social Captions → Settings**).

Stop it with `docker compose down`. Add `-v` to also delete the demo database and start fresh next time.
Port 8069 busy? Use `PORT=8070 docker compose up -d`.

## Demo script (2 minutes)

1. **Social Captions → Captions**: three example requests (Arabic café, English furniture, bilingual dental clinic) already have captions.
2. Click **New**, type a topic (e.g. `Summer yoga classes`), pick a tone and language, press **Generate 3 captions**.
3. Use **Copy** on any caption; press **Regenerate** for a new set.
4. Show **Settings**: add an API key to switch to Claude-written captions.

## Install into an existing Odoo 17

Copy `social_caption_generator/` into your addons path, restart Odoo, then **Apps → Update Apps List → Social Caption Generator → Activate**. It depends only on `base_setup` and Python `requests` (both ship with Odoo).

## Tests

```bash
docker compose run --rm odoo -d captions -u social_caption_generator \
  --test-tags /social_caption_generator --stop-after-init --no-http
```

6 tests cover the built-in generator, the Claude request (mocked), fallback on API errors, the X/Twitter 280-character limit, and the install-time examples.

## How captions are made

| Mode | When | Notes |
|---|---|---|
| Built-in | No API key | Phrase banks per tone and language. Instant and offline. Uses placeholders such as `[date]` / `[التاريخ]` instead of inventing facts. |
| Claude | API key set | Model `claude-opus-5-5` (changeable in Settings). Same rules: 3 angles, only facts you supply, platform hashtag and length limits. |
