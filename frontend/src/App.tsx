import { AuthContext } from './context/AuthContext';
import { useContext, type JSX } from 'react';
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import TravelPlanPage from './pages/TravelPlanPage';
import AddTripPage from './pages/AddTripPage';
import AddPlacePage from './pages/AddPlacePage';
import PlanDetailPage from './pages/PlanDetailPage';
import PublicTripLoader from './pages/PublicTripLoader';

export default function App() {
  // const { currentUser } = useContext(AuthContext);

  const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    const { currentUser, isLoading } = useContext(AuthContext);
    if (isLoading) {
      return <div>Loading User...</div>;
    }
    
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
        <Route path="/public/trip/:uuid" element={<PublicTripLoader />} />
        <Route
          path="/trips/:trip_id/days/:day_id"
          element={<PlanDetailPage />}
        />
        <Route
          path="/trips/:trip_id/days/:day_id/add-place"
          element={<AddPlacePage />}
        />
        <Route
          path="/trips/:trip_id/days/:day_id/places/:place_id/edit-place"
          element={<AddPlacePage />}
        />
        <Route
          path="/add-trip"
          element={
            <ProtectedRoute>
              <AddTripPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
