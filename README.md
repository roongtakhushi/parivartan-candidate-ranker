# Redrob AI Candidate Discovery & Ranking Engine

This repository contains the source code for the **Intelligent Candidate Discovery & Ranking Engine** built for the Redrob Hackathon. The system parses 100,000 candidate profiles and ranks the top 100 fits for the **Senior AI Engineer — Founding Team** role.

## Key Design Principles & Features

1. **Honeypot Screening Engine (0% Honeypot Rate)**:
   We enforce 9 logical consistency checks on-the-fly to filter out "impossible" candidate records, achieving a 0% honeypot rate in the top 100:
   - **Skill Duration Check**: Rejects candidates claiming "Expert" or "Advanced" skills with `duration_months == 0`.
   - **Current Job Duration Alignment**: Rejects candidates whose current job duration mismatches the time between start date and the reference date of June 2026.
   - **Individual Job Duration Check**: Rejects candidates whose single job duration exceeds their total years of experience.
   - **Sum Job Duration Check**: Rejects candidates whose sum of job durations exceeds their total experience by more than 2 years.
   - **Assessment Mismatch Check**: Rejects candidates with assessment scores for skills they do not list on their profile.
   - **Startup Founding Date Validation**: Rejects candidates who claim to have worked at real-world Indian startups (e.g. Sarvam AI, Krutrim, CRED, etc.) prior to their actual founding dates.
   - **Salary Range Contradiction**: Rejects candidates whose expected minimum salary is strictly greater than their maximum expected salary (min > max).
   - **Graduation vs. Experience**: Rejects candidates whose total years of experience exceed the years since they graduated college + 2.
   - **College Chronology Check**: Rejects candidates who claim to have started their first job more than 8 years before graduating college.

2. **Strict Disqualification Logic**:
   - **Service Company Only**: Candidates whose entire career is spent at IT consulting/services firms (TCS, Infosys, Accenture, Cognizant, Wipro, Capgemini, etc.) are filtered out.
   - **Pure Academic Researchers**: Candidates with only academic or research lab backgrounds and no industry software deployment experience are disqualified.
   - **Irrelevant Titles**: Candidates in sales, marketing, HR, operations, and support roles without a software engineering or ML background are filtered out.

3. **Hybrid Scoring Engine**:
   - **Experience Alignment (15 pts)**: Optimizes for the JD's 5-9 years sweet spot.
   - **Title Match (15 pts)**: Scores current titles (ML/AI Engineer > Data Scientist > Backend/Software Engineer).
   - **Technical Skill Relevance & Depth (45 pts)**: Scores Vector Search & IR, Deep Learning & NLP, and Backend & Systems skills.
   - **Company Fit (15 pts)**: Rewards candidates who have worked at product/startup companies, and penalizes service company tenure.
   - **Location Alignment (10 pts)**: Prioritizes candidates in Noida, Pune, Delhi NCR, and those willing to relocate.

4. **Multiplicative Behavioral Signal Modifier**:
   - Downweights candidates inactive for >6 months (by 0.6x) or with low recruiter response rates.
   - Upweights candidates active within 30 days, open to work, possessing sub-30-day notice periods, or with strong GitHub activity.
   - Identifies and penalizes "title-chasers" (candidates switching companies every <1.5 years on average).

5. **Dynamic, Fact-Based Recruiter Reasonings**:
   - Generates personalized, professional recruiter justifications highlighting candidate-specific years of experience, current titles, specific skills, and previous employers.
   - Employs 12 different templates selected dynamically based on a hash of the candidate ID to guarantee variation.

---

## Getting Started

### Prerequisites
- Python 3.8+ (Only standard libraries are used; no external dependencies).

### Reproduction Command
Run the ranker on the candidates dataset:
```bash
python rank.py --candidates "./judges dataset/candidates.jsonl" --out "./parivartan.csv"
```

### Validation
To run the validator script on the generated CSV file:
```bash
python "./judges dataset/validate_submission.py" "./parivartan.csv"
```

### Docker Sandbox Replication
You can build and run this engine in a fully sandboxed Docker container:
1. Build the Docker image:
   ```bash
   docker build -t redrob-ranker .
   ```
2. Run the ranker container (mounting your local data directory):
   ```bash
   docker run --rm -v "${PWD}:/data" redrob-ranker --candidates "/data/judges dataset/candidates.jsonl" --out "/data/parivartan.csv"
   ```

### Streamlit Web Sandbox Interface
To run the interactive web interface locally:
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## Performance Specs
- **Total Runtime**: **~9 seconds** on CPU (well within the 5-minute hackathon constraint).
- **RAM Usage**: **<100 MB** (well within the 16 GB constraint).
- **Network**: **Off** (fully local, offline execution).
