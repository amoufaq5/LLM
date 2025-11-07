# Lumen Medical LLM - Data Sources Reference

## Complete List of Public Medical Data Sources for MVP

---

## 1. DRUG INFORMATION DATABASES

### DrugBank
- **URL:** https://go.drugbank.com/
- **Content:** 14,000+ drugs, interactions, mechanisms, pharmacology
- **License:** Free for academic/research (requires attribution)
- **Format:** XML, CSV downloads
- **API:** Yes (limited on free tier)
- **Update Frequency:** Quarterly
- **Scraping Strategy:**
  - Download full database export
  - Parse XML structure
  - Extract: drug names, indications, contraindications, interactions, mechanisms
- **Priority:** HIGH - Core drug database

### DailyMed
- **URL:** https://dailymed.nlm.nih.gov/
- **Content:** FDA-approved drug labels (SPL format)
- **License:** Public domain (U.S. government)
- **Format:** XML (SPL), HTML
- **API:** Yes, free
- **Update Frequency:** Daily
- **Scraping Strategy:**
  - Use REST API for bulk downloads
  - Parse SPL XML for structured data
  - Extract: indications, dosage, warnings, adverse reactions
- **Priority:** HIGH - Official FDA labels

### RxNorm
- **URL:** https://www.nlm.nih.gov/research/umls/rxnorm/
- **Content:** Normalized drug terminology and relationships
- **License:** Free (requires UMLS license - free to obtain)
- **Format:** RRF files, database dumps
- **API:** RxNorm API (free)
- **Update Frequency:** Monthly
- **Scraping Strategy:**
  - Download RxNorm files
  - Use API for real-time lookups
  - Create normalized drug name mappings
- **Priority:** HIGH - Essential for drug name normalization

### OpenFDA
- **URL:** https://open.fda.gov/
- **Content:** Drug labels, adverse events, recalls, enforcement
- **License:** Public domain
- **Format:** JSON API
- **API:** Yes, high rate limits (1000 req/min)
- **Update Frequency:** Daily to weekly
- **Datasets:**
  - Drug adverse events (FAERS)
  - Drug product labeling
  - Drug recalls
  - NDC (National Drug Codes)
- **Scraping Strategy:**
  - Use API for all data
  - Implement pagination
  - Store raw JSON with metadata
- **Priority:** HIGH - Rich drug safety data

---

## 2. MEDICAL LITERATURE & RESEARCH

### PubMed Central (PMC)
- **URL:** https://www.ncbi.nlm.nih.gov/pmc/
- **Content:** 7+ million full-text biomedical articles
- **License:** Open access articles (check individual licenses)
- **Format:** XML, PDF
- **API:** E-utilities API (free, rate-limited to 3 req/sec)
- **Update Frequency:** Continuous
- **Scraping Strategy:**
  - Use E-utilities API (esearch, efetch)
  - Filter for open access articles
  - Extract: abstracts, methods, results, conclusions
  - Focus on: clinical trials, systematic reviews, treatment studies
- **Priority:** HIGH - Core medical knowledge
- **API Key:** Required (free, instant approval)

### PubMed
- **URL:** https://pubmed.ncbi.nlm.nih.gov/
- **Content:** 35+ million citations and abstracts
- **License:** Public domain
- **Format:** XML, JSON
- **API:** E-utilities API
- **Update Frequency:** Daily
- **Scraping Strategy:**
  - Use for abstracts when full text unavailable
  - Extract metadata (MeSH terms, keywords)
  - Link to PMC for full text when available
- **Priority:** MEDIUM - Supplement PMC

### NCBI Bookshelf
- **URL:** https://www.ncbi.nlm.nih.gov/books/
- **Content:** Medical textbooks, databases (e.g., StatPearls)
- **License:** Most are public domain or open access
- **Format:** HTML, XML
- **API:** E-utilities
- **Update Frequency:** Varies by book
- **Focus Areas:**
  - StatPearls (comprehensive medical reference)
  - Medical genetics
  - Clinical guidelines
- **Priority:** MEDIUM - Quality medical education content

---

## 3. FDA REGULATORY DATABASES

### Drugs@FDA
- **URL:** https://www.accessdata.fda.gov/scripts/cder/daf/
- **Content:** FDA-approved drugs, approval history, labels
- **License:** Public domain
- **Format:** HTML, PDF (labels)
- **API:** No official API (scraping required)
- **Update Frequency:** Daily
- **Scraping Strategy:**
  - Scrape drug approval pages
  - Download PDF labels
  - Extract: approval dates, indications, review documents
- **Priority:** HIGH - Official approval data

### FDA Guidance Documents
- **URL:** https://www.fda.gov/regulatory-information/search-fda-guidance-documents
- **Content:** Regulatory guidance for pharma industry
- **License:** Public domain
- **Format:** PDF, HTML
- **API:** No (scraping required)
- **Update Frequency:** Monthly
- **Focus Areas:**
  - GMP guidance
  - Quality systems
  - Validation protocols
  - Manufacturing guidelines
- **Scraping Strategy:**
  - Crawl guidance pages by topic
  - Download PDFs
  - Extract text and structure
  - Categorize by topic (GMP, validation, etc.)
- **Priority:** HIGH - Core pharma compliance content

### FDA Orange Book
- **URL:** https://www.accessdata.fda.gov/scripts/cder/ob/
- **Content:** Approved drug products with therapeutic equivalence
- **License:** Public domain
- **Format:** PDF, Excel, API
- **API:** Yes (basic)
- **Update Frequency:** Monthly
- **Scraping Strategy:**
  - Download monthly data files
  - Parse for drug equivalence information
- **Priority:** MEDIUM - Drug equivalence data

---

## 4. INTERNATIONAL REGULATORY AGENCIES

### MHRA (UK)
- **URL:** https://www.gov.uk/government/organisations/medicines-and-healthcare-products-regulatory-agency
- **Content:** UK drug approvals, GMP guidance, safety alerts
- **License:** Open Government License (free use with attribution)
- **Format:** HTML, PDF
- **API:** No (scraping required)
- **Update Frequency:** Weekly
- **Focus Areas:**
  - GMP guidance (similar to FDA but UK-specific)
  - Drug safety updates
  - Regulatory pathways
- **Scraping Strategy:**
  - Crawl guidance and publications sections
  - Extract GMP and quality guidelines
- **Priority:** MEDIUM - International pharma compliance

### EMA (European Medicines Agency)
- **URL:** https://www.ema.europa.eu/
- **Content:** EU drug approvals, guidelines, ICH documents
- **License:** Free use with attribution
- **Format:** PDF, HTML
- **API:** Limited
- **Update Frequency:** Weekly
- **Focus Areas:**
  - ICH (International Council for Harmonisation) guidelines
  - GMP guidance
  - Drug assessment reports
- **Scraping Strategy:**
  - Download ICH guidelines (Q7, Q9, Q10, etc.)
  - Extract GMP documentation
- **Priority:** MEDIUM - International compliance

### WHO (World Health Organization)
- **URL:** https://www.who.int/
- **Content:** Global health guidelines, GMP, prequalification
- **License:** CC BY-NC-SA 3.0 IGO
- **Format:** PDF, HTML
- **API:** No
- **Update Frequency:** Monthly
- **Focus Areas:**
  - WHO GMP guidelines
  - Pharmaceutical inspection reports
  - Global health recommendations
- **Scraping Strategy:**
  - Download essential medicines list
  - Extract GMP documentation
  - Focus on pharmaceutical quality
- **Priority:** LOW - Supplementary international guidance

---

## 5. CLINICAL INFORMATION & GUIDELINES

### MedlinePlus
- **URL:** https://medlineplus.gov/
- **Content:** Patient-friendly health information (5000+ topics)
- **License:** Public domain (NLM)
- **Format:** HTML, XML
- **API:** MedlinePlus Connect (for health records integration)
- **Update Frequency:** Daily
- **Scraping Strategy:**
  - Scrape health topics A-Z
  - Extract: disease descriptions, symptoms, treatments, prevention
  - Structure for patient Q&A
- **Priority:** HIGH - Patient education content

### CDC (Centers for Disease Control)
- **URL:** https://www.cdc.gov/
- **Content:** Disease information, prevention guidelines, public health
- **License:** Public domain
- **Format:** HTML, PDF
- **API:** No comprehensive API
- **Update Frequency:** Daily
- **Focus Areas:**
  - Disease descriptions
  - Vaccination schedules
  - Travel health
  - Outbreak information
- **Scraping Strategy:**
  - Crawl disease topics
  - Extract prevention guidelines
- **Priority:** MEDIUM - Public health information

### NIH (National Institutes of Health)
- **URL:** https://www.nih.gov/health-information
- **Content:** Health information, clinical trials
- **License:** Public domain
- **Format:** HTML
- **API:** Various (by institute)
- **Update Frequency:** Daily
- **Scraping Strategy:**
  - Extract from various NIH institutes
  - Focus on patient-facing content
- **Priority:** MEDIUM - Authoritative health info

### ClinicalTrials.gov
- **URL:** https://clinicaltrials.gov/
- **Content:** 440,000+ clinical trials worldwide
- **License:** Public domain
- **Format:** XML, JSON
- **API:** Yes (free)
- **Update Frequency:** Daily
- **Scraping Strategy:**
  - Use API for bulk downloads
  - Extract: conditions studied, interventions, outcomes
  - Link drugs to clinical evidence
- **Priority:** MEDIUM - Clinical trial data

---

## 6. MEDICAL KNOWLEDGE BASES

### UMLS (Unified Medical Language System)
- **URL:** https://www.nlm.nih.gov/research/umls/
- **Content:** Unified medical terminology, relationships between concepts
- **License:** Free (requires account and license agreement)
- **Format:** RRF files, MySQL database
- **API:** UTS API (free)
- **Update Frequency:** Bi-annual releases
- **Components:**
  - Metathesaurus (3M+ concepts)
  - SNOMED CT (clinical terms)
  - ICD-10 (diagnosis codes)
  - LOINC (lab codes)
- **Scraping Strategy:**
  - Download full release
  - Load into database
  - Use for medical concept normalization
- **Priority:** HIGH - Essential for medical NLP

### SNOMED CT
- **URL:** https://www.nlm.nih.gov/healthit/snomedct/
- **Content:** Clinical terminology (350,000+ concepts)
- **License:** Free in US (via NLM)
- **Format:** RF2 files
- **API:** Via UMLS
- **Update Frequency:** Bi-annual (March, September)
- **Priority:** MEDIUM - Clinical terminology (included in UMLS)

---

## 7. DRUG INTERACTIONS & SAFETY

### NLM Drug Interaction API
- **URL:** https://lhncbc.nlm.nih.gov/RxNav/APIs/
- **Content:** Drug-drug interaction checks
- **License:** Free
- **Format:** JSON API
- **API:** Yes, free, no rate limits
- **Update Frequency:** Monthly
- **Priority:** HIGH - Critical safety feature

### FAERS (FDA Adverse Event Reporting System)
- **URL:** Accessed via OpenFDA
- **Content:** Adverse event reports (10M+ reports)
- **License:** Public domain
- **Format:** JSON (via OpenFDA API)
- **API:** Yes (OpenFDA)
- **Update Frequency:** Quarterly
- **Priority:** MEDIUM - Drug safety surveillance

---

## 8. SUPPLEMENTARY MEDICAL SOURCES

### Mayo Clinic
- **URL:** https://www.mayoclinic.org/
- **Content:** Disease information, symptoms, treatments
- **License:** Copyrighted (check ToS - may need to avoid direct scraping)
- **Format:** HTML
- **Scraping Strategy:**
  - Use cautiously, respect robots.txt
  - Consider as reference only, not direct scraping
  - Alternative: Use their symptom checker with permission
- **Priority:** LOW - Use only if licensing allows

### WebMD
- **URL:** https://www.webmd.com/
- **Content:** Health information, symptom checker
- **License:** Copyrighted (cannot scrape)
- **Scraping Strategy:** Do NOT scrape - use as reference only
- **Priority:** NONE - Reference only

### OpenStax
- **URL:** https://openstax.org/subjects/science
- **Content:** Free medical textbooks (Anatomy & Physiology, etc.)
- **License:** CC BY 4.0 (free to use and modify)
- **Format:** PDF, HTML
- **Scraping Strategy:**
  - Download textbooks
  - Extract chapters as structured content
  - Use for medical education features
- **Priority:** LOW - Educational content

---

## 9. PHARMACEUTICAL MANUFACTURING & GMP

### ICH Guidelines
- **URL:** https://www.ich.org/page/ich-guidelines
- **Content:** International pharmaceutical quality standards
- **License:** Free to use
- **Format:** PDF
- **Update Frequency:** Annually
- **Key Guidelines:**
  - Q7 (GMP for APIs)
  - Q9 (Quality Risk Management)
  - Q10 (Pharmaceutical Quality System)
- **Scraping Strategy:**
  - Download all Q-series guidelines
  - Extract text and structure
  - Create Q&A pairs for compliance queries
- **Priority:** HIGH - Core pharma compliance

### FDA GMP Training Modules
- **URL:** Various FDA pages
- **Content:** Training materials for GMP compliance
- **License:** Public domain
- **Format:** PDF, HTML
- **Priority:** MEDIUM - Training content

---

## 10. LIFESTYLE & WELLNESS

### USDA Food Database
- **URL:** https://fdc.nal.usda.gov/
- **Content:** Nutritional information for 300,000+ foods
- **License:** Public domain
- **Format:** JSON API, CSV downloads
- **API:** Yes, free
- **Priority:** LOW - For lifestyle recommendations

### NIH Office of Dietary Supplements
- **URL:** https://ods.od.nih.gov/
- **Content:** Supplement fact sheets, safety information
- **License:** Public domain
- **Format:** HTML
- **Priority:** LOW - Supplement information

---

## DATA COLLECTION PRIORITY MATRIX

### Phase 1 (Weeks 1-2): Essential - Patient Care
1. DrugBank - Core drug database
2. OpenFDA - Drug labels and safety
3. DailyMed - FDA-approved labels
4. RxNorm - Drug name normalization
5. MedlinePlus - Patient education
6. NLM Drug Interaction API - Safety checks

### Phase 2 (Week 3): Essential - Pharma Compliance
1. FDA Guidance Documents - GMP and compliance
2. ICH Guidelines - International standards
3. MHRA Publications - UK regulations
4. EMA Guidelines - EU regulations

### Phase 3 (Week 4): Supplementary
1. PubMed Central - Research articles
2. ClinicalTrials.gov - Clinical evidence
3. UMLS - Medical terminology
4. CDC - Public health information

---

## ETHICAL SCRAPING GUIDELINES

### Rules to Follow:
1. **Respect robots.txt** - Always check and obey
2. **Rate Limiting** - Never exceed 1 request/second for websites without APIs
3. **User Agent** - Use descriptive user agent with contact info
4. **Attribution** - Keep source metadata for all data
5. **Terms of Service** - Review and comply with each site's ToS
6. **APIs First** - Always use official APIs when available
7. **No Personal Data** - Never scrape patient or personal information
8. **Caching** - Cache responses to avoid repeated requests

### Example User Agent:
```
Mozilla/5.0 (compatible; LumenMedicalBot/1.0; +https://yourdomain.com/bot; research@yourdomain.com)
```

### Proxy Rotation (if needed):
- Use only if rate-limited unfairly
- Consider services like ScraperAPI, Bright Data (costs money)
- For MVP: Respect limits, don't use aggressive scraping

---

## DATA STORAGE STRUCTURE

```
data/
├── raw/
│   ├── drugbank/
│   │   ├── metadata.json (source, date, version)
│   │   └── drugs.xml
│   ├── openfda/
│   │   ├── labels/
│   │   ├── adverse_events/
│   │   └── recalls/
│   ├── pubmed/
│   │   ├── articles/
│   │   └── metadata/
│   └── fda_guidance/
│       └── pdfs/
├── processed/
│   ├── drugs.parquet
│   ├── interactions.parquet
│   ├── medical_qa.parquet
│   └── pharma_compliance.parquet
└── datasets/
    ├── train/
    ├── validation/
    └── test/
```

---

## ESTIMATED DATA VOLUMES

| Source | Size | Records | Processing Time |
|--------|------|---------|-----------------|
| DrugBank | 500 MB | 14,000 drugs | 2 hours |
| OpenFDA | 10 GB | 1M+ events | 8 hours |
| DailyMed | 5 GB | 100,000+ labels | 6 hours |
| PubMed | 50 GB | 100,000 articles | 24 hours |
| FDA Guidance | 2 GB | 5,000 documents | 4 hours |
| Regulatory Docs | 3 GB | 10,000 pages | 6 hours |
| **Total** | **~70 GB** | **1M+ records** | **2-3 days** |

---

## NEXT STEPS

Once plan is approved, I will:
1. Build scrapers for priority sources (Week 1-3)
2. Set up data processing pipeline
3. Generate training datasets
4. Validate data quality

**All scrapers will be production-ready with:**
- Error handling and retry logic
- Logging and monitoring
- Resume capability (for interrupted scrapes)
- Data validation
- Deduplication
- Metadata tracking
