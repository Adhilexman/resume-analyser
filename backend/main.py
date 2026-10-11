from database import get_connection
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import fitz
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


SKILLS = [
    # Programming languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "php",

    # Frontend development
    "html",
    "css",
    "react",
    "angular",
    "vue",
    "bootstrap",
    "tailwind css",
    "responsive design",

    # Backend development
    "fastapi",
    "django",
    "flask",
    "node.js",
    "express",
    "rest api",

    # Databases
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "sqlite",

    # Tools and platforms
    "git",
    "github",
    "docker",
    "aws",
    "linux",
    "postman",

    # Data science and AI
    "machine learning",
    "artificial intelligence",
    "data analysis",
    "data visualization",
    "pandas",
    "numpy",
    "scikit-learn",
    "excel",

    # Testing and software practices
    "unit testing",
    "debugging",
    "api testing",
    "agile",
    "scrum",

    # Soft skills
    "communication",
    "teamwork",
    "leadership",
    "problem solving",
    "critical thinking",
    "time management",
    "adaptability",
    "creativity",
    "decision making",
    "attention to detail",
    "collaboration",
    "project management",
]



def extract_text(pdf_bytes):
    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


def find_skills(text):
    text = text.lower()
    found = []

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):
            found.append(skill)

    return found


@app.get("/")
def home():
    return {
        "message": "Resume Analyser API is running"
    }


@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    if resume.content_type != "application/pdf":
        return {
            "error": "Please upload a PDF resume"
        }

    pdf_bytes = await resume.read()

    try:
        resume_text = extract_text(pdf_bytes)
    except Exception:
        return {
            "error": "Unable to read this PDF file"
        }

    if not resume_text.strip():
        return {
            "error": "No readable text found in the PDF"
        }

    resume_skills = find_skills(resume_text)

    job_skills = find_skills(job_description)

    matching_skills = [
        skill for skill in job_skills
        if skill in resume_skills
    ]

    missing_skills = [
        skill for skill in job_skills
        if skill not in resume_skills
    ]

    if job_skills:
        score = round(
            len(matching_skills) / len(job_skills) * 100
        )
    else:
        score = 0

    suggestions = []

    if missing_skills:
        suggestions.append(
            "Consider learning or demonstrating: "
            + ", ".join(missing_skills)
        )

    if not resume_skills:
        suggestions.append(
            "Add relevant technical skills "
            "to your resume if you possess them."
        )

    if not suggestions:
        suggestions.append(
            "Your listed skills match all the "
            "skills detected in this job description."
        )

    
    # Save analysis in MySQL
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO analysis_history
            (
                filename,
                match_percentage,
                resume_skills,
                matching_skills,
                missing_skills
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            resume.filename,
            score,
            ", ".join(resume_skills),
            ", ".join(matching_skills),
            ", ".join(missing_skills)
        )

        cursor.execute(sql, values)
        connection.commit()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Analysis completed, but saving to MySQL failed."
        )

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return {
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "match_percentage": score,
        "suggestions": suggestions,
        "message": "Analysis saved successfully!"
    }


@app.get("/history")
def get_history():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                filename,
                match_percentage,
                resume_skills,
                matching_skills,
                missing_skills,
                created_at
            FROM analysis_history
            ORDER BY id DESC
        """)

        history = cursor.fetchall()

        return {"history": history}

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
