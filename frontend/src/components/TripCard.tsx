import React from 'react';
import { Card, Button, Row, Col } from 'react-bootstrap';

// import { useNavigate } from 'react-router-dom';

interface TripCardProps {
  id: number;
  title: string;
  location: string;
  dates: string;
  imageUrl: string;
  onDelete: (id: number) => void;
}

const TripCard: React.FC<TripCardProps> = ({
  id,
  title,
  location,
  dates,
  imageUrl,
  onDelete,
}) => {
  // const navigate = useNavigate();

  // TODO: update navigation url to /trips/${trip_id}/days/${dayId}
  // const handleClick = () => navigate(`/trips/${id}`);

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDelete(id);
  };

  return (
    <Card
      className="shadow-sm"
      style={{ height: '300px', cursor: 'pointer' }}
    >
      <Row className="h-100">
        <Col md={6} className="h-100">
          <Card.Img
            src={imageUrl}
            alt={title}
            className="rounded-start h-100"
            style={{ objectFit: 'cover' }}
          />
        </Col>

        <Col md={6} className="h-100">
          <Card.Body className="d-flex flex-column h-100">
            <Card.Title as="h5" className="fs-4">
              {title}
            </Card.Title>
            <Card.Text className="fs-5 mb-2">{location}</Card.Text>
            <Card.Text className="text-muted fs-6 mb-2">{dates}</Card.Text>
            <div className="mt-auto text-end">
              <Button variant="outline-danger" size="sm" onClick={handleDeleteClick}>
                <i className="bi bi-trash me-1"></i> Delete
              </Button>
            </div>
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
};

export default TripCard;
