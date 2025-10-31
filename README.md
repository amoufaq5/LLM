# Lumen Medical LLM

**AI-Powered Medical Intelligence Platform for Patients and Pharmaceutical Companies**

---

## Overview

Lumen is a medical AI platform designed to serve multiple stakeholders in healthcare:
- **Patients:** Medical Q&A, symptom assessment, drug information
- **Pharmaceutical Companies:** Regulatory compliance, QA documentation, GMP guidance
- **Future:** Students, researchers, doctors, hospitals

---

## Project Status

**Phase:** Planning
**Timeline:** 3 months MVP
**Budget:** $10,000 - $25,000
**Team:** Solo developer

---

## Documentation

📋 **[MVP Execution Plan](LUMEN_MVP_EXECUTION_PLAN.md)** - Complete 12-week development plan

📊 **[Data Sources Reference](DATA_SOURCES_REFERENCE.md)** - Public medical databases and APIs

⚙️ **[Technical Decisions](TECHNICAL_DECISIONS.md)** - Architecture and technology choices

---

## MVP Features

### Patient Features
- Medical Q&A system
- Symptom assessment & triage
- Drug interaction checker
- Patient profile management
- OTC medication recommendations

### Pharma Features
- Regulatory compliance assistant (FDA, MHRA, EMA)
- QA documentation generator
- GMP guidance and templates
- Drug information database

---

## Tech Stack

- **Model:** BioMistral-7B (fine-tuned with QLoRA)
- **Backend:** FastAPI + PostgreSQL + Redis
- **Frontend:** Next.js 14 + TypeScript
- **Vector DB:** Qdrant (for RAG)
- **Inference:** vLLM
- **Training:** RunPod (A100 GPUs)
- **Hosting:** Vercel + Railway + RunPod

---

## Project Structure

```
lumen/
├── data/                  # Data collection and processing
│   ├── scrapers/         # Web scrapers for medical data
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Cleaned and structured data
│   └── datasets/         # Training datasets
├── model/                # ML model development
│   ├── training/         # Fine-tuning scripts
│   ├── evaluation/       # Model evaluation
│   └── inference/        # Serving and inference
├── backend/              # FastAPI application
│   ├── api/              # API endpoints
│   ├── database/         # Database models
│   ├── services/         # Business logic
│   └── rag/              # RAG implementation
├── frontend/             # Next.js application
│   ├── app/              # App router
│   ├── components/       # React components
│   └── lib/              # Utilities
├── infrastructure/       # Deployment and DevOps
│   ├── docker/           # Docker configurations
│   └── scripts/          # Deployment scripts
├── docs/                 # Documentation
└── tests/                # Testing
```

---

## Development Phases

### Phase 1: Foundation (Weeks 1-4)
- Project setup
- Data collection (50K+ examples)
- Data processing pipeline

### Phase 2: Model Development (Weeks 5-7)
- Fine-tune BioMistral-7B
- Set up RAG system
- Model evaluation

### Phase 3: Backend (Weeks 8-9)
- FastAPI development
- Database setup
- Authentication & security

### Phase 4: Frontend (Weeks 10-11)
- Next.js UI
- Patient & pharma interfaces
- Responsive design

### Phase 5: Launch (Week 12)
- Testing & deployment
- Documentation
- Beta launch

---

## Budget Breakdown

| Category | Cost |
|----------|------|
| Model Training | $1,500 |
| Infrastructure (3 months) | $1,500 |
| Development Tools | $120 |
| Buffer | $1,000 |
| **Total** | **$4,000-5,000** |

---

## Key Principles

1. **Medical Safety First:** Disclaimers, confidence thresholds, source citations
2. **Privacy & Compliance:** HIPAA-aligned, encrypted, secure
3. **Informational Only:** No diagnostic claims (avoids FDA device classification)
4. **Open Source:** Full ownership of fine-tuned model
5. **Production Quality:** Clean, tested, documented code

---

## Data Sources

- **Drug Information:** DrugBank, DailyMed, OpenFDA
- **Medical Literature:** PubMed Central, NCBI Bookshelf
- **Regulatory:** FDA Guidance, MHRA, EMA, ICH Guidelines
- **Patient Education:** MedlinePlus, CDC, NIH
- **Clinical:** ClinicalTrials.gov, UMLS

See [DATA_SOURCES_REFERENCE.md](DATA_SOURCES_REFERENCE.md) for complete list.

---

## Security & Compliance

- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Access controls & authentication
- Audit logging
- HIPAA-aligned architecture
- Data retention policies

---

## Getting Started (Post-Approval)

1. **Setup:**
   ```bash
   git clone <repo>
   cd lumen
   pip install -r requirements.txt
   ```

2. **Data Collection:**
   ```bash
   python data/scrapers/run_all.py
   ```

3. **Model Training:**
   ```bash
   python model/training/train_qlora.py
   ```

4. **Run Backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```

5. **Run Frontend:**
   ```bash
   cd frontend && npm run dev
   ```

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Medical misinformation | RAG system, confidence thresholds, citations |
| HIPAA compliance | Encryption, access controls, audit logs |
| Budget overrun | Spot instances, self-hosting, cost monitoring |
| Timeline slip | Phased rollout, scope prioritization |

---

## Success Metrics

- **Technical:** >85% medical QA accuracy, <3s response time
- **Product:** 50+ beta users, 70%+ satisfaction
- **Business:** 5+ pilot customers, $500+ MRR

---

## Post-MVP Roadmap

- **Phase 2 (Months 4-6):** Medical imaging, USMLE education, mobile apps
- **Phase 3 (Months 7-12):** ERP features, hospital integration, enterprise sales
- **Phase 4 (Year 2+):** FDA clearance, global expansion, partnerships

---

## Contact & Support

- **Repository:** TBD
- **Documentation:** See `/docs` folder
- **Issues:** GitHub Issues (when repo created)

---

## License

To be determined (likely MIT or Apache 2.0 for code, with appropriate data licenses)

---

## Disclaimer

**Lumen is an informational tool and does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical decisions.**

---

**Status:** Awaiting plan approval to begin development

**Last Updated:** 2025-10-31
