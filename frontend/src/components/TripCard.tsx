import React from 'react';
import { Card, Button, Row, Col } from 'react-bootstrap';

interface TripCardProps {
  title: string;
  location: string;
  dates: string;
  duration: string;
  imageUrl: string;
}

const TripCard: React.FC<TripCardProps> = ({ title, location, dates, duration, imageUrl }) => {
    return (
    <Card className="mb-3 shadow-sm">
      <Row className="g-0">
        
        <Col md={4}>
          <Card.Img src={imageUrl} alt={title} className="img-fluid rounded-start" style={{ height: '100%', objectFit: 'cover' }} />
        </Col>

        <Col md={8}>
          <Card.Body>
            <Card.Title as="h5">{title}</Card.Title>
            <Card.Text>{location}</Card.Text>
            <Card.Text>
              <small className="text-muted">{dates} • {duration}</small>
            </Card.Text>
            
            <Button variant="outline-danger" size="sm">
              🗑️
            </Button>
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
};

export default TripCard;