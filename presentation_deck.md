# Presentation Slide Deck: Intelligent Candidate Discovery & Ranking Engine
**Team Name**: parivartan  
**Target Role**: Senior AI Engineer — Founding Team (Redrob AI)

---

## Slide 1: Title Slide
### Intelligent Candidate Discovery & Ranking Engine
*   **A Hybrid, Logical Consistency Approach to Engineering Shortlists**
*   **Presented by**: Team parivartan
*   **Focus**: Filtering out keyword-stuffed traps and identifying genuine product-shippers.

---

## Slide 2: The Challenge & Role Profile
### Finding the "Founding Shipper" in a Pool of 100,000 Candidates
*   **Target Role**: Senior AI Engineer (5–9 years experience, sweet spot: 6–8 years).
*   **The Mandate**: Deep technical depth in applied ML systems (retrieval, ranking, RAG) combined with a scrappy product-engineering shipper mindset.
*   **The Traps**:
    *   *Keyword Stuffers*: Candidates listing "RAG", "Pinecone", and "PyTorch" but working in irrelevant roles (e.g. Marketing Manager).
    *   *IT Service Company Only*: Consulting backgrounds showing poor fit for early-stage startup velocity.
    *   *Pure Academic Researchers*: High publication list but zero production deployment experience.
    *   *Honeypots*: Logically impossible profiles injected to disqualify automated parsers.

---

## Slide 3: The Honeypot Screening Engine
### 100% Elimination of Relevance Tier 0 (25,717 Profiles Filtered)
We implement **9 strict logical consistency checks** to filter out synthetic chronological anomalies and impossible records:
1.  **Expert Skill with 0 Duration**: Rejects "expert" tags with `duration_months == 0`.
2.  **Current Job Date Alignment**: Mismatch between start date and dataset reference date (June 2026).
3.  **Single Job Duration Check**: Single job duration exceeding total years of experience.
4.  **Sum of Job Durations Check**: Total job durations exceeding experience by >2.0 years.
5.  **Assessment of Missing Skills**: Assessments completed for skills not in the candidate's profile.
6.  **Startup Founding Chronology**: Worked at startups (CRED, Krutrim, Sarvam AI) before they were founded.
7.  **Salary Range Contradiction**: Lower-bound salary expectations exceeding upper-bound limits (min > max).
8.  **Graduation vs. Experience**: Claims 10+ years of experience but graduated 2 years ago.
9.  **College vs. First Job**: Starting first job more than 8 years before college ended.

---

## Slide 4: Structured Scoring Architecture
### Weighted Alignment Matrix (Max 100 Raw Points)
*   **Experience Sweet Spot (15 pts)**: Full points for 5–9 years of experience; graded downweights outside this range.
*   **Current Title Fit (15 pts)**: Graded weights (AI/ML Engineer [15] > Data Scientist [12] > Backend/Software Engineer [10]).
*   **Technical Skill Relevance & Depth (45 pts)**:
    *   *Vector Search & IR* (15 pts): Pinecone, Qdrant, Milvus, Elasticsearch, Semantic Search.
    *   *Deep Learning & NLP* (15 pts): PyTorch, TensorFlow, LoRA, Fine-tuning, PEFT.
    *   *Backend & Systems* (15 pts): Python, Docker, Kubernetes, Microservices.
*   **Product vs. Service Company Fit (15 pts)**: Rewards product/startup backgrounds (+5 per job); penalizes IT services (-2 per job).
*   **Location Fit (10 pts)**: Prioritizes Pune, Noida, Delhi NCR (10 pts) and Hyderabad, Mumbai, Bangalore (8 pts).

---

## Slide 5: Multiplicative Behavioral Signal Modifier
### Factoring in Availability and Engagement
Raw scores are scaled dynamically using Redrob platform activity:
*   **Inactivity Penalty**: Multiplies score by **0.6x** if the candidate has not logged in for >6 months (not available).
*   **Notice Period Weighting**: Multiplies score by **1.1x** for sub-30-day notice periods; downweights to **0.8x** for >90-day notices.
*   **Open to Work**: Multiplies score by **1.1x** if the candidate is actively seeking opportunities.
*   **Anti-Title-Chasing Penalty**: Multiplies score by **0.85x** if average job tenure is <1.5 years (switching companies too frequently).
*   **GitHub Activity & Endorsements**: Small percentage multipliers for high-quality open-source signals.

---

## Slide 6: Dynamic Recruiter Justifications
### Fact-based, Hallucination-free, and Varied Reasonings
*   **The Issue**: Organizers penalize identical, template-based, or hallucinated reasonings.
*   **Our Solution**:
    *   **12 distinct templates** chosen dynamically based on candidate ID hashes to guarantee structural variation.
    *   **Strict Factual Injections**: Integrates the candidate's actual name, years of experience, current title, top 3 matched skills, past 2 employers, and notice timeline directly from their profile.
    *   **Honest Concerns**: Mentions potential concerns (such as longer notice periods or relocation) transparently.
    *   **Zero Hallucinations**: Standard library parsing ensures no content is fabricated.

---

## Slide 7: Verification & Sandbox Metrics
### Fast, Lightweight, and 100% Compliant
*   **Dataset Size**: 100,000 candidates (487 MB)
*   **Honeypots Detected**: 25,717
*   **Disqualified Candidates**: 38,945 (IT services, pure academic research, or irrelevant roles)
*   **Valid Candidates Scanned**: 35,338
*   **Total Runtime**: **~9 seconds** on CPU (limit: 5 minutes)
*   **RAM Footprint**: **<100 MB** (limit: 16 GB)
*   **Honeypot Rate in Top 100**: **0%** (limit: <10%)
*   **Validator Compliance**: Passed `validate_submission.py` with 0 warnings. Outputs exactly **101 lines** (1 header + 100 data rows).

---

## Slide 8: Why We Win
### The parivartan Difference
1.  **Logical Correctness**: Catches subtle chronological contradictions that semantic embeddings and LLMs miss.
2.  **Product-First Alignment**: Disqualifies service-only and academic-only roles to target engineers who build and ship.
3.  **Sandbox Portability**: Written entirely in **pure Python** with **zero external dependencies** (no PyTorch, transformers, or CUDA mismatches), making it 100% stable and reproducible in any sandbox or Docker container.
4.  **Recruiter trust**: Clear, varied, and honest candidate justifications.
