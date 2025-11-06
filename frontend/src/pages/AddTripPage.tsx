import { useState } from 'react';
import 'bootstrap-icons/font/bootstrap-icons.css';
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
import Select from 'react-select';
import axiosInstance from '../api/axiosInstance';
import { useNavigate } from 'react-router-dom';
import NavigationBar from '../components/NavigationBar';
import { fetchPlaceImage } from '../utils/fetchPlaceImage';
import type { Trip } from '../types/tripTypes';

export default function AddTripPage() {
  const [formData, setFormData] = useState({
    name: '',
    destination_city: '',
    start_date: '',
    end_date: '',
    preferences: [] as string[],
  });
  const [submitting, setSubmitting] = useState(false);
  const [isCityInvalid, setIsCityInvalid] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const navigate = useNavigate();

  interface PreferenceOption {
    value: string;
    label: string;
  }

  const preferenceOptions: PreferenceOption[] = [
    { value: 'Eating and Drinking', label: '🍽️ Eating and Drinking' },
    { value: 'Shopping', label: '🛍️ Shopping' },
    { value: 'City Walk', label: '🚶 City Walk' },
    { value: 'Nature & Outdoor', label: '🌲 Nature & Outdoor' },
    { value: 'Historical & Cultural', label: '🏛️ Historical & Cultural' },
    { value: 'Nightlife', label: '🌃 Nightlife' },
    { value: 'Relaxation & Wellness', label: '💆 Relaxation & Wellness' },
  ];

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
    setIsCityInvalid(false);
    const place = event.features[0];
    const placeName =
      place.properties?.full_address || place.properties?.name || '';

    setFormData((prev) => ({
      ...prev,
      destination_city: placeName,
    }));
  };

  const handleMapboxClear = () => {
    setFormData((prev) => ({
      ...prev,
      destination_city: '',
    }));
  };

  // Handle multiple select preferences
  const handlePreferenceChange = (
    selected: readonly PreferenceOption[] | null
  ) => {
    const selectedValues = selected ? selected.map((opt) => opt.value) : [];
    setFormData((prev) => ({ ...prev, preferences: selectedValues }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate destination city (not empty)
    if (!formData.destination_city.trim()) {
      setIsCityInvalid(true);
      return;
    }

    // Validate dates
    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      setErrorMsg('End date cannot be earlier than start date.');
      return;
    }

    setSubmitting(true);

    try {
      // Fetch image URL based on destination city
      const imageUrl = await fetchPlaceImage(
        formData.destination_city.split(',')[0]
      );
      console.log('Fetched image URL:', imageUrl);

      const payload = { ...formData, image_url: imageUrl };
      console.log('Submitting trip data:', payload);
      const response = await axiosInstance.post('/api/plans/trips/', payload);
      console.log('Trip created:', response.data);

      const newTrip: Trip = response.data;

      const firstDayId = newTrip.firstDayId
        ? newTrip.firstDayId
        : newTrip.days?.[0]?.id;

      if (firstDayId) {
        navigate(`/trips/${newTrip.id}/days/${firstDayId}`);
      } else {
        console.error('New trip data is missing days, navigating to list.');
        navigate('/trips');
      }
    } catch (error) {
      console.error('Failed to create trip:', error);
      setErrorMsg(
        error instanceof Error ? error.message : 'Failed to create trip.'
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
          className="p-4 shadow-lg"
          style={{ maxWidth: '600px', width: '100%' }}
        >
          <Card.Body>
            <h2 className="text-center mb-4 text-primary fw-bold d-flex align-items-center justify-content-center">
              <i className="bi bi-airplane me-2"></i>
              Add New Travel Plan
            </h2>

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3" controlId="tripName">
                <Form.Label>Trip Title</Form.Label>
                <Form.Control
                  type="text"
                  name="name"
                  placeholder="e.g. Summer Vacation in New York"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </Form.Group>

              <Form.Group className="mb-3" controlId="destinationCity">
                <Form.Label>Destination City</Form.Label>
                <SearchBox
                  accessToken={import.meta.env.VITE_MAPBOX_TOKEN}
                  options={{
                    types: 'place',
                    language: 'en',
                  }}
                  onRetrieve={handleMapboxSelect}
                  onClear={handleMapboxClear}
                  value={formData.destination_city}
                  placeholder="Search for a city..."
                />
                <Form.Control
                  type="text"
                  style={{ display: 'none' }}
                  value={formData.destination_city}
                  required
                  readOnly
                  isInvalid={isCityInvalid}
                />
                <Form.Control.Feedback type="invalid">
                  Please select a destination city.
                </Form.Control.Feedback>
              </Form.Group>

              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3" controlId="startDate">
                    <Form.Label>Start Date</Form.Label>
                    <Form.Control
                      type="date"
                      name="start_date"
                      value={formData.start_date}
                      onChange={handleChange}
                      required
                    />
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group className="mb-3" controlId="endDate">
                    <Form.Label>End Date</Form.Label>
                    <Form.Control
                      type="date"
                      name="end_date"
                      value={formData.end_date}
                      onChange={handleChange}
                      required
                      isInvalid={
                        !!formData.start_date &&
                        !!formData.end_date &&
                        new Date(formData.end_date) <
                          new Date(formData.start_date)
                      }
                    />
                    <Form.Control.Feedback type="invalid">
                      End date must be after start date.
                    </Form.Control.Feedback>
                  </Form.Group>
                </Col>
              </Row>

              <Form.Group className="mb-4" controlId="preferences">
                <Form.Label>Travel Preferences</Form.Label>
                <Select
                  isMulti
                  options={preferenceOptions}
                  classNamePrefix="react-select"
                  placeholder="Select your travel preferences..."
                  onChange={handlePreferenceChange}
                  value={preferenceOptions.filter((opt) =>
                    formData.preferences.includes(opt.value)
                  )}
                />
                <Form.Text className="text-muted">
                  You can select multiple preferences or leave it blank.
                </Form.Text>
              </Form.Group>

              {errorMsg && <Alert variant="danger">{errorMsg}</Alert>}

              <div className="text-center mt-4 d-flex justify-content-center gap-3">
                <Button
                  variant="primary"
                  type="submit"
                  disabled={submitting}
                  className="px-4"
                >
                  {submitting ? 'Creating...' : 'Create Trip'}
                </Button>

                <Button
                  variant="outline-danger"
                  type="button"
                  className="px-4"
                  onClick={() => navigate('/trips')}
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
