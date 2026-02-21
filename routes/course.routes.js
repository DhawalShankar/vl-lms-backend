import express from 'express';
import {
  getCourses,
  getCourse,
  createCourse,
  updateCourse,
  deleteCourse,
  enrollCourse,
  getMyCourses,
  getInstructorCourses, // ✅ NEW
} from '../controllers/course.controller.js';
import { protect, restrictTo } from '../middleware/auth.middleware.js';

const router = express.Router();

// ── Public ────────────────────────────────────────────────────────────────────
router.get('/', getCourses);

// ── Named routes — MUST come before /:id ─────────────────────────────────────
// ⚠️  Express matches routes top-to-bottom. If /:id is defined first,
//     it will swallow "instructor" and "user" as id params → Mongoose cast error.

// Student: apne enrolled courses
router.get('/user/enrolled', protect, getMyCourses);

// ✅ NEW: Instructor: apne saare courses (drafts + published)
router.get('/instructor/mine', protect, restrictTo('instructor', 'admin'), getInstructorCourses);

// ── Instructor / Admin mutations ──────────────────────────────────────────────
router.post('/', protect, restrictTo('instructor', 'admin'), createCourse);
router.put('/:id', protect, restrictTo('instructor', 'admin'), updateCourse);
router.delete('/:id', protect, restrictTo('instructor', 'admin'), deleteCourse);

// ── Enrollment ────────────────────────────────────────────────────────────────
router.post('/:id/enroll', protect, enrollCourse);

// ── Single course — LAST so it doesn't eat named routes above ─────────────────
router.get('/:id', getCourse);

export default router;