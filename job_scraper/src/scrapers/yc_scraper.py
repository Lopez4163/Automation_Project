#!/usr/bin/env python3
"""MVP scraper for Y Combinator jobs.

Output fields per job:
- source
- title
- company
- location
- link
- description_snippet
- collected_at
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

YC_JOBS_URL = "https://www.ycombinator.com/jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; job-scraper-mvp/1.0)",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class JobRecord:
    source: str
    title: str
    company: str
    location: str
    link: str
    description_snippet: str
    collected_at: str


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _safe_get(obj: dict[str, Any], *keys: str, default: str = "") -> str:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    if cur is None:
        return default
    if isinstance(cur, (dict, list)):
        return default
    return _clean_text(str(cur))


def fetch_yc_jobs_page(timeout: int = 20) -> str:
    response = requests.get(YC_JOBS_URL, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def _extract_from_next_data(soup: BeautifulSoup, collected_at: str) -> list[JobRecord]:
    records: list[JobRecord] = []
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return records

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return records

    # Heuristic walk: collect dicts that look like job objects.
    stack: list[Any] = [data]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            title = _safe_get(item, "title") or _safe_get(item, "role")
            company = _safe_get(item, "companyName") or _safe_get(item, "company")
            link = _safe_get(item, "url") or _safe_get(item, "jobUrl") or _safe_get(item, "applyUrl")
            location = _safe_get(item, "location") or _safe_get(item, "locations")
            snippet = _safe_get(item, "description") or _safe_get(item, "summary")

            # A minimal signature to avoid false positives.
            if title and (company or link):
                full_link = link if link.startswith("http") else urljoin(YC_JOBS_URL, link)
                records.append(
                    JobRecord(
                        source="y_combinator",
                        title=title,
                        company=company,
                        location=location,
                        link=full_link,
                        description_snippet=snippet[:300],
                        collected_at=collected_at,
                    )
                )

            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)

    return records


def _extract_from_data_page(soup: BeautifulSoup, collected_at: str) -> list[JobRecord]:
    node = soup.find(attrs={"data-page": True})
    if not node:
        return []

    data_page = node.get("data-page")
    if not isinstance(data_page, str) or not data_page:
        return []

    try:
        payload = json.loads(html.unescape(data_page))
    except json.JSONDecodeError:
        return []

    props = payload.get("props", {})
    if not isinstance(props, dict):
        return []

    job_postings = props.get("jobPostings", [])
    if not isinstance(job_postings, list):
        return []

    records: list[JobRecord] = []
    for item in job_postings:
        if not isinstance(item, dict):
            continue

        title = _safe_get(item, "title")
        company = _safe_get(item, "companyName")
        location = _safe_get(item, "location")
        link = _safe_get(item, "url")
        snippet = _safe_get(item, "companyOneLiner")

        if not title or not link:
            continue

        full_link = link if link.startswith("http") else urljoin(YC_JOBS_URL, link)
        records.append(
            JobRecord(
                source="y_combinator",
                title=title,
                company=company,
                location=location,
                link=full_link,
                description_snippet=snippet[:300],
                collected_at=collected_at,
            )
        )

    return records


def _extract_from_html_cards(soup: BeautifulSoup, collected_at: str) -> list[JobRecord]:
    records: list[JobRecord] = []
    seen_links: set[str] = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "/companies/" not in href or "/jobs/" not in href:
            continue

        link = href if href.startswith("http") else urljoin(YC_JOBS_URL, href)
        if link in seen_links:
            continue
        seen_links.add(link)

        card = a.find_parent(["article", "li", "div"]) or a
        text = _clean_text(card.get_text(" ", strip=True))
        title = _clean_text(a.get_text(" ", strip=True))

        # Best-effort company extraction: take leading token block from card text.
        company = ""
        if text and title and title in text:
            prefix = text.split(title, 1)[0]
            company = _clean_text(prefix)

        records.append(
            JobRecord(
                source="y_combinator",
                title=title or "Unknown title",
                company=company,
                location="",
                link=link,
                description_snippet=text[:300],
                collected_at=collected_at,
            )
        )

    return records


def _dedupe(records: Iterable[JobRecord]) -> list[JobRecord]:
    unique: list[JobRecord] = []
    seen: set[tuple[str, str]] = set()
    for job in records:
        key = (job.link.strip().lower(), job.title.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique


def _split_terms(values: list[str] | None) -> list[str]:
    if not values:
        return []
    terms: list[str] = []
    for value in values:
        for part in value.split(","):
            cleaned = _clean_text(part).lower()
            if cleaned:
                terms.append(cleaned)
    return terms


def _passes_filters(
    job: dict[str, str],
    include_terms: list[str],
    exclude_terms: list[str],
    company_filter: str,
    location_filter: str,
    remote_only: bool,
) -> bool:
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    location = job.get("location", "").lower()
    snippet = job.get("description_snippet", "").lower()
    searchable = " ".join([title, company, location, snippet])

    if include_terms and not any(term in searchable for term in include_terms):
        return False
    if exclude_terms and any(term in searchable for term in exclude_terms):
        return False
    if company_filter and company_filter not in company:
        return False
    if location_filter and location_filter not in location:
        return False
    if remote_only and "remote" not in location:
        return False

    return True


def filter_jobs(
    jobs: list[dict[str, str]],
    include_terms: list[str],
    exclude_terms: list[str],
    company_filter: str,
    location_filter: str,
    remote_only: bool,
) -> list[dict[str, str]]:
    return [
        job
        for job in jobs
        if _passes_filters(
            job=job,
            include_terms=include_terms,
            exclude_terms=exclude_terms,
            company_filter=company_filter,
            location_filter=location_filter,
            remote_only=remote_only,
        )
    ]


def filter_nyc_or_remote(jobs: list[dict[str, str]]) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    for job in jobs:
        location = job.get("location", "").lower()
        if "remote" in location or "new york" in location or "nyc" in location:
            filtered.append(job)
    return filtered


def scrape_yc_jobs(html: str | None = None) -> list[dict[str, str]]:
    collected_at = datetime.now(timezone.utc).isoformat()
    if html is None:
        html = fetch_yc_jobs_page()

    soup = BeautifulSoup(html, "html.parser")

    from_data_page = _extract_from_data_page(soup, collected_at)
    from_next_data = _extract_from_next_data(soup, collected_at)
    from_cards = _extract_from_html_cards(soup, collected_at)

    merged = _dedupe([*from_data_page, *from_next_data, *from_cards])
    return [asdict(job) for job in merged]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Y Combinator jobs (MVP).")
    parser.add_argument("--out", help="Optional output JSON file path.")
    parser.add_argument("--limit", type=int, default=0, help="Optional max jobs to print/save.")
    parser.add_argument(
        "--keyword",
        action="append",
        help="Include jobs if this keyword appears (can repeat or use comma-separated values).",
    )
    parser.add_argument(
        "--exclude-keyword",
        action="append",
        help="Exclude jobs if this keyword appears (can repeat or use comma-separated values).",
    )
    parser.add_argument("--company", default="", help="Filter by company name substring.")
    parser.add_argument("--location", default="", help="Filter by location substring.")
    parser.add_argument("--remote-only", action="store_true", help="Only include remote jobs.")
    parser.add_argument(
        "--nyc-or-remote",
        action="store_true",
        help="Only include jobs in NYC (New York) or remote jobs.",
    )
    args = parser.parse_args()

    jobs = scrape_yc_jobs()
    jobs = filter_jobs(
        jobs=jobs,
        include_terms=_split_terms(args.keyword),
        exclude_terms=_split_terms(args.exclude_keyword),
        company_filter=_clean_text(args.company).lower(),
        location_filter=_clean_text(args.location).lower(),
        remote_only=args.remote_only,
    )
    if args.nyc_or_remote:
        jobs = filter_nyc_or_remote(jobs)

    if args.limit and args.limit > 0:
        jobs = jobs[: args.limit]

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=True)
        print(f"Saved {len(jobs)} jobs to {args.out}")
        return

    print(json.dumps(jobs, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
