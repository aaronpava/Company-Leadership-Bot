# Company Leadership Bot

A strategic decision analysis tool that facilitates high-stakes discussions between **twelve distinct leadership perspectives** at Company — a mission-driven federal contracting agency specializing in web development, Drupal expertise, open data, and open-source solutions for large federal agencies.

## Overview

The bot simulates a structured leadership forum where each of Company's twelve leaders evaluates a strategic decision from their unique role, expertise, and priorities. When an OpenAI API key is provided, each leader's response is AI-generated and grounded in their persona. Without a key, the bot runs in **demo mode** showing the structure of each perspective.

A final **strategic synthesis** summarizes areas of agreement, key tensions, and recommended next steps.

## The Twelve Leadership Perspectives

| # | Leader | Core Focus |
|---|--------|-----------|
| 1 | Chief Executive Officer (CEO) | Mission, strategy, long-term vision |
| 2 | Chief Technology Officer (CTO) | Technology architecture, open-source |
| 3 | Chief Financial Officer (CFO) | Financial health, DCAA compliance |
| 4 | Chief Operating Officer (COO) | Delivery, operations, agile execution |
| 5 | VP of Business Development | Pipeline, federal capture, teaming |
| 6 | VP of Engineering | Engineering org, DevSecOps, team health |
| 7 | Chief of Staff | Executive alignment, OKRs, coordination |
| 8 | Director of Drupal Practice | Drupal CoE, headless CMS, community |
| 9 | Director of Open Data Initiatives | Federal data policy, open portals |
| 10 | Director of Open Source Strategy | OSS contribution, OMB M-16-21 |
| 11 | Director of Federal Client Delivery | Client relations, CPARS, compliance |
| 12 | Director of People & Culture | Talent, DEI, org culture |

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Interactive (prompted topic)
```bash
python bot.py
```

### With a specific topic
```bash
python bot.py --topic "Should we pursue a new IDIQ vehicle for cloud services?"
```

### Multi-round discussion (leaders respond to each other)
```bash
python bot.py --topic "Should we expand our headless Drupal practice?" --rounds 2
```

### Save a Markdown report
```bash
python bot.py --topic "AI-assisted open data strategy?" --output analysis.md
```

### Skip the synthesis step
```bash
python bot.py --topic "New subcontracting partnership?" --no-synthesis
```

### List all personas
```bash
python bot.py --list-personas
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI-generated perspectives | *(demo mode if unset)* |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |

## Demo Mode

If `OPENAI_API_KEY` is not set, the bot runs in **demo mode** — displaying the structure of each leadership perspective (title, top priorities, communication style) without calling an external API. This is useful for understanding the personas and testing the tool.

## Testing

```bash
python -m pytest tests/ -v
```

## Company Context

Company is a federal IT contracting firm with ~150 FTEs delivering web modernization, Drupal CMS platforms, open data portals, and open-source solutions for agencies including CMS, HHS, USDA, EPA, DOE, and DOT. The firm operates under FISMA, Section 508, FedRAMP, and DCAA compliance requirements.
