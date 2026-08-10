import { createContext, useContext, useState, useEffect } from 'react';
import {
  getCurrentUser,
  loginUser as apiLoginUser,
  registerUser as apiRegisterUser,
  logoutUser as apiLogoutUser,
  checkUsernameAvailability as apiCheckUsernameAvailability,
} from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const u = await getCurrentUser();
      setUser(u);
      return u;
    } catch {
      setUser(null);
      return null;
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function initAuth() {
      try {
        const u = await getCurrentUser();
        if (isMounted) setUser(u);
      } catch {
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    initAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (identifier, password) => {
    const u = await apiLoginUser({ identifier, password });
    setUser(u);
    return u;
  };

  const register = async (fullName, username, email, password) => {
    const u = await apiRegisterUser({
      full_name: fullName,
      username,
      email,
      password,
    });
    setUser(u);
    return u;
  };

  const logout = async () => {
    try {
      await apiLogoutUser();
    } catch (err) {
      console.warn('Logout request error:', err);
    } finally {
      setUser(null);
    }
  };

  const checkUsernameAvailability = async (username) => {
    return apiCheckUsernameAvailability(username);
  };

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
    refreshUser,
    checkUsernameAvailability,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
