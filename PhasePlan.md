# NeuroPrep

# AI Mock Interview Web App

## 🚀 Overview

This AI-powered **Mock Interview Web App** simulates real-world technical interviews, assessing candidates on **Aptitude, Coding, Technical Knowledge, and Behavioral Skills** using AI/ML, automation, and proctoring techniques. The app extracts information from resumes, generates dynamic interview questions, assesses confidence via **emotion recognition**, and provides a **detailed performance report**.

## 🔹 Core Features

- ✅ **Resume Parsing & Skill Extraction**
- ✅ **Dynamic Question Generation (Gemini API)**
- ✅ **Live Coding Environment with AI-Based Evaluation**
- ✅ **TTS-Based Interviewer (AI Asks Questions)**
- ✅ **Speech-to-Text for Answer Assessment**
- ✅ **Emotion & Confidence Analysis (Facial Recognition)**
- ✅ **Eye-Tracking for Proctoring**
- ✅ **Timed Assessments & Cheating Prevention**
- ✅ **Detailed Score Reports & Graphical Analysis**
- ✅ **User Authentication & Data Storage (Supabase/PostgreSQL)**

---

## 📌 Tech Stack

| Feature | Tools & Technologies |
| --- | --- |
| **Frontend** | Flask/Django + HTML + CSS (Tailwind) + JavaScript |
| **Backend** | Python + Flask/Django + Supabase/PostgreSQL |
| **Resume Parsing** | PyPDF2, pdfplumber, SpaCy |
| **AI Question Generation** | Gemini API |
| **Text-to-Speech (TTS)** | Google TTS / ElevenLabs |
| **Speech-to-Text (STT)** | Whisper AI / Google Speech API |
| **Live Coding Environment** | CodeMirror / Ace Editor |
| **Code Evaluation** | Gemini API |
| **Emotion & Confidence Analysis** | OpenCV + DeepFace |
| **Proctoring (Eye-Tracking)** | OpenCV + dlib |
| **Analytics & Reports** | Matplotlib / Chart.js |
| **Deployment** | Render / AWS / Azure / Google Cloud |

---

## 📍 Roadmap

### 📌 **Phase 1: Project Setup & UI**

- Set up Flask/Django project with required dependencies
- Design UI using TailwindCSS for a professional look
- Implement User Authentication (Signup/Login with Supabase)

### 📌 **Phase 2: Resume Parsing & Skill Extraction**

- Allow users to upload resumes (PDF, DOCX)
- Extract skillsets, experience level, and projects using NLP (SpaCy)
- Store parsed information in the database

### 📌 **Phase 3: AI-Generated Interview Questions**

- Integrate **Gemini API** to generate custom interview questions
- Categorize questions into Aptitude, Coding, Technical, HR
- Ensure each interview session is unique

### 📌 **Phase 4: Aptitude & Reasoning Round**

- Generate timed multiple-choice questions (MCQs)
- Auto-evaluate correctness and calculate scores

### 📌 **Phase 5: Live Coding Assessment**

- Embed a coding editor (CodeMirror / Ace Editor)
- Integrate **Gemini API** for evaluating code submissions
- Support Python, Java, C++, JavaScript

### 📌 **Phase 6: AI-Based Technical Interview (TTS + STT)**

- Convert AI-generated questions into speech (Google TTS)
- Capture user responses via Speech-to-Text (Whisper AI)
- Analyze responses for correctness using Gemini API

### 📌 **Phase 7: Emotion & Confidence Analysis**

- Implement Facial Emotion Recognition (DeepFace)
- Monitor expressions to assess confidence levels
- Store emotional insights for final report generation

### 📌 **Phase 8: Proctoring & Anti-Cheating Mechanism**

- Implement **Eye-Tracking** using OpenCV to detect distractions
- Display warnings if user looks away frequently (Max: 10 warnings)

### 📌 **Phase 9: Performance Report & Feedback System**

- Compile all test results into a **detailed PDF report**
- Use **Chart.js** / **Matplotlib** for graphical analysis
- Provide personalized feedback & improvement tips

### 📌 **Phase 10: Deployment & Testing**

- Host backend on Render/AWS/Azure/GCP
- Conduct stress testing with multiple users
- Optimize database queries & API calls

---

## 📢 Future Enhancements

- 🔹 **Mock Interviews with Real HRs & Engineers**
- 🔹 **Integration with LinkedIn & Job Portals**
- 🔹 **Live AI Coaching & Answer Suggestions**
- 🔹 **Gamification & Interview Leaderboard**

---

## 💡 Why This Project is a Winner

✅ **AI-Powered & Fully Automated** (Dynamic questions, not hardcoded)
✅ **Complete Interview Simulation** (Aptitude, Coding, Technical, HR)
✅ **Real-Time Feedback & Proctoring** (Confidence & Eye Tracking)
✅ **Scalable & Market-Ready** (Can be turned into a SaaS Product)

---

## Prompt

"You are my AI assistant helping me build a web app called **NeuroMock**—an AI-powered **mock interview platform**. This app:

1. **Extracts resume data** to assess skills, experience, and projects.
2. **Uses Gemini AI** to generate **adaptive interview questions** based on the resume.
3. **Conducts AI-driven interviews** with:
    - **TTS (Text-to-Speech)** to ask questions.
    - **Speech-to-Text (STT)** for user responses.
    - **Video-based emotion analysis** to assess confidence.
    - **Proctoring features** (eye tracking, distraction detection).
4. **Includes coding tests** where users write code, which is then evaluated by Gemini.
5. **Generates a detailed report** with performance analysis, graphs, and feedback.
6. **Uses Flask/Django**, integrates databases for user history, and deploys on Google/AWS/Azure.
7. **Ensures cheat-proofing** with dynamic questions and proctoring alerts.

The UI must be **beautiful & professional**, following a modern design. The project must be **scalable** and **MVP-ready** in a short time. Our tech stack includes **Python, Flask/Django, ML, NLP, Automation, Google/AWS/Azure, Gemini AI, API integrations, GitHub Actions**.

Whenever I ask about this project, recall this scope and help me with **coding, AI model integrations, UI/UX, database handling, automation, and deployment.** Keep everything structured and efficient."