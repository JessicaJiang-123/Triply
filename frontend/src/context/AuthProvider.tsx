import { useEffect, useState, type ReactNode } from 'react';
import axiosInstance from '../api/axiosInstance';
import { AuthContext } from './AuthContext';
import type { CurrentUser } from '../types/tripTypes';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await axiosInstance.get('/api/user/profile/');
        if (response.data.is_authenticated) {
          setCurrentUser(response.data);
          console.log('User fetched:', response.data);
        } else {
          setCurrentUser(null);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setCurrentUser(null);
      } finally {
        setReady(true);
      }
    };

    fetchUser();
  }, []);

  // TODO: Show a loading spinner on Login Page
  if (!ready) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ currentUser, setCurrentUser }}>
      {children}
    </AuthContext.Provider>
  );
};
