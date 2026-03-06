# AI Job Scraper with AI Summaries & Telegram Alerts

An automated system that monitors job boards, analyzes job listings using AI, and sends relevant opportunities directly to your phone through Telegram notifications.

The goal of this project is to automate the repetitive process of searching for software engineering jobs and internships by combining web scraping, AI analysis, and automated notifications.

---

# Overview

Searching for jobs manually requires repeatedly visiting multiple job boards, reading through long descriptions, and filtering out irrelevant postings.

This project automates that workflow by:

1. Scraping job listings from selected job boards
2. Extracting job information using Python
3. Sending job descriptions to an AI model for summarization and analysis
4. Filtering listings based on relevance
5. Sending notifications through a Telegram bot

This reduces the time spent searching for jobs and helps users quickly identify relevant opportunities.

---

# Architecture

```
Job Boards
   │
   ▼
OpenClaw Automation
   │
   ▼
Web Scraper (BeautifulSoup)
   │
   ▼
Job Data Extraction
   │
   ▼
AI Processing (Groq API - Llama 3)
   │
   ▼
Filtering & Scoring
   │
   ▼
Telegram Bot Notifications
   │
   ▼
User
```

---

# Features

- Automated job scraping
- AI-generated job summaries
- Skill extraction from job descriptions
- Relevance filtering
- Telegram notifications
- Duplicate job detection
- Expandable job board support

---

# Technology Stack

| Component | Technology |
|--------|--------|
| Programming Language | Python |
| Web Scraping | BeautifulSoup |
| Automation Framework | OpenClaw |
| AI Model | Groq Cloud (Llama 3) |
| Notifications | Telegram Bot API |
| Data Storage | JSON |

---

# Project Structure

```
ai-job-scraper/

├── README.md
├── PROPOSAL.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── scraper/
│   ├── job_scraper.py
│   ├── parsers.py
│   └── sources.py
│
├── ai/
│   └── groq_client.py
│
├── pipeline/
│   └── job_pipeline.py
│
├── notifier/
│   └── telegram_bot.py
│
├── scheduler/
│   └── cron_runner.py
│
├── storage/
│   └── deduplicate.py
│
├── data/
│   ├── raw_jobs.json
│   └── processed_jobs.json
│
└── diagrams/
    └── architecture.md
```

---

# Setup Instructions

## 1. Clone the Repository

```
git clone https://github.com/yourusername/ai-job-scraper.git
cd ai-job-scraper
```

---

## 2. Install Dependencies

```
pip install -r requirements.txt
```

---

## 3. Create Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```
GROQ_API_KEY=your_api_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 4. Run the Pipeline

```
python main.py
```

The system will:

1. Scrape job listings
2. Send job descriptions to the AI model
3. Filter relevant jobs
4. Send notifications through Telegram

---

# Example Telegram Notification

```
Software Engineer Intern — Company XYZ

Summary:
This role focuses on backend development using Python and cloud services.

Skills:
Python
Docker
AWS
SQL

Apply:
https://job-link.com
```

---

# Testing

Basic tests can be run with:

```
pytest
```

---

# Future Improvements

Possible improvements include:

- Support for more job boards
- Resume-to-job matching
- Job ranking using AI scoring
- Web dashboard for job tracking
- Slack or email notifications
- Database storage instead of JSON
- User preference configuration

---

# Educational Purpose

This project was developed as part of an automation systems assignment to demonstrate how automation tools, AI models, and messaging platforms can be combined to reduce manual workflows.

---
