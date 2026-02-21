import express from 'express';
import { protect, restrictTo } from '../middleware/auth.middleware.js';
import {
  getUsers,
  updateRole,
  toggleStatus,
  deleteUser
} from '../controllers/admin.controller.js';

const router = express.Router();

router.use(protect, restrictTo('admin'));

router.get('/users', getUsers);
router.patch('/users/:id/role', updateRole);
router.patch('/users/:id/toggle', toggleStatus);
router.delete('/users/:id', deleteUser);

export default router;