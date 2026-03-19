#!/usr/bin/env python3
"""Generate an AI summary for scraped jobs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests


def _fallback_summary(jobs: list[dict[str, str]], max_jobs: int) -> str:
    lines = ["Weekly job summary (rule-based fallback):"]
    for idx, job in enumerate(jobs[:max_jobs], start=1):
        title = job.get("title", "").strip() or "Unknown title"
        company = job.get("company", "").strip() or "Unknown company"
        location = job.get("location", "").strip() or "Unknown location"
        link = job.get("link", "").strip()
        lines.append(f"{idx}. {title} - {company} ({location})")
        if link:
            lines.append(f"   {link}")
    return "\n".join(lines)


def _ai_summary(jobs: list[dict[str, str]], max_jobs: int) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback_summary(jobs, max_jobs)

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    trimmed = []
    for job in jobs[: min(len(jobs), 20)]:
        trimmed.append(
            {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "link": job.get("link", ""),
                "description_snippet": job.get("description_snippet", "")[:220],
            }
        )

    prompt = (
        "You are organizing startup job listings for a student.\n"
        "Prioritize remote and NYC roles first.\n"
        f"Return exactly {max_jobs} concise numbered items.\n"
        "Each item format: Title - Company (Location) | Why fit: <short reason> | <link>\n"
        "Keep total under 1400 characters.\n\n"
        f"Jobs JSON:\n{json.dumps(trimmed, ensure_ascii=True)}"
    )

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": "You produce compact, practical job digests."},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return str(content).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize scraped jobs with AI.")
    parser.add_argument("--input", required=True, help="Input JSON from scraper.")
    parser.add_argument("--out", required=True, help="Output text summary path.")
    parser.add_argument("--max-jobs", type=int, default=5, help="How many jobs to highlight.")
    args = parser.parse_args()

    jobs_path = Path(args.input)
    jobs = json.loads(jobs_path.read_text(encoding="utf-8")) if jobs_path.exists() else []
    summary = _ai_summary(jobs, max(1, args.max_jobs))
    Path(args.out).write_text(summary + "\n", encoding="utf-8")
    print(f"Saved summary to {args.out}")


if __name__ == "__main__":
    main()
