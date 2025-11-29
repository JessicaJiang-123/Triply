import { useEffect, useState } from 'react';
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
import axios from 'axios';

export default function AddPlacePage() {
  const { trip_id, day_id, place_id } = useParams<{
    trip_id: string;
    day_id: string;
    place_id?: string;
  }>();

  const isEditMode = !!place_id;
  const [dayDate, setDayDate] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    address: '',
    start_time: '',
    end_time: '',
    notes: '',
    mapbox_id: '',
  });

  const [changeCover, setChangeCover] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isPlaceInvalid, setIsPlaceInvalid] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  // Fetch day date based on day_id
  useEffect(() => {
    const fetchDayDate = async () => {
      try {
        const response = await axiosInstance.get(
          `/api/plans/trips/${trip_id}/days/${day_id}/`
        );
        setDayDate(response.data.date);
      } catch {
        // console.error('Error fetching day date:', error);
      }
    };

    fetchDayDate();
  }, [trip_id, day_id]);

  // If in edit mode, fetch existing place details
  useEffect(() => {
    if (!isEditMode) return;
    const fetchPlace = async () => {
      try {
        const response = await axiosInstance.get(
          `/api/plans/trips/${trip_id}/days/${day_id}/places/${place_id}/`
        );
        const place = response.data;
        setFormData({
          name: place.name || '',
          address: place.address || '',
          start_time: place.start_time || '',
          end_time: place.end_time || '',
          notes: place.notes || '',
          mapbox_id: place.mapbox_id || '',
        });
      } catch {
        // console.error('Failed to fetch place details:', error);
        setErrorMsg('Failed to load existing place details.');
      }
    };
    fetchPlace();
  }, [trip_id, day_id, place_id, isEditMode]);

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
    const mapbox_id = feature.properties?.mapbox_id || '';

    setFormData((prev) => ({
      ...prev,
      name: name,
      address: address,
      mapbox_id: mapbox_id,
    }));
  };

  const handleMapboxClear = () => {
    setFormData((prev) => ({
      ...prev,
      name: '',
      address: '',
      mapbox_id: '',
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate place field
    if (!formData.name.trim()) {
      setIsPlaceInvalid(true);
      return;
    }

    // Validate address field and mapbox_id field
    if (!formData.address.trim() || !formData.mapbox_id.trim()) {
      setErrorMsg('Please select a valid place with an address.');
      return;
    }

    // Validate start time
    if (!formData.start_time) {
      setErrorMsg('Please provide a valid start time.');
      return;
    }

    // Validate end time
    if (!formData.end_time) {
      setErrorMsg('Please provide a valid end time.');
      return;
    }

    // Validate time
    if (formData.end_time < formData.start_time) {
      setErrorMsg('End time must be after start time.');
      return;
    }

    setSubmitting(true);

    try {
      let imageUrl = '';

      // Only fetch a new image if user is adding a new place
      // or wants to change the cover in edit mode
      if (!isEditMode || changeCover) {
        imageUrl = 'need to be updated in backend'; // Placeholder, backend will handle image fetching
      }

      const payload = {
        ...formData,
        trip: trip_id,
        day: day_id,
        mapbox_supported: true,
        ...(imageUrl && { image_url: imageUrl }),
      };
      // console.log('Submitting place:', payload);

      if (isEditMode) {
        // Update existing place
        await axiosInstance.post(
          `/api/plans/trips/${trip_id}/days/${day_id}/places/${place_id}/`,
          payload
        );
        // console.log('Place updated: ', response.data);
      } else {
        // Create new place
        await axiosInstance.post(
          `/api/plans/trips/${trip_id}/days/${day_id}/places/`,
          payload
        );
        // console.log('Place added: ', response.data);
      }

      // Navigate back to the trip's current date view
      navigate(`/trips/${trip_id}/days/${day_id}`);
    } catch (error) {
      // console.error('Failed to add place:', error);
      if (axios.isAxiosError(error) && error.response) {
        setErrorMsg(
          error.response.data.detail ||
            'An error occurred while adding the place.'
        );
      } else {
        setErrorMsg('An unexpected error occurred. Please try again.');
      }
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
              {isEditMode
                ? `Edit Travel Place for ${dayDate ?? `Day ${day_id}`}`
                : `Add New Travel Place for ${dayDate ?? `Day ${day_id}`}`}
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
                  value={formData.name}
                  placeholder="Search for a place..."
                />
                <Form.Control
                  type="text"
                  style={{ display: 'none' }}
                  value={formData.name}
                  required
                  readOnly
                  isInvalid={isPlaceInvalid}
                />
                <Form.Control.Feedback type="invalid">
                  Please select a place.
                </Form.Control.Feedback>

                {formData.address && (
                  <div className="text-muted small mt-2">
                    <i className="bi bi-geo-alt-fill me-1 text-secondary"></i>
                    {formData.address}
                  </div>
                )}
              </Form.Group>

              {/* Change Cover Image (edit mode only) */}
              {isEditMode && (
                <Form.Group className="mb-4" controlId="changeCoverImage">
                  <Form.Check
                    type="switch"
                    id="change-cover-switch"
                    label="Change cover image (randomly fetched based on place name)"
                    checked={changeCover}
                    onChange={(e) => setChangeCover(e.target.checked)}
                  />
                </Form.Group>
              )}

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
                  maxLength={200}
                />
                <div className="text-muted small text-end mt-1">
                  {formData.notes.length}/200 characters
                </div>
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
                  {submitting
                    ? 'Submitting...'
                    : isEditMode
                      ? 'Save Changes'
                      : 'Add Place'}
                </Button>

                <Button
                  variant="outline-danger"
                  type="button"
                  className="px-4"
                  onClick={() => navigate(`/trips/${trip_id}/days/${day_id}`)}
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
