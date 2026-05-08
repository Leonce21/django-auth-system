/**
 * Password reset confirmation page.
 * Enter OTP and new password.
 */

import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ResetPassword: React.FC = () => {
  const location = useLocation();
  const { resetPassword } = useAuth();
  
  const [formData, setFormData] = useState({
    email: location.state?.email || '',
    otp_code: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.email) newErrors.email = 'Email is required';
    if (formData.otp_code.length !== 6) newErrors.otp_code = 'Enter 6-digit code';
    if (formData.new_password.length < 8) newErrors.new_password = 'Min 8 characters';
    if (formData.new_password !== formData.new_password_confirm) {
      newErrors.new_password_confirm = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setIsLoading(true);
    
    try {
      await resetPassword({
        email: formData.email,
        otp_code: formData.otp_code,
        new_password: formData.new_password,
        new_password_confirm: formData.new_password_confirm,
      });
      setIsSuccess(true);
    } catch (err: any) {
      setErrors({ general: err.response?.data?.error || 'Reset failed' });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
        <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md text-center">
          <div className="text-green-500 text-5xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-gray-900">Password Reset Successful</h2>
          <p className="mt-2 text-gray-600">
            Your password has been updated. You can now sign in with your new password.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-block w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
        <div>
          <h2 className="text-3xl font-bold text-center text-gray-900">Set New Password</h2>
          <p className="mt-2 text-center text-gray-600">
            Enter the OTP and your new password
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {errors.general && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {errors.general}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">OTP Code</label>
            <input
              type="text"
              name="otp_code"
              maxLength={6}
              value={formData.otp_code}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 text-center tracking-[0.5em] border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="______"
            />
            {errors.otp_code && <p className="text-red-500 text-sm mt-1">{errors.otp_code}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">New Password</label>
            <input
              type="password"
              name="new_password"
              value={formData.new_password}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.new_password && <p className="text-red-500 text-sm mt-1">{errors.new_password}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
            <input
              type="password"
              name="new_password_confirm"
              value={formData.new_password_confirm}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.new_password_confirm && <p className="text-red-500 text-sm mt-1">{errors.new_password_confirm}</p>}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600">
          <Link to="/forgot-password" className="font-medium text-blue-600 hover:text-blue-500">
            Resend OTP
          </Link>
        </p>
      </div>
    </div>
  );
};

export default ResetPassword;