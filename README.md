\# HireSense AI - Smart Resume and Job Matching Platform



An intelligent job matching platform that helps you find the right jobs, optimize your resume, and track applications across multiple job portals including Indeed, Naukri, and Internshala.



\# HireSense AI - Smart Resume and Job Matching Platform



\[!\[BSL 1.1 License](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)

\[!\[Non-Commercial Use](https://img.shields.io/badge/Use-Non--Commercial-red.svg)](LICENSE)

\[!\[Commercial License Available](https://img.shields.io/badge/Commercial-License%20Available-green.svg)](COMMERCIAL\_LICENSE.md)



⚠️ \*\*License Notice\*\*: This software is for non-commercial use only. Commercial use requires a paid license. See \[LICENSE](LICENSE) and \[COMMERCIAL\_LICENSE.md](COMMERCIAL\_LICENSE.md) for details.



\---



\## TABLE OF CONTENTS



1\. Overview

2\. Features

3\. Tech Stack

4\. Project Structure

5\. Prerequisites

6\. Installation Instructions

7\. Configuration and Setup

8\. Running the Application

9\. API Documentation

10\. Database Schema

11\. Web Scrapers

12\. Authentication System

13\. Deployment Guide

14\. Docker Deployment

15\. Google Cloud Deployment

16\. Environment Variables

17\. Security Best Practices

18\. Performance Optimization

19\. Troubleshooting

20\. Testing

21\. Contributing

22\. Roadmap

23\. FAQ

24\. Version History

25\. License

26\. Contact and Support



\---



\## 1. OVERVIEW



HireSense AI is a comprehensive career management platform designed to streamline the entire job search process. It combines web scraping, cloud storage, intelligent matching, and application tracking into a single unified platform.



The platform consists of four main components. First is the FastAPI backend which handles all API services, authentication, and business logic. Second is the Streamlit frontend which provides an interactive web interface for users. Third is the Firebase integration which manages authentication, Firestore database, and Cloud Storage. Fourth is the web scrapers which aggregate job listings from multiple job portals.



The system is built with scalability in mind and can be deployed locally, on Google Cloud Run, or any cloud platform that supports Docker containers.



\---



\## 2. FEATURES



CORE FEATURES:



User Authentication and Authorization

Secure user registration and login system using JWT tokens. Passwords are hashed using bcrypt encryption. Token-based authentication with configurable expiration time. Session management through Streamlit session state.



Profile Management

Create and update professional profiles with detailed information. Add skills, experience level, target roles, target cities, and target companies. Profile completion tracking. Real-time profile updates stored in Firestore.



Resume Management

Upload multiple resumes in PDF or DOCX format. Cloud storage using Google Cloud Storage buckets. Set primary resume for quick applications. View, download, and delete resumes. Resume metadata stored in Firestore with cloud URLs.



Smart Job Search

Search jobs from three major Indian job portals. Filter by keyword, location, and source platform. Real-time scraping from Indeed India, Naukri.com, and Internshala. Automatic skill extraction from job descriptions. Job results saved to Firestore for future reference.



Application Tracking

Track all job applications in one place. Status management with four stages: Applied, Interview, Rejected, and Offer. Match score tracking for each application. Notes and comments for each application. Date tracking for application timeline.



Multi-Source Job Integration

Unified search across Indeed, Naukri, and Internshala. Consistent job data format across all sources. Source URL tracking for original job listings. Automatic deduplication of job results.



ADVANCED FEATURES (PLANNED):



AI-powered resume optimization and scoring. Automated skill gap analysis between resume and job description. Interview preparation module with common questions. Salary insights and market analysis. LinkedIn profile integration. Email notifications for new matching jobs. Advanced analytics dashboard with charts. Resume ATS compatibility scoring. Company reviews and ratings integration. Mentor network and career coaching. Mobile application for iOS and Android. Batch resume processing for recruiters.



\---



\## 3. TECH STACK



BACKEND TECHNOLOGIES:



FastAPI version 0.104.1 is used as the main web framework. It is a modern, fast, async Python web framework built on top of Starlette and Pydantic. It provides automatic API documentation through Swagger UI and ReDoc.



Uvicorn version 0.24.0 serves as the ASGI server for running the FastAPI application. It handles HTTP requests and WebSocket connections efficiently.



Pydantic version 2.5.0 handles data validation and serialization. All request and response models are defined using Pydantic for type safety and automatic validation.



PyJWT version 2.8.1 manages JSON Web Token creation and verification for authentication. Tokens are signed using HS256 algorithm.



Passlib version 1.7.4 with bcrypt version 4.1.1 handles password hashing. All passwords are securely hashed before storage.



Python-multipart version 0.0.6 handles file uploads through multipart form data.



FRONTEND TECHNOLOGIES:



Streamlit version 1.28.1 provides the interactive web interface. It allows rapid development of data-driven web applications using Python.



Streamlit Option Menu version 0.3.6 provides the sidebar navigation menu with icons.



Pandas version 2.1.3 handles data manipulation and display in tables and dataframes.



FIREBASE AND GOOGLE CLOUD:



Firebase Admin SDK version 6.2.0 provides server-side Firebase integration including authentication, Firestore, and Storage.



Google Cloud Storage version 2.10.0 handles file upload, download, and management in cloud storage buckets.



Google Cloud Firestore version 2.13.0 provides the NoSQL database for storing user profiles, jobs, and applications.



Google Auth version 2.25.2 handles service account authentication with Google Cloud Platform.



WEB SCRAPING:



Requests version 2.31.0 makes HTTP requests to job portal websites.



BeautifulSoup4 version 4.12.2 parses HTML content from scraped web pages.



Selenium version 4.15.2 provides browser automation for JavaScript-heavy websites.



LXML version 4.9.3 provides fast XML and HTML parsing.



DATA PROCESSING:



NumPy version 1.26.2 provides numerical computing capabilities.



PyPDF2 version 3.0.1 extracts text from PDF resume files.



Python-docx version 0.8.11 processes DOCX resume files.



PDFPlumber version 0.10.3 provides advanced PDF text extraction.



MACHINE LEARNING (OPTIONAL):



Scikit-learn version 1.3.2 provides machine learning algorithms for matching.



Transformers version 4.35.2 provides NLP models for text analysis.



Sentence Transformers version 2.2.2 generates sentence embeddings for similarity matching.



PyTorch version 2.1.1 serves as the deep learning framework backend.



OTHER TOOLS:



Python-dotenv version 1.0.0 loads environment variables from .env files.



Python-dateutil version 2.8.2 provides date parsing and manipulation.



SQLAlchemy version 2.0.23 provides optional SQL database support.



\---



\## 4. PROJECT STRUCTURE



The project follows a modular structure with clear separation of concerns.



Root Directory: hiresense-ai/



Configuration Files:

\- .gitignore: Git ignore rules for sensitive files and build artifacts

\- .env.example: Template for environment variables

\- requirements.txt: Python package dependencies

\- Dockerfile: Docker container configuration

\- README.md: Project documentation (this file)



Config Package: config/

\- \_\_init\_\_.py: Package initialization

\- firebase\_config.py: Firebase SDK initialization with service account credentials, Firestore client setup, and Cloud Storage bucket configuration



App Package: app/

\- \_\_init\_\_.py: App package initialization

\- main.py: FastAPI application entry point with all route definitions, authentication middleware, CORS configuration, and application startup



App API Package: app/api/

\- \_\_init\_\_.py: API package initialization

\- auth.py: Authentication routes for register and login endpoints

\- jobs.py: Job search and retrieval routes

\- resumes.py: Resume upload, list, and delete routes



App Services Package: app/services/

\- \_\_init\_\_.py: Services package initialization with exports

\- firestore\_service.py: All Firestore database operations including user profiles, resumes, jobs, applications, and analysis history

\- cloud\_storage\_service.py: Google Cloud Storage operations for resume file management

\- resume\_parser.py: Resume text extraction from PDF and DOCX files

\- resume\_scorer.py: Resume scoring algorithm against job descriptions

\- skill\_extractor.py: Technical skill extraction from text

\- company\_services.py: Company information management

\- comparison\_service.py: Job comparison logic

\- learning\_services.py: Learning path recommendations

\- rag\_pipeline.py: Retrieval Augmented Generation pipeline

\- llm.py: Large Language Model integration

\- chunking.py: Text chunking utility for document processing

\- cleaner.py: Data cleaning and preprocessing

\- embedding.py: Text embedding generation

\- parser.py: General text parsing utilities

\- retriever.py: Document retrieval from vector store

\- scorer.py: General scoring utility

\- vector\_store.py: Vector database management



App Models Package: app/models/

\- \_\_init\_\_.py: Models package initialization



App Data Package: app/data/

\- \_\_init\_\_.py: Data package initialization



Scrapers Package: scrapers/

\- \_\_init\_\_.py: Scrapers package initialization

\- indeed\_scraper.py: Indeed India job scraper

\- naukri\_scraper.py: Naukri.com job scraper

\- internshala\_scraper.py: Internshala job and internship scraper



\---



\## 5. PREREQUISITES



Before setting up the project, ensure you have the following installed and configured.



Required Software:

\- Python 3.11 or higher (download from python.org)

\- pip (Python package manager, comes with Python)

\- Git (download from git-scm.com)

\- A code editor (VS Code, PyCharm, or Notepad++)

\- Web browser (Chrome, Firefox, or Edge)



Required Accounts:

\- GitHub account (github.com)

\- Google Cloud Platform account (console.cloud.google.com)

\- Firebase account (automatically included with GCP)



Required GCP Setup:

\- Active GCP project named hiresense-ai-resumes

\- Firebase enabled in the GCP project

\- Cloud Firestore database created

\- Cloud Storage bucket created

\- Service Account with Editor permissions

\- Service Account JSON key downloaded



Optional Software:

\- Docker Desktop (for container deployment)

\- Google Cloud SDK (for cloud deployment)

\- Postman (for API testing)



Hardware Requirements:

\- Minimum 4 GB RAM (8 GB recommended)

\- 2 GB free disk space

\- Stable internet connection



\---



\## 6. INSTALLATION INSTRUCTIONS



STEP 1: CLONE THE REPOSITORY



Open your terminal or command prompt and run the following commands.



git clone https://github.com/lonewolf1621/hiresense-ai.git

cd hiresense-ai



This will download all project files to your local machine.



STEP 2: CREATE PYTHON VIRTUAL ENVIRONMENT



For Windows:

python -m venv venv

venv\\Scripts\\activate



For macOS and Linux:

python3 -m venv venv

source venv/bin/activate



After activation, you should see (venv) at the beginning of your terminal prompt. This indicates the virtual environment is active.



STEP 3: INSTALL PYTHON DEPENDENCIES



pip install -r requirements.txt



This will install all required Python packages. The installation typically takes 5 to 10 minutes depending on your internet speed. If you encounter any errors, try installing packages individually.



STEP 4: DOWNLOAD FIREBASE SERVICE ACCOUNT KEY



Go to Google Cloud Console at console.cloud.google.com. Navigate to IAM and Admin, then Service Accounts. Find your service account or create a new one with the name hiresense-sa. Click on the service account, go to Keys tab, click Add Key, then Create New Key. Select JSON format and click Create. The key file will be downloaded automatically.



Move the downloaded JSON file to your project root directory and rename it to service-account-key.json.



IMPORTANT: Never commit this file to GitHub. It is already included in the .gitignore file.



STEP 5: CREATE ENVIRONMENT FILE



Copy the example environment file:

cp .env.example .env



For Windows:

copy .env.example .env



Edit the .env file with your specific values. At minimum, change the SECRET\_KEY to a strong random string.



STEP 6: VERIFY INSTALLATION



Test Firebase connection:

python -c "from config.firebase\_config import db; print('Firebase connected successfully')"



Test FastAPI import:

python -c "from app.main import app; print('FastAPI app loaded successfully')"



If both commands print success messages, your installation is complete.



\---



\## 7. CONFIGURATION AND SETUP



FIREBASE CONFIGURATION:



The Firebase configuration is managed in config/firebase\_config.py. This file initializes the Firebase Admin SDK using your service account credentials. It creates connections to Firestore database and Cloud Storage bucket.



The configuration expects:

\- service-account-key.json file in the project root

\- Storage bucket name: hiresense-ai-resumes.appspot.com

\- The Firebase project must have Firestore and Storage enabled



FIRESTORE DATABASE SETUP:



Firestore collections are created automatically when data is first written. The main collections are:

\- users: Stores user profiles, credentials, and metadata

\- jobs: Stores scraped job listings from all sources



Sub-collections under each user document:

\- resumes: Stores resume metadata and cloud storage URLs

\- applications: Stores job application records and status

\- analysisHistory: Stores resume-job analysis results



FIRESTORE SECURITY RULES:



Set these rules in Firebase Console under Firestore Database, Rules tab:



rules\_version = '2';

service cloud.firestore {

&#x20; match /databases/{database}/documents {

&#x20;   match /users/{userId} {

&#x20;     allow read, write: if request.auth != null \&\& request.auth.uid == userId;

&#x20;     match /{subcollection}/{docId} {

&#x20;       allow read, write: if request.auth != null \&\& request.auth.uid == userId;

&#x20;     }

&#x20;   }

&#x20;   match /jobs/{jobId} {

&#x20;     allow read: if request.auth != null;

&#x20;     allow write: if request.auth != null;

&#x20;   }

&#x20; }

}



CLOUD STORAGE SETUP:



The storage bucket should be named hiresense-ai-resumes.appspot.com. Files are organized in the following structure:

\- resumes/{user\_id}/{filename}: User resume files



Storage security rules should allow authenticated users to read and write only their own files.



STREAMLIT CONFIGURATION:



Create a .streamlit directory and config.toml file for custom Streamlit settings. This is optional but recommended for production.



\---



\## 8. RUNNING THE APPLICATION



The application requires two processes running simultaneously: the FastAPI backend and the Streamlit frontend.



STARTING THE BACKEND:



Open a terminal window. Navigate to the project directory.



cd C:\\Users\\reddy.LAPTOP-L2J44UFO\\hiresense



Activate the virtual environment.



venv\\Scripts\\activate



Start the FastAPI server.



uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



The --reload flag enables auto-reload during development. Remove it for production.



Expected output:

INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

INFO: Started reloader process

INFO: Started server process

INFO: Application startup complete



The backend API will be accessible at:

\- API Base URL: http://localhost:8000

\- Interactive API Docs: http://localhost:8000/docs

\- Alternative API Docs: http://localhost:8000/redoc

\- Health Check: http://localhost:8000/health



STARTING THE FRONTEND:



Open a second terminal window. Navigate to the same project directory and activate the virtual environment.



cd C:\\Users\\reddy.LAPTOP-L2J44UFO\\hiresense

venv\\Scripts\\activate



Start the Streamlit application.



streamlit run streamlit\_app.py



Expected output:

You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501

Network URL: http://192.168.x.x:8501



The Streamlit frontend should automatically open in your default web browser at http://localhost:8501.



USING THE APPLICATION:



When you first open the application, you will see the login and registration page. On the left side is the login form for existing users. On the right side is the registration form for new users.



After logging in, you will see the sidebar navigation with the following options:

\- Dashboard: Overview of your activity, metrics, and recent applications

\- Profile: Edit your professional profile, skills, and preferences

\- Resumes: Upload, view, and manage your resume files

\- Find Jobs: Search jobs from Indeed, Naukri, and Internshala

\- Applications: Track all your job applications and their status

\- Logout: End your session and return to login page



STOPPING THE APPLICATION:



To stop the backend, press CTRL+C in the backend terminal.

To stop the frontend, press CTRL+C in the frontend terminal.



\---



\## 9. API DOCUMENTATION



BASE URL: http://localhost:8000/api



All API responses are in JSON format. Authentication is required for most endpoints using Bearer token in the Authorization header. The token is obtained during login or registration.



AUTHENTICATION ENDPOINTS:



POST /api/auth/register



Purpose: Register a new user account.



Request Body:

{

&#x20; "email": "user@example.com",

&#x20; "password": "SecurePassword123",

&#x20; "name": "John Doe",

&#x20; "phone": "+91 9999999999"

}



Success Response (200):

{

&#x20; "message": "User registered successfully",

&#x20; "user\_id": "550e8400-e29b-41d4-a716-446655440000",

&#x20; "access\_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

&#x20; "token\_type": "bearer"

}



Error Response (400):

{

&#x20; "detail": "Email already exists"

}



POST /api/auth/login



Purpose: Login to an existing account.



Request Body:

{

&#x20; "email": "user@example.com",

&#x20; "password": "SecurePassword123"

}



Success Response (200):

{

&#x20; "message": "Login successful",

&#x20; "user\_id": "550e8400-e29b-41d4-a716-446655440000",

&#x20; "name": "John Doe",

&#x20; "email": "user@example.com",

&#x20; "access\_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

&#x20; "token\_type": "bearer"

}



Error Response (401):

{

&#x20; "detail": "Invalid credentials"

}



PROFILE ENDPOINTS:



GET /api/profile



Purpose: Retrieve the authenticated user's profile.

Authentication: Required (Bearer token).



Success Response (200):

{

&#x20; "email": "user@example.com",

&#x20; "name": "John Doe",

&#x20; "phone": "+91 9999999999",

&#x20; "profile": {

&#x20;   "experience": 3,

&#x20;   "skills": \["Python", "SQL", "AWS"],

&#x20;   "targetRoles": \["Senior Developer"],

&#x20;   "targetCities": \["Bangalore", "Hyderabad"],

&#x20;   "targetCompanies": \["Google", "Microsoft"],

&#x20;   "createdAt": "2026-06-29T10:00:00",

&#x20;   "updatedAt": "2026-06-29T15:30:00"

&#x20; }

}



PUT /api/profile



Purpose: Update the authenticated user's profile.

Authentication: Required (Bearer token).



Request Body:

{

&#x20; "name": "John Doe",

&#x20; "phone": "+91 9999999999",

&#x20; "experience": 5,

&#x20; "skills": \["Python", "SQL", "AWS", "Docker", "Kubernetes"],

&#x20; "targetRoles": \["Senior Developer", "Tech Lead"],

&#x20; "targetCities": \["Bangalore"],

&#x20; "targetCompanies": \["Google"]

}



Success Response (200):

{

&#x20; "message": "Profile updated successfully"

}



RESUME ENDPOINTS:



POST /api/resumes/upload



Purpose: Upload a resume file to cloud storage.

Authentication: Required (Bearer token).

Content-Type: multipart/form-data



Form Fields:

\- file: The resume file (PDF or DOCX)

\- name: Display name for the resume

\- isPrimary: Boolean indicating if this is the primary resume



Success Response (200):

{

&#x20; "message": "Resume uploaded successfully",

&#x20; "resume\_id": "550e8400-e29b-41d4-a716-446655440001",

&#x20; "url": "https://storage.googleapis.com/hiresense-ai-resumes.appspot.com/resumes/user\_id/filename.pdf"

}



GET /api/resumes



Purpose: Get all resumes for the authenticated user.

Authentication: Required (Bearer token).



Success Response (200):

{

&#x20; "resumes": \[

&#x20;   {

&#x20;     "name": "Senior Developer Resume",

&#x20;     "gcsUrl": "https://storage.googleapis.com/...",

&#x20;     "uploadedDate": "2026-06-29T10:30:00",

&#x20;     "isPrimary": true

&#x20;   },

&#x20;   {

&#x20;     "name": "General Resume",

&#x20;     "gcsUrl": "https://storage.googleapis.com/...",

&#x20;     "uploadedDate": "2026-06-28T14:20:00",

&#x20;     "isPrimary": false

&#x20;   }

&#x20; ]

}



DELETE /api/resumes/{resume\_id}



Purpose: Delete a specific resume.

Authentication: Required (Bearer token).



Success Response (200):

{

&#x20; "message": "Resume deleted successfully"

}



JOB ENDPOINTS:



POST /api/jobs/search



Purpose: Search for jobs across multiple job portals.

Authentication: Required (Bearer token).



Request Body:

{

&#x20; "keyword": "Python Developer",

&#x20; "location": "Bangalore",

&#x20; "source": "Indeed"

}



The source field is optional. If omitted or set to null, all three sources (Indeed, Naukri, Internshala) will be searched. Valid values are "Indeed", "Naukri", and "Internshala".



Success Response (200):

{

&#x20; "total": 15,

&#x20; "jobs": \[

&#x20;   {

&#x20;     "title": "Senior Python Developer",

&#x20;     "company": "Google India",

&#x20;     "location": "Bangalore, Karnataka",

&#x20;     "salary": "20-30 LPA",

&#x20;     "description": "We are looking for a senior Python developer with experience in cloud technologies...",

&#x20;     "skills": \["python", "aws", "docker"],

&#x20;     "source": "Indeed",

&#x20;     "sourceUrl": "https://in.indeed.com/jobs?q=...",

&#x20;     "postedDate": "2026-06-29T00:00:00"

&#x20;   }

&#x20; ]

}



GET /api/jobs



Purpose: Get all jobs stored in the database.

Authentication: Required (Bearer token).



Success Response (200):

{

&#x20; "jobs": \[...]

}



GET /api/jobs/{job\_id}



Purpose: Get a specific job by its ID.

Authentication: Required (Bearer token).



Success Response (200):

{

&#x20; "title": "Senior Python Developer",

&#x20; "company": "Google India",

&#x20; "location": "Bangalore",

&#x20; "salary": "20-30 LPA",

&#x20; "description": "...",

&#x20; "skills": \["python", "aws"],

&#x20; "source": "Indeed",

&#x20; "sourceUrl": "https://...",

&#x20; "postedDate": "2026-06-29",

&#x20; "scrapedDate": "2026-06-29T10:30:00"

}



Error Response (404):

{

&#x20; "detail": "Job not found"

}



APPLICATION ENDPOINTS:



POST /api/applications



Purpose: Save a new job application.

Authentication: Required (Bearer token).



Request Body:

{

&#x20; "jobId": "job-uuid-string",

&#x20; "jobTitle": "Senior Python Developer",

&#x20; "company": "Google India",

&#x20; "matchScore": 85.5,

&#x20; "notes": "Applied through company website"

}



Success Response (200):

{

&#x20; "message": "Application saved successfully",

&#x20; "application\_id": "app-uuid-string"

}



GET /api/applications



Purpose: Get all applications for the authenticated user.

Authentication: Required (Bearer token).



Success Response (200):

{

&#x20; "applications": \[

&#x20;   {

&#x20;     "jobId": "job-uuid",

&#x20;     "jobTitle": "Senior Python Developer",

&#x20;     "company": "Google India",

&#x20;     "status": "Applied",

&#x20;     "appliedDate": "2026-06-29T10:30:00",

&#x20;     "matchScore": 85.5,

&#x20;     "notes": "Applied through company website"

&#x20;   },

&#x20;   {

&#x20;     "jobId": "job-uuid-2",

&#x20;     "jobTitle": "Backend Engineer",

&#x20;     "company": "Microsoft",

&#x20;     "status": "Interview",

&#x20;     "appliedDate": "2026-06-25T09:00:00",

&#x20;     "matchScore": 92.0,

&#x20;     "notes": "Phone interview scheduled for July 5"

&#x20;   }

&#x20; ]

}



PUT /api/applications/{app\_id}



Purpose: Update the status of an application.

Authentication: Required (Bearer token).



Query Parameter: status (string)

Valid values: Applied, Interview, Rejected, Offer



Success Response (200):

{

&#x20; "message": "Application updated successfully"

}



HEALTH CHECK ENDPOINT:



GET /health



Purpose: Check if the API server is running.

Authentication: Not required.



Response (200):

{

&#x20; "status": "ok"

}



ROOT ENDPOINT:



GET /



Purpose: API information and version.

Authentication: Not required.



Response (200):

{

&#x20; "message": "HireSense API",

&#x20; "version": "1.0.0",

&#x20; "docs": "/docs"

}



\---



\## 10. DATABASE SCHEMA



FIRESTORE DATABASE STRUCTURE:



The application uses Google Cloud Firestore as its primary database. Firestore is a NoSQL document database that stores data in collections and documents. Each document contains fields with values.



USERS COLLECTION:



Collection name: users

Document ID: UUID string generated during registration



Each user document contains the following fields:



email (string): User's email address used for login

name (string): User's full name

phone (string): User's phone number with country code

password (string): Bcrypt hashed password (never stored in plain text)

profile (map): Nested object containing profile details

&#x20; experience (number): Years of professional experience

&#x20; skills (array of strings): List of technical and soft skills

&#x20; targetRoles (array of strings): Desired job titles or roles

&#x20; targetCities (array of strings): Preferred work locations

&#x20; targetCompanies (array of strings): Dream companies to work for

&#x20; createdAt (timestamp): Account creation date and time

&#x20; updatedAt (timestamp): Last profile update date and time

resumes (map): Reserved for inline resume data

applications (map): Reserved for inline application data

savedJobs (map): Reserved for saved/bookmarked jobs

analysisHistory (map): Reserved for analysis records



RESUMES SUB-COLLECTION:



Path: users/{userId}/resumes/{resumeId}

Document ID: UUID string generated during upload



Each resume document contains:



name (string): Display name for the resume

gcsUrl (string): Google Cloud Storage public URL

uploadedDate (timestamp): Upload date and time

isPrimary (boolean): Whether this is the primary/default resume



APPLICATIONS SUB-COLLECTION:



Path: users/{userId}/applications/{applicationId}

Document ID: UUID string generated during application



Each application document contains:



jobId (string): Reference to the job document

jobTitle (string): Title of the job applied for

company (string): Company name

status (string): Current application status (Applied, Interview, Rejected, or Offer)

appliedDate (timestamp): Date when application was submitted

matchScore (number): Resume-job match percentage (0 to 100)

notes (string): User's personal notes about the application

updatedAt (timestamp): Last status update date and time



ANALYSIS HISTORY SUB-COLLECTION:



Path: users/{userId}/analysisHistory/{analysisId}

Document ID: UUID string generated during analysis



Each analysis document contains:



jobDescription (string): The job description text that was analyzed

matchScore (number): Calculated match percentage

matchedSkills (array of strings): Skills found in both resume and job

missingSkills (array of strings): Skills in job but not in resume

suggestions (array of strings): Improvement suggestions

date (timestamp): Analysis date and time



JOBS COLLECTION:



Collection name: jobs

Document ID: UUID string generated during scraping



Each job document contains:



title (string): Job title

company (string): Hiring company name

location (string): Job location (city, state, or Remote)

salary (string): Salary range or "Not specified"

description (string): Full job description text

skills (array of strings): Required technical skills extracted from description

source (string): Source platform (Indeed, Naukri, or Internshala)

sourceUrl (string): Direct link to original job posting

postedDate (timestamp): Original posting date

scrapedDate (timestamp): Date and time when the job was scraped



RECOMMENDED FIRESTORE INDEXES:



For optimal query performance, create these composite indexes in Firebase Console.



Users collection index: email ascending for login queries.

Jobs collection index: location ascending and salary ascending for filtered searches.

Jobs collection index: source ascending and scrapedDate descending for source-filtered queries.

Applications sub-collection index: status ascending and appliedDate descending for filtered application views.



\---



\## 11. WEB SCRAPERS



The application includes three web scrapers that collect job listings from major Indian job portals.



INDEED SCRAPER:



File: scrapers/indeed\_scraper.py

Class: IndeedScraper

Target: https://in.indeed.com



The Indeed scraper searches for jobs on Indeed India. It constructs search URLs using the provided keyword and location, then parses the HTML response to extract job cards. Each card is parsed to extract the job title, company name, location, salary, description snippet, and job URL.



The scraper extracts technical skills from job descriptions by matching against a predefined list of common skills including Python, Java, JavaScript, SQL, AWS, Docker, React, Angular, Node.js, FastAPI, Django, Kubernetes, MongoDB, PostgreSQL, REST API, Machine Learning, TensorFlow, Pandas, and Git.



NAUKRI SCRAPER:



File: scrapers/naukri\_scraper.py

Class: NaukriScraper

Target: https://www.naukri.com



The Naukri scraper searches for jobs on Naukri.com, one of India's largest job portals. It follows a similar pattern to the Indeed scraper but uses Naukri-specific HTML classes and URL structures.



Additional skills detected by the Naukri scraper include C++, C#, .NET, PHP, Golang, and Scala.



INTERNSHALA SCRAPER:



File: scrapers/internshala\_scraper.py

Class: InternshalaScraper

Target: https://internshala.com



The Internshala scraper focuses on internships and entry-level jobs. It is particularly useful for students and fresh graduates. Additional skills detected include PHP, WordPress, Figma, UI/UX, and Graphic Design.



SCRAPER LIMITATIONS:



All scrapers use requests library with BeautifulSoup for HTML parsing. This approach has several limitations. Job portals frequently change their HTML structure, which may break the scrapers. Some portals use JavaScript rendering, which requires Selenium for proper scraping. Portals may implement rate limiting or CAPTCHA challenges. Excessive scraping may result in IP blocking.



BEST PRACTICES FOR SCRAPING:



Add delays between requests to avoid rate limiting. Use rotating user agents to reduce detection. Implement retry logic with exponential backoff. Cache results to minimize redundant requests. Consider using official APIs when available. Respect robots.txt and terms of service.



\---



\## 12. AUTHENTICATION SYSTEM



The application uses a custom JWT-based authentication system.



REGISTRATION FLOW:



1\. User submits registration form with name, email, password, and phone number.

2\. System checks if email already exists in Firestore.

3\. If email is unique, password is hashed using bcrypt with automatic salt generation.

4\. User document is created in Firestore with hashed password and profile data.

5\. JWT access token is generated with user ID as the subject claim.

6\. Token and user details are returned to the client.



LOGIN FLOW:



1\. User submits login form with email and password.

2\. System queries Firestore for user document matching the email.

3\. If user found, submitted password is verified against stored bcrypt hash.

4\. If password matches, new JWT access token is generated.

5\. Token, user ID, name, and email are returned to the client.



TOKEN STRUCTURE:



The JWT token contains the following claims:

\- sub: User ID (UUID string)

\- exp: Expiration timestamp (30 minutes from creation)



TOKEN VERIFICATION:



For protected endpoints, the token is extracted from the Authorization header. The format must be "Bearer {token}". The token is decoded using the secret key and HS256 algorithm. If the token is expired or invalid, a 401 Unauthorized error is returned.



PASSWORD SECURITY:



Passwords are hashed using bcrypt through the Passlib library. Bcrypt automatically generates a random salt for each password. The hash includes the salt, making rainbow table attacks ineffective. Password verification compares the submitted password against the stored hash without ever decrypting the original password.



SESSION MANAGEMENT:



The Streamlit frontend manages sessions using Streamlit session state. The JWT token, user ID, and user name are stored in session state after successful login. These values persist across page navigation but are cleared when the browser tab is closed or when the user clicks Logout.



\---



\## 13. DEPLOYMENT GUIDE



LOCAL DEPLOYMENT:



Local deployment is the simplest option for development and testing. Follow the installation instructions in section 6 and running instructions in section 8.



PRODUCTION CONSIDERATIONS:



For production deployment, make the following changes:



1\. Change the SECRET\_KEY to a strong, randomly generated string.

2\. Remove the --reload flag from the uvicorn command.

3\. Use a process manager like Gunicorn for the backend.

4\. Set DEBUG to False in environment variables.

5\. Configure HTTPS with SSL certificates.

6\. Set up proper logging and monitoring.

7\. Configure firewall rules to allow only necessary ports.

8\. Use environment variables for all sensitive configuration.



\---



\## 14. DOCKER DEPLOYMENT



DOCKERFILE:



The project includes a Dockerfile that creates a containerized version of the FastAPI backend.



The Dockerfile uses Python 3.11 slim as the base image. It installs system dependencies, copies the requirements file, installs Python packages, copies application code, exposes port 8000, and runs the uvicorn server.



BUILDING THE DOCKER IMAGE:



docker build -t hiresense-ai .



This command builds the Docker image with the tag hiresense-ai. The build process may take several minutes as it installs all dependencies.



RUNNING THE CONTAINER:



docker run -p 8000:8000 -e SECRET\_KEY=your-secret-key hiresense-ai



This maps port 8000 from the container to port 8000 on your host machine.



DOCKER COMPOSE (OPTIONAL):



For running both backend and frontend together, create a docker-compose.yml file:



version: '3.8'

services:

&#x20; api:

&#x20;   build: .

&#x20;   ports:

&#x20;     - "8000:8000"

&#x20;   environment:

&#x20;     - SECRET\_KEY=your-secret-key

&#x20;   volumes:

&#x20;     - ./service-account-key.json:/app/service-account-key.json



Run with: docker-compose up



\---



\## 15. GOOGLE CLOUD DEPLOYMENT



PREREQUISITES:



Install Google Cloud SDK from cloud.google.com/sdk.

Authenticate with your GCP account.



STEP 1: CONFIGURE GCP PROJECT



gcloud config set project hiresense-ai-resumes

gcloud auth login



STEP 2: ENABLE REQUIRED APIS



gcloud services enable run.googleapis.com

gcloud services enable artifactregistry.googleapis.com

gcloud services enable cloudbuild.googleapis.com



STEP 3: CREATE ARTIFACT REGISTRY



gcloud artifacts repositories create hiresense-repo --repository-format=docker --location=us-central1



STEP 4: BUILD AND PUSH IMAGE



gcloud builds submit --tag us-central1-docker.pkg.dev/hiresense-ai-resumes/hiresense-repo/api:latest



STEP 5: DEPLOY TO CLOUD RUN



gcloud run deploy hiresense-api --image us-central1-docker.pkg.dev/hiresense-ai-resumes/hiresense-repo/api:latest --platform managed --region us-central1 --allow-unauthenticated --set-env-vars SECRET\_KEY=your-production-secret-key



STEP 6: GET DEPLOYMENT URL



After deployment, Cloud Run will provide a URL like https://hiresense-api-xxxxx-uc.a.run.app. Update the API\_BASE\_URL in your Streamlit app to use this URL.



STREAMLIT CLOUD DEPLOYMENT:



For the frontend, use Streamlit Cloud for free hosting.



1\. Push your code to GitHub.

2\. Go to streamlit.io/cloud.

3\. Connect your GitHub account.

4\. Select the repository lonewolf1621/hiresense-ai.

5\. Set the main file path to streamlit\_app.py.

6\. Add environment variables in the Streamlit Cloud settings.

7\. Deploy.



\---



\## 16. ENVIRONMENT VARIABLES



All environment variables are listed below with their descriptions and default values.



FIREBASE\_PROJECT\_ID: The GCP project ID. Default: hiresense-ai-resumes

GCS\_BUCKET\_NAME: Cloud Storage bucket name. Default: hiresense-ai-resumes.appspot.com

SECRET\_KEY: JWT signing key. Must be changed for production. Default: your-secret-key-change-in-production

ALGORITHM: JWT algorithm. Default: HS256

ACCESS\_TOKEN\_EXPIRE\_MINUTES: Token expiration time in minutes. Default: 30

API\_BASE\_URL: Backend API URL for frontend. Default: http://localhost:8000/api

HOST: Server bind address. Default: 0.0.0.0

PORT: Server port. Default: 8000

DEBUG: Debug mode flag. Default: False



Generate a secure SECRET\_KEY:

python -c "import secrets; print(secrets.token\_urlsafe(32))"



\---



\## 17. SECURITY BEST PRACTICES



PASSWORD SECURITY:

All passwords are hashed using bcrypt before storage. Never log or print plain text passwords. Implement minimum password length of 8 characters. Consider adding password strength validation.



TOKEN SECURITY:

JWT tokens expire after 30 minutes. Use HTTPS in production to prevent token interception. Store tokens securely on the client side. Implement token refresh mechanism for long sessions.



API SECURITY:

CORS middleware is configured to allow all origins in development. Restrict CORS origins in production to your frontend domain only. Rate limit authentication endpoints to prevent brute force attacks. Validate and sanitize all user inputs.



DATA SECURITY:

Never commit service account keys to version control. Use environment variables for sensitive configuration. Encrypt data in transit using HTTPS. Enable encryption at rest in Cloud Storage and Firestore.



FIREBASE SECURITY:

Configure Firestore security rules to restrict access. Users should only read and write their own data. Service account should have minimum required permissions. Regularly rotate service account keys.



\---



\## 18. PERFORMANCE OPTIMIZATION



DATABASE OPTIMIZATION:

Create composite indexes for frequently used queries. Use pagination for large data sets (limit to 20 items per page). Cache frequently accessed data in memory. Use Firestore batch operations for multiple writes.



API OPTIMIZATION:

Enable GZIP compression for API responses. Use connection pooling for database connections. Implement response caching for static data. Use async/await for non-blocking operations.



FRONTEND OPTIMIZATION:

Store user data in Streamlit session state to reduce API calls. Use st.cache\_data decorator for expensive computations. Lazy load content that is not immediately visible. Minimize the number of API calls per page load.



SCRAPER OPTIMIZATION:

Cache job listings for a configurable period (default 1 hour). Use concurrent scraping with ThreadPoolExecutor. Implement retry logic with exponential backoff. Limit the number of pages scraped per source.



\---



\## 19. TROUBLESHOOTING



FIREBASE AUTHENTICATION ERROR:

Symptom: "Failed to initialize Firebase" or credential errors.

Solution: Verify service-account-key.json exists and contains valid credentials. Ensure the file path in firebase\_config.py matches the actual file location. Check that Firestore and Storage are enabled in the GCP console.



MODULE NOT FOUND ERROR:

Symptom: "ModuleNotFoundError: No module named 'app'" or similar.

Solution: Ensure virtual environment is activated. Run pip install -r requirements.txt. Verify Python version is 3.11 or higher. Make sure you are running commands from the project root directory.



PORT ALREADY IN USE:

Symptom: "Address already in use" when starting the server.

Solution for Windows: Run netstat -ano | findstr :8000 to find the process, then taskkill /PID {pid} /F to kill it. Alternatively, use a different port with --port 8001.



STREAMLIT NOT OPENING:

Symptom: Streamlit starts but browser does not open.

Solution: Manually navigate to http://localhost:8501 in your browser. Check if another Streamlit instance is already running. Clear browser cache and cookies.



DATABASE CONNECTION TIMEOUT:

Symptom: Firestore operations hang or timeout.

Solution: Check internet connection. Verify GCP project is active and not suspended. Ensure Cloud Firestore API is enabled. Check service account permissions.



CORS ERRORS:

Symptom: "Cross-Origin Request Blocked" in browser console.

Solution: CORS is configured in app/main.py. Verify the backend server is running. Check that API\_BASE\_URL in the frontend matches the backend URL.



RESUME UPLOAD FAILURE:

Symptom: "Failed to upload resume" error.

Solution: Check service account has Storage Object Admin permission. Verify the storage bucket exists and is accessible. Check file size is under 100 MB. Ensure file is in PDF or DOCX format.



WEB SCRAPER NOT RETURNING RESULTS:

Symptom: Job search returns empty results.

Solution: Check internet connection. The target website may have changed its HTML structure. The website may be blocking automated requests. Try adding longer delays between requests. Consider using Selenium for JavaScript-heavy sites.



JWT TOKEN ERRORS:

Symptom: "Token expired" or "Invalid token" errors.

Solution: Login again to get a fresh token. Verify SECRET\_KEY is the same in backend and frontend. Check system clock is synchronized. Ensure token format is "Bearer {token}" in Authorization header.



\---



\## 20. TESTING



RUNNING TESTS:



Install testing dependencies:

pip install pytest pytest-asyncio httpx



Run all tests:

pytest



Run specific test file:

pytest tests/test\_auth.py



Run with verbose output:

pytest -v



Run with coverage report:

pytest --cov=app tests/



MANUAL API TESTING:



Use the interactive API documentation at http://localhost:8000/docs to test endpoints manually. Click "Try it out" on any endpoint to send test requests.



Alternatively, use curl commands:



Test health check:

curl http://localhost:8000/health



Test registration:

curl -X POST http://localhost:8000/api/auth/register -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"test123","name":"Test User"}'



Test login:

curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"test123"}'



\---



\## 21. CONTRIBUTING



We welcome contributions from the community. Here is how to contribute.



CONTRIBUTION PROCESS:



1\. Fork the repository on GitHub.

2\. Clone your fork to your local machine.

3\. Create a new branch for your feature: git checkout -b feature/your-feature-name

4\. Make your changes and test thoroughly.

5\. Write or update tests for your changes.

6\. Commit your changes with a clear message: git commit -m "Add: description of your feature"

7\. Push to your fork: git push origin feature/your-feature-name

8\. Open a Pull Request on the original repository.



CODE STANDARDS:



Follow PEP 8 Python style guidelines. Use type hints for all function parameters and return values. Write docstrings for all classes and functions. Keep functions focused on a single responsibility. Use meaningful variable and function names. Maximum line length is 100 characters.



COMMIT MESSAGE FORMAT:



Use descriptive commit messages with a prefix:

\- Add: For new features

\- Fix: For bug fixes

\- Update: For modifications to existing features

\- Remove: For deleted code or features

\- Docs: For documentation changes

\- Refactor: For code restructuring

\- Test: For test additions or modifications



\---



\## 22. ROADMAP



COMPLETED (Version 1.0.0 - 29 June 2026):

User authentication with JWT tokens.

User profile management.

Resume upload to Google Cloud Storage.

Job search from Indeed, Naukri, and Internshala.

Application tracking with status management.

Firestore database integration.

Streamlit frontend with login dashboard.

FastAPI backend with RESTful API.

Docker containerization.



PLANNED (Version 1.1.0 - Q3 2026):

Resume parsing and text extraction.

Skill extraction from resumes.

Job-resume matching algorithm.

User analytics dashboard.

Email notifications for new jobs.



PLANNED (Version 2.0.0 - Q4 2026):

AI-powered resume optimization.

Interview preparation module.

Salary insights and market analysis.

LinkedIn profile integration.

Advanced analytics with charts.



PLANNED (Version 3.0.0 - 2027):

Mobile application for iOS and Android.

Company reviews integration.

Mentor network platform.

Career coaching features.

Batch processing for recruiters.

Real-time job alerts via push notifications.



\---



\## 23. FREQUENTLY ASKED QUESTIONS



Q: Is HireSense AI free to use?

A: Yes, it is open source and free under the MIT License.



Q: Is my resume data secure?

A: Yes, all files are stored in Google Cloud Storage with encryption. Only authenticated users can access their own data.



Q: How often are job listings updated?

A: Job listings are fetched in real-time when you search. Previously scraped jobs are stored in the database for quick access.



Q: Can I use this for commercial purposes?

A: Yes, the MIT License allows commercial use, modification, and distribution.



Q: What file formats are supported for resumes?

A: Currently PDF and DOCX formats are supported.



Q: Can I deploy this on my own server?

A: Yes, follow the deployment guide in section 13 through 15.



Q: What if a web scraper stops working?

A: Job portal websites may change their HTML structure. Open a GitHub issue and we will update the scraper.



Q: Can I add more job sources?

A: Yes, create a new scraper class following the existing pattern and add it to the search endpoint.



Q: How do I report a bug?

A: Open an issue on GitHub at https://github.com/lonewolf1621/hiresense-ai/issues with steps to reproduce.



Q: Can I contribute new features?

A: Yes, fork the repository and submit a pull request. See the contributing guidelines in section 21.



Q: What Python version is required?

A: Python 3.11 or higher is required for compatibility.



Q: Can I use a different database?

A: The application is designed for Firestore, but you can modify the service layer to use other databases.



\---



\## 24. VERSION HISTORY



Version 1.0.0 - Released 29 June 2026

Initial release with complete feature set.

User authentication and authorization.

Profile management system.

Resume upload and cloud storage.

Multi-source job search.

Application tracking.

Streamlit frontend.

FastAPI backend.

Firebase integration.

Docker support.

Comprehensive documentation.



Previous Development Commits:

Fix: Downgrade to Python 3.11 for Streamlit compatibility.

Major update: Universal Resume Optimizer with multi-field support, interview prep, and salary insights.

Fix: Embed field data directly in app, remove external dependencies.

Major upgrade: Universal career optimizer with multi-job comparison and resume upload.

Add Firebase integration, Firestore service, Cloud Storage, and web scrapers.



\---



\## 25. LICENSE



\## 25. LICENSE



HIRESENSE AI - Business Source License (BSL 1.1)



This software is free for non-commercial use only. You can:

✅ Use it personally

✅ Modify it

✅ Use it internally in your organization

✅ Learn and study the code

✅ Contribute improvements



You CANNOT:

❌ Sell this software

❌ Offer it as a paid service

❌ White-label and resell it

❌ Include it in commercial products

❌ Charge users for this software



COMMERCIAL LICENSE AVAILABLE:

If you want to use this commercially, you can purchase a Commercial License for $5,000 USD per year.



Contact: license@hiresense-ai.com



AUTOMATIC CONVERSION:

On 29 June 2030 (4 years from release), this license automatically converts to Apache License 2.0, making it fully open source with no restrictions.



Full License Text: See LICENSE file

\---



\## 26. CONTACT AND SUPPORT



Author: Vishal Reddy

GitHub: https://github.com/lonewolf1621

Repository: https://github.com/lonewolf1621/hiresense-ai

Issues: https://github.com/lonewolf1621/hiresense-ai/issues



For questions, bug reports, or feature requests, please open a GitHub issue.



\---



Project: HireSense AI

Version: 1.0.0

Release Date: 29 June 2026

Last Updated: 29 June 2026

Status: Production Ready

License: MIT

Author: Vishal Reddy

GitHub: https://github.com/lonewolf1621/hiresense-ai

