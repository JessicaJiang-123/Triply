import { createContext } from 'react';

interface User {
  username: string;
  email: string;
  picture: string;
  is_authenticated: boolean;
  id: number;
}

interface AuthContextType {
  currentUser: User | null;
  setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
  isLoading: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  currentUser: null,
  setCurrentUser: () => {},
  isLoading: true,
});

export type { User, AuthContextType };
