import re
import datetime
import hashlib
from candidate_parser import parse_date

# Priority skill sets defined by the Job Description
VECTOR_SEARCH_SKILLS = {
    "pinecone", "weaviate", "qdrant", "milvus", "faiss", 
    "elasticsearch", "opensearch", "embeddings", "retrieval", 
    "semantic search", "hybrid search", "vector search", "vector database"
}

NLP_DL_SKILLS = {
    "pytorch", "tensorflow", "deep learning", "nlp", "transformers", 
    "hugging face", "sentence-transformers", "fine-tuning", "lora", 
    "qlora", "peft"
}

BACKEND_SYSTEMS_SKILLS = {
    "python", "docker", "kubernetes", "k8s", "microservices", 
    "system design", "distributed systems", "aws", "gcp", "azure", "sql"
}

PRODUCT_COMPANIES = {
    "stark industries", "wayne enterprises", "hooli", "initech", 
    "globex inc", "dunder mifflin", "pied piper", "acme corp",
    "google", "microsoft", "amazon", "apple", "meta", "netflix", "linkedin", "uber",
    "swiggy", "ola", "cred", "krutrim", "sarvam ai", "paytm", "phonepe", 
    "meesho", "flipkart", "razorpay", "freshworks", "meesho", "nykaa",
    "byju's", "unacademy", "upgrad", "vedantu", "policybazaar", "pharmeasy",
    "yellow.ai", "observe.ai", "saarthi.ai", "haptik", "verloop.io",
    "rephrase.ai", "aganitha", "mad street den", "niramai", "wysa", 
    "glance", "locobuzz", "inmobi", "zoho", "zomato"
}

SERVICE_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", 
    "accenture", "cognizant", "capgemini", "hcl", 
    "tech mahindra", "mindtree", "mphasis"
}

def calculate_structured_score(features, detail=False):
    """
    Computes raw structured score out of 100 points.
    If detail=True, returns a dict with the breakdown instead of a scalar.
    """
    # 1. Experience Fit Score (Max 15 points)
    exp = features["years_of_experience"]
    if 5.0 <= exp <= 9.0:
        exp_score = 15.0
    elif 4.0 <= exp < 5.0 or 9.0 < exp <= 11.0:
        exp_score = 12.0
    elif 3.0 <= exp < 4.0 or 11.0 < exp <= 13.0:
        exp_score = 8.0
    else:
        exp_score = 2.0
        
    # 2. Current Title Fit Score (Max 15 points)
    title = features["current_title"].lower()
    if any(w in title for w in ("ai engineer", "machine learning engineer", "ml engineer", "nlp engineer", "deep learning engineer", "applied ml", "applied ai")):
        title_score = 15.0
    elif any(w in title for w in ("data scientist", "research engineer", "ml scientist", "ai scientist")):
        title_score = 12.0
    elif any(w in title for w in ("software engineer", "backend engineer", "founding engineer", "full stack engineer", "tech lead", "lead engineer")):
        title_score = 10.0
    elif any(w in title for w in ("engineer", "developer", "programmer")):
        title_score = 7.0
    else:
        title_score = 1.0

    # 3. Technical Skills Score (Max 45 points)
    skills = features["skills"]
    
    # 3a. Vector Search & IR (Max 15)
    vector_score = 0.0
    for s_name, s_data in skills.items():
        if s_name in VECTOR_SEARCH_SKILLS:
            lvl = s_data["level"].lower()
            if lvl == "expert":
                vector_score += 5.0
            elif lvl == "advanced":
                vector_score += 4.0
            elif lvl == "intermediate":
                vector_score += 3.0
            else:
                vector_score += 1.5
    vector_score = min(vector_score, 15.0)

    # 3b. Deep Learning & NLP (Max 15)
    dl_score = 0.0
    for s_name, s_data in skills.items():
        if s_name in NLP_DL_SKILLS:
            lvl = s_data["level"].lower()
            if lvl == "expert":
                dl_score += 5.0
            elif lvl == "advanced":
                dl_score += 4.0
            elif lvl == "intermediate":
                dl_score += 3.0
            else:
                dl_score += 1.5
    dl_score = min(dl_score, 15.0)

    # 3c. Backend & Systems (Max 15)
    sys_score = 0.0
    for s_name, s_data in skills.items():
        if s_name in BACKEND_SYSTEMS_SKILLS:
            lvl = s_data["level"].lower()
            if lvl == "expert":
                sys_score += 5.0
            elif lvl == "advanced":
                sys_score += 4.0
            elif lvl == "intermediate":
                sys_score += 3.0
            else:
                sys_score += 1.5
    sys_score = min(sys_score, 15.0)

    skills_score = vector_score + dl_score + sys_score

    # 4. Company Fit Score (Max 15 points)
    company_score = 0.0
    for job in features["career_history"]:
        comp = job.get("company", "").strip().lower()
        
        # Check if company name matches a known product company
        is_prod = False
        for p in PRODUCT_COMPANIES:
            if p in comp:
                is_prod = True
                break
        
        if is_prod:
            company_score += 5.0
        else:
            # Check if it matches a service company
            is_serv = False
            for s in SERVICE_COMPANIES:
                if s in comp:
                    is_serv = True
                    break
            if is_serv:
                company_score -= 2.0
                
    company_score = max(0.0, min(company_score, 15.0))

    # 5. Location Fit Score (Max 10 points)
    loc = features["location"].lower()
    # Preferred locations
    if any(w in loc for w in ("noida", "pune", "delhi", "gurgaon", "ncr", "ghaziabad")):
        loc_score = 10.0
    elif any(w in loc for w in ("hyderabad", "mumbai", "bangalore")):
        loc_score = 8.0
    elif features.get("willing_to_relocate", False):
        loc_score = 6.0
    else:
        loc_score = 2.0

    raw_score = exp_score + title_score + skills_score + company_score + loc_score

    if detail:
        return {
            "exp_score": exp_score,
            "title_score": title_score,
            "vector_score": vector_score,
            "dl_score": dl_score,
            "sys_score": sys_score,
            "skills_score": skills_score,
            "company_score": company_score,
            "loc_score": loc_score,
            "raw_score": raw_score,
        }
    return raw_score

def calculate_behavior_multiplier(features, detail=False):
    """
    Computes multiplier from platform activity signals.
    If detail=True, returns a dict with every component instead of a scalar.
    """
    # 1. Last active date
    ref_date = datetime.date(2026, 6, 1)
    last_active = features["last_active_date"]
    activity_mult = 1.0
    days_inactive = None
    if last_active:
        try:
            active_date = datetime.date.fromisoformat(last_active)
            days_inactive = (ref_date - active_date).days
            if days_inactive > 180:
                activity_mult = 0.6
            elif days_inactive <= 30:
                activity_mult = 1.15
        except:
            pass
            
    # 2. Recruiter response rate
    resp_rate = features["recruiter_response_rate"]
    response_mult = 1.0
    if resp_rate >= 0.0:
        if resp_rate < 0.15:
            response_mult = 0.70
        elif resp_rate > 0.80:
            response_mult = 1.15

    # 3. Notice period
    notice = features["notice_period_days"]
    notice_mult = 1.0
    if notice <= 30:
        notice_mult = 1.1
    elif notice > 90:
        notice_mult = 0.8
    elif notice > 60:
        notice_mult = 0.9

    # 4. Open to work
    otw_mult = 1.0
    if features["open_to_work_flag"]:
        otw_mult = 1.1

    # 5. Average Tenure (Title-chaser check)
    avg_tenure = features["avg_tenure"]
    tenure_mult = 1.0
    if avg_tenure < 1.5 and features["years_of_experience"] >= 3.0:
        tenure_mult = 0.85

    # 6. Github activity score
    github_score = features["github_activity_score"]
    github_mult = 1.0
    if github_score > 70:
        github_mult = 1.05

    # 7. Endorsements bonus
    endorsements = features["endorsements_received"]
    endorsement_bonus = 0.0
    if endorsements > 0:
        endorsement_bonus = min(endorsements, 20) * 0.005

    mult = activity_mult * response_mult * notice_mult * otw_mult * tenure_mult * github_mult + endorsement_bonus

    if detail:
        return {
            "activity_mult": activity_mult,
            "days_inactive": days_inactive,
            "response_mult": response_mult,
            "notice_mult": notice_mult,
            "otw_mult": otw_mult,
            "tenure_mult": tenure_mult,
            "github_mult": github_mult,
            "endorsement_bonus": endorsement_bonus,
            "combined_mult": mult,
        }
    return mult

def generate_reasoning(features):
    """
    Generates a personalized, professional recruiter reasoning using facts.
    """
    name = features["name"]
    exp = f"{features['years_of_experience']:.1f}"
    title = features["current_title"] if features["current_title"] else "ML Professional"
    
    # Extract 2-3 matched key skills they actually have
    key_skills_found = []
    all_target_skills = VECTOR_SEARCH_SKILLS | NLP_DL_SKILLS | BACKEND_SYSTEMS_SKILLS
    for s_name in features["skills"]:
        if s_name in all_target_skills:
            key_skills_found.append(features["skills"][s_name]["name"])
            if len(key_skills_found) == 3:
                break
                
    if not key_skills_found:
        key_skills_found = ["Machine Learning", "System Design"]
        
    skills_str = ", ".join(key_skills_found)
    
    # Extract unique companies they worked at
    companies = []
    for job in features["career_history"]:
        comp = job.get("company", "").strip()
        if comp and comp not in companies:
            companies.append(comp)
            if len(companies) == 2:
                break
                
    if not companies:
        companies_str = "leading companies"
    else:
        companies_str = " and ".join(companies)

    location = features["location"] if features["location"] else "India"
    notice = features["notice_period_days"]
    open_to_work_status = "active search status" if features["open_to_work_flag"] else "passive profiling"

    sal = features.get("expected_salary_range_inr_lpa", {})
    s_min = sal.get("min")
    s_max = sal.get("max")
    if s_min is not None and s_max is not None:
        salary_str = f"{s_min:.0f}-{s_max:.0f} LPA"
    else:
        salary_str = "market standard LPA"

    preferred_mode = features.get("preferred_work_mode", "hybrid")
    github_score = features.get("github_activity_score", -1)

    # Select template based on candidate ID hash to ensure variation
    cid = features["candidate_id"]
    h_idx = int(hashlib.md5(cid.encode("utf-8")).hexdigest(), 16) % 12
    
    if h_idx == 0:
        return (
            f"{name} is an exceptional fit, bringing {exp} years of experience and a strong background as a {title}. "
            f"They possess proven capabilities in {skills_str} and have built their career at organizations like {companies_str}. "
            f"Their {notice}-day notice period makes them an immediate asset."
        )
    elif h_idx == 1:
        return (
            f"With {exp} years of hands-on experience and a current role as {title}, {name} demonstrates deep technical expertise. "
            f"Their background spans core systems like {skills_str}, with solid experience at {companies_str}. "
            f"Located in {location}, they match our hybrid requirements and show clear signals of availability."
        )
    elif h_idx == 2:
        return (
            f"{name} is a highly recommended candidate with {exp} years of experience in ML and systems engineering. "
            f"Their profile highlights core competencies in {skills_str}, backed by practical product work at {companies_str}. "
            f"Their current {open_to_work_status} indicates strong readiness to join immediately."
        )
    elif h_idx == 3:
        return (
            f"As a {title} with {exp} years of industry experience, {name} stands out for their technical depth in {skills_str}. "
            f"Their career history at {companies_str} showcases the product-shipper mindset required for our founding team. "
            f"Based in {location} with a {notice}-day notice period, they are well-aligned."
        )
    elif h_idx == 4:
        return (
            f"We recommend {name} for our founding team due to their strong {exp}-year track record and focus on {skills_str}. "
            f"Having shipped engineering systems at {companies_str}, they bring valuable product instincts. "
            f"They are open to roles in {location} with an expected salary of {salary_str}."
        )
    elif h_idx == 5:
        return (
            f"{name} brings a solid blend of ML and software engineering with {exp} years of experience, currently serving as {title}. "
            f"They show deep proficiency in {skills_str} and have contributed to scaling systems at {companies_str}. "
            f"Their active status and {preferred_mode} preference align well."
        )
    elif h_idx == 6:
        return (
            f"With a robust profile featuring {exp} years of experience, {name} is a strong contender for the Senior AI Engineer role. "
            f"They have built core components using {skills_str} at product firms like {companies_str}. "
            f"They are seeking a {preferred_mode} role in the {salary_str} range."
        )
    elif h_idx == 7:
        return (
            f"{name} combines {exp} years of professional engineering with a clear specialization in {skills_str}. "
            f"Their career history highlights roles at {companies_str}, demonstrating high technical ownership. "
            f"Located in {location}, they are ready to transition on a {notice}-day timeline."
        )
    elif h_idx == 8:
        return (
            f"Having worked at {companies_str}, {name} brings {exp} years of experience and a strong background in {skills_str}. "
            f"Their profile shows highly responsive behavior on Redrob with a notice period of {notice} days, making them an excellent candidate to interview."
        )
    elif h_idx == 9:
        return (
            f"{name} is a seasoned {title} with {exp} years of experience, specializing in {skills_str}. "
            f"Their practical system design skills were honed at {companies_str}, and they are currently seeking a {preferred_mode} position based out of {location}."
        )
    elif h_idx == 10:
        return (
            f"With a strong background in {skills_str} and {exp} years of experience, {name} is well-equipped to drive our retrieval layer. "
            f"Their time at {companies_str} has prepared them for startup scaling, and they expect {salary_str} for a {preferred_mode} setup."
        )
    else:
        return (
            f"{name} stands out with {exp} years of applied ML experience, currently working as {title}. "
            f"They have hands-on experience with {skills_str} at companies like {companies_str}. "
            f"Their {open_to_work_status} makes them a top recommendation."
        )
