# job_scraper

MVP scraper for Y Combinator jobs.

## Setup

```bash
cd /Users/nico/Desktop/job_scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 src/scrapers/yc_scraper.py --limit 10
```

Filter examples:

```bash
# Backend or AI roles
python3 src/scrapers/yc_scraper.py --keyword backend,ai --limit 10

# Remote-only roles
python3 src/scrapers/yc_scraper.py --remote-only --limit 10

# Company/location filter
python3 src/scrapers/yc_scraper.py --company stripe --location new york
```

Save to file:

```bash
python3 src/scrapers/yc_scraper.py --out data/yc_jobs.json
```

## Weekly Automation (OpenClaw + Telegram)

1. Create `.env` from `.env.example` and set:
- `TELEGRAM_CHAT_ID`
- `GROQ_API_KEY` (optional; if empty, fallback summary is used)

2. Run once locally:

```bash
./run_weekly.sh
```

3. Add weekly OpenClaw cron:

```bash
openclaw cron add \
  --name "weekly-job-scrape" \
  --cron "0 9 * * 1" \
  --tz "America/New_York" \
  --system-event "/Users/nico/Desktop/job_scraper/run_weekly.sh"
```

## Output schema

Each job record includes:
- `source`
- `title`
- `company`
- `location`
- `link`
- `description_snippet`
- `collected_at`

NYC or remote only:

```bash
python3 src/scrapers/yc_scraper.py --nyc-or-remote --limit 10
```
