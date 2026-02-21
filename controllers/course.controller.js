import Course from '../models/course.model.js';
import User from '../models/user.model.js';

export const getCourses = async (req, res, next) => {
  try {
    const { language, level, category, page = 1, limit = 10 } = req.query;
    const filter = { isPublished: true };
    if (language) filter.language = language;
    if (level) filter.level = level;
    if (category) filter.category = category;

    const skip = (page - 1) * limit;
    const [courses, total] = await Promise.all([
      Course.find(filter).populate('instructor', 'name email').sort('-createdAt').skip(skip).limit(Number(limit)),
      Course.countDocuments(filter)
    ]);

    res.status(200).json({
      success: true,
      data: {
        courses,
        pagination: { total, page: Number(page), limit: Number(limit), pages: Math.ceil(total / limit) }
      }
    });
  } catch (err) { next(err); }
};

// ✅ NEW — instructor ke apne saare courses (drafts bhi)
export const getInstructorCourses = async (req, res, next) => {
  try {
    const courses = await Course.find({ instructor: req.user._id }).sort('-createdAt');
    res.status(200).json({ success: true, data: { courses } });
  } catch (err) { next(err); }
};

export const getCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id).populate('instructor', 'name email');
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });
    res.status(200).json({ success: true, data: { course } });
  } catch (err) { next(err); }
};

export const createCourse = async (req, res, next) => {
  try {
    const { title, description, language, level, category, duration, modules, tags } = req.body;
    if (!title || !language)
      return res.status(400).json({ success: false, message: 'Title and language are required.' });

    const course = await Course.create({
      title, description, language, level, category, duration, modules, tags,
      instructor: req.user._id
    });
    res.status(201).json({ success: true, message: 'Course created!', data: { course } });
  } catch (err) { next(err); }
};

export const updateCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });

    if (course.instructor.toString() !== req.user._id.toString() && req.user.role !== 'admin')
      return res.status(403).json({ success: false, message: 'Not authorized to update this course.' });

    const updated = await Course.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true });
    res.status(200).json({ success: true, message: 'Course updated!', data: { course: updated } });
  } catch (err) { next(err); }
};

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

export const enrollCourse = async (req, res, next) => {
  try {
    const course = await Course.findById(req.params.id);
    if (!course) return res.status(404).json({ success: false, message: 'Course not found.' });
    if (!course.isPublished)
      return res.status(400).json({ success: false, message: 'This course is not available yet.' });

    const user = await User.findById(req.user._id);
    if (user.enrolledCourses.includes(req.params.id))
      return res.status(400).json({ success: false, message: 'Already enrolled in this course.' });

    user.enrolledCourses.push(req.params.id);
    await user.save({ validateBeforeSave: false });
    await Course.findByIdAndUpdate(req.params.id, { $inc: { enrolledCount: 1 } });

    res.status(200).json({ success: true, message: `Successfully enrolled in "${course.title}"!` });
  } catch (err) { next(err); }
};

export const getMyCourses = async (req, res, next) => {
  try {
    const user = await User.findById(req.user._id).populate('enrolledCourses');
    res.status(200).json({ success: true, data: { courses: user.enrolledCourses } });
  } catch (err) { next(err); }
};