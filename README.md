# 🎯 ATS Resume Scorer

An AI-powered Applicant Tracking System (ATS) Resume Scorer that evaluates how well a resume matches a job description and provides actionable feedback. Built with **FastAPI** and **Streamlit**, it leverages **spaCy** for local NLP/semantic matching, and the **Groq API (Llama 3)** for generating detailed LLM suggestions. The backend is fully optimized to run in low-memory environments (like Render's 512MB RAM free tier).

---

## ✨ Features

1. **Dual Analysis Modes**:
   * **General ATS Score**: Evaluates overall resume formatting, structure, and quality without a job description.
   * **Job Description Comparison**: Conducts semantic matching between the resume and a specific job description.
2. **Semantic Similarity Matching**: Uses spaCy's medium English model (`en_core_web_md`) to calculate a meaning-based match score rather than just simple keyword matching.
3. **Skill Validation**: Cross-references listed skills against projects and work experience to verify credibility.
4. **Actionable Feedback**: Identifies critical issues (e.g., missing contact info, weak action verbs, lack of metrics) and provides AI-generated suggestions for improvement.
5. **PDF Report Export**: Allows users to download a beautifully formatted PDF report of their analysis.
6. **Local Mock Mode (No Supabase Required)**: If Supabase credentials are not configured, the app automatically runs in a local mock session, allowing instant testing without database setup.
7. **Windows-Friendly**: Features a built-in fallback for `libmagic` to prevent crashes on Windows systems.

---

## 🛠️ Tech Stack

* **Frontend**: Streamlit
* **Backend**: FastAPI (Python)
* **NLP**: spaCy (`en_core_web_md`)
* **LLM**: Groq API (Llama 3)
* **Auth + Database**: Supabase (Optional; email/password and Google OAuth)
* **PDF Report Export**: WeasyPrint + Jinja2

---

## 📁 Project Structure

```text
-ATS-Resume-Scorer/
├── backend/              # FastAPI app, NLP services, API routes
├── frontend/             # Streamlit app, views, components
├── jupyter notebooks/    # Research and dataset prep (not used at runtime)
├── requirements.txt      # Combined backend + frontend dependencies
└── .env.example          # Template for environment variables
```

---

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Abhijeet1102/-ATS-Resume-Scorer.git
cd -ATS-Resume-Scorer
```

### 2. Create a Virtual Environment
```bash
# Windows
py -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

*Note: For PDF export on Linux, WeasyPrint needs system libraries:*
```bash
# Debian / Ubuntu
sudo apt install -y libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libffi-dev

# Fedora
sudo dnf install -y cairo pango gdk-pixbuf2 libffi
```

### 4. Configure Environment Variables
Create a `.env` file at the root of the project:
```bash
cp .env.example .env
```

Open `.env` and configure your keys:
```env
# Groq API Key (Required for LLM suggestions)
GROQ_API_KEY=your_groq_api_key

# Supabase Configuration (Optional - leave blank to run in Local Mock Mode)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_KEY=
SUPABASE_JWT_SECRET=
```

---

## 🏃 Running the Application

### 1. Start the Backend
From the project root directory, run:
```bash
# Windows / macOS / Linux
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at [http://localhost:8000](http://localhost:8000).

### 2. Start the Frontend
In a new terminal (with the virtual environment activated), run:
```bash
streamlit run frontend/streamlit_app.py
```
The web interface will open automatically at [http://localhost:8501](http://localhost:8501).

---

## 📝 Notes & Development
* **Local Mock Mode**: When running without Supabase, the application automatically signs you in as `local-user@example.com` in a mock session. You can perform unlimited resume analyses, but history saving will be disabled.
* **Groq API**: If you do not have a Groq API key, the scoring and keyword matching will still work using the local spaCy-based fallback parser, but the LLM suggestions section will be empty.
