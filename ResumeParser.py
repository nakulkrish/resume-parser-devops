import pdfplumber
import json
import csv
import re
from collections import Counter

# Skill keywords expanded for accurate classification
SKILL_KEYWORDS = [
    # Computer Science
    'python', 'java', 'c++', 'machine learning', 'data science', 'html', 'css', 'javascript',
    'react', 'sql', 'mysql', 'aws', 'azure', 'linux',

    # Mechanical Engineering
    'cad', 'solidworks', 'ansys', 'autocad', 'catia', 'thermodynamics', 'fluid mechanics',
    'hvac', 'cam', 'fea', 'mechanical design', 'mechatronics',

    # Electrical / Electronics
    'embedded systems', 'arduino', 'raspberry pi', 'matlab', 'circuit design', 'verilog',
    'vhdl', 'power systems', 'signal processing', 'simulink', 'proteus', 'electronics',

    # Civil Engineering
    'staad pro', 'etabs', 'autocad civil', 'revit', 'structural design', 'geotechnical',
    'transportation engineering', 'construction planning', 'civil 3d', 'site engineering',

    # Medical
    'mbbs', 'md', 'internship', 'residency', 'research', 'clinical', 'medical practice',
    'surgery', 'diagnosis', 'pharmacology', 'treatment', 'hospital',

    # Biotechnology / Pharma
    'molecular biology', 'cell culture', 'pcr', 'elisa', 'biochemistry', 'genomics', 'proteomics',
    'clinical trials', 'drug discovery',

    # Business / Management
    'finance', 'marketing', 'excel', 'data analysis', 'business analysis', 'project management',
    'erp', 'sap', 'leadership', 'communication', 'strategic planning', 'crm', 'agile', 'scrum',

    # Law / Legal Domain
    'legal research', 'case law', 'litigation', 'corporate law', 'contract law',
    'intellectual property', 'ip law', 'civil law', 'criminal law', 'constitutional law',
    'legal writing', 'drafting', 'arbitration', 'mediation', 'compliance', 'moot court',
    'legal documentation', 'legal advice', 'legal analysis', 'court procedure', 'lawyer',
    'attorney', 'barrister', 'solicitor'
]

# Role prediction with more precise keyword mapping
DOMAIN_ROLES = {
    'Computer Science': {'python', 'machine learning', 'java', 'sql', 'web development', 'aws'},
    'Mechanical Engineer': {'solidworks', 'autocad', 'thermodynamics', 'hvac', 'fea', 'cam'},
    'Electrical Engineer': {'matlab', 'arduino', 'circuit', 'simulink', 'vhdl', 'electronics'},
    'Civil Engineer': {'staad pro', 'etabs', 'revit', 'civil 3d', 'site engineering', 'autocad civil'},
    'Biotech / Pharma': {'cell culture', 'pcr', 'genomics', 'clinical trials'},
    'Business Analyst / Manager': {'finance', 'marketing', 'project management', 'business analysis'},
    'Lawyer / Legal Professional': {
        'litigation', 'contract law', 'corporate law', 'intellectual property',
        'criminal law', 'civil law', 'legal research', 'legal writing', 'arbitration'
    },
    'Doctor / Medical Professional': {
        'mbbs', 'md', 'residency', 'clinical', 'diagnosis', 'surgery', 'medical practice', 'treatment'
    }
}

SCORE_DISTRIBUTION_BY_DOMAIN = {
    'Doctor / Medical Professional': {
        'internship': 20,
        'research': 20,
        'experience': 20,
        'skills': 20,
        'formatting': 20
    },
    'Computer Science': {
        'skills': 30,
        'projects': 25,
        'certifications': 15,
        'experience': 10,
        'formatting': 20
    },
    'Lawyer / Legal Professional': {
        'legal_experience': 30,
        'legal_skills': 25,
        'moots_certifications': 15,
        'internships': 10,
        'formatting': 20
    },
    'Mechanical Engineer': {
        'cad_skills': 30,
        'projects': 25,
        'certifications': 10,
        'experience': 15,
        'formatting': 20
    },
    'Civil Engineer': {
        'cad_skills': 20,
        'projects': 25,
        'certifications': 15,
        'internship': 20,
        'formatting': 20
    },
    'Electrical Engineer': {
        'circuit_skills': 25,
        'projects': 25,
        'certifications': 15,
        'internship': 15,
        'formatting': 20
    },
    'Business Analyst / Manager': {
        'skills': 25,
        'projects': 20,
        'certifications': 15,
        'experience': 20,
        'formatting': 20
    },
    'Biotech / Pharma': {
        'skills': 25,
        'projects': 20,
        'research': 15,
        'certifications': 20,
        'formatting': 20
    }
}

def extract_text_from_pdf(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text.lower()

def extract_name_email(text):
    lines = text.splitlines()
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)

    name_match = None
    for line in lines[:6]:
        potential_name = re.match(r"^[A-Za-z]+(?: [A-Za-z]+)+$", line.strip())
        if potential_name:
            name_match = potential_name.group(0)
            break
    if not name_match:
        for line in lines[:6]:
            if len(line.split()) > 1:
                name_match = line.strip()
                break
    return name_match if name_match else "Unknown", email_match.group(0) if email_match else "Not found"

def predict_role(skills):
    skill_set = set(skills)
    role_scores = {}
    for domain, keywords in DOMAIN_ROLES.items():
        match_count = len(skill_set & keywords)
        # Bonus weight if unique civil terms are present
        if domain == "Civil Engineer":
            for civil_term in ['staad pro', 'etabs', 'revit', 'civil 3d', 'site engineering', 'geotechnical']:
                if civil_term in skill_set:
                    match_count += 2  # give weight
        role_scores[domain] = match_count
    best_match = max(role_scores, key=role_scores.get)
    return best_match


def score_and_extract_skills(text, domain):
    skill_counts = Counter({skill: text.count(skill) for skill in SKILL_KEYWORDS if skill in text})
    top_skills = [skill for skill, _ in skill_counts.most_common(5)]

    score_config = SCORE_DISTRIBUTION_BY_DOMAIN.get(domain, {})
    score = {}

    if 'skills' in score_config:
        score['skills'] = min(score_config['skills'], len(skill_counts) * 2)

    if 'cad_skills' in score_config:
        cad_related = sum(text.count(skill) for skill in ['cad', 'autocad', 'fea', 'civil 3d', 'revit'])
        score['cad_skills'] = min(score_config['cad_skills'], cad_related * 5)

    if 'circuit_skills' in score_config:
        circuit_related = sum(text.count(skill) for skill in ['circuit', 'vhdl', 'simulink'])
        score['circuit_skills'] = min(score_config['circuit_skills'], circuit_related * 5)

    if 'projects' in score_config:
        score['projects'] = score_config['projects'] if 'project' in text else 5

    if 'certifications' in score_config:
        score['certifications'] = score_config['certifications'] if 'certificate' in text else 5

    if 'experience' in score_config:
        score['experience'] = score_config['experience'] if 'experience' in text else 5

    if 'internship' in score_config:
        score['internship'] = score_config['internship'] if 'internship' in text else 5

    if 'research' in score_config:
        score['research'] = score_config['research'] if 'research' in text else 5

    if 'legal_experience' in score_config:
        score['legal_experience'] = score_config['legal_experience'] if 'law firm' in text or 'court' in text else 5

    if 'legal_skills' in score_config:
        legal_related = sum(text.count(skill) for skill in DOMAIN_ROLES['Lawyer / Legal Professional'])
        score['legal_skills'] = min(score_config['legal_skills'], legal_related * 2)

    if 'moots_certifications' in score_config:
        score['moots_certifications'] = score_config['moots_certifications'] if 'moot' in text else 5

    if 'formatting' in score_config:
        score['formatting'] = score_config['formatting']

    total_score = sum(score.values())
    return top_skills, total_score, score

def save_as_json(data, filename='resume_result.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def save_as_csv(data, filename='resume_result.csv'):
    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data.keys())
        writer.writerow(data.values())

def process_resume(pdf_path, json_filename='resume_result.json', csv_filename='resume_result.csv'):
    """Process a resume PDF and save results.

    Args:
        pdf_path (str): Path to the PDF file to process.
        json_filename (str): Output JSON filename (will be created in current dir).
        csv_filename (str): Output CSV filename (will be created in current dir).

    Returns:
        dict: Parsed result dictionary.
    """
    text = extract_text_from_pdf(pdf_path)
    name, email = extract_name_email(text)
    top_skills = [skill for skill in SKILL_KEYWORDS if skill in text]
    domain = predict_role(top_skills)
    top_skills, score, breakdown = score_and_extract_skills(text, domain)

    result = {
        'name': name.lower(),
        'email': email,
        'top_skills': top_skills,
        'predicted_domain': domain,
        'score': score,
        'score_breakdown': breakdown
    }

    # Save to the requested filenames
    save_as_json(result, filename=json_filename)
    save_as_csv({
        'name': name,
        'email': email,
        'score': score,
        'top_skills': ', '.join(top_skills),
        'predicted_domain': domain
    }, filename=csv_filename)

    print(json.dumps(result, indent=2))
    return result

# Example usage:
# process_resume("D:\ResumeParser\ResumeParser\Civil1.pdf")