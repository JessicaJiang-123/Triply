import React from 'react';
import { Card, Button, Row, Col } from 'react-bootstrap';

interface TripCardProps {
  id: number;
  title: string;
  location: string;
  start_date: string;
  end_date: string;
  image_url?: string;
  onDelete: (id: number) => void;
  onShare: (id: number) => void;
  isOwner: boolean;
  ownerName: string;
}

const TripCard: React.FC<TripCardProps> = ({
  id,
  title,
  location,
  start_date,
  end_date,
  image_url,
  onDelete,
  onShare,
  isOwner,
  ownerName,
}) => {
  const handleDeleteClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDelete(id);
  };
  const handleShareClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onShare(id);
  };

  // Format location to be concise
  const formatLocation = (loc: string): string => {
    if (!loc) return '';
    const parts = loc
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    if (parts.length <= 2) return loc; // short enough
    return `${parts[0]}, ${parts[parts.length - 1]}`;
  };

  // Calculate days and nights
  const getDurationText = (start: string, end: string): string | null => {
    if (!start || !end) return null;
    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffDays =
      Math.round(
        (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
      ) + 1;
    if (diffDays <= 0) return null;
    const nights = diffDays - 1;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ${nights} night${nights > 1 ? 's' : ''}`;
  };

  const durationText = getDurationText(start_date, end_date);
  const dateRange = `${start_date} to ${end_date}`;

  return (
    <Card
      className="shadow-sm h-100 overflow-hidden"
      style={{ cursor: 'pointer' }}
    >
      <Row className="h-100">
        <Col xs={6} className="h-100" style={{ minHeight: '200px' }}>
          <Card.Img
            src={image_url}
            alt={title}
            className="h-100 w-100"
            style={{ objectFit: 'cover' }}
          />
        </Col>

        <Col xs={6} className="d-flex flex-column h-100">
          <Card.Body className="d-flex flex-column h-100">
            {/* --- Title --- */}
            <Card.Title
              as="h4"
              className="fw-bold text-dark mb-3"
              style={{ fontSize: '1.6rem', lineHeight: '1.2' }}
            >
              {title}
            </Card.Title>

            {/* --- Destination City Label --- */}
            <Card.Text className="fw-semibold text-secondary mb-1">
              Destination City:
            </Card.Text>

            {/* --- Location --- */}
            {location && (
              <Card.Text className="fs-6 text-secondary mb-3">
                <i className="bi bi-geo-fill me-2 text-primary"></i>
                {formatLocation(location)}
              </Card.Text>
            )}

            {/* --- Dates --- */}
            <Card.Text className="text-muted fs-6 mb-2">{dateRange}</Card.Text>

            {/* --- Duration --- */}
            {durationText && (
              <Card.Text className="text-muted small mb-4">
                {durationText}
              </Card.Text>
            )}

            {/* --- Start condition rendering logic --- */}
            {isOwner ? (
              // If owner, show all buttons
              <div className="mt-auto text-end d-flex gap-2 justify-content-end">
                <Button
                  variant="outline-primary"
                  size="sm"
                  onClick={handleShareClick}
                >
                  <i className="bi bi-share me-1"></i> Share
                </Button>
                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={handleDeleteClick}
                >
                  <i className="bi bi-trash me-1"></i> Delete
                </Button>
              </div>
            ) : (
              // If not owner, show "Shared by"
              <div className="mt-auto text-end">
                <small className="text-muted" style={{ fontSize: '0.9rem' }}>
                  <i className="bi bi-person-check-fill me-1"></i>
                  Shared by <strong>{ownerName}</strong>
                </small>
              </div>
            )}
            {/* --- End condition rendering logic --- */}
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
};

export default TripCard;
