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
    <Card className="shadow-sm" style={{ height: '300px' }}>
        <Row className="h-100">
            <Col md={6} className="h-100">
                <Card.Img src={imageUrl} alt={title} className="rounded-start h-100" style={{ objectFit: 'cover' }} />
            </Col>

            <Col md={6} className="h-100"> 
                <Card.Body className="d-flex flex-column h-100"> 
                    <Card.Title as="h5" className="fs-4">{title}</Card.Title>
                    <Card.Text className="fs-5 mb-2">{location}</Card.Text>
                    <Card.Text className="text-muted fs-6 mb-2">{dates}</Card.Text>
                    <Card.Text className="text-muted fs-6 mb-2">{duration}</Card.Text>
                    <div className="mt-auto text-end">
                        <Button variant="outline-danger" size="sm">
                            🗑️ Delete
                        </Button>
                    </div>
                </Card.Body>
            </Col>
        </Row>
    </Card>
  );
};

export default TripCard;