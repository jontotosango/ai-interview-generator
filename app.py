import os
import json
import pdfplumber
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# Configuration générale
# =========================
load_dotenv()

st.set_page_config(
    page_title="AI Interview Generator",
    page_icon="🤖",
    layout="wide"
)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("La clé OPENAI_API_KEY est introuvable dans le fichier .env")
    st.stop()

client = OpenAI(api_key=api_key)


# =========================
# Fonctions utilitaires
# =========================
def extract_cv_text(uploaded_file) -> str:
    """
    Extrait le texte d'un CV PDF.
    """
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du PDF : {e}")

    return text.strip()


def build_prompt(job_title: str, seniority: str, interview_duration: str, job_description: str, cv_text: str) -> str:
    """
    Construit le prompt envoyé au modèle.
    """
    return f"""
You are a senior technical recruiter and interviewer specialized in tech and data roles.

Your task is to analyze a candidate CV against a job description and generate a structured interview guide.

Return ONLY valid JSON with the following structure:

{{
  "candidate_summary": "string",
  "match_score": {{
    "overall": 0,
    "technical_fit": 0,
    "seniority_fit": 0,
    "communication_fit": 0
  }},
  "strengths": ["string", "string", "string"],
  "risks": ["string", "string", "string"],
  "screening_questions": ["string", "string", "string", "string", "string"],
  "technical_questions": ["string", "string", "string", "string", "string", "string", "string", "string"],
  "behavioral_questions": ["string", "string", "string", "string", "string"],
  "follow_up_questions": ["string", "string", "string", "string", "string"],
  "evaluation_scorecard": [
    {{
      "criterion": "string",
      "what_to_look_for": "string"
    }}
  ],
  "recommendation": "string"
}}

Rules:
- Be specific and practical.
- Questions must be relevant to the job description.
- Avoid generic questions.
- Scores must be between 0 and 10.
- Focus on tech/data hiring.
- Recommendation must be one of:
  - "Strong fit"
  - "Potential fit"
  - "Weak fit"

Job title:
{job_title}

Expected seniority:
{seniority}

Interview duration:
{interview_duration}

Job description:
{job_description}

Candidate CV:
{cv_text}
"""


def generate_interview_guide(prompt: str) -> dict:
    """
    Appelle OpenAI et retourne un dictionnaire Python.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert technical recruiter. "
                    "You always return clean and valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(
            "Le modèle n'a pas renvoyé un JSON valide. "
            "Réessaie avec un CV plus simple ou une fiche de poste plus claire."
        )


def display_scores(scores: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall", scores.get("overall", "N/A"))
    col2.metric("Technical fit", scores.get("technical_fit", "N/A"))
    col3.metric("Seniority fit", scores.get("seniority_fit", "N/A"))
    col4.metric("Communication fit", scores.get("communication_fit", "N/A"))


def display_list(title: str, items: list) -> None:
    st.subheader(title)
    if not items:
        st.write("Aucun élément généré.")
        return
    for item in items:
        st.markdown(f"- {item}")


def build_markdown_report(result: dict, job_title: str, seniority: str) -> str:
    """
    Génère un rapport markdown exportable / copiable.
    """
    lines = []
    lines.append(f"# AI Interview Guide — {job_title}")
    lines.append("")
    lines.append(f"**Seniority:** {seniority}")
    lines.append("")
    lines.append("## Candidate Summary")
    lines.append(result.get("candidate_summary", ""))
    lines.append("")
    lines.append("## Match Score")
    score = result.get("match_score", {})
    lines.append(f"- Overall: {score.get('overall', '')}")
    lines.append(f"- Technical fit: {score.get('technical_fit', '')}")
    lines.append(f"- Seniority fit: {score.get('seniority_fit', '')}")
    lines.append(f"- Communication fit: {score.get('communication_fit', '')}")
    lines.append("")
    lines.append("## Strengths")
    for item in result.get("strengths", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Risks")
    for item in result.get("risks", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Screening Questions")
    for item in result.get("screening_questions", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Technical Questions")
    for item in result.get("technical_questions", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Behavioral Questions")
    for item in result.get("behavioral_questions", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Follow-up Questions")
    for item in result.get("follow_up_questions", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Evaluation Scorecard")
    for item in result.get("evaluation_scorecard", []):
        criterion = item.get("criterion", "")
        look_for = item.get("what_to_look_for", "")
        lines.append(f"- **{criterion}**: {look_for}")
    lines.append("")
    lines.append("## Recommendation")
    lines.append(result.get("recommendation", ""))
    lines.append("")
    return "\n".join(lines)


# =========================
# Interface utilisateur
# =========================
st.title("🤖 AI Interview Generator")
st.write("Génère un guide d’entretien structuré à partir d’un CV et d’une fiche de poste.")

with st.sidebar:
    st.header("Configuration")
    job_title = st.text_input("Job title", value="Data Engineer")
    seniority = st.selectbox("Seniority", ["Junior", "Mid-level", "Senior"])
    interview_duration = st.selectbox("Interview duration", ["30 min", "45 min", "60 min"])
    st.info("Conseil : utilise un CV PDF texte, pas un scan image.")

job_description = st.text_area(
    "Job description",
    height=250,
    placeholder="Paste the job description here..."
)

cv_file = st.file_uploader("Upload candidate CV (PDF)", type=["pdf"])

generate = st.button("Generate Interview Guide", type="primary")

if generate:
    if not job_description.strip():
        st.warning("Merci de renseigner la fiche de poste.")
        st.stop()

    if cv_file is None:
        st.warning("Merci d’uploader un CV PDF.")
        st.stop()

    try:
        with st.spinner("Lecture du CV..."):
            cv_text = extract_cv_text(cv_file)

        if not cv_text:
            st.error("Impossible d’extraire du texte du PDF. Le fichier est peut-être un scan image.")
            st.stop()

        with st.spinner("Analyse par l’IA en cours..."):
            prompt = build_prompt(
                job_title=job_title,
                seniority=seniority,
                interview_duration=interview_duration,
                job_description=job_description,
                cv_text=cv_text[:15000]  # limite simple pour éviter des prompts trop longs
            )
            result = generate_interview_guide(prompt)

        st.success("Guide d’entretien généré avec succès.")

        st.divider()
        st.header("Candidate Summary")
        st.write(result.get("candidate_summary", ""))

        st.divider()
        st.header("Match Score")
        display_scores(result.get("match_score", {}))

        st.divider()
        display_list("Strengths", result.get("strengths", []))
        display_list("Risks", result.get("risks", []))

        st.divider()
        display_list("Screening Questions", result.get("screening_questions", []))
        display_list("Technical Questions", result.get("technical_questions", []))
        display_list("Behavioral Questions", result.get("behavioral_questions", []))
        display_list("Follow-up Questions", result.get("follow_up_questions", []))

        st.divider()
        st.subheader("Evaluation Scorecard")
        scorecard = result.get("evaluation_scorecard", [])
        if scorecard:
            for item in scorecard:
                st.markdown(f"**{item.get('criterion', '')}**")
                st.write(item.get("what_to_look_for", ""))
        else:
            st.write("Aucune scorecard générée.")

        st.divider()
        st.subheader("Recommendation")
        st.write(result.get("recommendation", ""))

        st.divider()
        st.subheader("Export")
        report_md = build_markdown_report(result, job_title, seniority)

        st.download_button(
            label="Download report as .md",
            data=report_md,
            file_name="interview_guide.md",
            mime="text/markdown"
        )

        with st.expander("Voir le texte brut du CV extrait"):
            st.text(cv_text[:5000])

        with st.expander("Voir le JSON brut généré"):
            st.json(result)

    except Exception as e:
        st.error(f"Erreur : {e}")