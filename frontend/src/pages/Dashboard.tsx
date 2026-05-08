/**
 * Protected dashboard page showing user profile and navigation.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, isLoading } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const [imgError, setImgError] = useState(false);

  console.log('[AUTH_FLOW] Dashboard mounted');
  console.log('[AUTH_FLOW] User:', user);

  useEffect(() => {
    console.log('[AUTH_FLOW] Dashboard useEffect - user changed:', user);
    console.log('[AUTH_FLOW] profile_image URL:', user?.profile_image);
  }, [user]);

  const handleLogout = async () => {
    console.log('[AUTH_FLOW] Logout clicked');
    await logout();
  };

  // Generate initials for avatar fallback
  const getInitials = () => {
    const first = user?.first_name?.[0] || '';
    const last = user?.last_name?.[0] || '';
    return (first + last).toUpperCase() || '?';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">DigiAuth Dashboard</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Profile Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="flex items-center space-x-2 focus:outline-none"
                >
                  {user?.profile_image && !imgError ? (
                    <img
                      src={user.profile_image}
                      alt="Profile"
                      className="h-8 w-8 rounded-full object-cover"
                      onError={(e) => {
                        console.error('[AUTH_FLOW] Profile image failed to load:', user.profile_image);
                        setImgError(true);
                      }}
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-sm">
                      {getInitials()}
                    </div>
                  )}
                  <span className="text-sm font-medium text-gray-700">
                    {user?.first_name} {user?.last_name}
                  </span>
                </button>

                {showMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10">
                    <button
                      onClick={() => {
                        navigate('/update-password');
                        setShowMenu(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Change Password
                    </button>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h2>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-500">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-500">Status</label>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user?.is_email_verified 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {user?.is_email_verified ? 'Verified' : 'Pending'}
                  </span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-500">First Name</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.first_name}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-500">Last Name</label>
                  <p className="mt-1 text-sm text-gray-900">{user?.last_name}</p>
                </div>
              </div>

              {/* Profile Image Section */}
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-500">Profile Image</label>
                <div className="mt-2">
                  {user?.profile_image && !imgError ? (
                    <div className="relative">
                      <img
                        src={user.profile_image}
                        alt="Profile"
                        className="h-32 w-32 rounded-lg object-cover border border-gray-200"
                        
                      />
                     
                    </div>
                  ) : (
                    <div className="h-32 w-32 rounded-lg bg-gray-200 flex items-center justify-center">
                      <span className="text-gray-400 text-4xl">{getInitials()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* API Documentation Card */}
          <div className="mt-6 bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-2">API Documentation</h2>
              <p className="text-sm text-gray-600 mb-4">
                Explore the API endpoints using Swagger UI.
              </p>
              <a
                href="http://localhost:8000/swagger/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
              >
                Open Swagger Docs
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;