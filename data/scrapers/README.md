# Lumen Medical LLM - Data Scrapers

Ethical web scrapers and API clients for collecting medical and pharmaceutical data.

---

## Overview

This module contains scrapers for collecting data from public medical and pharmaceutical databases:

### Medical Data Sources
- **PubMed** - Medical research articles (7M+ papers)
- **DrugBank** - Comprehensive drug database (14K+ drugs)
- **OpenFDA** - FDA drug labels, adverse events, recalls
- **DailyMed** - FDA-approved drug labels (structured SPL format)
- **RxNorm** - Drug name normalization and relationships

### Pharmaceutical/Regulatory Sources
- **FDA Guidance** - GMP, validation, quality systems guidance
- **MHRA** - UK regulatory guidance (TODO)
- **EMA** - EU regulatory guidance (TODO)
- **ICH Guidelines** - International pharmaceutical standards (TODO)

---

## Quick Start

### Run All Scrapers

```bash
python data/scrapers/run_all_scrapers.py
```

### Run Individual Scraper

```bash
# PubMed
python data/scrapers/medical/pubmed_scraper.py

# OpenFDA
python data/scrapers/medical/openfda_client.py

# DailyMed
python data/scrapers/medical/dailymed_scraper.py

# RxNorm
python data/scrapers/medical/rxnorm_client.py

# FDA Guidance
python data/scrapers/pharma/fda_guidance_scraper.py
```

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# PubMed (optional but recommended)
PUBMED_API_KEY=your_api_key_here
PUBMED_EMAIL=your_email@example.com

# FDA (optional)
FDA_API_KEY=your_fda_api_key

# Scraper settings
SCRAPER_USER_AGENT=LumenMedicalBot/1.0 (+https://your-domain.com)
SCRAPER_DELAY=1.0  # Seconds between requests
SCRAPER_MAX_RETRIES=3
```

### Get API Keys

**PubMed API Key** (free, instant):
1. Go to: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
2. Sign up for NCBI account
3. Request API key
4. Increases rate limit from 3/sec to 10/sec

**OpenFDA API Key** (optional):
- No registration required for basic use
- Optional key for higher rate limits: https://open.fda.gov/apis/authentication/

---

## Scrapers Documentation

### 1. PubMed Scraper

**Source:** PubMed Central (PMC)
**API:** E-utilities
**Rate Limit:** 3 req/sec (10 with API key)
**License:** Public domain

```python
from data.scrapers.medical.pubmed_scraper import PubMedScraper

scraper = PubMedScraper(
    api_key="your_key",
    email="your_email@example.com",
)

articles = scraper.run()
```

**Output:**
- `data/raw/pubmed/pubmed_all_articles.json` - All articles
- `data/raw/pubmed/pubmed_batch_*.json` - Batched results

### 2. DrugBank Parser

**Source:** DrugBank
**Format:** XML
**License:** Free for academic use (requires citation)

**⚠️ Manual Download Required:**
1. Go to: https://go.drugbank.com/releases/latest
2. Create free account
3. Download "All full database" XML (~1GB)
4. Place at: `data/raw/drugbank/full_database.xml`

```python
from data.scrapers.medical.drugbank_parser import DrugBankParser

parser = DrugBankParser()
drugs = parser.run()
```

**Output:**
- `data/raw/drugbank/drugbank_all_drugs.json` - All drugs
- `data/raw/drugbank/drugbank_category_*.json` - By category

### 3. OpenFDA Client

**Source:** openFDA
**API:** REST API
**Rate Limit:** 1000 req/min (no key needed)
**License:** Public domain

```python
from data.scrapers.medical.openfda_client import OpenFDAClient

client = OpenFDAClient(api_key=None)  # Optional API key
data = client.run()
```

**Output:**
- `data/raw/openfda/openfda_drug_labels.json` - Drug labels
- `data/raw/openfda/openfda_drug_recalls.json` - Recalls
- `data/raw/openfda/openfda_adverse_events_*.json` - Adverse events

### 4. DailyMed Scraper

**Source:** DailyMed (NLM)
**API:** REST API
**Rate Limit:** No official limit (be respectful)
**License:** Public domain

```python
from data.scrapers.medical.dailymed_scraper import DailyMedScraper

scraper = DailyMedScraper()
labels = scraper.run()
```

**Output:**
- `data/raw/dailymed/dailymed_all_labels.json` - All labels
- `data/raw/dailymed/dailymed_class_*.json` - By drug class

### 5. RxNorm Client

**Source:** RxNorm (NLM)
**API:** REST API
**Rate Limit:** No official limit
**License:** Free, no authentication

```python
from data.scrapers.medical.rxnorm_client import RxNormClient

client = RxNormClient()
drugs = client.run()
```

**Output:**
- `data/raw/rxnorm/rxnorm_drug_database.json` - Normalized drug data
- `data/raw/rxnorm/rxnorm_drug_interactions_sample.json` - Interactions

### 6. FDA Guidance Scraper

**Source:** FDA
**Format:** HTML + PDF
**Rate Limit:** 1 req/sec (be respectful)
**License:** Public domain

```python
from data.scrapers.pharma.fda_guidance_scraper import FDAGuidanceScraper

scraper = FDAGuidanceScraper()
guidance = scraper.run()
```

**Output:**
- `data/raw/fda_guidance/fda_guidance_all.json` - All guidance
- `data/raw/fda_guidance/fda_guidance_*.json` - By category
- `data/raw/fda_guidance/pdfs/*.pdf` - Downloaded PDFs

---

## Ethical Scraping Practices

All scrapers implement:

✅ **Rate Limiting** - Respect server constraints
✅ **User Agent** - Identify ourselves with contact info
✅ **Retry Logic** - Exponential backoff on errors
✅ **Checkpoints** - Resume interrupted scraping
✅ **Robots.txt** - Respect crawling rules
✅ **Terms of Service** - Comply with website policies

### Rate Limits

| Source | Rate Limit | Notes |
|--------|------------|-------|
| PubMed | 3 req/sec (10 with API key) | Required for large-scale |
| OpenFDA | 1000 req/min | 240 req/min per IP |
| DailyMed | ~1-2 req/sec | No official limit |
| RxNorm | ~10 req/sec | No official limit |
| FDA.gov | ~1 req/sec | Be respectful |

---

## Data Storage

```
data/
├── raw/                    # Raw scraped data
│   ├── pubmed/
│   │   ├── pubmed_all_articles.json
│   │   └── pubmed_batch_*.json
│   ├── drugbank/
│   │   ├── drugbank_all_drugs.json
│   │   └── drugbank_category_*.json
│   ├── openfda/
│   │   ├── openfda_drug_labels.json
│   │   ├── openfda_drug_recalls.json
│   │   └── openfda_adverse_events_*.json
│   ├── dailymed/
│   │   ├── dailymed_all_labels.json
│   │   └── dailymed_class_*.json
│   ├── rxnorm/
│   │   └── rxnorm_drug_database.json
│   └── fda_guidance/
│       ├── fda_guidance_all.json
│       └── pdfs/
├── processed/              # Cleaned data
└── datasets/               # Training datasets
```

---

## Troubleshooting

### Rate Limiting Errors

```python
# Reduce rate in scraper
scraper = PubMedScraper(requests_per_second=1.0)
```

### Network Errors

Scrapers automatically retry with exponential backoff (2s, 4s, 8s).

### Checkpoint Recovery

If scraping is interrupted:

```python
# Scrapers automatically resume from checkpoint
scraper.run()  # Continues where it left off
```

### Memory Issues (DrugBank)

DrugBank XML is large (~1GB). Parser uses `iterparse` for memory efficiency.

---

## Adding New Scrapers

Extend `BaseScraper`:

```python
from data.scrapers.utils.base_scraper import BaseScraper

class MyNewScraper(BaseScraper):
    def __init__(self, output_dir: str = "data/raw/my_source"):
        super().__init__(
            name="MySource",
            output_dir=output_dir,
            requests_per_second=2.0,
        )

    def scrape(self) -> List[Dict[str, Any]]:
        # Implement scraping logic
        data = []

        # Use self.get() for rate-limited requests
        response = self.get("https://api.example.com/data")

        # Save data
        self.save_json(data, "output.json")

        return data
```

---

## License & Attribution

### Data Licenses

- **PubMed/PMC:** Public domain (U.S. government)
- **DrugBank:** Free for academic use (cite: Wishart DS, et al. DrugBank 5.0)
- **OpenFDA:** Public domain (U.S. government)
- **DailyMed:** Public domain (U.S. government)
- **RxNorm:** Public domain (U.S. government)
- **FDA Guidance:** Public domain (U.S. government)

### Attribution

Always cite original sources in publications and provide attribution in your application.

---

## Support

Issues or questions? Check:
- API documentation links in each scraper
- Scraper logs: `data/scrapers/scraping.log`
- Source code comments
