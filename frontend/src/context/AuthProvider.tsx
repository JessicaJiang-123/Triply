import { useEffect, useState, type ReactNode } from 'react';
import axiosInstance from '../api/axiosInstance';
import { AuthContext, type User } from './AuthContext';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  // const [ready, setReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

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
        // setReady(true);
        setIsLoading(false);
      }
    };

    fetchUser();
  }, []);

  // TODO: Show a loading spinner on Login Page
  // if (!isLoading) {
  //   return <div>Loading...</div>;
  // }

  return (
    <AuthContext.Provider value={{ currentUser, setCurrentUser, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
