import { AuthContext } from './context/AuthContext';
import { useContext, type JSX } from 'react';
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import TravelPlanPage from './pages/TravelPlanPage';
import AddTripPage from './pages/AddTripPage';
import AddPlacePage from './pages/AddPlacePage';

export default function App() {
  const { currentUser } = useContext(AuthContext);

  const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    if (!currentUser) {
      return <Navigate to="/login" />;
    }
    return children;
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/trips" replace />} />
        <Route
          path="/trips"
          element={
            <ProtectedRoute>
              <TravelPlanPage />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/add-trip"
          element={
            <ProtectedRoute>
              <AddTripPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/trips/:trip_id/:date/add-place"
          element={
            <ProtectedRoute>
              <AddPlacePage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
