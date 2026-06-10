# 🔐 Password Reset Walkthrough Bot - Complete Development Prompts

## 📌 Master Project Prompt

Develop a complete AI-Powered Password Reset Walkthrough Bot that helps users securely recover their accounts.

The system must include:

* User Registration
* User Login
* Session Management
* OTP-Based Password Recovery
* AI Risk Assessment Engine
* Password Reset Functionality
* User Dashboard
* FastAPI Backend
* SQLite Database
* Responsive Frontend
* Deployment Ready Architecture

The project should be developed in 7 phases:

1. Authentication System
2. OTP Recovery Module
3. AI Risk Assessment Engine
4. Backend API Development
5. Frontend Integration
6. Testing & Validation
7. Deployment & Documentation

All code should be modular, secure, scalable, and production-ready.

---

# Phase 1 – Authentication System

Build the Authentication Module for the Password Reset Walkthrough Bot.

### Requirements

* User Registration
* User Login
* Password Hashing using bcrypt
* Session Management
* Logout Functionality
* SQLite Database Integration

### Frontend Pages

* register.html
* login.html
* dashboard.html

### Backend

* FastAPI
* SQLAlchemy
* SQLite

### Security Requirements

* Validate user inputs
* Prevent duplicate registrations
* Store hashed passwords only
* Protect user sessions

### Deliverables

* Authentication APIs
* Database Models
* Login System
* Registration System
* Dashboard Access Control

---

# Phase 2 – OTP Recovery Module

Extend the Authentication Module with a secure OTP-Based Password Recovery System.

### Requirements

* Forgot Password Workflow
* OTP Generation
* OTP Storage
* OTP Expiration Handling
* OTP Verification
* Password Reset Functionality

### Database Updates

* OTP Table
* Expiration Timestamp
* Verification Status

### Security

* OTP valid for 5 minutes
* Prevent OTP reuse
* Validate email ownership
* Secure password reset process

### Frontend Pages

* forgot_password.html
* verify_otp.html
* reset_password.html

### Deliverables

* OTP Service
* Recovery APIs
* Password Reset Workflow

---

# Phase 3 – AI Risk Assessment Engine

Develop an AI-Inspired Risk Assessment Engine for password recovery requests.

### Objectives

* Analyze recovery attempts
* Generate risk score
* Classify threat level

### Inputs

* Request frequency
* Recovery attempts
* Device information
* Session patterns

### Output Example

```json
{
  "risk_level": "SAFE",
  "risk_score": 100
}
```

### Risk Categories

* SAFE
* MEDIUM_RISK
* HIGH_RISK

### Deliverables

* risk_engine.py
* Scoring Algorithm
* Risk API Integration

---

# Phase 4 – Backend API Development

Develop the complete backend architecture using FastAPI.

### Authentication APIs

POST /register

POST /login

GET /logout

### Recovery APIs

POST /forgot-password

POST /verify-otp

POST /reset-password

### Risk APIs

POST /risk-analysis

### Requirements

* Pydantic Validation
* Structured JSON Responses
* Exception Handling
* Modular Routing
* Database Integration

### Architecture

backend/
├── routes/
├── services/
├── models/
├── database/
├── utils/
└── main.py

### Deliverables

* Fully Functional FastAPI Backend
* Modular API Structure
* Deployment Ready Backend

---

# Phase 5 – Frontend Integration

Develop a modern responsive frontend.

### Pages

* Login
* Registration
* Dashboard
* Forgot Password
* OTP Verification
* Password Reset

### Requirements

* Bootstrap 5
* Responsive Design
* API Integration
* Form Validation
* Error Handling
* Professional UI

### User Experience Goals

* Simple Navigation
* Guided Recovery Process
* Mobile Friendly Design
* Consistent Interface

### Deliverables

* Complete Frontend
* Backend Integration
* Responsive UI

---

# Phase 6 – Testing & Validation

Perform comprehensive testing.

### Authentication Testing

* Registration Testing
* Login Testing
* Logout Testing

### Recovery Testing

* OTP Generation Testing
* OTP Expiration Testing
* OTP Verification Testing
* Password Reset Testing

### Backend Testing

* API Testing
* Validation Testing
* Exception Handling Testing

### Security Testing

* Password Hash Verification
* Session Security
* Unauthorized Access Checks

### Deliverables

* test_report.md
* validation_report.md
* bug_report.md

---

# Phase 7 – Deployment & Documentation

Prepare the project for deployment and public release.

### Documentation

* README.md
* API Documentation
* User Manual
* Deployment Guide
* Architecture Diagram
* Workflow Diagram

### Deployment Platforms

* GitHub
* Render
* Vercel

### Requirements

* requirements.txt
* Environment Configuration
* Deployment Instructions

### Repository Structure

Password_Reset_Bot/
├── backend/
├── frontend/
├── database/
├── docs/
├── screenshots/
├── prompts/
├── README.md
└── requirements.txt

### Final Deliverables

* Production Ready Application
* Complete Documentation
* Deployment Guide
* Portfolio Ready Repository
* Recruiter Friendly Project Structure

---

## 🎯 Project Outcome

The Password Reset Walkthrough Bot demonstrates practical implementation of:

* Cybersecurity Principles
* Secure Authentication
* OTP Verification
* AI-Based Risk Assessment
* FastAPI Development
* Database Integration
* Full Stack Development
* Software Engineering Best Practices
* Deployment and Documentation

This project is designed to showcase industry-level development practices and real-world password recovery workflows.
