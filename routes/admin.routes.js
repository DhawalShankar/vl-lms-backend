import express from 'express';
import { protect, restrictTo } from '../middleware/auth.middleware.js';
import {
  getStats,
  getUsers,
  updateRole,
  toggleStatus,
  deleteUser
} from '../controllers/admin.controller.js';
import {
  getAdminCourses,
  deleteCourse
} from '../controllers/course.controller.js';

const router = express.Router();

// All admin routes require auth + admin role
router.use(protect, restrictTo('admin'));

// ── Stats ──────────────────────────────────────────────────────────────────────
router.get('/stats', getStats);

// ── Users ──────────────────────────────────────────────────────────────────────
router.get('/users', getUsers);
router.patch('/users/:id/role', updateRole);
router.patch('/users/:id/status', toggleStatus);   // ← frontend expects /status
router.patch('/users/:id/toggle', toggleStatus);   // ← legacy alias kept
router.delete('/users/:id', deleteUser);

// ── Courses (admin view — ALL courses, draft + published) ─────────────────────
router.get('/courses', getAdminCourses);
router.delete('/courses/:id', deleteCourse);

export default router;