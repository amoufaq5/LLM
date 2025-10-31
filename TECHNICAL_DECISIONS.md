# Lumen Medical LLM - Technical Decisions & Comparisons

This document explains key technical decisions for the MVP and compares alternatives.

---

## 1. MODEL SELECTION

### Recommended: BioMistral-7B

**Why BioMistral-7B?**
- Pre-trained on PubMed Central (medical literature)
- Apache 2.0 license (full ownership, commercial use allowed)
- 7B parameters (fits on single A100 40GB)
- Strong medical reasoning baseline
- Active community support

**Alternatives Considered:**

| Model | Size | License | Medical Pre-training | Pros | Cons | Verdict |
|-------|------|---------|---------------------|------|------|---------|
| **BioMistral-7B** | 7B | Apache 2.0 | Yes (PubMed) | Best medical baseline, efficient, fully open | Smaller than Llama 70B | **BEST FOR MVP** |
| Llama 3.1 8B | 8B | Llama 3.1 License | No | Great general model, large community | Not medical-specific, requires more fine-tuning | Good backup |
| Llama 3.1 70B | 70B | Llama 3.1 License | No | More powerful | 5-8x more expensive to train & serve | Too expensive for MVP |
| Meditron-7B | 7B | Llama 2 License | Yes (medical) | Medical-focused | Based on older Llama 2, less capable base | Older architecture |
| Med-PaLM 2 | ? | Proprietary | Yes | Google's medical AI | Not available, closed source | Not accessible |
| GPT-4 Medical | ? | Proprietary | ? | Powerful | No ownership, expensive API, privacy concerns | Not for MVP |

**Decision: BioMistral-7B** (with Llama 3.1 8B as backup)

---

## 2. FINE-TUNING APPROACH

### Recommended: QLoRA (Quantized Low-Rank Adaptation)

**Why QLoRA?**
- **Cost:** 10x cheaper than full fine-tuning (~$500 vs ~$5000)
- **Performance:** 95-98% of full fine-tuning quality
- **Efficiency:** Trains on single A100 40GB GPU
- **Ownership:** You own the LoRA adapters
- **Flexibility:** Can update adapters without retraining full model

**Technical Details:**
- Quantize base model to 4-bit (NF4)
- Train low-rank adapters (rank 16-64)
- Use bfloat16 for adapter weights
- Merge adapters with base model for deployment

**Alternatives:**

| Method | Cost (A100 hours) | Quality | GPU Memory | Verdict |
|--------|------------------|---------|------------|---------|
| **QLoRA** | 50-100 hours | 95-98% | 40GB | **BEST** |
| LoRA | 75-150 hours | 98-99% | 40GB | Slightly better but more expensive |
| Full Fine-tuning | 200-500 hours | 100% | 80GB x 4 | Too expensive |
| Prompt Tuning | 10-20 hours | 80-85% | 40GB | Insufficient quality |

**Decision: QLoRA** (best cost/performance ratio)

---

## 3. RAG (RETRIEVAL AUGMENTED GENERATION) SYSTEM

### Why RAG is Essential

Medical AI requires:
1. **Accuracy:** Source-backed responses, not just model memory
2. **Freshness:** Access to latest research and guidelines
3. **Explainability:** Cite sources for claims
4. **Reduced Hallucination:** Ground responses in retrieved documents

### RAG Architecture

```
User Query
    ↓
Embedding Model (sentence-transformers)
    ↓
Vector Search (Qdrant)
    ↓
Retrieve Top-K Documents (k=3-5)
    ↓
Construct Prompt with Context
    ↓
LLM Generation (BioMistral)
    ↓
Response + Citations
```

### Vector Database Comparison

| Database | Cost | Performance | Ease of Use | Verdict |
|----------|------|-------------|-------------|---------|
| **Qdrant** | Free (self-host) or $50/mo | Fast, Rust-based | Excellent API, Docker-ready | **BEST** |
| Pinecone | $70/mo starter | Very fast | Easy but paid only | Good but costs more |
| Weaviate | Free (self-host) | Fast | Good, more complex setup | Solid alternative |
| Chroma | Free (self-host) | Good | Very easy | Good for dev, production concerns |
| PostgreSQL pgvector | Free | Slower | Simple | Too slow for scale |

**Decision: Qdrant** (self-hosted initially, cloud when scaling)

### Embedding Model

**Recommended: all-MiniLM-L6-v2** (free, fast)
- Size: 23M parameters
- Speed: Very fast
- Quality: Good for medical texts
- Cost: Free

**Alternative: OpenAI Ada v2** ($0.10 per 1M tokens)
- Better quality but costs money
- Use only if accuracy issues with free models

**Decision: Start with free embeddings, upgrade if needed**

---

## 4. BACKEND FRAMEWORK

### Recommended: FastAPI

**Why FastAPI?**
- Modern, fast (async support)
- Auto-generated API docs (Swagger)
- Type hints (Python 3.8+)
- Great for AI/ML services
- Excellent performance

**Alternatives:**

| Framework | Async | Performance | Docs | ML Integration | Verdict |
|-----------|-------|-------------|------|----------------|---------|
| **FastAPI** | Yes | Excellent | Auto-generated | Excellent | **BEST** |
| Flask | No (unless with extensions) | Good | Manual | Good | Older, slower |
| Django | Yes (3.1+) | Good | Manual | Good | Too heavy for API |
| Node.js (Express) | Yes | Excellent | Manual | Poor for ML | Wrong language |

**Decision: FastAPI**

---

## 5. LLM SERVING / INFERENCE

### Recommended: vLLM

**Why vLLM?**
- **Speed:** 10-20x faster than HuggingFace transformers
- **Throughput:** Handles concurrent requests efficiently
- **Memory:** PagedAttention reduces memory usage
- **Cost:** Serve more users on fewer GPUs
- **Compatibility:** Works with HuggingFace models

**Alternatives:**

| Tool | Speed | Throughput | Ease | Cost | Verdict |
|------|-------|------------|------|------|---------|
| **vLLM** | Excellent | Excellent | Good | Low | **BEST** |
| Text Generation Inference (TGI) | Excellent | Excellent | Good | Low | Equally good |
| HuggingFace Transformers | Slow | Poor | Easy | High | Too slow for production |
| TensorRT-LLM | Fastest | Excellent | Hard | Low | Complex setup |
| llama.cpp | Good | Good | Easy | Very low | CPU inference, slower |

**Decision: vLLM** (or TGI - both excellent)

---

## 6. FRONTEND FRAMEWORK

### Recommended: Next.js 14 (React)

**Why Next.js?**
- Server-side rendering (SSR) for SEO
- App router (modern React)
- API routes (optional, we use FastAPI)
- Great developer experience
- Vercel deployment (free tier)

**Alternatives:**

| Framework | Performance | SEO | Learning Curve | Hosting | Verdict |
|-----------|-------------|-----|----------------|---------|---------|
| **Next.js** | Excellent | Excellent | Medium | Easy (Vercel) | **BEST** |
| React (CRA) | Good | Poor | Easy | Manual | Outdated approach |
| Vue.js (Nuxt) | Excellent | Excellent | Easy | Manual | Good but smaller community |
| Svelte (SvelteKit) | Excellent | Excellent | Easy | Manual | Great but less mature |
| Angular | Good | Good | Hard | Manual | Too heavy |

**Decision: Next.js 14**

---

## 7. DATABASE CHOICES

### Primary Database: PostgreSQL

**Why PostgreSQL?**
- **Reliability:** Battle-tested, ACID compliant
- **Features:** JSON support, full-text search, extensions
- **HIPAA:** Can be configured for compliance
- **Hosting:** Available everywhere (Supabase, Railway, RDS)

**Use Cases:**
- User accounts and authentication
- Patient profiles
- Conversation history
- Audit logs

### Vector Database: Qdrant

(See RAG section above)

**Use Cases:**
- Medical knowledge base embeddings
- Drug information vectors
- Regulatory document vectors

### Cache: Redis

**Why Redis?**
- **Speed:** In-memory, microsecond latency
- **Features:** Sessions, rate limiting, pub/sub
- **Simple:** Easy to set up and use

**Use Cases:**
- Session management
- API rate limiting
- Response caching
- Queue for async tasks (with Celery)

**Database Summary:**
- **PostgreSQL:** User data, profiles, structured data
- **Qdrant:** Vector search, RAG system
- **Redis:** Cache, sessions, queues

---

## 8. HOSTING & INFRASTRUCTURE

### MVP Infrastructure

| Component | Service | Cost | Reason |
|-----------|---------|------|--------|
| **Model Training** | RunPod (A100) | ~$2000 | Spot instances, flexible |
| **Model Inference** | RunPod Serverless | ~$400/mo | Pay-per-second, auto-scale |
| **Backend API** | Railway or Render | $20-50/mo | Easy deploy, PostgreSQL included |
| **Frontend** | Vercel | Free-$20/mo | Best Next.js hosting |
| **Vector DB** | Self-hosted (w/ backend) | Free | Or Qdrant Cloud $50/mo |
| **Redis** | Upstash | $10-20/mo | Serverless Redis |
| **Storage** | Cloudflare R2 | $5-10/mo | S3-compatible, cheaper |
| **Domain** | Namecheap/Cloudflare | $10/year | Standard |

**Total Monthly Cost:** $450-550 (after training)

### Scaling Path (Post-MVP)

- **Frontend:** Vercel Pro ($20/mo)
- **Backend:** Railway Pro ($50/mo) or AWS ECS
- **Database:** Supabase Pro ($25/mo) or AWS RDS
- **Inference:** RunPod dedicated pods or AWS Inferentia
- **Monitoring:** Better Stack ($20/mo)

---

## 9. DEVELOPMENT TOOLS

### Must-Have Tools

| Category | Tool | Cost | Purpose |
|----------|------|------|---------|
| **IDE** | VS Code | Free | Development |
| **AI Assistant** | Cursor or GitHub Copilot | $20/mo | Speed up coding |
| **Version Control** | Git + GitHub | Free | Code management |
| **Training Tracking** | Weights & Biases | Free tier | Monitor training |
| **API Testing** | Postman or Insomnia | Free | Test APIs |
| **Monitoring** | Better Stack or Sentry | $20/mo or free tier | Production monitoring |
| **Analytics** | PostHog | Free tier | Usage analytics (HIPAA-compliant mode) |

**Total Tool Cost:** $40/month (optional, can use free tiers)

---

## 10. SECURITY & COMPLIANCE

### HIPAA Compliance Checklist (MVP)

**Technical Safeguards:**
- [x] Encryption at rest (AES-256)
- [x] Encryption in transit (TLS 1.3)
- [x] Access controls (authentication + authorization)
- [x] Audit logging (all data access)
- [x] Automatic session timeout
- [x] Strong password requirements
- [x] Two-factor authentication (optional for MVP)

**Administrative Safeguards:**
- [ ] Privacy policy (legal review needed)
- [ ] Terms of service
- [ ] User data deletion capability
- [ ] Data retention policy
- [ ] Incident response plan

**Physical Safeguards:**
- [ ] BAA (Business Associate Agreement) with all service providers
  - RunPod: Check BAA availability
  - Railway/Render: Check BAA
  - Vercel: Has BAA option

**MVP Approach:**
- Build technical safeguards into architecture
- Add "Informational purposes only" disclaimers
- Don't make diagnostic claims (avoid FDA device classification)
- Get legal review before handling real patient data

---

## 11. COST OPTIMIZATION STRATEGIES

### Training Cost Optimization

1. **Use Spot Instances:** 50-70% cheaper on RunPod
2. **Efficient Hyperparameter Search:** Use Optuna, limit experiments
3. **Smaller Model First:** Start with 7B, consider 13B only if needed
4. **QLoRA:** 10x cheaper than full fine-tuning
5. **Resume Capability:** Save checkpoints to resume if interrupted

**Expected Training Cost: $500-1500** (instead of $5000+)

### Inference Cost Optimization

1. **Serverless:** Pay per second on RunPod Serverless
2. **Quantization:** Run 4-bit or 8-bit quantized models (2-4x cheaper)
3. **Batch Requests:** Process multiple queries together
4. **Caching:** Cache common queries in Redis
5. **Smart Routing:** Use RAG for facts, LLM only for reasoning

**Expected Inference Cost: $300-500/month** for 1000-5000 requests/day

### Overall Budget Tracking

- **Development:** 3 months × $0 (solo) = $0
- **Training:** $1500 (one-time)
- **Infrastructure:** 3 months × $500 = $1500
- **Tools:** 3 months × $40 = $120
- **Buffer:** $1000
- **Total MVP Cost: $4,000-5,000** (well within budget)

---

## 12. MONITORING & OBSERVABILITY

### Key Metrics to Track

**Model Metrics:**
- Response latency (P50, P95, P99)
- Tokens per second (throughput)
- Concurrent requests
- Hallucination rate (spot checks)
- User satisfaction scores

**System Metrics:**
- API uptime
- Error rates
- Database query performance
- Cache hit rates
- API rate limit violations

**Business Metrics:**
- Daily/monthly active users
- Queries per user
- Feature usage (patient vs pharma)
- User retention
- Conversion to paid (post-MVP)

**Tools:**
- **Application:** Better Stack, Sentry
- **Infrastructure:** RunPod dashboard, Railway metrics
- **Custom:** Prometheus + Grafana (if self-hosting)

---

## 13. TESTING STRATEGY

### Testing Pyramid

```
        /\
       /E2E\         End-to-End Tests (10%)
      /------\       - User flows
     /Integration\   Integration Tests (30%)
    /------------\   - API + DB + LLM
   / Unit Tests  \  Unit Tests (60%)
  /----------------\ - Individual functions
```

### Test Coverage Goals

- **Unit Tests:** 70%+ coverage
- **Integration Tests:** Critical paths
- **E2E Tests:** Core user journeys

### Medical-Specific Testing

1. **Accuracy Testing:**
   - Curated medical Q&A test set
   - Expert review of responses
   - Benchmark against medical exams

2. **Safety Testing:**
   - Test dangerous queries (suicide, self-harm)
   - Verify appropriate escalation
   - Check disclaimer presence

3. **Hallucination Detection:**
   - Fact-check responses
   - Source verification
   - Confidence thresholds

---

## 14. DEPLOYMENT STRATEGY

### MVP Deployment (Week 12)

**Phase 1: Staging (Week 12 Day 1-3)**
- Deploy to staging environment
- Run automated tests
- Manual QA testing
- Performance testing (load testing)

**Phase 2: Beta Launch (Week 12 Day 4-5)**
- Deploy to production
- Soft launch to 5-10 beta testers
- Monitor closely
- Fix critical bugs

**Phase 3: Public Launch (Week 12 Day 6-7)**
- Open to public (with rate limits)
- Marketing materials
- Documentation
- Support channels

### CI/CD Pipeline

```
Git Push → GitHub Actions → Tests → Build → Deploy
```

**Automated Steps:**
- Run tests (unit + integration)
- Lint code (Ruff, ESLint)
- Type checking (mypy, TypeScript)
- Build Docker images
- Deploy to staging (auto)
- Deploy to production (manual approval)

---

## 15. ALTERNATIVES ANALYSIS SUMMARY

### What We're NOT Doing (and Why)

**1. Building Model from Scratch**
- **Why not:** $5-10M cost, 18-24 months, requires research team
- **Our choice:** Fine-tune open-source model

**2. Using Proprietary APIs (OpenAI, Anthropic)**
- **Why not:** No ownership, ongoing costs, privacy concerns
- **Our choice:** Self-hosted fine-tuned model

**3. Microservices Architecture**
- **Why not:** Over-engineering for MVP, adds complexity
- **Our choice:** Monolithic FastAPI app (can split later)

**4. Building Mobile Apps First**
- **Why not:** Doubles development time, web-first is faster
- **Our choice:** Responsive web app, PWA for mobile-like experience

**5. Multi-tenancy**
- **Why not:** Adds complexity, not needed for MVP
- **Our choice:** Single instance, add multi-tenancy in Phase 2

**6. Real-time Features (WebSockets)**
- **Why not:** Streaming responses nice-to-have, not critical
- **Our choice:** Standard HTTP requests (can add streaming later)

---

## 16. TECHNICAL DEBT TO ACCEPT (MVP)

**Acceptable for MVP:**
- No WebSockets (regular HTTP polling acceptable)
- Basic UI (polish later)
- Self-hosted services (migrate to managed later)
- Limited test coverage (60% vs 90%)
- Manual deployment (automate later)
- No mobile apps (web-first)
- English only (i18n later)

**Not Acceptable:**
- Security vulnerabilities
- Data privacy issues
- Medical misinformation
- Poor response quality
- No disclaimers
- Slow performance (>5s response)

---

## 17. DECISION LOG

| Decision | Option Chosen | Date | Rationale |
|----------|---------------|------|-----------|
| Base Model | BioMistral-7B | (Pending approval) | Best medical pre-training, Apache 2.0 license |
| Fine-tuning | QLoRA | (Pending approval) | 10x cheaper, 95%+ quality |
| Backend | FastAPI | (Pending approval) | Modern, fast, great for ML |
| Frontend | Next.js 14 | (Pending approval) | Best React framework, Vercel hosting |
| Database | PostgreSQL | (Pending approval) | Reliable, feature-rich |
| Vector DB | Qdrant | (Pending approval) | Fast, free to self-host |
| Hosting | RunPod + Railway + Vercel | (Pending approval) | Best cost/performance |
| LLM Serving | vLLM | (Pending approval) | 10x faster inference |

---

## QUESTIONS FOR YOU

Before finalizing these decisions:

1. **Model:** Approve BioMistral-7B or prefer Llama 3.1 8B?
2. **Budget:** Confirm $10-25K, optimize for lower ($6-10K)?
3. **Timeline:** 3 months firm, or flexible if needed?
4. **Hosting:** Comfortable with RunPod for GPU workloads?
5. **Open Source:** All components open source, or okay with some proprietary tools?

---

**Next Step:** Once you approve these technical decisions, I'll begin implementation.
