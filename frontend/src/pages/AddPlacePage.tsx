import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Form,
  Button,
  Card,
  Container,
  Row,
  Col,
  Alert,
} from 'react-bootstrap';
import { SearchBox } from '@mapbox/search-js-react';
import 'bootstrap-icons/font/bootstrap-icons.css';
import NavigationBar from '../components/NavigationBar';
import axiosInstance from '../api/axiosInstance';
import { fetchPlaceImage } from '../utils/fetchPlaceImage';

export default function AddPlacePage() {
  const { trip_id, date } = useParams<{ trip_id: string; date: string }>();

  const [formData, setFormData] = useState({
    place_name: '',
    place_address: '',
    start_time: '',
    end_time: '',
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [isPlaceInvalid, setIsPlaceInvalid] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrorMsg(null);
  };

  // Handle Mapbox place selection
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMapboxSelect = (event: any) => {
    setIsPlaceInvalid(false);
    const feature = event.features[0];

    const name = feature.properties?.name || '';
    const address = feature.properties?.full_address || '';

    setFormData((prev) => ({
      ...prev,
      place_name: name,
      place_address: address,
    }));
  };

  const handleMapboxClear = () => {
    setFormData((prev) => ({
      ...prev,
      place_name: '',
      place_address: '',
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate place field
    if (!formData.place_name.trim()) {
      setIsPlaceInvalid(true);
      return;
    }

    // Validate time
    if (formData.end_time < formData.start_time) {
      setErrorMsg('End time must be after start time.');
      return;
    }

    setSubmitting(true);

    try {
      // Fetch place image URL based on place name
      const imageUrl = await fetchPlaceImage(formData.place_name);
      console.log('Fetched image URL:', imageUrl);

      const payload = {
        ...formData,
        date,
        trip: trip_id,
        imageURL: imageUrl,
      };
      console.log('Submitting place:', payload);
      const response = await axiosInstance.post('/api/places/', payload);
      console.log('Place added: ', response.data);

      // Navigate back to the trip's current date view
      navigate(`/trips/${trip_id}/${date}`);
    } catch (error) {
      console.error('Failed to add place:', error);
      setErrorMsg(
        error instanceof Error ? error.message : 'Failed to add place.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <NavigationBar />
      <Container className="my-5 d-flex justify-content-center">
        <Card
          className="p-4 shadow-lg w-100"
          style={{ maxWidth: '720px', minWidth: '360px' }}
        >
          <Card.Body>
            <h2 className="text-center mb-4 text-primary fw-bold d-flex align-items-center justify-content-center">
              <i className="bi bi-geo-alt me-2"></i>
              Add New Travel Place for {date}
            </h2>

            <Form onSubmit={handleSubmit}>
              {/* Place field with Mapbox */}
              <Form.Group className="mb-3" controlId="placeName">
                <Form.Label>Place Name</Form.Label>
                <SearchBox
                  accessToken={import.meta.env.VITE_MAPBOX_TOKEN}
                  options={{
                    types: 'poi,address',
                    language: 'en',
                  }}
                  onRetrieve={handleMapboxSelect}
                  onClear={handleMapboxClear}
                  value={formData.place_name}
                  placeholder="Search for a place..."
                />
                <Form.Control
                  type="text"
                  style={{ display: 'none' }}
                  value={formData.place_name}
                  required
                  readOnly
                  isInvalid={isPlaceInvalid}
                />
                <Form.Control.Feedback type="invalid">
                  Please select a place.
                </Form.Control.Feedback>

                {formData.place_address && (
                  <div className="text-muted small mt-2">
                    <i className="bi bi-geo-alt-fill me-1 text-secondary"></i>
                    {formData.place_address}
                  </div>
                )}
              </Form.Group>

              {/* Start & End time */}
              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3" controlId="startTime">
                    <Form.Label>Estimated Start Time</Form.Label>
                    <Form.Control
                      type="time"
                      name="start_time"
                      value={formData.start_time}
                      onChange={handleChange}
                      required
                    />
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group className="mb-3" controlId="endTime">
                    <Form.Label>Estimated End Time</Form.Label>
                    <Form.Control
                      type="time"
                      name="end_time"
                      value={formData.end_time}
                      onChange={handleChange}
                      required
                      isInvalid={
                        !!formData.start_time &&
                        !!formData.end_time &&
                        formData.end_time < formData.start_time
                      }
                    />
                    <Form.Control.Feedback type="invalid">
                      End time must be after start time.
                    </Form.Control.Feedback>
                  </Form.Group>
                </Col>
              </Row>

              {/* Notes */}
              <Form.Group className="mb-4" controlId="notes">
                <Form.Label>Comment (Optional)</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  name="notes"
                  placeholder="Add any comments about this place..."
                  value={formData.notes}
                  onChange={handleChange}
                />
              </Form.Group>

              {errorMsg && <Alert variant="danger">{errorMsg}</Alert>}

              {/* Action buttons */}
              <div className="text-center mt-4 d-flex justify-content-center gap-3">
                <Button
                  variant="primary"
                  type="submit"
                  disabled={submitting}
                  className="px-4"
                >
                  {submitting ? 'Adding...' : 'Add Place'}
                </Button>

                <Button
                  variant="outline-danger"
                  type="button"
                  className="px-4"
                  onClick={() => navigate(`/trips/${trip_id}/${date}`)}
                >
                  Cancel
                </Button>
              </div>
            </Form>
          </Card.Body>
        </Card>
      </Container>
    </>
  );
}
