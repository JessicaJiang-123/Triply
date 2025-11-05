import { Card, Row, Col } from 'react-bootstrap';
import type { ReactElement } from 'react';

type PlaceCardProps = {
  name: string;
  notes?: string;
  start_time?: string;
  end_time?: string;
  image_url?: string;
  order?: number;
};

export default function PlaceCard({
  name,
  notes,
  start_time,
  end_time,
  image_url,
  order,
}: PlaceCardProps): ReactElement {
  function fmtTime(t?: string) {
    if (!t) return '--';
    // Accept formats like HH:MM:SS or HH:MM or H:MM
    const m = t.match(/^(\d{1,2}):(\d{2})(:?\d{2})?$/);
    if (m) return `${m[1].padStart(2, '0')}:${m[2]}`;
    return t;
  }
  return (
    <Card className="mb-3 border-0" style={{ boxShadow: 'none' }}>
      <Row className="g-0">
        <Col xs={5}>
          <Card.Img
            src={image_url || ''}
            alt={name}
            style={{ height: 120, objectFit: 'cover', borderRadius: 8 }}
          />
        </Col>
        <Col xs={7}>
          <Card.Body>
            <div className="d-flex justify-content-between align-items-start">
              <Card.Title className="mb-1" style={{ fontSize: 16 }}>
                {order ? `${order}. ` : ''}
                {name}
              </Card.Title>
            </div>
            {notes && <div className="text-muted small mb-2">{notes}</div>}
            <div style={{ fontSize: 13 }}>
              <strong>Estimated Travel Time:</strong>
              <div>
                {fmtTime(start_time)} - {fmtTime(end_time)}
              </div>
            </div>
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
}
