import User from '../models/user.model.js';
import Course from '../models/course.model.js';

// ── Stats ─────────────────────────────────────────────────────────────────────
export const getStats = async (req, res, next) => {
  try {
    const [totalUsers, totalCourses, publishedCourses, activeUsers] = await Promise.all([
      User.countDocuments(),
      Course.countDocuments(),
      Course.countDocuments({ isPublished: true }),
      User.countDocuments({ isActive: true })
    ]);

    // Total enrollments = sum of enrolledCount across all courses
    const enrollmentAgg = await Course.aggregate([
      { $group: { _id: null, total: { $sum: '$enrolledCount' } } }
    ]);
    const totalEnrollments = enrollmentAgg[0]?.total || 0;

    // Recent activity — last 5 registered users
    const recentUsers = await User.find()
      .sort('-createdAt')
      .limit(5)
      .select('name email role createdAt');

    // Breakdown by role
    const roleBreakdown = await User.aggregate([
      { $group: { _id: '$role', count: { $sum: 1 } } }
    ]);

    res.status(200).json({
      success: true,
      data: {
        stats: {
          totalUsers,
          totalCourses,
          publishedCourses,
          draftCourses: totalCourses - publishedCourses,
          totalEnrollments,
          activeUsers,
          inactiveUsers: totalUsers - activeUsers
        },
        roleBreakdown,
        recentUsers
      }
    });
  } catch (err) { next(err); }
};

// ── Users ─────────────────────────────────────────────────────────────────────
export const getUsers = async (req, res, next) => {
  try {
    const { search, role, page = 1, limit = 50 } = req.query;
    const filter = {};
    if (role) filter.role = role;
    if (search) {
      filter.$or = [
        { name: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } }
      ];
    }

    const skip = (page - 1) * limit;
    const [users, total] = await Promise.all([
      User.find(filter)
        .select('-password -refreshToken -passwordResetToken -passwordResetExpiry')
        .sort('-createdAt')
        .skip(skip)
        .limit(Number(limit)),
      User.countDocuments(filter)
    ]);

    res.status(200).json({
      success: true,
      data: { users, pagination: { total, page: Number(page), limit: Number(limit) } }
    });
  } catch (err) { next(err); }
};

export const updateRole = async (req, res, next) => {
  try {
    const { role } = req.body;
    const allowed = ['student', 'instructor', 'admin'];
    if (!allowed.includes(role))
      return res.status(400).json({ success: false, message: `Invalid role. Must be one of: ${allowed.join(', ')}` });

    const user = await User.findByIdAndUpdate(
      req.params.id,
      { role },
      { new: true, runValidators: true }
    ).select('-password -refreshToken');

    if (!user) return res.status(404).json({ success: false, message: 'User not found.' });

    res.status(200).json({ success: true, message: `Role updated to "${role}".`, data: { user } });
  } catch (err) { next(err); }
};

// Unified toggle — works at /status (frontend) AND /toggle (legacy)
export const toggleStatus = async (req, res, next) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) return res.status(404).json({ success: false, message: 'User not found.' });

    user.isActive = !user.isActive;
    await user.save({ validateBeforeSave: false });

    res.status(200).json({
      success: true,
      message: `User ${user.isActive ? 'activated' : 'deactivated'} successfully.`,
      data: { isActive: user.isActive }
    });
  } catch (err) { next(err); }
};

export const deleteUser = async (req, res, next) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) return res.status(404).json({ success: false, message: 'User not found.' });

    // Prevent self-deletion
    if (req.params.id === req.user._id.toString())
      return res.status(400).json({ success: false, message: 'You cannot delete your own account.' });

    await user.deleteOne();
    res.status(200).json({ success: true, message: 'User deleted successfully.' });
  } catch (err) { next(err); }
};