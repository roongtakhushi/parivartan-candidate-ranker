import json
import datetime

# Real-world company founding years for startup anomalies
REAL_COMPANY_FOUNDING = {
    "Sarvam AI": 2023,
    "Krutrim": 2023,
    "Glance": 2019,
    "Rephrase.ai": 2019,
    "CRED": 2018,
    "Observe.AI": 2017,
    "Saarthi.ai": 2017,
    "Yellow.ai": 2016,
    "PhonePe": 2015,
    "Meesho": 2015,
    "PharmEasy": 2015,
    "Unacademy": 2015,
    "upGrad": 2015,
    "Wysa": 2015,
    "Swiggy": 2014,
    "Razorpay": 2014,
}

SERVICE_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", 
    "accenture", "cognizant", "capgemini", "hcl", 
    "tech mahindra", "mindtree", "mphasis"
}

IRRELEVANT_TITLE_WORDS = {
    "sales", "marketing", "hr", "recruiter", "operations", "support", 
    "customer success", "content writer", "accountant", "finance", 
    "legal", "lawyer", "ui designer", "product designer", "graphic designer", 
    "civil engineer", "mechanical engineer", "electrical engineer", 
    "chemical engineer", "business analyst", "project manager", "scrum master"
}

ACADEMIC_WORDS = {
    "postdoc", "phd scholar", "teaching assistant", "professor", 
    "lecturer", "academic lab", "doctoral candidate", "graduate assistant", 
    "doctoral researcher"
}

def parse_date(dt_str):
    if not dt_str:
        return None
    try:
        parts = dt_str.split("-")
        return int(parts[0]), int(parts[1])
    except:
        return None

def is_honeypot(cand):
    """
    Applies the 6 logical consistency checks to identify honeypots.
    Returns (True, reason) if it is a honeypot, else (False, "").
    """
    skills = cand.get("skills", [])
    
    # 1. Expert/Advanced skill with 0 duration
    for s in skills:
        lvl = str(s.get("proficiency", s.get("level", ""))).lower()
        dur = s.get("duration_months", 0)
        if lvl in ("expert", "advanced") and dur == 0:
            return True, f"Skill duration anomaly: expert/advanced skill '{s.get('name')}' has 0 months duration."

    career = cand.get("career_history", [])
    
    # 2. Current job duration mismatch (ref date June 2026)
    if career:
        curr_job = career[0]
        if curr_job.get("is_current"):
            start = curr_job.get("start_date")
            parsed_start = parse_date(start)
            if parsed_start:
                y, m = parsed_start
                # Calculate expected months between start date and reference date June 2026
                expected_months = (2026 - y) * 12 + (6 - m)
                reported_dur = curr_job.get("duration_months", 0)
                if abs(expected_months - reported_dur) > 2:
                    return True, f"Current job duration mismatch: start {start} expects ~{expected_months} months, but reported {reported_dur}."

    # 3 & 4. Individual and sum job duration vs total experience
    profile = cand.get("profile", {})
    total_exp = profile.get("years_of_experience", 0.0)
    sum_dur = 0.0
    for job in career:
        dur = job.get("duration_months", 0) / 12.0
        if dur > total_exp + 0.5:
            return True, f"Job duration anomaly: single job duration ({dur:.1f} yrs) exceeds total experience ({total_exp} yrs)."
        sum_dur += dur
    if sum_dur > total_exp + 2.0:
        return True, f"Job duration anomaly: sum of job durations ({sum_dur:.1f} yrs) exceeds total experience ({total_exp} yrs)."

    # 5. Assessment for missing skill
    assessment = cand.get("platform_assessment", {})
    if not assessment:
        assessment = cand.get("redrob_signals", {}).get("skill_assessment_scores", {})
    if assessment:
        skill_names = {str(s.get("name", "")).strip().lower() for s in skills if s.get("name")}
        for ass_skill in assessment.keys():
            if ass_skill.strip().lower() not in skill_names:
                return True, f"Assessment anomaly: assessed for skill '{ass_skill}' which does not exist in skills list."

    # 6. Company founding year violations
    for job in career:
        comp = job.get("company", "").strip()
        start = job.get("start_date")
        if comp in REAL_COMPANY_FOUNDING and start:
            parsed_start = parse_date(start)
            if parsed_start:
                sy, sm = parsed_start
                if sy < REAL_COMPANY_FOUNDING[comp]:
                    return True, f"Founding date violation: worked at {comp} in {sy}, but company was founded in {REAL_COMPANY_FOUNDING[comp]}."

    # 7. Salary range contradiction
    sal = cand.get("redrob_signals", {}).get("expected_salary_range_inr_lpa", {})
    sal_min = sal.get("min")
    sal_max = sal.get("max")
    if sal_min is not None and sal_max is not None:
        if sal_min > sal_max:
            return True, f"Salary anomaly: expected salary min ({sal_min} LPA) exceeds max ({sal_max} LPA)."

    # 8. Graduation vs Experience chronology mismatch
    education = cand.get("education", [])
    grad_years = [edu.get("end_year") for edu in education if edu.get("end_year")]
    if grad_years and total_exp > 0:
        min_grad = min(grad_years)
        max_possible_exp = (2026 - min_grad) + 2
        if total_exp > max_possible_exp + 1.0:
            return True, f"Chronology anomaly: total experience ({total_exp} yrs) exceeds maximum possible experience ({max_possible_exp} yrs) based on graduation year ({min_grad})."

    # 9. College chronology mismatch (earliest job year vs latest college graduation year)
    if career and education:
        job_years = []
        for job in career:
            start = job.get("start_date")
            if start:
                try:
                    job_years.append(int(start.split("-")[0]))
                except:
                    pass
        if job_years and grad_years:
            earliest_job_yr = min(job_years)
            latest_grad_yr = max(grad_years)
            if latest_grad_yr - earliest_job_yr > 8:
                return True, f"College chronology anomaly: first job started in {earliest_job_yr}, but college ended in {latest_grad_yr}."

    return False, ""

def is_service_only(career):
    if not career:
        return False
    for job in career:
        comp = job.get("company", "").strip().lower()
        matched = False
        for s in SERVICE_COMPANIES:
            if s in comp:
                matched = True
                break
        if not matched:
            return False
    return True

def is_pure_researcher(career):
    if not career:
        return False
    all_jobs_academic = True
    has_industry_role = False
    
    for job in career:
        title = job.get("title", "").lower()
        is_academic = any(w in title for w in ACADEMIC_WORDS)
        if not is_academic:
            all_jobs_academic = False
            # Check if it looks like a corporate developer/engineer role
            if any(w in title for w in ("engineer", "developer", "programmer", "architect", "lead", "scientist")):
                has_industry_role = True
                
    if all_jobs_academic or (not has_industry_role):
        return True
    return False

def check_disqualification(cand):
    """
    Checks if a candidate is disqualified based on JD criteria.
    Returns (True, reason) or (False, "").
    """
    career = cand.get("career_history", [])
    
    # 1. Service company only
    if is_service_only(career):
        return True, "Disqualified: Entire career is at IT consulting/services firms (TCS, Infosys, etc.)."
        
    # 2. Pure academic researcher
    if is_pure_researcher(career):
        return True, "Disqualified: Pure research/academic profile without industry software engineering deployment."
        
    # 3. Irrelevant current title
    if career:
        curr_title = career[0].get("title", "").lower()
        if any(w in curr_title for w in IRRELEVANT_TITLE_WORDS):
            # Check if they have ANY software or ML background, if not, disqualify
            has_se_past = False
            for job in career[1:]:
                past_title = job.get("title", "").lower()
                if any(w in past_title for w in ("engineer", "developer", "programmer", "data scientist", "ml")):
                    has_se_past = True
                    break
            if not has_se_past:
                return True, f"Disqualified: Irrelevant current title '{career[0].get('title')}' with no software/ML engineering background."
                
    return False, ""

def extract_features(cand):
    """
    Parses and extracts key structured features for ranking.
    """
    profile = cand.get("profile", {})
    signals = cand.get("redrob_signals", {})
    skills = cand.get("skills", [])
    career = cand.get("career_history", [])
    
    # Honeypot check
    is_hp, hp_reason = is_honeypot(cand)
    
    # Disqualification check
    is_dq, dq_reason = check_disqualification(cand) if not is_hp else (False, "")
    
    # Experience
    total_exp = profile.get("years_of_experience", 0.0)
    
    # Current title
    current_title = career[0].get("title", "") if career else ""
    
    # Skills mapping
    skills_dict = {}
    for s in skills:
        name = s.get("name", "").strip()
        lvl = s.get("proficiency", s.get("level", "")).strip()
        dur = s.get("duration_months", 0)
        skills_dict[name.lower()] = {
            "name": name,
            "level": lvl,
            "duration": dur
        }
        
    # Average Tenure (Title-chaser check)
    total_jobs = len(career)
    if total_jobs > 1 and total_exp > 0:
        avg_tenure = total_exp / total_jobs
    else:
        avg_tenure = total_exp
        
    return {
        "candidate_id": cand.get("candidate_id"),
        "name": profile.get("anonymized_name", ""),
        "years_of_experience": total_exp,
        "current_title": current_title,
        "skills": skills_dict,
        "location": profile.get("location", ""),
        "notice_period_days": signals.get("notice_period_days", 90),
        "open_to_work_flag": signals.get("open_to_work_flag", False),
        "last_active_date": signals.get("last_active_date", ""),
        "recruiter_response_rate": signals.get("recruiter_response_rate", -1.0),
        "github_activity_score": signals.get("github_activity_score", -1),
        "endorsements_received": signals.get("endorsements_received", 0),
        "avg_tenure": avg_tenure,
        "expected_salary_range_inr_lpa": signals.get("expected_salary_range_inr_lpa", {}),
        "preferred_work_mode": signals.get("preferred_work_mode", ""),
        "is_honeypot": is_hp,
        "honeypot_reason": hp_reason,
        "is_disqualified": is_dq,
        "disqualification_reason": dq_reason,
        "career_history": career,
        "platform_assessment": cand.get("platform_assessment", {})
    }
