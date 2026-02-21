import User from '../models/user.model.js';

export const getUsers = async (req, res) => {
  const users = await User.find().select('-password -refreshToken');
  res.status(200).json({
    success: true,
    data: { users }
  });
};

export const updateRole = async (req, res) => {
  const { role } = req.body;
  const user = await User.findByIdAndUpdate(
    req.params.id,
    { role },
    { new: true }
  );
  res.status(200).json({ success: true, data: { user } });
};

export const toggleStatus = async (req, res) => {
  const user = await User.findById(req.params.id);
  user.isActive = !user.isActive;
  await user.save();
  res.status(200).json({ success: true });
};

export const deleteUser = async (req, res) => {
  await User.findByIdAndDelete(req.params.id);
  res.status(200).json({ success: true });
};