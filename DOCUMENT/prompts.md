# Password Reset Walkthrough Bot

## Project Goal

Develop a production-ready AI-powered Password Reset Walkthrough Bot that assists users in securely recovering access to their accounts through a guided password reset process.

The system should combine secure authentication practices, OTP verification, AI-assisted risk assessment, user-friendly walkthrough guidance, and modern web technologies.

---

## Core Requirements

Build a complete full-stack application with:

### Authentication Module

* User Registration
* Secure Login
* Password Hashing
* Session Management
* Logout Functionality

### Password Recovery Module

* Forgot Password Workflow
* OTP Generation
* OTP Verification
* OTP Expiration Handling
* Secure Password Reset

### Walkthrough Assistant

* Step-by-step guidance during recovery
* Clear instructions for users
* Progress tracking
* Error handling and recovery suggestions
* User-friendly conversational workflow

### AI Risk Analysis Engine

* Analyze password reset requests
* Calculate risk score
* Classify requests as:

  * SAFE
  * MEDIUM RISK
  * HIGH RISK
* Provide recommendations based on risk level

### Dashboard

* User profile information
* Account management
* Recovery history
* Security status display

---

## Technical Stack

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript

### Backend

* Python
* FastAPI
* Uvicorn

### Database

* SQLite

### Security

* Password Hashing
* OTP Verification
* Session Protection
* Input Validation

---

## Functional Workflow

1. User registers an account.
2. User logs into the system.
3. User forgets password.
4. User initiates password recovery.
5. System generates OTP.
6. OTP is sent to registered email.
7. Walkthrough Bot guides user through verification steps.
8. AI engine evaluates request risk.
9. OTP validation is performed.
10. User creates a new password.
11. Password is securely updated.
12. User regains account access.

---

## AI Walkthrough Behavior

The bot should:

* Explain each recovery step.
* Provide contextual guidance.
* Detect invalid inputs.
* Suggest corrective actions.
* Reduce user confusion.
* Improve recovery success rate.

Example:

Step 1: Enter your registered email.

Step 2: Check your email inbox for the OTP.

Step 3: Enter the received OTP.

Step 4: Create a strong new password.

Step 5: Confirm password update.

Recovery completed successfully.

---

## Security Requirements

* Store passwords using hashing.
* Never store plain-text passwords.
* OTP must expire after a fixed duration.
* Prevent unauthorized password resets.
* Validate all user inputs.
* Protect against common web vulnerabilities.

---

## API Endpoints

### Authentication

* POST /register
* POST /login
* GET /logout

### Password Recovery

* POST /forgot-password
* POST /verify-otp
* POST /reset-password

### AI Analysis

* POST /risk-analysis

---

## Project Deliverables

* Complete source code
* Frontend pages
* Backend APIs
* Database integration
* Documentation
* Screenshots
* Deployment guide
* Architecture diagram
* Testing report

---

## Expected Outcome

The final system should function as a secure, intelligent, and user-friendly Password Reset Walkthrough Bot capable of assisting users through password recovery while maintaining strong security standards and demonstrating practical AI integration in authentication workflows.
