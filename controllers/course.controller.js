import Course from '../models/course.model.js';
import User from '../models/user.model.js';

// ── Public: Browse published courses ─────────────────────────────────────────
export const getCourses = async (req, res, next) => {
  try {
    const { language, level, category, search, page = 1, limit = 12 } = req.query;
    const filter = { isPublished: true };
    if (language) filter.language = language;
    if (level) filter.level = level;
    if (category) filter.category = category;
    if (search) filter.title = { $regex: search, $options: 'i' };

    const skip = (page - 1) * limit;
    const [courses, total] = await Promise.all([
      Course.find(filter)
        .populate('instructor', 'name email')
        .sort('-createdAt')
        .skip(skip)
        .limit(Number(limit)),
      Course.countDocuments(filter)
    ]);

    res.status(200).json({
      success: true,
      data: {
        courses,
        pagination: {
          total,
          page: Number(page),
          limit: Number(limit),
          pages: Math.ceil(total / limit)
        }
      }
    });
  } catch (err) { next(err); }
};

// ── Instructor: own courses (drafts + published) ──────────────────────────────
export const getInstructorCourses = async (req, res, next) => {
  try {
    const courses = await Course.find({ instructor: req.user._id }).sort('-createdAt');
    res.status(200).json({ success: true, data: { courses } });
  } catch (err) { next(err); }
};

// ── Admin: ALL courses (no isPublished filter) ────────────────────────────────
export const getAdminCourses = async (req, res, next) => {
  try {
    const { search, language, level, page = 1, limit = 50 } = req.query;
    const filter = {};
    if (language) filter.language = language;
    if (level) filter.level = level;
    if (search) filter.title = { $regex: search, $options: 'i' };

    const skip = (page - 1) * limit;
    const [courses, total] = await Promise.all([
      Course.find(filter)
        .populate('instructor', 'name email')
        .sort('-createdAt')
        .skip(skip)
        .limit(Number(limit)),
      Course.countDocuments(filter)
    ]);

    res.status(200).json({
      success: true,
      data: {
        courses,
        pagination: {
          total,
          page: Number(page),
          limit: Number(limit),
          pages: Math.ceil(total / limit)
        }
      }
    });
  } catch (err) { next(err); }
};

// ── Public: Single course ─────────────────────────────────────────────────────
export const getCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id).populate('instructor', 'name email');
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });
    res.status(200).json({ success: true, data: { course } });
  } catch (err) { next(err); }
};

// ── Instructor/Admin: Create course ──────────────────────────────────────────
export const createCourse = async (req, res, next) => {
  try {
    const { title, description, language, level, category, duration, modules, tags, resources, thumbnail, isPublished } = req.body;
    if (!title || !language)
      return res.status(400).json({ success: false, message: 'Title and language are required.' });

    const course = await Course.create({
      title, description, language, level, category, duration,
      modules: modules || (resources ? resources.length : 0),
      tags, resources, thumbnail, instructor: req.user._id,
      isPublished: isPublished || false
    });

    res.status(201).json({ success: true, message: 'Course created!', data: { course } });
  } catch (err) { next(err); }
};

// ── Instructor/Admin: Update course (including resources) ─────────────────────
export const updateCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });

    if (course.instructor.toString() !== req.user._id.toString() && req.user.role !== 'admin')
      return res.status(403).json({ success: false, message: 'Not authorized to update this course.' });

    // Auto-sync modules count from resources if resources are provided
    const updates = { ...req.body };
    if (updates.resources && Array.isArray(updates.resources)) {
      updates.modules = updates.modules ?? updates.resources.length;
    }

    const updated = await Course.findByIdAndUpdate(req.params.id, updates, { new: true, runValidators: true })
      .populate('instructor', 'name email');

    res.status(200).json({ success: true, message: 'Course updated!', data: { course: updated } });
  } catch (err) { next(err); }
};

// ── Instructor/Admin: Delete course ──────────────────────────────────────────
export const deleteCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });

    if (course.instructor.toString() !== req.user._id.toString() && req.user.role !== 'admin')
      return res.status(403).json({ success: false, message: 'Not authorized to delete this course.' });

    await course.deleteOne();
    res.status(200).json({ success: true, message: 'Course deleted successfully.' });
  } catch (err) { next(err); }
};

// ── Student: Enroll in course ─────────────────────────────────────────────────
export const enrollCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });
    if (!course.isPublished)
      return res.status(400).json({ success: false, message: 'This course is not available yet.' });

    const user = await User.findById(req.user._id);
    if (user.enrolledCourses.map(String).includes(req.params.id))
      return res.status(400).json({ success: false, message: 'Already enrolled in this course.' });

    user.enrolledCourses.push(req.params.id);
    await user.save({ validateBeforeSave: false });
    await Course.findByIdAndUpdate(req.params.id, { $inc: { enrolledCount: 1 } });

    res.status(200).json({ success: true, message: `Successfully enrolled in "${course.title}"!` });
  } catch (err) { next(err); }
};

// ── Student: View enrolled courses ───────────────────────────────────────────
export const getMyCourses = async (req, res, next) => {
  try {
    const user = await User.findById(req.user._id).populate({
      path: 'enrolledCourses',
      populate: { path: 'instructor', select: 'name email' }
    });
    res.status(200).json({ success: true, data: { courses: user.enrolledCourses } });
  } catch (err) { next(err); }
};

// ── Instructor: Add a resource to a course ────────────────────────────────────
export const addResource = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });

    if (course.instructor.toString() !== req.user._id.toString() && req.user.role !== 'admin')
      return res.status(403).json({ success: false, message: 'Not authorized.' });

    course.resources.push(req.body);
    course.modules = course.resources.length;
    await course.save();

    res.status(201).json({ success: true, message: 'Resource added!', data: { course } });
  } catch (err) { next(err); }
};

// ── Instructor: Delete a resource from a course ───────────────────────────────
export const deleteResource = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });

    if (course.instructor.toString() !== req.user._id.toString() && req.user.role !== 'admin')
      return res.status(403).json({ success: false, message: 'Not authorized.' });

    course.resources = course.resources.filter(r => r._id.toString() !== req.params.resourceId);
    course.modules = course.resources.length;
    await course.save();

    res.status(200).json({ success: true, message: 'Resource removed.', data: { course } });
  } catch (err) { next(err); }
};