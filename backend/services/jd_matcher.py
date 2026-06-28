from typing import List, Dict
import spacy
from backend.utils.matching import fuzzy_match_keywords, normalize_skill
from rapidfuzz import fuzz


def calculate_semantic_similarity(
    resume_text: str, jd_text: str, nlp: spacy.Language
) -> float:
    try:
        doc1 = nlp(resume_text[:5000])
        doc2 = nlp(jd_text[:5000])
        if doc1.vector_norm and doc2.vector_norm:
            return float(doc1.similarity(doc2))
        return 0.0
    except Exception:
        return 0.0


def identify_matched_keywords(
    resume_keywords: List[str], jd_keywords: List[str]
) -> List[str]:
    result = fuzzy_match_keywords(resume_keywords, jd_keywords, threshold=80)
    return result['matched']


def identify_missing_keywords(
    resume_keywords: List[str], jd_keywords: List[str], top_n: int = 15
) -> List[str]:

    result = fuzzy_match_keywords(resume_keywords, jd_keywords, threshold=80)
    return result['missing'][:top_n]


def analyze_skills_gap(
    resume_skills: List[str], jd_text: str, nlp: spacy.Language
) -> List[str]:
    doc       = nlp(jd_text[:5000])
    jd_skills = set()

    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'ORG', 'LANGUAGE']:
            jd_skills.add(ent.text.lower())

    for chunk in doc.noun_chunks:
        ct = chunk.text.lower().strip()
        if 1 <= len(ct.split()) <= 4:
            jd_skills.add(ct)

    # Normalize resume skills for comparison
    resume_normalized = {normalize_skill(s) for s in resume_skills}

    gap = []
    for jd_skill in jd_skills:
        jd_norm = normalize_skill(jd_skill)

        # Check canonical match first
        if jd_norm in resume_normalized:
            continue

        # Then try fuzzy match against all resume skills
        best_score = max(
            (fuzz.token_sort_ratio(jd_norm, rs) for rs in resume_normalized),
            default=0,
        )
        if best_score < 75:
            gap.append(jd_skill)

    return sorted(gap)[:20]


def calculate_match_percentage(
    resume_keywords: List[str],
    jd_keywords: List[str],
    semantic_similarity: float,
) -> float:
    if not jd_keywords:
        return 0.0
    matched = identify_matched_keywords(resume_keywords, jd_keywords)
    keyword_overlap = len(matched) / len(jd_keywords)
    match_pct = (keyword_overlap * 0.6 + semantic_similarity * 0.4) * 100
    return float(min(100.0, max(0.0, match_pct)))


def compare_resume_with_jd(
    resume_text: str,
    resume_keywords: List[str],
    resume_skills: List[str],
    jd_text: str,
    jd_keywords: List[str],
    nlp: spacy.Language,
) -> Dict:
    semantic_similarity = calculate_semantic_similarity(resume_text, jd_text, nlp)
    matched_keywords    = identify_matched_keywords(resume_keywords, jd_keywords)
    missing_keywords    = identify_missing_keywords(resume_keywords, jd_keywords)
    skills_gap          = analyze_skills_gap(resume_skills, jd_text, nlp)
    match_percentage    = calculate_match_percentage(
        resume_keywords, jd_keywords, semantic_similarity
    )

    return {
        'match_percentage':    match_percentage,
        'semantic_similarity': semantic_similarity,
        'matched_keywords':    matched_keywords,
        'missing_keywords':    missing_keywords,
        'skills_gap':          skills_gap,
    }
