import express from 'express';
import {
  getCourses, getCourse, createCourse, updateCourse, deleteCourse, enrollCourse, getMyCourses
} from '../controllers/course.controller.js';
import { protect, restrictTo } from '../middleware/auth.middleware.js';

const router = express.Router();

// Public
router.get('/', getCourses);
router.get('/:id', getCourse);

// Protected — any logged in user
router.get('/user/enrolled', protect, getMyCourses);
router.post('/:id/enroll', protect, enrollCourse);

// Instructor / Admin only
router.post('/', protect, restrictTo('instructor', 'admin'), createCourse);
router.put('/:id', protect, restrictTo('instructor', 'admin'), updateCourse);
router.delete('/:id', protect, restrictTo('instructor', 'admin'), deleteCourse);

export default router;