# 🪐 ATLAS (SmartClassScheduler)

> The Intelligent Architect of Academic Time.

ATLAS is an AI-powered academic scheduling system designed to automatically generate conflict-free timetables. By leveraging **Constraint Programming**, it balances faculty workload, maximizes room utilization, and adapts to complex multidisciplinary curricula in seconds.

## ✨ Key Features

* **AI-Driven Optimization:** Utilizes Google OR-Tools (CP-SAT Solver) to mathematically eliminate scheduling clashes and fulfill availability constraints.
* **Role-Based Access Control (RBAC):**
    * **Admin Dashboard:** Add subjects, manage faculty, set curriculum rules, and trigger the schedule generation algorithm.
    * **Faculty Portal:** Instructors can log in to view their personalized schedules and set preferred teaching hours.
* **Zero-Build Glassmorphism UI:** A highly responsive, single-page frontend built without heavy frameworks. Features 60fps GSAP animations and a custom futuristic aesthetic.
* **Decoupled Architecture:** Clean separation of concerns between the Django REST API and the Vanilla JS frontend.

---

## 🛠️ Tech Stack

**Backend (The Engine):**
* Python 3.x
* Django & Django REST Framework
* Google OR-Tools (Constraint Programming)
* SQLite3

**Frontend (The Interface):**
* Vanilla JavaScript (Single Page Application)
* Tailwind CSS (via CDN)
* GSAP (GreenSock Animation Platform)
* Google Fonts (Exo 2, Outfit)

---

## 🚀 Getting Started

To run this project locally, you will need to run the backend and frontend simultaneously in **two separate terminal windows**.

### Prerequisites
* Python installed on your machine.
* Git installed.

### 1. Clone the Repository
\`\`\`bash
git clone https://github.com/17mohak/SmartClassScheduler.git
cd SmartClassScheduler
\`\`\`

### 2. Backend Setup (Terminal 1)
Navigate to the project root and set up the virtual environment:

**For Windows:**
\`\`\`cmd
python -m venv venv
venv\Scripts\activate
cd backend
pip install -r requirements.txt
\`\`\`

**Set up the Database & Load Dummy Data:**
We have included a fixture file so you don't have to start with an empty dashboard.
\`\`\`cmd
python manage.py migrate
python manage.py loaddata dummy_data.json
\`\`\`

**Start the API Server:**
\`\`\`cmd
python manage.py runserver
\`\`\`
*(Keep this terminal open and running. The API is hosted at `http://127.0.0.1:8000/api`)*

### 3. Frontend Setup (Terminal 2)
Open a new terminal window, navigate to the frontend folder, and start a local HTTP server:

**For Windows:**
\`\`\`cmd
cd SmartClassScheduler\frontend
python -m http.server 5173
\`\`\`

### 4. Access the Application
Open your web browser and navigate to:
**[http://localhost:5173](http://localhost:5173)**

**Test Credentials:**
* **Admin:** `admin` / `adminpassword` *(Update these based on your actual dummy data)*
* **Faculty:** `faculty1` / `password123` *(Update these based on your actual dummy data)*

---

## 🧠 How the Algorithm Works
Traditional scheduling relies on looping algorithms which often fail when variables become too complex. ATLAS treats scheduling as a **Constraint Satisfaction Problem (CSP)**. 
1.  **Hard Constraints:** A teacher cannot be in two places at once. A batch cannot have overlapping classes.
2.  **Soft Constraints:** Teachers prefer specific time slots (e.g., Morning vs. Afternoon).
The Google OR-Tools CP-SAT solver explores millions of mathematical permutations to find a valid grid that satisfies all hard constraints while optimizing for the soft constraints.

---

## 👨‍💻 Author
**Mohak Mandwani**
