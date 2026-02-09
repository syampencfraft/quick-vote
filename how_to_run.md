# Smart Secure E-Voting System - Setup Guide

This project is a Django-based E-Voting system with Face Recognition and OTP verification.

## Prerequisites

1. **Python 3.10+**: Make sure Python is installed and added to your PATH.
2. **C++ Compiler**: To install the `face-recognition` library (specifically `dlib`), you need Visual Studio C++ build tools installed on Windows.
   - [Download VS Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and select "Desktop development with C++".

## Setup Instructions

### 1. Create a Virtual Environment (Recommended)
Open your terminal in the project directory and run:
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

> [!TIP]
> **If you see "Failed building wheel for dlib":**
> You already have the library, but pip is trying to refresh it. Run these two commands:
> ```bash
> pip install face_recognition_models
> pip install face-recognition --no-deps
> ```

### 3. Database Migrations
Apply the initial migrations to set up your database schema:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create an Admin Account
To manage elections and view candidates, you need an admin account:
```bash
python manage.py createsuperuser
```
Follow the prompts to set a username, email, and password.

### 5. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## Project Workflow

1. **User Registration**:
   - Go to `/register`.
   - Fill in your details.
   - You will receive an OTP in the terminal (since `EMAIL_BACKEND` is set to console).

2. **OTP Verification**:
   - Enter the 6-digit OTP from the console to activate your account.

3. **Face Enrollment (Voters)**:
   - After logging in, voters must upload a clear face photo to complete their profile.
   - This photo will be used to verify your identity before you can vote.

4. **Admin Dashboard**:
   - Access `http://127.0.0.1:8000/admin` to manage:
     - Election details (dates, names).
     - Candidate lists.
     - User accounts.

5. **Voting**:
   - Once an election is active, log in as a voter and cast your vote!
