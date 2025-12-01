import React, { useState, useEffect, useContext } from 'react';
import 'bootstrap-icons/font/bootstrap-icons.css';
import { Container, Button, Row, Col, Alert } from 'react-bootstrap';
import NavigationBar from '../components/NavigationBar';
import TripCard from '../components/TripCard';
import { useNavigate, Link } from 'react-router-dom';
import axiosInstance from '../api/axiosInstance';
import type { Trip } from '../types/tripTypes';
import ShareTripModal from '../components/ShareTripModal';
import { AuthContext } from '../context/AuthContext';

const TravelPlanPage: React.FC = () => {
  const navigate = useNavigate();

  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [sharingTripId, setSharingTripId] = useState<number | null>(null);
  const { currentUser } = useContext(AuthContext);
  const [selectedTab, setSelectedTab] = useState<'owned' | 'shared'>('owned');

  useEffect(() => {
    const fetchTrips = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axiosInstance.get('/api/plans/trips/');
        // console.log('Fetched trips:', response.data);
        setTrips(response.data);
      } catch {
        // console.error('Error fetching trips:', err);
        setError('Failed to load your trips. Are you logged in?');
      } finally {
        setLoading(false);
      }
    };

    fetchTrips();
  }, []);

  const handleAddTrip = () => {
    navigate('/add-trip');
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this trip?')) {
      try {
        await axiosInstance.delete(`/api/plans/trips/${id}/`);
        setTrips((prevTrips) => prevTrips.filter((trip) => trip.id !== id));
      } catch {
        // console.error('Failed to delete trip:', err);
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
          <div className="d-flex flex-column align-items-center gap-3">
            <h1 className="fw-bold mb-0">My Travel Plans</h1>
            <div className="btn-group" role="group" aria-label="Trip filters">
              <button
                type="button"
                className={`btn ${selectedTab === 'owned' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setSelectedTab('owned')}
              >
                Created by me
              </button>
              <button
                type="button"
                className={`btn ${selectedTab === 'shared' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setSelectedTab('shared')}
              >
                Shared with me
              </button>
            </div>
          </div>
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
              {trips
                .filter((trip) => {
                  if (!currentUser) return false;
                  const isOwner = currentUser.id === trip.owner.id;
                  return selectedTab === 'owned' ? isOwner : !isOwner;
                })
                .map((trip) => (
                  <Col key={trip.id}>
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
                        image_url={
                          trip.unsplash_image?.local_image_url || trip.image_url
                        }
                        isOwner={currentUser?.id === trip.owner.id ? true : false}
                        ownerName={trip.owner.username}
                      />
                    </Link>
                  </Col>
                ))}
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
