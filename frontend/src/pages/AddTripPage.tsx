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
import type { Trip } from '../types/tripTypes';
import axios from 'axios';

export default function AddTripPage() {
  const [formData, setFormData] = useState({
    name: '',
    destination_city: '',
    start_date: '',
    end_date: '',
    preferences: [] as string[],
  });
  const [submitting, setSubmitting] = useState(false);
  // AI submission states
  const [isAiSubmitting, setIsAiSubmitting] = useState(false);
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

  // Handle form submission for both manual and AI modes
  const handleSubmit = async (
    e: React.FormEvent,
    mode: 'manual' | 'ai' = 'manual'
  ) => {
    e.preventDefault();

    setErrorMsg(null);

    // Validate trip name (not empty)
    if (!formData.name.trim()) {
      setErrorMsg('Trip title is required.');
      return;
    }

    // Validate destination city (not empty)
    if (!formData.destination_city.trim()) {
      setIsCityInvalid(true);
      return;
    }

    // Validate start date
    if (!formData.start_date) {
      setErrorMsg('Start date is required.');
      return;
    }

    // Validate end date
    if (!formData.end_date) {
      setErrorMsg('End date is required.');
      return;
    }

    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);

    // Check valid start date parsing
    if (Number.isNaN(start.getTime())) {
      setErrorMsg('Start date is invalid.');
      return;
    }

    // Check valid end date parsing
    if (Number.isNaN(end.getTime())) {
      setErrorMsg('End date is invalid.');
      return;
    }

    // Validate year ranges
    const MIN_YEAR = 2024;
    const MAX_YEAR = 2030;

    console.log('Start year:', start.getFullYear());
    console.log('End year:', end.getFullYear());

    if (start.getFullYear() < MIN_YEAR || start.getFullYear() > MAX_YEAR) {
      setErrorMsg(
        `Start date year must be between ${MIN_YEAR} and ${MAX_YEAR}.`
      );
      return;
    }

    if (end.getFullYear() < MIN_YEAR || end.getFullYear() > MAX_YEAR) {
      setErrorMsg(`End date year must be between ${MIN_YEAR} and ${MAX_YEAR}.`);
      return;
    }

    // Validate dates order
    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      setErrorMsg('End date cannot be earlier than start date.');
      return;
    }

    // start submitting states
    if (mode === 'manual') {
      setSubmitting(true);
      setIsAiSubmitting(false);
    } else {
      setIsAiSubmitting(true);
      setSubmitting(false);
    }

    try {
      const payload = { ...formData };
      console.log('Submitting trip data:', payload);

      const endpoint =
        mode === 'ai' ? '/api/plans/generate-ai-plan/' : '/api/plans/trips/';

      const response = await axiosInstance.post(endpoint, payload);
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
      if (axios.isAxiosError(error) && error.response) {
        setErrorMsg(
          error.response.data.detail ||
            'An error occurred while creating the trip.'
        );
      } else {
        setErrorMsg('An unexpected error occurred. Please try again.');
      }
    } finally {
      setSubmitting(false);
      setIsAiSubmitting(false);
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
                  variant="outline-primary"
                  type="button"
                  onClick={(e) => handleSubmit(e, 'ai')}
                  disabled={submitting || isAiSubmitting}
                  className="px-4"
                >
                  {isAiSubmitting ? 'Generating...' : '✨ Generate with AI'}
                </Button>

                <Button
                  variant="primary"
                  type="submit"
                  disabled={submitting || isAiSubmitting}
                  className="px-4"
                >
                  {submitting ? 'Creating...' : 'Create Manually'}
                </Button>

                <Button
                  variant="outline-danger"
                  type="button"
                  className="px-4"
                  onClick={() => navigate('/trips')}
                  disabled={submitting || isAiSubmitting}
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
