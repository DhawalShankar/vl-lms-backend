// auth controller
import jwt from 'jsonwebtoken';
import User from '../models/user.model.js';

const generateTokens = (userId, role) => {
  const accessToken = jwt.sign(
    { id: userId, role },
    process.env.JWT_SECRET,
    { expiresIn: '15m' }
  );
  const refreshToken = jwt.sign(
    { id: userId },
    process.env.JWT_REFRESH_SECRET,
    { expiresIn: '7d' }
  );
  return { accessToken, refreshToken };
};

export const register = async (req, res, next) => {
  try {
    const { name, email, password, role } = req.body; // ✅ role destructure kiya

    if (!name || !email || !password)
      return res.status(400).json({ success: false, message: 'Name, email, and password are required.' });

    if (password.length < 8)
      return res.status(400).json({ success: false, message: 'Password must be at least 8 characters.' });

    if (!/(?=.*[A-Z])(?=.*\d)/.test(password))
      return res.status(400).json({ success: false, message: 'Password must contain at least one uppercase letter and one number.' });

    // ✅ Sirf allowed roles accept karo — admin kabhi bhi self-register nahi kar sakta
    const allowedRoles = ['student', 'instructor'];
    const assignedRole = allowedRoles.includes(role) ? role : 'student';

    const existing = await User.findOne({ email: email.toLowerCase() });
    if (existing)
      return res.status(409).json({ success: false, message: 'An account with this email already exists.' });

    const user = await User.create({ name, email, password, role: assignedRole }); // ✅ role pass kiya
    const { accessToken, refreshToken } = generateTokens(user._id, user.role);

    user.refreshToken = refreshToken;
    await user.save({ validateBeforeSave: false });

    console.log(`✅ New user registered: ${email} as ${user.role}`);

    res.status(201).json({
      success: true,
      message: 'Account created successfully!',
      data: { user, accessToken, refreshToken }
    });
  } catch (err) {
    next(err);
  }
};

export const login = async (req, res, next) => {
  try {
    const { email, password } = req.body;

    if (!email || !password)
      return res.status(400).json({ success: false, message: 'Email and password are required.' });

    const user = await User.findOne({ email: email.toLowerCase() }).select('+password');
    if (!user || !(await user.comparePassword(password)))
      return res.status(401).json({ success: false, message: 'Invalid email or password.' });

    if (!user.isActive)
      return res.status(403).json({ success: false, message: 'Account deactivated. Contact support.' });

    const { accessToken, refreshToken } = generateTokens(user._id, user.role);
    user.refreshToken = refreshToken;
    user.lastLogin = new Date();
    await user.save({ validateBeforeSave: false });

    console.log(`✅ User logged in: ${email} | role: ${user.role}`);

    res.status(200).json({
      success: true,
      message: 'Login successful!',
      data: { user, accessToken, refreshToken }
    });
  } catch (err) {
    next(err);
  }
};

export const refreshToken = async (req, res, next) => {
  try {
    const { refreshToken: token } = req.body;
    if (!token)
      return res.status(401).json({ success: false, message: 'Refresh token required.' });

    const decoded = jwt.verify(token, process.env.JWT_REFRESH_SECRET);
    const user = await User.findById(decoded.id).select('+refreshToken');

    if (!user || user.refreshToken !== token)
      return res.status(401).json({ success: false, message: 'Invalid or expired refresh token.' });

    const tokens = generateTokens(user._id, user.role);
    user.refreshToken = tokens.refreshToken;
    await user.save({ validateBeforeSave: false });

    res.status(200).json({ success: true, data: tokens });
  } catch (err) {
    if (err.name === 'TokenExpiredError')
      return res.status(401).json({ success: false, message: 'Session expired. Please login again.' });
    next(err);
  }
};

export const logout = async (req, res, next) => {
  try {
    await User.findByIdAndUpdate(req.user._id, { refreshToken: null });
    res.status(200).json({ success: true, message: 'Logged out successfully.' });
  } catch (err) {
    next(err);
  }
};

export const getMe = (req, res) => {
  res.status(200).json({ success: true, data: { user: req.user } });
};