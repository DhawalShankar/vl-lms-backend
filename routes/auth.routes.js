import express from 'express';
import { register, login, refreshToken, logout, getMe } from '../controllers/auth.controller.js';
import { protect } from '../middleware/auth.middleware.js';

const router = express.Router();

// Public
router.post('/register', register);
router.post('/login', login);
router.post('/refresh', refreshToken);

// Protected
router.post('/logout', protect, logout);
router.get('/me', protect, getMe);

export default router;