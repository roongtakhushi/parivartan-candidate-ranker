import streamlit as st
import pandas as pd
import json
import io
import hashlib
from candidate_parser import extract_features
from ranker import calculate_structured_score, calculate_behavior_multiplier, generate_reasoning

# Page configuration for high premium aesthetics
st.set_page_config(
    page_title="parivartan | AI Candidate Ranker Sandbox",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for glassmorphism and modern UI styling
st.markdown("""
<style>
    .main-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF4B4B, #FF8F8F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        color: #888888;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FF4B4B;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #AAAAAA;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar metadata
st.sidebar.markdown("<h2 style='color:#FF4B4B; font-weight:700;'>🎯 parivartan</h2>", unsafe_allow_html=True)
st.sidebar.markdown("**Role Profile**: Senior AI Engineer (Founding Team)")
st.sidebar.markdown("**Evaluation Target**: 5-9 yrs exp, applied ML/RAG, product companies.")
st.sidebar.markdown("---")
st.sidebar.markdown("### Submission Spec Compliance")
st.sidebar.markdown("- **Output format**: `candidate_id,rank,score,reasoning`")
st.sidebar.markdown("- **Validation**: Passed Stage 1 & 2 script check")
st.sidebar.markdown("- **Honeypot Screening**: 9 logical consistency checks")

# Main Page Header
st.markdown("<div class='main-title'>AI Candidate Discovery & Ranking Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Hosted Sandbox Demonstration | Team parivartan</div>", unsafe_allow_html=True)

# Load helper functions for parsing uploaded datasets
def process_data(file_content, is_jsonl=True):
    candidates = []
    
    if is_jsonl:
        # Process JSONL format
        lines = file_content.decode("utf-8").splitlines()
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                candidates.append(json.loads(line))
            except Exception as e:
                st.error(f"Error parsing JSONL line {idx+1}: {e}")
    else:
        # Process JSON list format
        try:
            candidates = json.loads(file_content.decode("utf-8"))
            if not isinstance(candidates, list):
                candidates = [candidates]
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            
    return candidates

# File Uploader
uploaded_file = st.file_uploader(
    "Upload Candidate Data (JSON/JSONL format, max 100 profiles recommended for sandbox)", 
    type=["json", "jsonl"],
    help="Upload candidates.jsonl or sample_candidates.json"
)

# Use preloaded sample candidates if no file uploaded
candidates = []
if uploaded_file is not None:
    is_jsonl = uploaded_file.name.endswith("jsonl")
    candidates = process_data(uploaded_file.getvalue(), is_jsonl)
    st.success(f"Successfully loaded {len(candidates)} candidates from {uploaded_file.name}!")
else:
    # Try to load the default sample_candidates.json
    try:
        with open("judges dataset/sample_candidates.json", "rb") as f:
            candidates = process_data(f.read(), is_jsonl=False)
        st.info(f"Showing pre-loaded candidate sample ({len(candidates)} candidates from sample_candidates.json).")
    except Exception as e:
        st.warning("No file uploaded and default sample_candidates.json was not found in 'judges dataset/' folder.")

# Core Evaluation Pipeline
if candidates:
    honeypot_count = 0
    disqualified_count = 0
    valid_candidates = []
    
    # Process candidates
    for cand in candidates:
        feat = extract_features(cand)
        
        if feat["is_honeypot"]:
            honeypot_count += 1
            # Still keep track of blocked candidates for transparency/UI reporting
            feat["status"] = "🚫 Honeypot (Blocked)"
            feat["filter_reason"] = feat["honeypot_reason"]
            feat["score"] = 0.0
            feat["reasoning"] = f"Filtered out: {feat['honeypot_reason']}"
        elif feat["is_disqualified"]:
            disqualified_count += 1
            feat["status"] = "⚠️ Disqualified"
            feat["filter_reason"] = feat["disqualification_reason"]
            feat["score"] = 0.0
            feat["reasoning"] = f"Disqualified: {feat['disqualification_reason']}"
        else:
            feat["status"] = "✅ Valid"
            feat["filter_reason"] = ""
            # Calculate raw and behavioral score
            raw_score = calculate_structured_score(feat)
            multiplier = calculate_behavior_multiplier(feat)
            final_score = round(raw_score * multiplier, 3)
            feat["score"] = final_score
            feat["reasoning"] = generate_reasoning(feat)
            valid_candidates.append(feat)

    # Sort valid candidates
    valid_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Ranks assignments
    for i, cand in enumerate(valid_candidates):
        cand["rank"] = i + 1

    # Merge all processed candidates for detailed exploration
    all_processed = []
    for cand in candidates:
        # Search by ID in valid_candidates to get ranks
        cid = cand.get("candidate_id")
        match = next((x for x in valid_candidates if x["candidate_id"] == cid), None)
        if match:
            all_processed.append(match)
        else:
            # Add blocked candidates
            feat = extract_features(cand)
            feat["status"] = "🚫 Honeypot (Blocked)" if feat["is_honeypot"] else "⚠️ Disqualified"
            feat["filter_reason"] = feat["honeypot_reason"] if feat["is_honeypot"] else feat["disqualification_reason"]
            feat["score"] = 0.0
            feat["rank"] = "-"
            feat["reasoning"] = feat["filter_reason"]
            all_processed.append(feat)

    # Layout for KPIs
    st.markdown("### Evaluation Summary")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(candidates)}</div><div class='metric-label'>Total Scanned</div></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#FF9F00;'>{honeypot_count}</div><div class='metric-label'>Honeypots Blocked</div></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#FF4B4B;'>{disqualified_count}</div><div class='metric-label'>Disqualified</div></div>", unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"<div class='metric-card'><div class='metric-value' style='color:#00C853;'>{len(valid_candidates)}</div><div class='metric-label'>Valid Candidates</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["🏆 Ranked Shortlist", "🔍 Detailed Candidate Auditor", "🚨 Blocked Candidates Report"])

    with tab1:
        st.markdown("### Top Ranked Shortlist")
        if valid_candidates:
            # Build display dataframe
            rows = []
            for cand in valid_candidates:
                rows.append({
                    "Rank": cand["rank"],
                    "Candidate ID": cand["candidate_id"],
                    "Name": cand["name"],
                    "Experience (Years)": f"{cand['years_of_experience']:.1f}",
                    "Score": cand["score"],
                    "Current Title": cand["current_title"] if cand["current_title"] else "N/A",
                    "Location": cand["location"] if cand["location"] else "India",
                    "Recruiter Justification": cand["reasoning"]
                })
            df_ranked = pd.DataFrame(rows)
            st.dataframe(df_ranked, use_container_width=True)

            # CSV download button matching submission formats
            output_buffer = io.StringIO()
            import csv
            writer = csv.writer(output_buffer, lineterminator="\n")
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for cand in valid_candidates:
                writer.writerow([cand["candidate_id"], cand["rank"], cand["score"], cand["reasoning"]])
            csv_content = output_buffer.getvalue().rstrip("\r\n")

            st.download_button(
                label="📥 Download Ranked CSV Submission",
                data=csv_content,
                file_name="parivartan_sandbox_shortlist.csv",
                mime="text/csv",
                help="Download formatted CSV matching Stage 1 & 2 schema requirements."
            )
        else:
            st.warning("No valid candidates passed the filtering and screening checks.")

    with tab2:
        st.markdown("### Individual Candidate Auditor")
        st.write("Select a candidate to view their complete score breakdown, keyword matches, and behavioral multipliers:")
        
        cand_options = [f"{c['candidate_id']} - {c['name']} ({c['status']})" for c in all_processed]
        selected_option = st.selectbox("Select Candidate to Audit", options=cand_options)
        
        if selected_option:
            selected_cid = selected_option.split(" - ")[0]
            cand = next(x for x in all_processed if x["candidate_id"] == selected_cid)
            
            # Show profile status
            col_status1, col_status2 = st.columns(2)
            with col_status1:
                st.subheader(f"{cand['name']}")
                st.write(f"**Candidate ID**: `{cand['candidate_id']}`")
                st.write(f"**Experience**: {cand['years_of_experience']:.1f} years")
                st.write(f"**Current Title**: `{cand['current_title']}`")
                st.write(f"**Location**: {cand['location'] if cand['location'] else 'N/A'}")
            with col_status2:
                st.subheader("Auditor Status")
                st.write(f"**Overall Status**: {cand['status']}")
                if cand['filter_reason']:
                    st.error(f"**Filter Reason**: {cand['filter_reason']}")
                else:
                    st.success(f"**Final Rank**: #{cand['rank']} (Score: **{cand['score']}**)")
            
            if cand["status"] == "✅ Valid":
                st.markdown("#### Score Component Breakdown")
                
                # Manual calculation of components for audit display
                from ranker import (
                    VECTOR_SEARCH_SKILLS, NLP_DL_SKILLS, BACKEND_SYSTEMS_SKILLS,
                    SERVICE_COMPANIES
                )
                
                # 1. Experience Score
                exp = cand["years_of_experience"]
                exp_score = 0.0
                if 5.0 <= exp <= 9.0:
                    exp_score = 15.0
                elif 3.0 <= exp < 5.0:
                    exp_score = 10.0
                elif 9.0 < exp <= 12.0:
                    exp_score = 10.0
                elif exp > 12.0:
                    exp_score = 5.0
                
                # 2. Title Score
                title = cand["current_title"].lower()
                title_score = 0.0
                if any(w in title for w in ["applied ml", "ai engineer", "machine learning engineer", "ml engineer", "nlp engineer", "search engineer", "information retrieval"]):
                    title_score = 15.0
                elif "data scientist" in title or "ml researcher" in title:
                    title_score = 12.0
                elif any(w in title for w in ["software engineer", "backend", "full stack", "systems engineer"]):
                    title_score = 10.0
                    
                # 3. Skill Score
                skill_score = 0.0
                matched_ir = [s for s in cand["skills"] if s in VECTOR_SEARCH_SKILLS]
                matched_nlp = [s for s in cand["skills"] if s in NLP_DL_SKILLS]
                matched_sys = [s for s in cand["skills"] if s in BACKEND_SYSTEMS_SKILLS]
                skill_score += min(len(matched_ir) * 5.0, 15.0)
                skill_score += min(len(matched_nlp) * 5.0, 15.0)
                skill_score += min(len(matched_sys) * 5.0, 15.0)
                
                # 4. Product Score
                prod_score = 10.0
                for job in cand["career_history"]:
                    comp = job.get("company", "").strip().lower()
                    if comp:
                        is_serv = False
                        for sc in SERVICE_COMPANIES:
                            if sc in comp:
                                is_serv = True
                                break
                        if is_serv:
                            prod_score -= 2.0
                        else:
                            prod_score += 5.0
                prod_score = max(0.0, min(prod_score, 15.0))
                
                # 5. Location Score
                loc = cand["location"].strip().lower()
                loc_score = 0.0
                if any(m in loc for m in ["noida", "pune", "delhi", "gurgaon", "ncr"]):
                    loc_score = 10.0
                elif any(m in loc for m in ["bangalore", "bengaluru", "hyderabad", "mumbai"]):
                    loc_score = 8.0
                elif loc:
                    loc_score = 5.0
                    
                raw_total = exp_score + title_score + skill_score + prod_score + loc_score
                
                # 6. Multipliers
                notice = cand["notice_period_days"]
                notice_mult = 1.0
                if notice <= 15:
                    notice_mult = 1.10
                elif notice <= 30:
                    notice_mult = 1.05
                elif notice > 60:
                    notice_mult = 0.80
                    
                act_mult = 1.0
                # parse inactivity
                try:
                    from datetime import datetime
                    active_dt = datetime.strptime(cand["last_active_date"], "%Y-%m-%d")
                    ref_dt = datetime(2026, 6, 1)
                    inactive_months = (ref_dt - active_dt).days / 30.0
                    if inactive_months > 6:
                        act_mult = 0.60
                    elif inactive_months <= 1:
                        act_mult = 1.10
                except:
                    pass
                    
                otw_mult = 1.10 if cand["open_to_work_flag"] else 1.0
                
                tenure_mult = 1.0
                if cand["avg_tenure"] < 1.5:
                    tenure_mult = 0.85
                    
                git_mult = 1.0
                if cand["github_activity_score"] >= 80:
                    git_mult = 1.05
                elif cand["github_activity_score"] >= 50:
                    git_mult = 1.02
                    
                total_mult = notice_mult * act_mult * otw_mult * tenure_mult * git_mult
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Structured Alignment Scores (Max 100 Raw Points):**")
                    st.write(f"- 📅 **Experience Sweet-Spot**: {exp_score} / 15.0")
                    st.write(f"- 🏷️ **Current Title Match**: {title_score} / 15.0")
                    st.write(f"- 🛠️ **Technical Skill Depth**: {skill_score} / 45.0")
                    st.write(f"- 🏢 **Product vs. Service History**: {prod_score} / 15.0")
                    st.write(f"- 📍 **Location / Relocation**: {loc_score} / 10.0")
                    st.markdown(f"**Total Raw Score**: **{raw_total}**")
                with col2:
                    st.markdown("**Engagement & Reliability Multipliers:**")
                    st.write(f"- ⏱️ **Notice Period Factor**: {notice_mult}x ({cand['notice_period_days']} days)")
                    st.write(f"- ⚡ **Inactivity Factor**: {act_mult}x (Last active: {cand['last_active_date']})")
                    st.write(f"- 🟢 **Open to Work Flag**: {otw_mult}x")
                    st.write(f"- 🏃‍♂️ **Tenure Factor (Anti-chasing)**: {tenure_mult}x (Avg tenure: {cand['avg_tenure']:.1f} yrs)")
                    st.write(f"- 🐙 **GitHub Score Factor**: {git_mult}x (GitHub score: {cand['github_activity_score']})")
                    st.markdown(f"**Combined Scaling Multiplier**: **{total_mult:.4f}x**")
                
                st.markdown("---")
                st.write("**Generated Recruiter Justification:**")
                st.info(cand["reasoning"])

    with tab3:
        st.markdown("### Blocked Candidates Audit Log")
        st.write("The screening engine isolated the following candidate records due to logical failures or inconsistencies:")
        
        blocked_rows = []
        for cand in all_processed:
            if cand["status"] != "✅ Valid":
                blocked_rows.append({
                    "Candidate ID": cand["candidate_id"],
                    "Name": cand["name"],
                    "Status": cand["status"],
                    "Reason for Isolation": cand["filter_reason"]
                })
        
        if blocked_rows:
            df_blocked = pd.DataFrame(blocked_rows)
            st.dataframe(df_blocked, use_container_width=True)
        else:
            st.success("0 anomalous candidates detected in the current pool.")
else:
    st.info("Please upload a candidate JSON/JSONL file to begin processing.")
