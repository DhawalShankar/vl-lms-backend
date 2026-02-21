# VartaLang LMS – Scalable Backend System with JWT & Role-Based Access

## Overview

VartaLang LMS is a production-ready backend system built using **Node.js, Express, and MongoDB**.

This backend demonstrates secure authentication, role-based authorization, modular REST architecture, and scalable system design suitable for production deployment.

This repository contains the **complete backend implementation**.
A minimal frontend is deployed separately to demonstrate API interaction.

---

## 🌐 Live Deployment

### Backend (Render)

[https://vl-lms-backend.onrender.com](https://vl-lms-backend.onrender.com)

Base API URL:
`https://vl-lms-backend.onrender.com/api/v1`

### Frontend Demo (Vercel)

[https://vartalang-education.vercel.app](https://vartalang-education.vercel.app)

---

## Architecture Overview

The system follows a modular MVC structure:

* **Controllers** → Business logic
* **Routes** → API definitions
* **Middleware** → Authentication & Authorization
* **Models** → Mongoose schemas
* **Config** → Database connection
* **Versioned APIs** → `/api/v1`

Designed for extensibility and production-readiness.

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

Authorization handled via middleware:

* `protect` → Verifies JWT
* `restrictTo(...)` → Enforces role-based access

Examples:

* Only instructors/admin can create courses
* Only course owner or admin can update/publish
* Only students can enroll
* Public can view only published courses
* Only admin can manage users

---

### 3️⃣ Course Management Workflow

**Instructor Flow**

* Create course (default: draft)
* Update course
* Publish course (`isPublished = true`)
* View own courses (draft + published)

**Public Flow**

* View published courses
* Pagination & filtering support

**Student Flow**

* Enroll in published courses
* View enrolled courses
* Enrollment count auto-increment

---

### 4️⃣ Admin Management Module

Admin-specific capabilities:

* View all registered users
* Update user roles (student/instructor/admin)
* Activate / Deactivate users
* Delete users
* View all platform courses
* Delete courses

Admin routes are protected via:

```
protect → restrictTo('admin')
```

---

## API Structure

### Authentication

* POST `/api/v1/auth/register`
* POST `/api/v1/auth/login`
* GET `/api/v1/auth/me`
* POST `/api/v1/auth/logout`
* POST `/api/v1/auth/refresh`

---

### Admin (Protected)

* GET `/api/v1/admin/users`
* PATCH `/api/v1/admin/users/:id/role`
* PATCH `/api/v1/admin/users/:id/toggle`
* DELETE `/api/v1/admin/users/:id`

---

### Public

* GET `/api/v1/courses`
* GET `/api/v1/courses/:id`

---

### Instructor (Protected)

* POST `/api/v1/courses`
* PUT `/api/v1/courses/:id`
* GET `/api/v1/courses/instructor/mine`

---

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
* enrolledCourses (reference to Course)
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

### Indexes

* language + level
* instructor

---

## Security Practices

* bcrypt password hashing (12 rounds)
* JWT signed with environment secrets
* Refresh token stored securely in DB
* Role-based middleware enforcement
* Helmet security headers
* Rate limiting (global + auth-specific)
* CORS restricted to frontend origin
* No credentials committed to repository
* Admin self-registration disabled

---

## Scalability & Design Considerations

* Modular architecture
* Versioned API (`/api/v1`)
* Stateless authentication
* Indexed database queries
* Separation of concerns
* Easily extendable to:

  * Redis caching
  * Centralized logging
  * Docker containerization
  * Microservices architecture

The backend is structured for horizontal scaling and future feature expansion.

---

## End-to-End Tested Flows

### Instructor

1. Register / Login
2. Create course
3. Publish course
4. View own courses

### Student

1. Register / Login
2. Browse published courses
3. Enroll
4. View enrolled courses

### Admin

1. Login
2. View all users
3. Update roles
4. Toggle user status
5. Delete users / courses

All flows verified via Postman collection.

---

## API Documentation

Postman collection included:

`VL-LMS-API.postman_collection.json`

Contains complete end-to-end test flow for:

* Authentication
* Instructor operations
* Student enrollment
* Admin management

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

* Secure REST API design
* Role-based access control
* Database modeling
* Authentication best practices
* Production-grade middleware
* Scalable system architecture

The frontend was implemented strictly to demonstrate API interaction and protected route behavior.

