import { createContext } from 'react';

interface User {
  username: string;
  email: string;
  picture: string;
  is_authenticated: boolean;
}

interface AuthContextType {
  currentUser: User | null;
  setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
}

export const AuthContext = createContext<AuthContextType>({
  currentUser: null,
  setCurrentUser: () => {},
});

export type { User, AuthContextType };
