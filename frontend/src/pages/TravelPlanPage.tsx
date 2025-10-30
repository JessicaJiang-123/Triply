import NavigationBar from '../components/NavigationBar';
import Container from 'react-bootstrap/Container';

export default function TravelPlanPage() {
  return (
    <>
      <NavigationBar />
      <Container className="mt-4">
        <h3>Your Travel Plans</h3>
      </Container>
    </>
  );
}
