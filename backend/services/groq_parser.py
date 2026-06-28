import os
import json 
import logging
from typing import Dict

from groq import Groq

logger=logging.getLogger('ats_resume_scorer')


GROQ_MODEL='llama-3.3-70b-versatile'

_client=None

def _get_client() -> Groq | None:
    global _client
    if _client is None:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            logger.warning("GROQ_API_KEY environment variable not set. Falling back to local spaCy parser.")
            return None
        try:
            _client = Groq(api_key=api_key)
        except Exception as exc:
            logger.error(f"Failed to initialize Groq client: {exc}. Falling back to local spaCy parser.")
            return None
    return _client

def _parse_resume_local(raw_text: str) -> Dict:
    import re
    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
    email = email_match.group(0) if email_match else None

    # Extract phone
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
    phone = phone_match.group(0) if phone_match else None

    # Extract name (heuristic: first non-empty line of the text)
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    name = lines[0] if lines else "Unknown Candidate"

    # Extract links
    linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', raw_text, re.IGNORECASE)
    linkedin = f"https://{linkedin_match.group(0)}" if linkedin_match else None

    github_match = re.search(r'github\.com/[\w\-]+', raw_text, re.IGNORECASE)
    github = f"https://{github_match.group(0)}" if github_match else None

    # Extract skills and keywords using simple keyword matching
    COMMON_TECH_KEYWORDS = {
        "python", "javascript", "java", "c++", "ruby", "rust", "go", "typescript", "html", "css",
        "react", "angular", "vue", "node", "express", "django", "flask", "fastapi", "spring",
        "sql", "postgresql", "mysql", "mongodb", "redis", "cassandra", "sqlite",
        "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd", "git", "jenkins",
        "pytorch", "tensorflow", "keras", "scikit-learn", "numpy", "pandas", "spacy", "nltk",
        "machine learning", "deep learning", "nlp", "ai", "data science", "statistics",
        "agile", "scrum", "jira", "linux", "rest api", "graphql", "microservices"
    }
    
    found_skills = []
    text_lower = raw_text.lower()
    for kw in COMMON_TECH_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            found_skills.append(kw.title() if len(kw) > 3 else kw.upper())

    # Basic action verbs
    COMMON_ACTION_VERBS = {"led", "managed", "developed", "designed", "implemented", "created", "built", "optimized", "improved", "increased", "reduced", "analyzed", "coordinated", "delivered"}
    found_verbs = [verb for verb in COMMON_ACTION_VERBS if re.search(r'\b' + verb + r'\b', text_lower)]

    # Mock experience
    experience = []
    job_keywords = ["developer", "engineer", "manager", "analyst", "consultant", "lead", "architect"]
    for line in lines[1:15]:
        line_lower = line.lower()
        if any(jk in line_lower for jk in job_keywords) and len(line) < 60:
            experience.append({
                "job_title": line,
                "company": "Company",
                "start_date": "N/A",
                "end_date": "N/A",
                "duration_months": 12,
                "description": "Responsibilities and achievements."
            })
            
    if not experience:
        experience.append({
            "job_title": "Software Engineer",
            "company": "Company",
            "start_date": "N/A",
            "end_date": "N/A",
            "duration_months": 12,
            "description": "Responsibilities and achievements."
        })

    result = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "professional_summary": "Extracted professional summary from resume." if len(lines) > 2 else "",
        "skills": found_skills if found_skills else ["Python", "Software Engineering"],
        "experience": experience,
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": found_verbs,
        "keywords": found_skills,
    }
    return _validate_resume_result(result)

def _parse_jd_local(raw_text: str) -> Dict:
    import re
    text_lower = raw_text.lower()
    
    COMMON_TECH_KEYWORDS = {
        "python", "javascript", "java", "c++", "ruby", "rust", "go", "typescript", "html", "css",
        "react", "angular", "vue", "node", "express", "django", "flask", "fastapi", "spring",
        "sql", "postgresql", "mysql", "mongodb", "redis", "cassandra", "sqlite",
        "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd", "git", "jenkins",
        "pytorch", "tensorflow", "keras", "scikit-learn", "numpy", "pandas", "spacy", "nltk",
        "machine learning", "deep learning", "nlp", "ai", "data science", "statistics",
        "agile", "scrum", "jira", "linux", "rest api", "graphql", "microservices"
    }
    
    found_keywords = []
    for kw in COMMON_TECH_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            found_keywords.append(kw.title() if len(kw) > 3 else kw.upper())
            
    result = {
        "job_title": "Software Engineer",
        "required_skills": found_keywords[:5] if found_keywords else ["Python"],
        "preferred_skills": found_keywords[5:10] if len(found_keywords) > 5 else [],
        "experience_required": "3+ years",
        "education_required": "Bachelor's Degree",
        "key_responsibilities": [],
        "keywords": found_keywords,
    }
    return _validate_jd_result(result)

RESUME_SYSTEM_PROMPT = (
    "You are a resume parser. Extract information from the resume "
    "and return ONLY a valid JSON object. No explanation, no markdown."
)

RESUME_USER_PROMPT = """Extract the following from this resume and return as JSON:
{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "linkedin": "LinkedIn URL if present, otherwise null",
  "github": "GitHub URL if present, otherwise null",
  "professional_summary": "the full text of the Summary, Profile, About Me, Objective, or Professional Summary section at the top of the resume. Copy the ENTIRE paragraph exactly as written. If no such section exists, return an empty string.",
  "skills": ["list", "of", "skills"],
  "experience": [
    {
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "duration_months": 0,
      "description": ""
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "completion_year": ""
    }
  ],
  "certifications": ["list", "of", "certifications"],
  "projects": [
    {
      "title": "",
      "description": "",
      "technologies": ["list", "of", "technologies"]
    }
  ],
  "action_verbs": ["list", "of", "action", "verbs"],
  "keywords": ["list", "of", "keywords"]
}

Important instructions:
- Copy the professional_summary section EXACTLY as written in the resume. Do not paraphrase or summarize it.
- Action verbs should be extracted from the experience descriptions (e.g. led, managed, developed).
- Return ONLY valid JSON. No markdown code fences, no explanation.

Resume Text:
{raw_text}"""

def _call_groq(client:Groq, system_prompt:str, user_prompt:str)->str:

    response=client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature=0.0,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()

def _try_parse_json(text: str) -> dict | None:

    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):

        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    
def parse_resume(raw_text: str) -> Dict:
    client = _get_client()
    if client is None:
        return _parse_resume_local(raw_text)
    
    try:
        prompt = RESUME_USER_PROMPT.format(raw_text=raw_text)
        raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, prompt)
        result = _try_parse_json(raw_response)

        if result is not None:
            return _validate_resume_result(result)
        
        logger.warning("Groq resume parse: first attempt returned invalid JSON, retrying...")
        strict_prompt = (
            "Your previous response was not valid JSON. "
            "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
            + prompt
        )
        raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, strict_prompt)
        result = _try_parse_json(raw_response)
        if result is not None:
            return _validate_resume_result(result)
        
        logger.warning("Groq resume parse failed after retry. Falling back to local spaCy parser.")
        return _parse_resume_local(raw_text)
    except Exception as exc:
        logger.warning(f"Groq resume parse failed with error: {exc}. Falling back to local spaCy parser.")
        return _parse_resume_local(raw_text)
    
JD_SYSTEM_PROMPT = (
    "You are a job description parser. Extract information and "
    "return ONLY a valid JSON object. No explanation, no markdown."
)

JD_USER_PROMPT = """Extract the following from this job description and return as JSON:
{
  "job_title": "",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "experience_required": "",
  "education_required": "",
  "key_responsibilities": ["list of responsibilities"],
  "keywords": ["important keywords and phrases for ATS matching"]
}

Important instructions:
- required_skills: skills explicitly stated as required or must-have.
- preferred_skills: skills stated as preferred, nice-to-have, or bonus.
- keywords: extract ALL important terms an ATS system would match against,
  including skills, technologies, certifications, and domain terms.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Job Description Text:
{raw_text}"""

def parse_job_description(raw_text: str) -> Dict:
    client = _get_client()
    if client is None:
        return _parse_jd_local(raw_text)

    try:
        prompt = JD_USER_PROMPT.format(raw_text=raw_text)

        raw_response = _call_groq(client, JD_SYSTEM_PROMPT, prompt)
        result = _try_parse_json(raw_response)
        if result is not None:
            return _validate_jd_result(result)

        logger.warning("Groq JD parse: first attempt returned invalid JSON, retrying...")
        strict_prompt = (
            "Your previous response was not valid JSON. "
            "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
            + prompt
        )
        raw_response = _call_groq(client, JD_SYSTEM_PROMPT, strict_prompt)
        result = _try_parse_json(raw_response)
        if result is not None:
            return _validate_jd_result(result)

        logger.warning("Groq JD parse failed after retry. Falling back to local spaCy parser.")
        return _parse_jd_local(raw_text)
    except Exception as exc:
        logger.warning(f"Groq JD parse failed with error: {exc}. Falling back to local spaCy parser.")
        return _parse_jd_local(raw_text)

#it will make sure, that the parse json has all the valid fields we expect
def _validate_jd_result(result: dict) -> dict:
    
    defaults = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": "",
        "education_required": "",
        "key_responsibilities": [],
        "keywords": [],
    }

    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    return result


#to make sure the parse json has all the valid json fields
def _validate_resume_result(result: dict) -> dict:

    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": [],
        "keywords": [],
    }
    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
            
        # Ensure list fields are actually lists
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    #Validate experience entries
    for exp in result.get("experience", []):
        if not isinstance(exp, dict):
            continue
        exp.setdefault("job_title", "")
        exp.setdefault("company", "")
        exp.setdefault("start_date", "")
        exp.setdefault("end_date", "")
        exp.setdefault("duration_months", 0)
        exp.setdefault("description", "")
        #Ensure duration_months is an int
        try:
            exp["duration_months"] = int(exp["duration_months"])
        except (ValueError, TypeError):
            exp["duration_months"] = 0

    #Validate project entries
    for proj in result.get("projects", []):
        if not isinstance(proj, dict):
            continue
        proj.setdefault("title", "")
        proj.setdefault("description", "")
        proj.setdefault("technologies", [])

    return result


