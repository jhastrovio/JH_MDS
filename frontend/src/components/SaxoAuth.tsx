'use client';

import { useState, useEffect } from 'react';
import { Shield, ShieldCheck, AlertTriangle, ExternalLink } from 'lucide-react';

interface AuthStatus {
  authenticated: boolean;
  message: string;
}

interface AuthResponse {
  auth_url: string;
  state: string;
  message: string;
}

export default function SaxoAuth() {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL; // Define once

  // Check auth status on component mount
  useEffect(() => {
    checkAuthStatus();
    
    // Listen for postMessage from OAuth callback popup
    const handleMessage = (event: MessageEvent) => {
      // Verify origin for security (optional but recommended)
      if (event.origin !== apiBaseUrl) {
        return;
      }
      
      if (event.data.type === 'SAXO_AUTH_SUCCESS') {
        // Store the access token in localStorage
        localStorage.setItem('saxo_access_token', event.data.token);
        localStorage.setItem('saxo_token_expires_at', event.data.expires_at);
        
        // Update auth status
        setAuthStatus({
          authenticated: true,
          message: 'Authentication successful'
        });
        setLoading(false);
      } else if (event.data.type === 'SAXO_AUTH_ERROR') {
        setAuthStatus({
          authenticated: false,
          message: event.data.error || 'Authentication failed'
        });
        setLoading(false);
      }
    };
    
    window.addEventListener('message', handleMessage);
    
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [apiBaseUrl]);

  const checkAuthStatus = async () => {
    if (!apiBaseUrl) {
      console.error('NEXT_PUBLIC_API_BASE_URL is not defined');
      setAuthStatus({
        authenticated: false,
        message: 'API URL not configured. Please contact support.'
      });
      return;
    }
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/status`);
      if (!response.ok) { // Check if response is ok
        const errorText = await response.text();
        throw new Error(`Failed to fetch auth status: ${response.status} ${errorText}`);
      }
      const status: AuthStatus = await response.json();
      setAuthStatus(status);
    } catch (error) {
      console.error('Failed to check auth status:', error);
      setAuthStatus({
        authenticated: false,
        message: 'Failed to check authentication status'
      });
    }
  };

  const initiateAuth = async () => {
    if (!apiBaseUrl) {
      console.error('NEXT_PUBLIC_API_BASE_URL is not defined');
      setAuthStatus({
        authenticated: false,
        message: 'API URL not configured. Please contact support.'
      });
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/login`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Authentication initiation failed: ${response.status} ${errorText}`);
      }
      
      const authData: AuthResponse = await response.json();
      
      // Redirect to SaxoBank for authentication
      window.open(authData.auth_url, '_blank');
      
      // Start polling for auth completion
      const pollInterval = setInterval(async () => {
        // Check if component is still mounted or auth already happened to avoid errors
        if (authStatus?.authenticated) {
          clearInterval(pollInterval);
          setLoading(false);
          return;
        }
        await checkAuthStatus(); 
      }, 3000); // Polling interval
      
      // Stop polling after some time (e.g., 5 minutes)
      setTimeout(() => {
        clearInterval(pollInterval);
        if (!authStatus?.authenticated) { // Only set loading to false if not yet authenticated
          setLoading(false);
        }
      }, 300000); // Stop polling after 5 minutes
      
    } catch (error) {
      console.error('Authentication initiation failed:', error);
      setAuthStatus({
        authenticated: false,
        message: 'Failed to initiate authentication'
      });
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    if (!authStatus) return <Shield className="h-5 w-5 text-gray-400" />;
    if (authStatus.authenticated) return <ShieldCheck className="h-5 w-5 text-green-500" />;
    return <AlertTriangle className="h-5 w-5 text-red-500" />;
  };

  const getStatusColor = () => {
    if (!authStatus) return 'border-gray-300 bg-gray-50';
    if (authStatus.authenticated) return 'border-green-200 bg-green-50';
    return 'border-red-200 bg-red-50';
  };

  return (
    <div className={`rounded-lg border p-4 ${getStatusColor()}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-sm font-medium text-gray-900">
              SaxoBank Authentication
            </h3>
            <p className="text-xs text-gray-600">
              {authStatus?.message || 'Checking authentication status...'}
            </p>
          </div>
        </div>
        
        {!authStatus?.authenticated && (
          <button
            onClick={initiateAuth}
            disabled={loading}
            className="flex items-center space-x-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <ExternalLink className="h-4 w-4" />
            )}
            <span>{loading ? 'Authenticating...' : 'Authenticate'}</span>
          </button>
        )}
        
        {authStatus?.authenticated && (
          <button
            onClick={checkAuthStatus}
            className="rounded-md bg-gray-600 px-3 py-2 text-sm font-medium text-white hover:bg-gray-700"
          >
            Refresh Status
          </button>
        )}
      </div>
      
      {authStatus?.authenticated && (
        <div className="mt-3 rounded-md bg-green-100 p-3">
          <p className="text-xs text-green-800">
            ✅ Connected to SaxoBank Live API - Real market data is now available
          </p>
        </div>
      )}
    </div>
  );
} 