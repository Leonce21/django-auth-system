/**
 * Email verification page.
 * Users land here after registration to enter OTP code.
 */

import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const VerifyEmail: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { verifyEmail, resendOTP } = useAuth();
  
  // Get email from navigation state (passed from Register)
  const email = location.state?.email || '';
  
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);

  console.log('[AUTH_FLOW] VerifyEmail mounted');
  console.log('[AUTH_FLOW] Location state:', location.state);
  console.log('[AUTH_FLOW] Email from state:', email);

  // Countdown timer for resend button
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCanResend(true);
    }
  }, [resendTimer]);

  // Redirect if no email in state
  useEffect(() => {
    console.log('[AUTH_FLOW] Checking email in state:', email);
    if (!email) {
      console.log('[AUTH_FLOW] No email found, redirecting to /register');
      navigate('/register');
    }
  }, [email, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[AUTH_FLOW] Verify form submitted, OTP:', otpCode);
    
    if (otpCode.length !== 6) {
      console.log('[AUTH_FLOW] OTP validation failed: not 6 digits');
      setError('Please enter a valid 6-digit code');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      console.log('[AUTH_FLOW] Calling verifyEmail API...');
      await verifyEmail(email, otpCode);
      console.log('[AUTH_FLOW] Verify success, navigating to /dashboard');
      navigate('/dashboard', { replace: true });
      console.log('[AUTH_FLOW] Navigation to /dashboard triggered');
    } catch (err: any) {
      console.error('[AUTH_FLOW] Verify failed:', err);
      setError(err.response?.data?.error || 'Verification failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    console.log('[AUTH_FLOW] Resend OTP clicked');
    try {
      await resendOTP(email);
      setResendTimer(60);
      setCanResend(false);
      setError('');
      console.log('[AUTH_FLOW] OTP resent, timer reset');
    } catch (err: any) {
      console.error('[AUTH_FLOW] Resend failed:', err);
      setError(err.response?.data?.error || 'Failed to resend OTP');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
        <div>
          <h2 className="text-3xl font-bold text-center text-gray-900">Verify Your Email</h2>
          <p className="mt-2 text-center text-gray-600">
            We've sent a 6-digit code to<br />
            <span className="font-medium text-gray-900">{email}</span>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-center">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 text-center">
              Enter Verification Code
            </label>
            <input
              type="text"
              maxLength={6}
              value={otpCode}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, '');
                setOtpCode(value);
                setError('');
              }}
              className="mt-1 block w-full px-3 py-4 text-center text-2xl tracking-[0.5em] border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="______"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || otpCode.length !== 6}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isLoading ? 'Verifying...' : 'Verify Email'}
          </button>

          <div className="text-center">
            {canResend ? (
              <button
                type="button"
                onClick={handleResend}
                className="text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                Resend OTP
              </button>
            ) : (
              <p className="text-sm text-gray-500">
                Resend OTP in {resendTimer}s
              </p>
            )}
          </div>
        </form>

        <p className="text-center text-sm text-gray-600">
          Wrong email?{' '}
          <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
            Go back
          </Link>
        </p>
      </div>
    </div>
  );
};

export default VerifyEmail;