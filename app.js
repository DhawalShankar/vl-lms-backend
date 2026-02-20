import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import 'dotenv/config';

import connectDB from './config/database.js';
import authRoutes from './routes/auth.routes.js';
import courseRoutes from './routes/course.routes.js';

const app = express();

connectDB();

// Security
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: { success: false, message: 'Too many login attempts. Try again in 15 minutes.' }
});

app.use('/api/', limiter);
app.use(express.json({ limit: '10kb' }));

// Health check
app.get('/health', (req, res) =>
  res.json({ success: true, message: 'VartaLang API is running 🎓', timestamp: new Date() })
);

// Routes
app.use('/api/v1/auth', authLimiter, authRoutes);
app.use('/api/v1/courses', courseRoutes);

// 404
app.use('*', (req, res) =>
  res.status(404).json({ success: false, message: `Route ${req.originalUrl} not found` })
);

// Global error handler
app.use((err, req, res, next) => {
  console.error('Error:', err.message);
  res.status(err.statusCode || 500).json({
    success: false,
    message: err.message || 'Internal Server Error'
  });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`🚀 VartaLang server running on http://localhost:${PORT}`));

export default app;