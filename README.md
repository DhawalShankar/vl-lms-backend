# VartaLang LMS – Scalable Backend System with JWT & Role-Based Access

## Overview

VartaLang LMS is a production-ready backend system built using **Node.js, Express, and MongoDB**.

This project demonstrates:

* Secure authentication using JWT (Access + Refresh tokens)
* Role-Based Access Control (Student, Instructor, Admin)
* Modular REST API design
* Protected CRUD operations
* Course publishing workflow
* Enrollment system with tracking
* Production-level middleware (Helmet, Rate Limiting)
* Clean scalable architecture

This repository contains the **backend implementation**.
A minimal frontend is included separately to demonstrate API interaction.

---

## 🌐 Live Deployment

### Backend (Render)

[https://vl-lms-backend.onrender.com](https://vl-lms-backend.onrender.com)

### Frontend Demo (Vercel)

[https://vartalang-education.vercel.app](https://vartalang-education.vercel.app)

---

## Architecture Overview

The system follows a modular MVC structure:

* Controllers → Business logic
* Routes → API definitions
* Middleware → Authentication & Authorization
* Models → Mongoose schemas
* Config → Database connection
* Versioned APIs → `/api/v1`

The backend is designed for extensibility and production-readiness.

---

## Core Backend Features

### 1️⃣ Authentication System

* User Registration (Student / Instructor)
* Secure Login
* Password hashing using bcrypt (12 rounds)
* JWT Access Token (15 minutes)
* JWT Refresh Token (7 days)
* Refresh token rotation
* Logout with refresh token invalidation
* Protected route middleware
* Account deactivation support

---

### 2️⃣ Role-Based Access Control

Roles implemented:

* Student
* Instructor
* Admin (manually assigned in database)

Access enforcement is handled via middleware:

* `protect` → verifies JWT
* `restrictTo(...)` → enforces role authorization

Examples:

* Only instructors/admin can create courses
* Only course owner or admin can update/publish
* Only students can enroll
* Public can only see published courses

---

### 3️⃣ Course Management Workflow

Instructor Flow:

* Create course (draft mode by default)
* Update course
* Publish course (`isPublished = true`)
* View all own courses (draft + published)

Public Flow:

* View published courses only
* Pagination & filtering supported

Student Flow:

* Enroll in published courses
* View enrolled courses
* Enrollment count auto-increment

---

## API Structure

### Authentication

* POST `/api/v1/auth/register`
* POST `/api/v1/auth/login`
* GET `/api/v1/auth/me`
* POST `/api/v1/auth/logout`
* POST `/api/v1/auth/refresh`

### Public

* GET `/api/v1/courses`
* GET `/api/v1/courses/:id`

### Instructor (Protected)

* POST `/api/v1/courses`
* PUT `/api/v1/courses/:id`
* GET `/api/v1/courses/instructor/mine`

### Student (Protected)

* POST `/api/v1/courses/:id/enroll`
* GET `/api/v1/courses/user/enrolled`

---

## Database Design

### User Schema

* name
* email (unique)
* password (hashed)
* role (student / instructor / admin)
* enrolledCourses (reference)
* refreshToken
* isActive
* lastLogin
* timestamps

### Course Schema

* title
* description
* language
* level
* category
* duration
* modules
* tags
* instructor (reference)
* isPublished
* enrolledCount
* timestamps

Indexes:

* language + level
* instructor

---

## Security Practices

* Password hashing using bcrypt
* JWT signed with environment secrets
* Refresh tokens stored securely in database
* Rate limiting for brute force protection
* Helmet for secure HTTP headers
* CORS restricted to frontend origin
* No sensitive credentials stored in repository
* Admin role cannot self-register

---

## Scalability & Design Considerations

* Modular folder structure
* Versioned API (`/api/v1`)
* Middleware-based authorization
* Indexed database queries
* Stateless JWT authentication
* Easy integration with:

  * Redis caching
  * Logging systems
  * Docker deployment
  * Microservices architecture

The backend is structured to support horizontal scaling and feature expansion.

---

## End-to-End Tested Flows

Instructor:

1. Register/Login
2. Create course
3. Publish course
4. View own courses

Student:

1. Register/Login
2. Browse published courses
3. Enroll
4. View enrolled courses

All flows verified using Postman collection included in repository.

---

## API Documentation

Postman collection included:

`VL-LMS-API.postman_collection.json`

This includes complete authentication, instructor, student, and public flows.

---

## Local Setup

Clone repository:

```
git clone <repo-link>
```

Install dependencies:

```
npm install
```

Create `.env` file:

```
PORT=5000
MONGODB_URI=your_mongodb_uri
JWT_SECRET=your_secret
JWT_REFRESH_SECRET=your_refresh_secret
FRONTEND_URL=http://localhost:3000
```

Run server:

```
npm run dev
```

---

## Submission Context

This backend was developed as part of a Backend Developer Internship Assignment focused on:

* Secure API design
* Role-based access control
* Database modeling
* Authentication best practices
* Scalable system architecture

The frontend was implemented solely to demonstrate API interaction and protected route handling.

