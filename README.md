# AdaptLearn — AI-Powered Adaptive Learning Platform

> **An AI-powered learning platform that adapts what students learn, how they learn, and what they practice based on their real-time performance.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.16-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.3-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![OpenRouter](https://img.shields.io/badge/AI_Engine-OpenRouter-6366F1?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Vercel](https://img.shields.io/badge/Frontend_Deploy-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Render](https://img.shields.io/badge/Backend_Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com)

---

## 📑 Table of Contents

1. [Project Overview](#-project-overview)
2. [Problem Statement](#-problem-statement)
3. [The Solution: Adaptive Closed-Loop Learning](#-the-solution-adaptive-closed-loop-learning)
4. [Key Features](#-key-features)
5. [How the Adaptive Learning System Works](#-how-the-adaptive-learning-system-works)
6. [AI Architecture](#-ai-architecture)
7. [System Architecture](#-system-architecture)
8. [Screenshots & Product Walkthrough](#-screenshots--product-walkthrough)
9. [Tech Stack](#-tech-stack)
10. [Project Structure](#-project-structure)
11. [Learning Flow](#-learning-flow)
12. [API & Backend Overview](#-api--backend-overview)
13. [Environment Variables](#-environment-variables)
14. [Local Development Setup](#-local-development-setup)
15. [Deployment Architecture](#-deployment-architecture)
16. [Future Scope](#-future-scope)
17. [Why This Project Matters](#-why-this-project-matters)
18. [Author & Contact](#-author--contact)
19. [License](#-license)

---

## 🌟 Project Overview

**AdaptLearn** is a full-stack, AI-driven adaptive learning platform built to solve the fundamental limitation of traditional education: **the one-size-fits-all curriculum**. 

In conventional classrooms and static e-learning systems, every student is served identical lessons, at identical paces, with static question banks—regardless of whether they have already mastered the material or are struggling with prerequisite fundamentals. 

AdaptLearn replaces static content pipelines with an **active, pedagogical closed loop**. The platform models each learner's latent ability ($\theta$), traces skill acquisition using Bayesian Knowledge Tracing (BKT), diagnoses specific error patterns, monitors cognitive load and fatigue, and dynamically generates tailored explanations, analogies, and practice questions in real time.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                ADAPTIVE LEARNING LOOP                                  │
│                                                                                        │
│   Student ──► Initial Assessment ──► Performance Analysis ──► Adaptive Teaching       │
│      ▲                                                                    │            │
│      │                                                                    ▼            │
│   Next Recommendation ◄── Learning Velocity & Progress ◄── Targeted Practice Drills  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚨 Problem Statement

### 1. The Rigidity of Static Education
* **Fixed Sequences:** Students are forced through monolithic syllabi regardless of individual strengths or weaknesses.
* **Uniform Explanations:** Explanations assume a uniform baseline comprehension, leaving struggling students behind and boring advanced learners.
* **Static Question Banks:** Repetitive or uncalibrated questions fail to target the student's exact frontier of learning (Zone of Proximal Development).
* **Missing Error Analysis:** Incorrect answers are simply marked "wrong" without identifying *why* the misconception occurred (e.g., calculation slip vs. foundational conceptual misunderstanding).

### 2. The Flaw of "Chatbots Bolted to Textbooks"
Most generic AI education apps simply attach an LLM chat interface to a PDF:
* **Passive Engagement:** They rely entirely on students knowing what questions to ask.
* **No Pedagogical Memory:** They cannot track latent mastery decay, item discrimination, or student learning velocity over time.
* **Cognitive Overload:** They generate unbounded walls of text that overwhelm working memory.
* **No Curriculum Steering:** They fail to enforce prerequisite mastery before jumping into advanced concepts.

---

## 💡 The Solution: Adaptive Closed-Loop Learning

AdaptLearn treats learning as a **dynamic control system**:

* **Micro-Curriculum Atomization:** Decomposes complex subjects into fine-grained, single-concept **Teaching Atoms** (`TeachingAtom`).
* **Active Diagnostic Steering:** Conducts initial baseline assessments to seed student ability ($\theta$) before instruction begins.
* **Multi-Modal Teaching:** Delivers concise explanations paired with real-world analogies, concrete examples, visual concept diagrams, and curated video recommendations.
* **Item Response Theory (IRT) & BKT Calibration:** Adjusts question difficulty dynamically to match estimated student ability, while updating mastery probabilities on every response.
* **Multi-Factor Pacing Engine:** Assesses response latency, hint dependency, and error types to decide whether to **speed up**, **reteach**, **continue practice**, or **recommend a break**.

---

## ✨ Key Features

### 🎓 Student Experience & Learning Engine
* **Subject & Concept Discovery:** Explore structured curriculum domains or generate custom learning paths on-demand for any topic.
* **Initial Adaptive Diagnostic Quiz:** Micro-assessments calibrate baseline ability ($\theta$) and assign initial pacing bands.
* **Multi-Modal Teaching Modules:** Structured breakdowns containing definitions, dual-coding analogies, code/math examples, common misconceptions, and "Why This Matters" summaries.
* **AI Question Generation via OpenRouter:** Fresh, pedagogically calibrated multiple-choice questions generated on-the-fly to fit the learner's active mastery state.
* **Novelty & Paraphrase Filtering:** Pure-Python Jaccard & SequenceMatcher similarity detection rejects duplicate or repetitive questions from session history.
* **Balanced Option Shuffling:** Eliminates bias (such as Option A bias) by programmatically randomizing answer placement while maintaining strict answer validation.
* **Cognitive Operations Tagging:** Questions are categorized by cognitive demand (`Recall`, `Apply`, `Analyze`) with calibrated time baselines.
* **Tiered Hints & Dependency Tracking:** Multi-level hints with telemetry warnings if a student becomes over-reliant on hints.
* **Visual Knowledge & Mermaid Diagrams:** Concept maps and relational diagrams illustrate abstract architectures and hierarchies directly in the UI.
* **Curated Video Recommendations:** Integrated educational video tutorials dynamically matched to the active concept.
* **Real-Time Learning Velocity & Telemetry:** Visual sparkline analytics tracking mastery speed ($V = \frac{\text{Atoms Mastered}}{\text{Time Spent}}$).
* **Cognitive Fatigue Monitoring:** Multi-factor fatigue tracking based on session duration, accuracy decay, and skip frequency.
* **AI Doubt Assistant:** Context-aware interactive AI tutor to answer questions specifically about the active atom.
* **AI Study Timetable Planner:** Generates structured weekly study schedules tailored to student goals and daily availability.
* **Gamified XP & Leaderboards:** Milestone XP rewards and competitive rankings to incentivize sustained practice.

### 👩‍🏫 Teacher Command Center
* **Class-Wide Analytics:** Live dashboards displaying mastery distributions, average velocity, and error type heatmaps.
* **Student Drill-Down:** Deep psychometric inspectability into individual student ability ($\theta$), progress, and fatigue logs.
* **Curriculum & Content Management:** Teachers can override AI-generated lessons with custom notes, examples, and curated analogies.
* **Question Moderation:** Review, approve, edit, or disable AI-generated assessment questions.
* **Pedagogical Interventions (Overrides):** Reset mastery, force immediate reviews, adjust targets, or assign remedial modules.
* **Target Milestones & Deadlines:** Set class-wide or individual mastery goals.

### 👨‍👩‍👧 Parent Portal
* **Secure Child Linking:** Pair parent and child accounts using single-use invite codes.
* **Progress & Activity Insights:** Non-intrusive visibility into weekly sessions, completed concepts, study streaks, and mastery rates.
* **Actionable Guidance:** Clear summaries of student milestones and areas needing encouragement without micromanagement.

---

## ⚙️ How the Adaptive Learning System Works

The adaptive engine coordinates psychometric models and pedagogical heuristics on every student action:

```
[ Subject & Concept Selection ]
               │
               ▼
   [ Diagnostic Micro-Quiz ] ──► Computes Initial Ability (θ) & Prior Mastery
               │
               ▼
     [ Active Atom Selection ] ◄────────────────────────────────────────┐
               │                                                        │
               ▼                                                        │
     [ Teaching-First Module ]                                          │
       • Concise Breakdown & Analogy                                    │
       • Visual Diagrams & Curated Video                                │
       • Common Misconceptions & Examples                               │
               │                                                        │
               ▼                                                        │
    [ Calibrated Practice Drills ]                                      │
       • OpenRouter AI Questions (IRT-matched)                          │
       • Tiered Hints & Latency Tracking                                │
               │                                                        │
               ▼                                                        │
  [ Psychometric & Error Evaluation ]                                   │
       • 2PL IRT Ability Update (θ)                                     │
       • Bayesian Knowledge Tracing Pt(L)                               │
       • 6-Class Error Categorization                                   │
               │                                                        │
               ▼                                                        │
     { Pacing Engine Decision }                                         │
       ├─► Mastery < 40% / Conceptual Error ──► [ Reteach / Simplify ] ─┤
       ├─► 40% ≤ Mastery < 80% ─────────────► [ Targeted Practice ] ────┤
       ├─► Fatigue High ────────────────────► [ Rest / Light Task ] ────┤
       └─► Mastery ≥ 80% & Streak ≥ 2 ──────► [ Advance to Next Atom ] ─┘
               │
               ▼
    [ Concept Final Challenge ] ──► Weak Topic Detection & Mastery Milestone
```

### 1. Psychometric Foundations

#### Item Response Theory (2PL IRT Model)
Student ability is modeled as continuous parameter $\theta$, where probability of a correct response depends on item difficulty $b$ and discrimination $a$:
$$P(\text{correct} \mid \theta, a, b) = \frac{1}{1 + e^{-a(\theta - b)}}$$
Upon submission, $\theta$ is calibrated via gradient ascent on the log-likelihood function weighted by response time and error classification.

#### Bayesian Knowledge Tracing (BKT)
Mastery probability $P(L_t)$ updates on every observation, accounting for slip ($P(S)$) and guess ($P(G)$) probabilities:
$$P(L_t \mid \text{correct}) = \frac{P(L_{t-1})(1 - P(S))}{P(L_{t-1})(1 - P(S)) + (1 - P(L_{t-1}))P(G)}$$
$$P(L_t) = P(L_t \mid \text{obs}) + (1 - P(L_t \mid \text{obs})) \cdot P(T)$$
This ensures lucky guesses do not cause false progression and careless slips do not unfairly penalize students.

#### 6-Class Error Typology
| Error Type | Detection Signal | Pedagogical Penalty | Engine Response |
| :--- | :--- | :--- | :--- |
| **Guessing** | Incorrect answer in $< 50\%$ expected time | Low ($-0.02$) | Reinforce question; disallow fast skip |
| **Attentional** | Fast slip on an already mastered concept | Low ($-0.03$) | Provide attention check prompt |
| **Factual** | Incorrect on recall-oriented question | Medium ($-0.06$) | Highlight missing definition |
| **Procedural** | Multi-step computation or logic failure | High ($-0.08$) | Provide step-by-step scaffolding |
| **Conceptual** | Slow incorrect response on core concept ($> 1.3\times$ time) | Severe ($-0.12$) | Trigger simplified analogy & remediation |
| **Structural** | Comparison failure across related sub-concepts | Severe ($-0.10$) | Highlight concept relationship map |

---

## 🤖 AI Architecture

AdaptLearn uses **OpenRouter** as its centralized AI provider for all generation tasks, ensuring high availability, model flexibility, and cost efficiency.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       OPENROUTER AI PIPELINE                            │
│                                                                         │
│  Django Backend (openrouter_client.py)                                  │
│         │                                                               │
│         ├── Reads API_KEY & MODEL from Environment Variables            │
│         ├── Calls OpenRouter API Endpoint (https://openrouter.ai/api/v1) │
│         │                                                               │
│         ▼                                                               │
│  Active Model: nvidia/nemotron-3.5-lightning:free                       │
│         │                                                               │
│         ├── Candidate Batching (Generates N + 1 candidates per call)   │
│         ├── Multi-Stage JSON Parsing & Sanitization                     │
│         ├── Pure-Python Novelty Gate (Jaccard + SequenceMatcher ≥ 0.72) │
│         ├── Programmatic Option Shuffling (A/B/C/D balancing)           │
│         └── Candidate Validation (Validates correct answers)            │
│         │                                                               │
│         ▼                                                               │
│  Delivered to Student Practice Session                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### AI Pipeline Features
1. **Dynamic Configuration:** Strictly driven by `API_KEY` and `MODEL` environment variables—zero hardcoded credentials or model strings.
2. **Configured Model:** Defaulted to `nvidia/nemotron-3.5-lightning:free` via OpenRouter.
3. **Pure-Python Novelty Gate:** Evaluates candidate questions against active session history and intra-batch items using normalized token sets, n-grams, and Jaccard similarity (threshold `0.72`). No heavy local embedding models are loaded into memory.
4. **Option Balancing:** Answers are shuffled programmatically across all positions ($A, B, C, D$) to eliminate positional bias while maintaining exact key mapping.
5. **Zero Static Fallbacks:** Questions and teaching materials are generated dynamically to preserve pedagogical freshness.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Clients["Frontend Layer (Vercel)"]
        A["React 19 + Vite Single Page Application"]
        A1["Tailwind CSS + Glassmorphic UI"]
        A2["React Router v7 + Context API"]
        A3["Axios Interceptor (JWT Auth)"]
    end

    subgraph Backend["Backend Layer (Render)"]
        B["Django 6.0 + Django REST Framework"]
        
        subgraph Apps["Django Apps"]
            C1["accounts (Auth, Profiles, Views, Serializers)"]
            C2["learning_engine (Psychometrics & Orchestration)"]
        end
        
        subgraph Engine["Learning Engine Core"]
            D1["adaptive_flow.py (State Machine)"]
            D2["pacing_engine.py (Telemetry & Pacing)"]
            D3["knowledge_tracing.py (BKT & IRT)"]
            D4["question_generator.py (Novelty & Shuffling)"]
            D5["openrouter_client.py (Centralized AI Client)"]
        end
    end

    subgraph Data["Database Layer"]
        DB[("PostgreSQL Database")]
    end

    subgraph AI["AI & External Services"]
        AI1["OpenRouter API"]
        AI2["nvidia/nemotron-3.5-lightning:free"]
        EXT1["YouTube Search API"]
    end

    A -->|HTTPS / REST API Requests| B
    B --> C1
    B --> C2
    C2 --> Engine
    B -->|dj-database-url / ORM| DB
    D5 -->|Chat Completions| AI1
    AI1 --> AI2
    C2 -->|Video & Resource Search| EXT1
```

> **Note on Mermaid Diagrams:** AdaptLearn utilizes Mermaid-based diagrams within both the interactive student frontend (for knowledge structure visualization) and within this technical architecture documentation.

---

## 📸 Screenshots & Product Walkthrough

The following walkthrough demonstrates the full end-to-end user experience in AdaptLearn:

### 1. User Authentication & Sign-In
![AdaptLearn Sign-In](frontend/public/6.png)
*Secure JWT authentication portal highlighting the platform's core algorithmic foundations: Item Response Theory (IRT), Bayesian Knowledge Tracing (BKT), and gamified XP rewards.*

---

### 2. User Registration & Onboarding
![AdaptLearn Create Account](frontend/public/7.png)
*Clean account creation interface onboarding students, parents, and educators into personalized learning pathways.*

---

### 3. Student Learning Dashboard
![AdaptLearn Student Dashboard](frontend/public/2.png)
*The central student hub featuring quick access to new learning sessions, comprehensive progress telemetry, learning calendar, gamified leaderboard rankings, and active concept discovery.*

---

### 4. Learning Session Initiation & Knowledge Level Selection
![AdaptLearn Session Start](frontend/public/3.png)
*Session creation interface where students select their subject (e.g., Object Oriented Programming, Mathematics, Microprocessors), target concept, and baseline knowledge level to calibrate the initial learning path.*

---

### 5. Multi-Modal Adaptive Teaching Module
![AdaptLearn Teaching Module](frontend/public/4.png)
*Structured atomic teaching screen presenting diagnostic quiz feedback (accuracy, mastery, latent ability $\theta$, and pace), concise explanations, curated video tutorials, visual concept diagrams, practical code examples, intuitive real-world analogies, and common misconceptions.*

---

### 6. Real-Time Adaptive Practice & Assessment
![AdaptLearn Adaptive Practice](frontend/public/5.png)
*Interactive assessment drill presenting dynamically generated questions calibrated to the student's ability level (`EASY`, `APPLY`), live mastery tracking ($30\%$, $\theta = 0.25$), and instant submission feedback.*

---

### 7. Parent Dashboard & Child Mastery Insights
![AdaptLearn Parent Portal](frontend/public/1.png)
*Dedicated parent view displaying linked children profiles, active weekly learning sessions, last activity timestamps, single-use invite code generator, and deep mastery insights.*

---

## 💻 Tech Stack

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Frontend Framework** | **React 19.2** | Modern reactive user interface |
| **Build Tool** | **Vite 8.0** | High-performance frontend build pipeline |
| **Styling** | **Tailwind CSS 3.3** | Custom dark/light glassmorphic styling system |
| **Icons & UI Assets** | **Lucide React** | Consistent iconography across dashboards |
| **Routing & State** | **React Router v7 + Context API** | Client-side routing and global telemetry state |
| **HTTP Client** | **Axios (with JWT Interceptors)** | Authenticated REST communication with auto-refresh |
| **Backend Framework** | **Django 6.0** | Enterprise-grade Python web framework |
| **API Layer** | **Django REST Framework (DRF)** | Standardized RESTful endpoints and serializers |
| **Authentication** | **SimpleJWT** | Stateless JSON Web Token authentication |
| **Database** | **PostgreSQL** | Relational persistence for profiles, sessions, and mastery |
| **AI Provider** | **OpenRouter** | Centralized LLM gateway for question & concept generation |
| **Configured AI Model** | **`nvidia/nemotron-3.5-lightning:free`** | LLM model for question and content generation |
| **Static File Handling** | **WhiteNoise** | High-efficiency static file serving for Django |
| **WSGI Server** | **Gunicorn** | Production WSGI HTTP server |
| **Frontend Deployment** | **Vercel** | Edge-deployed SPA frontend |
| **Backend Deployment** | **Render** | Managed backend service running Django/Gunicorn |

---

## 📁 Project Structure

```
AdaptiveLearning/
├── backend/                             # Django REST API & Adaptive Learning Engine
│   ├── core/                            # Project settings, WSGI, root URL routing
│   │   ├── settings.py                  # Environment config, DB, JWT, OpenRouter settings
│   │   ├── urls.py                      # Root URL configuration & token refresh
│   │   └── wsgi.py                      # WSGI entry point for Gunicorn
│   ├── accounts/                        # Authentication, User Models, REST Views
│   │   ├── models.py                    # Student, Teacher, Parent, Session & Mastery models
│   │   ├── serializers.py               # DRF serializers for API payloads
│   │   ├── views.py                     # ViewSets & API endpoints for learning flow & auth
│   │   ├── urls.py                      # API route definitions (/api/...)
│   │   └── subject_data.py              # Seed curriculum & fallback knowledge structures
│   ├── learning_engine/                 # Psychometrics, AI Integration & Pacing
│   │   ├── openrouter_client.py         # Centralized OpenRouter API client
│   │   ├── question_generator.py        # Question generator, novelty gate & option shuffler
│   │   ├── adaptive_flow.py             # Adaptive loop orchestrator & atom selector
│   │   ├── pacing_engine.py             # 10-feature pacing, fatigue & velocity engine
│   │   ├── knowledge_tracing.py         # 2PL IRT theta calibration & BKT updates
│   │   ├── cognitive_load.py            # Cognitive load measurement & session shaping
│   │   ├── external_resources.py        # YouTube tutorial and resource integration
│   │   ├── ai_assistant.py              # Contextual AI doubt solving assistant
│   │   ├── ai_study_planner.py          # AI weekly study timetable generator
│   │   └── tests_question_generation.py # Comprehensive test suite
│   ├── manage.py                        # Django management CLI
│   ├── requirements.txt                 # Backend Python dependencies
│   ├── Procfile                         # Render deployment process configuration
│   └── .env.example                     # Sample backend environment configuration
│
├── frontend/                            # React 19 + Vite Frontend SPA
│   ├── public/                          # Static assets and screenshots
│   │   ├── 1.png - 7.png                # Application walkthrough screenshots
│   │   └── vite.svg                     # Vite brand asset
│   ├── src/
│   │   ├── components/
│   │   │   ├── Learning/                # Adaptive learning loop components
│   │   │   │   ├── TeachingFirstFlow.jsx# Core interactive learning state machine
│   │   │   │   ├── TeachingModule.jsx   # Lesson explanation, analogy & video viewer
│   │   │   │   ├── QuestionsFromTeaching.jsx # Practice drill runner & timer
│   │   │   │   ├── LearningVelocityGraph.jsx # Real-time velocity telemetry graph
│   │   │   │   ├── FatigueIndicator.jsx # Break and fatigue alerts
│   │   │   │   └── WeakTopicDetector.jsx# Post-assessment weakness locator
│   │   │   ├── Teacher/                 # Teacher command center components
│   │   │   ├── Parent/                  # Parent portal & child insights components
│   │   │   ├── Planner/                 # AI study timetable scheduler
│   │   │   ├── Dashboard.jsx            # Student home dashboard
│   │   │   ├── Leaderboard.jsx          # Gamified XP ranking
│   │   │   ├── Login.jsx & Register.jsx # Authentication interfaces
│   │   │   └── Navbar.jsx               # Navigation bar with dark mode toggle
│   │   ├── context/                     # AuthContext & LearningContext
│   │   ├── pages/                       # Standalone pages (AI Assistant)
│   │   ├── axiosConfig.js               # Centralized Axios instance with JWT interceptors
│   │   ├── App.jsx                      # Route definitions
│   │   ├── main.jsx                     # Application bootstrap
│   │   └── index.css                    # Tailwind CSS design system tokens
│   ├── package.json                     # Frontend dependencies & scripts
│   ├── vite.config.js                   # Vite bundler configuration
│   ├── tailwind.config.js               # Tailwind CSS theme customization
│   └── vercel.json                      # Vercel SPA rewrite routing configuration
│
└── README.md                            # Comprehensive project documentation
```

---

## 🔄 Learning Flow

The complete student journey through an AdaptLearn module progresses through clear pedagogical stages:

```
1. Discovery & Selection
   └─► Student selects a Subject (e.g. Microprocessors) and Concept (e.g. Memory Interfacing).

2. Diagnostic Micro-Quiz
   └─► Rapid 3-question baseline test computes initial latent ability (θ) and seeds prior BKT mastery.

3. Atomic Teaching Module
   ├─► Concise structured breakdown of a single atom.
   ├─► Real-world intuitive analogy and code/practical examples.
   ├─► Embedded visual diagrams and curated video recommendations.
   └─► Interactive AI Doubt Assistant available for immediate clarification.

4. Calibrated Practice Drills
   ├─► OpenRouter AI generates questions matching current ability (θ).
   ├─► Cognitive operation tagged (Recall / Apply / Analyze).
   ├─► Millisecond timer captures latency to detect guessing vs. deliberation.
   └─► Tiered hints available with dependency tracking.

5. Instant Psychometric Feedback
   ├─► Real-time mastery bar update and θ trajectory visualization.
   └─► 6-Class error explanation if incorrect (explains the underlying misconception).

6. Pacing & Progression Verdict
   ├─► Mastery < 40% / Conceptual Error ──► Trigger simplified reteaching with new analogies.
   ├─► High Fatigue Detected ────────────► Recommend structured break or lighter exploratory task.
   └─► Mastery ≥ 80% with Streak ≥ 2 ────► Atom completed, award XP, advance to next atom.

7. Concept Final Challenge
   └─► Comprehensive cross-atom assessment with Weak Topic Detection for targeted remediation.
```

---

## 🔌 API & Backend Overview

All endpoints are prefixed under `/auth/api/` or `/api/` and secured via JWT Bearer authentication (except login and registration):

### Authentication & Profiles
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/api/register/` | Register new student account |
| `POST` | `/auth/api/login/` | Authenticate user and obtain JWT tokens |
| `POST` | `/api/token/refresh/` | Refresh expired access token |
| `GET` | `/auth/api/dashboard/` | Retrieve student profile, XP, streak, and recent concepts |

### Adaptive Learning Engine
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/api/start-teaching-session/` | Initialize learning session and select starting atom |
| `POST` | `/auth/api/initial-quiz/` | Generate diagnostic baseline questions |
| `POST` | `/auth/api/submit-initial-quiz-answer/` | Record diagnostic response and calculate baseline $\theta$ |
| `POST` | `/auth/api/complete-initial-quiz/` | Finalize diagnostic and establish initial pacing band |
| `GET` | `/auth/api/teaching-content/` | Retrieve active atom explanation, analogy, examples, and resources |
| `POST` | `/auth/api/generate-questions-from-teaching/` | Generate OpenRouter questions tailored to active atom and $\theta$ |
| `POST` | `/auth/api/submit-atom-answer/` | Evaluate answer, update BKT/IRT, classify errors, and update pacing |
| `POST` | `/auth/api/complete-atom/` | Finalize atom mastery, award XP, and advance streak |
| `GET` | `/auth/api/next-learning-step/` | Compute weakest atom and recommend next action (`TEACH`/`PRACTICE`/`ADVANCE`) |
| `POST` | `/auth/api/adaptive-reteach/` | Generate simplified remedial lessons for struggling concepts |
| `POST` | `/auth/api/concept-final-challenge/` | Generate cross-atom final evaluation challenge |
| `POST` | `/auth/api/complete-concept-final-challenge/` | Complete final challenge and trigger weak topic locator |

### Telemetry & Diagnostics
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/auth/api/velocity-graph/` | Retrieve time-series learning velocity data points |
| `GET` | `/auth/api/fatigue-status/` | Evaluate real-time cognitive fatigue and rest recommendations |
| `POST` | `/auth/api/record-break/` | Log student rest period and reset fatigue counters |
| `POST` | `/auth/api/record-hint/` | Log hint usage and track hint dependency ratio |
| `POST` | `/auth/ai-assistant/` | Context-aware AI tutor for active atom doubt resolution |
| `GET` | `/auth/api/concept-resources/` | Retrieve curated YouTube tutorial links |

### Multi-Stakeholder Portals
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/auth/api/teacher/class-analytics/` | Class-wide mastery, velocity trends, and error heatmaps |
| `GET` | `/auth/api/teacher/students/` | Complete student roster with psychometric indices |
| `POST` | `/auth/api/teacher/content/` | Author custom teacher lessons overriding AI defaults |
| `POST` | `/auth/api/teacher/question-approve/` | Review, edit, approve, or reject AI questions |
| `POST` | `/auth/api/teacher/overrides/` | Apply direct pedagogical intervention to a student |
| `GET` | `/auth/api/parent/children/` | List linked children profiles |
| `POST` | `/auth/api/parent/link-child/` | Link child account using secure invite code |
| `GET` | `/auth/api/parent/child/<id>/insights/` | Child mastery overview, study streaks, and alerts |
| `POST` | `/auth/create-planner/` | Generate weekly AI study timetable |
| `GET` | `/auth/today-study/` | Today's assigned study schedule items and completion status |

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend/` directory.

```env
# =====================================================================
# OpenRouter AI Configuration (Question & Content Generation)
# =====================================================================
API_KEY=your_openrouter_api_key_here
MODEL=nvidia/nemotron-3.5-lightning:free

# =====================================================================
# Database Configuration (PostgreSQL in Production / SQLite in Dev)
# =====================================================================
DATABASE_URL=postgresql://user:password@host:5432/adaptlearn_db

# =====================================================================
# Django Security & Host Settings
# =====================================================================
SECRET_KEY=your-secure-random-django-secret-key
DEBUG=False
ALLOWED_HOSTS=*

# =====================================================================
# Optional External Services
# =====================================================================
SERPAPI_KEY=your_optional_serpapi_key_for_images
```

> **Security Notice:** Never commit actual API keys or credentials to Git repositories. Store secrets securely in environment variables on your deployment platforms (Render / Vercel).

---

## 🚀 Local Development Setup

### Prerequisites
* **Python 3.11+**
* **Node.js 18+ & npm**
* **Git**

---

### Backend Setup

1. **Clone the repository and enter the backend directory:**
   ```bash
   git clone https://github.com/Durvankur-Joshi/AdaptLearn.git
   cd AdaptLearn/backend
   ```

2. **Create and activate a Python virtual environment:**
   ```bash
   # On Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and configure API_KEY and MODEL
   ```

5. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the Django development server:**
   ```bash
   python manage.py runserver
   ```
   *The backend REST API will be available at `http://127.0.0.1:8000/`.*

---

### Frontend Setup

1. **Open a new terminal and navigate to the frontend directory:**
   ```bash
   cd AdaptLearn/frontend
   ```

2. **Install frontend dependencies:**
   ```bash
   npm install
   ```

3. **Start the Vite development server:**
   ```bash
   npm run dev
   ```
   *The frontend application will open at `http://localhost:5173/`.*

---

## 🌐 Deployment Architecture

AdaptLearn is architected for production cloud deployment:

```
┌─────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│     Vercel (Frontend)   │ ──────► │     Render (Backend)    │ ──────► │   PostgreSQL (Database) │
│                         │  HTTPS  │                         │  TCP    │                         │
│ • React 19 + Vite SPA   │  REST   │ • Django 6.0 REST API   │  SSL    │ • Persistent storage    │
│ • Edge CDN Distribution │         │ • Gunicorn WSGI Server  │         │ • Psychometrics & stats │
│ • vercel.json SPA Route │         │ • WhiteNoise Static     │         │ • Multi-role profiles   │
└─────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘
                                                 │
                                                 ▼ HTTPS (API_KEY)
                                    ┌─────────────────────────┐
                                    │    OpenRouter Gateway   │
                                    │                         │
                                    │ • nemotron-3.5-lightning│
                                    └─────────────────────────┘
```

1. **Frontend (Vercel):**
   * Built with `npm run build` producing optimized static assets in `dist/`.
   * Single-page routing managed via `vercel.json` rewrite rules.
   * Interacts with the production Render backend via secure HTTPS requests with JWT headers.

2. **Backend (Render):**
   * Managed web service executing `gunicorn core.wsgi` via `Procfile`.
   * Static assets served directly via `whitenoise`.
   * OpenRouter AI requests orchestrated asynchronously with timeout guards.

3. **Database (PostgreSQL):**
   * Production-grade relational storage parsed via `dj-database-url`.
   * Connection pooling and SSL connections enforced in production.

---

## 🔭 Future Scope

* **Multimodal Voice Tutoring:** Interactive conversational voice agent for auditory learners.
* **Semantic Free-Text Grading:** LLM-powered rubric evaluation for open-ended essay and derivation responses.
* **Classroom Multiplayer Sprints:** Synchronous adaptive battle-quizzes for gamified classroom engagement.
* **Native Mobile Apps:** Cross-platform mobile clients built with React Native for offline study session caching.
* **Institutional LMS Integrations:** LTI 1.3 / Canvas / Moodle export integrations for enterprise school deployment.

---

## 💡 Why This Project Matters

In 1984, educational psychologist Benjamin Bloom identified the **2-Sigma Problem**: students tutored one-on-one using mastery learning techniques performed **two standard deviations better** than students taught in conventional classrooms. 

One-on-one human tutoring is economically impossible for every student on Earth. **AdaptLearn bridges this gap** by leveraging modern generative AI and psychometric science to make individualized, adaptive mastery learning accessible to any student with an internet connection.

---

## 👨‍💻 Author & Contact

**Durvankur Joshi**
* GitHub: [@Durvankur-Joshi](https://github.com/Durvankur-Joshi)
* Repository: [AdaptLearn](https://github.com/Durvankur-Joshi/AdaptLearn)

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
