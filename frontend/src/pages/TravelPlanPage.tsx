import React from 'react';
import 'bootstrap-icons/font/bootstrap-icons.css';
import { Container, Button, Row, Col } from 'react-bootstrap';
import NavigationBar from '../components/NavigationBar';
import TripCard from '../components/TripCard';
import { useNavigate } from 'react-router-dom';

// Use dummy data to show multiple TripCards
const mockTrips = [
  {
    id: 1,
    title: 'Paris Travel Plan',
    location: 'Paris, France',
    dates: '10.3 - 10.5',
    duration: '3 Days 2 Nights',
    imageUrl: '/images/paris.jpg',
  },
  {
    id: 2,
    title: 'Beijing Travel Plan',
    location: 'Beijing, China',
    dates: '8.3 - 8.6',
    duration: '4 Days 3 Nights',
    imageUrl: '/images/beijing.jpg',
  },
  {
    id: 3,
    title: 'NYC Travel Plan',
    location: 'New York, US',
    dates: '11.13 - 11.16',
    duration: '4 Days 3 Nights',
    imageUrl: '/images/newyork.jpg',
  },
];

const TravelPlanPage: React.FC = () => {
  const navigate = useNavigate();

  const handleAddTrip = () => {
    navigate('/add-trip');
  };

  return (
    <>
      <NavigationBar />
      <Container>
        <h1 className="mb-5">Travel Plan Page</h1>

        <Row xs={1} md={2} className="g-5 mb-5">
          {mockTrips.map((trip) => (
            <Col key={trip.id}>
              <TripCard
                id={trip.id}
                title={trip.title}
                location={trip.location}
                dates={trip.dates}
                duration={trip.duration}
                imageUrl={trip.imageUrl}
              />
            </Col>
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
