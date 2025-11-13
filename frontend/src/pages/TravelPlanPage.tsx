import React, { useState, useEffect } from 'react';
import 'bootstrap-icons/font/bootstrap-icons.css';
import { Container, Button, Row, Alert } from 'react-bootstrap';
import NavigationBar from '../components/NavigationBar';
import TripCard from '../components/TripCard';
import { useNavigate, Link } from 'react-router-dom';
import axiosInstance from '../api/axiosInstance';
import type { CurrentUser, Trip } from '../types/tripTypes';
import ShareTripModal from '../components/ShareTripModal';

const TravelPlanPage: React.FC = () => {
  const navigate = useNavigate();

  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [sharingTripId, setSharingTripId] = useState<number | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // const response = await axiosInstance.get('/api/plans/trips/');
        const mePromise = axiosInstance.get<CurrentUser>('/api/auth/profile/');
        const tripsPromise = axiosInstance.get<Trip[]>('/api/plans/trips/');
        const [meResponse, tripsResponse] = await Promise.all([
          mePromise,
          tripsPromise,
        ]);
        if (meResponse.data.is_authenticated) {
            setCurrentUser(meResponse.data);
            setTrips(tripsResponse.data);
        } else {
            setError('User not authenticated. Please log in.');
        }
        // console.log('Fetched trips:', response.data);
        // setTrips(response.data);
      } catch (err) {
        console.error('Error fetching trips:', err);
        setError('Failed to load your trips. Are you logged in?');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleAddTrip = () => {
    navigate('/add-trip');
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this trip?')) {
      try {
        await axiosInstance.delete(`/api/plans/trips/${id}/`);
        setTrips((prevTrips) => prevTrips.filter((trip) => trip.id !== id));
      } catch (err) {
        console.error('Failed to delete trip:', err);
        setError('Failed to delete the trip. Please try again.');
      }
    }
  };

  const handleShare = (id: number) => {
    setSharingTripId(id);
    setShowShareModal(true);
  };

  if (loading) {
    return (
      <>
        <NavigationBar />
        <Container className="pt-5 text-center">
          <h1>Loading Travel Plans...</h1>
        </Container>
      </>
    );
  }

  if (error) {
    return (
      <>
        <NavigationBar />
        <Container className="pt-5">
          <Alert variant="danger">{error}</Alert>
        </Container>
      </>
    );
  }

  return (
    <>
      <NavigationBar />

      {/* Main Layout */}
      <div
        style={{
          height: 'calc(100vh - 64px)', // minus navbar height
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Fixed Header */}
        <div className="flex-shrink-0 text-center py-4">
          <h1 className="fw-bold mb-0">My Travel Plans</h1>
        </div>

        {/* Scrollable Trip Cards Area */}
        <div
          className="flex-grow-1 overflow-auto d-flex justify-content-center"
          style={{
            backgroundColor: '#fff',
            padding: '0 2rem 100px 2rem', // adds space left/right and bottom
          }}
        >
          <div style={{ width: '100%', maxWidth: '1200px' }}>
            <Row xs={1} md={2} className="g-5">
              {trips.map((trip) => {
                const isOwner = currentUser ? currentUser.id === trip.owner.id : false;
                return (
                  <Link
                    key={trip.id}
                    to={`/trips/${trip.id}/days/${trip.firstDayId}`}
                    className="col"
                    style={{ textDecoration: 'none' }}
                  >
                    <TripCard
                      id={trip.id}
                      onDelete={handleDelete}
                      onShare={handleShare}
                      title={trip.name}
                      location={trip.destination_city}
                      start_date={trip.start_date}
                      end_date={trip.end_date}
                      image_url={trip.image_url || '/login_bg.jpg'}
                      isOwner={isOwner}
                      ownerName={trip.owner.username}
                    />
                  </Link>
                );
              })}
            </Row>

            {trips.length === 0 && (
              <div className="text-center text-muted mt-5">
                You don't have any travel plans yet.
              </div>
            )}
          </div>
        </div>

        {/* Fixed Bottom Add Button */}
        <div
          className="p-3 border-top flex-shrink-0"
          style={{
            backgroundColor: '#fff',
            boxShadow: '0 -2px 8px rgba(0,0,0,0.05)',
            position: 'sticky',
            bottom: 0,
            zIndex: 10,
          }}
        >
          <div className="text-center">
            <Button
              className="d-flex align-items-center justify-content-center mx-auto px-4 py-2"
              variant="primary"
              onClick={handleAddTrip}
            >
              <i className="bi bi-plus-circle me-2 fs-5"></i>
              Add new plan
            </Button>
          </div>
        </div>
      </div>
      <ShareTripModal
        show={showShareModal}
        onHide={() => setShowShareModal(false)}
        tripId={sharingTripId}
      />
    </>
  );
};

export default TravelPlanPage;
