import React, { useState, useEffect } from 'react';
import 'bootstrap-icons/font/bootstrap-icons.css';
import { Container, Button, Row, Alert } from 'react-bootstrap';
import NavigationBar from '../components/NavigationBar';
import TripCard from '../components/TripCard';
import { useNavigate, Link } from 'react-router-dom';
import axiosInstance from '../api/axiosInstance';

interface ITrip {
  id: number;
  name: string;
  destination_city: string;
  start_date: string;
  end_date: string;
  imageURL?: string;
  firstDayId?: number;
}

const TravelPlanPage: React.FC = () => {
  const navigate = useNavigate();

  const [trips, setTrips] = useState<ITrip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrips = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axiosInstance.get('/api/plans/trips/');
        setTrips(response.data); 
      } catch (err) {
        console.error("Error fetching trips:", err);
        setError("Failed to load your trips. Are you logged in?");
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
            setTrips(prevTrips => prevTrips.filter(trip => trip.id !== id));

        } catch (err) {
            console.error("Failed to delete trip:", err);
            setError("Failed to delete the trip. Please try again.");
        }
    }
  };

  if (loading) {
    return (
      <>
        <NavigationBar />
        <Container>
          <h1 className="mb-5">Loading Travel Plans...</h1>
        </Container>
      </>
    );
  }

  if (error) {
    return (
      <>
        <NavigationBar />
        <Container>
          <Alert variant="danger">{error}</Alert>
        </Container>
      </>
    );
  }

  return (
    <>
      <NavigationBar />
      <Container className="pt-5">
        <h1 className="mb-5 text-center fw-bold">My Travel Plans</h1>

        <Row xs={1} md={2} className="g-5 mb-5">
          {trips.map((trip) => (
            <Link 
              key={trip.id} 
              to={`/trips/${trip.id}/days/${trip.firstDayId}`}
              className="col" 
              style={{ textDecoration: 'none' }}
            >
              <TripCard
                id={trip.id}
                onDelete={handleDelete}
                title={trip.name}
                location={trip.destination_city}
                dates={`${trip.start_date} to ${trip.end_date}`}
                imageUrl={trip.imageURL || '/images/default-placeholder.jpg'}
              />
            </Link>
          ))}
        </Row>

        <div className="text-center my-4">
          <Button className="fab-add-plan" onClick={handleAddTrip}>
            <i className="bi bi-plus-circle me-2"></i> Add new plan
          </Button>
        </div>
      </Container>
    </>
  );
};

export default TravelPlanPage;