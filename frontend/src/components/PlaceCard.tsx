import { Card, Row, Col, Button } from 'react-bootstrap';
import type { ReactElement } from 'react';
import { useNavigate } from 'react-router-dom';

type PlaceCardProps = {
  name: string;
  address?: string;
  id?: number;
  mapbox_id: string;
  mapbox_supported: boolean;
  notes?: string;
  start_time?: string;
  end_time?: string;
  image_url?: string;
  order?: number;
  onDelete?: (id: number, mapbox_id: string) => void;
  onPreviewComments?: (mapbox_id: string) => void;
  trip_id?: number;
  day_id?: number;
  isOwner: boolean;
};

export default function PlaceCard({
  id,
  name,
  address,
  notes,
  start_time,
  end_time,
  image_url,
  order,
  onDelete,
  trip_id,
  day_id,
  isOwner,
  mapbox_id,
  mapbox_supported,
  onPreviewComments,
}: PlaceCardProps): ReactElement {
  const navigate = useNavigate();

  // Format time from "HH:MM:SS" to "HH:MM"
  function fmtTime(t?: string) {
    if (!t) return '--';
    // Accept formats like HH:MM:SS or HH:MM or H:MM
    const m = t.match(/^(\d{1,2}):(\d{2})(:?\d{2})?$/);
    if (m) return `${m[1].padStart(2, '0')}:${m[2]}`;
    return t;
  }

  // Shorten address: only keep the first 2 parts
  const shortAddress = address
    ? address.split(',').slice(0, 2).join(',').trim()
    : '';

  return (
    <Card
      className="mb-3 border-0 shadow-sm rounded-3"
      style={{ overflow: 'hidden' }}
    >
      <Row className="g-0">
        {/* Image column: now takes up 4/10 of width */}
        <Col xs={4}>
          <Card.Img
            src={image_url || '/login_bg.jpg'}
            alt={name}
            role={onPreviewComments ? 'button' : undefined}
            tabIndex={onPreviewComments ? 0 : undefined}
            onClick={() =>
              onPreviewComments && mapbox_id && onPreviewComments(mapbox_id)
            }
            onKeyDown={(e: React.KeyboardEvent) => {
              if (!onPreviewComments || !mapbox_id) return;
              if (e.key === 'Enter' || e.key === ' ')
                onPreviewComments(mapbox_id);
            }}
            style={{
              height: 140,
              width: '100%',
              objectFit: 'cover',
              cursor: onPreviewComments ? 'pointer' : undefined,
            }}
          />
        </Col>

        {/* Content column: 6/10 width */}
        <Col xs={8}>
          <Card.Body className="d-flex flex-column h-100">
            <div className="d-flex justify-content-between align-items-start mb-2">
              <div className="d-flex align-items-center">
                <Card.Title
                  className="mb-0 fw-bold"
                  role={onPreviewComments ? 'button' : undefined}
                  tabIndex={onPreviewComments ? 0 : undefined}
                  onClick={() =>
                    onPreviewComments &&
                    mapbox_id &&
                    onPreviewComments(mapbox_id)
                  }
                  onKeyDown={(e: React.KeyboardEvent) => {
                    if (!onPreviewComments || !mapbox_id) return;
                    if (e.key === 'Enter' || e.key === ' ')
                      onPreviewComments(mapbox_id);
                  }}
                  style={{
                    cursor: onPreviewComments ? 'pointer' : undefined,
                    fontSize: 18,
                    lineHeight: 1.3,
                  }}
                >
                  {order ? `${order}. ` : ''}
                  {name}
                </Card.Title>

                {/* Warning icon if mapbox_supported = false */}
                {!mapbox_supported && (
                  <i
                    className="bi bi-exclamation-triangle-fill text-warning ms-2"
                    style={{
                      fontSize: 16,
                      cursor: 'pointer',
                      opacity: 0.9,
                    }}
                    title="This place is not supported or verified by the map system. Coordinates or routes may be inaccurate."
                  ></i>
                )}
              </div>
            </div>

            {/* Address */}
            {shortAddress && shortAddress !== '' && (
              <div className="text-secondary small mb-1 d-flex align-items-center">
                <i className="bi bi-geo-alt-fill me-1 text-muted"></i>
                <span style={{ lineHeight: 1.4 }}>{shortAddress}</span>
              </div>
            )}

            {/* Notes */}
            {notes && (
              <div
                className="text-muted small mb-2"
                style={{ lineHeight: 1.4 }}
              >
                {notes}
              </div>
            )}

            {/* Estimated Travel Time */}
            <div style={{ fontSize: 13 }} className="mb-3">
              <strong>Estimated Travel Time:</strong>
              <div>
                {fmtTime(start_time)} - {fmtTime(end_time)}
              </div>
            </div>

            {/* Action buttons */}
            {isOwner && (
              <div className="mt-auto d-flex justify-content-end gap-2">
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() =>
                    navigate(
                      `/trips/${trip_id}/days/${day_id}/places/${id}/edit-place`
                    )
                  }
                >
                  <i className="bi bi-pencil me-1"></i> Edit
                </Button>

                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={() =>
                    id && mapbox_id && onDelete && onDelete(id, mapbox_id)
                  }
                >
                  <i className="bi bi-trash me-1"></i> Delete
                </Button>
              </div>
            )}
          </Card.Body>
        </Col>
      </Row>
    </Card>
  );
}
