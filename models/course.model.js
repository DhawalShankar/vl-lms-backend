import mongoose from 'mongoose';

const courseSchema = new mongoose.Schema({
  title: {
    type: String,
    required: [true, 'Course title is required'],
    trim: true,
    minlength: [3, 'Title must be at least 3 characters'],
    maxlength: [100, 'Title cannot exceed 100 characters']
  },
  description: {
    type: String,
    trim: true,
    maxlength: [1000, 'Description cannot exceed 1000 characters']
  },
  language: {
    type: String,
    required: [true, 'Language is required'],
    enum: ['Hindi', 'English', 'Tamil', 'Telugu', 'Bengali', 'Marathi',
           'Gujarati', 'Kannada', 'Malayalam', 'Punjabi', 'Urdu', 'Other']
  },
  level: {
    type: String,
    enum: ['foundation', 'professional', 'mastery'],
    default: 'foundation'
  },
  category: {
    type: String,
    enum: ['grammar', 'vocabulary', 'pronunciation', 'conversation', 'exam-prep', 'cultural'],
    default: 'grammar'
  },
  duration: { type: String },
  modules: { type: Number, default: 0 },
  isPublished: { type: Boolean, default: false },
  enrolledCount: { type: Number, default: 0 },
  instructor: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  tags: [{ type: String, trim: true }]
}, {
  timestamps: true,
  toJSON: { versionKey: false }
});

courseSchema.index({ language: 1, level: 1 });
courseSchema.index({ instructor: 1 });

const Course = mongoose.model('Course', courseSchema);
export default Course;