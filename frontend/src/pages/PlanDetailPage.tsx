import { useEffect, useState } from 'react';
import type { ReactElement } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../api/axiosInstance';
import NavigationBar from '../components/NavigationBar';
import { Button } from 'react-bootstrap';
import PlaceCard from '../components/PlaceCard';
import Map from '../components/Map';
import { useRef } from 'react';
import type { Place, Trip } from '../types/tripTypes';

export default function PlanDetailPage(): ReactElement {
  const { trip_id, day_id } = useParams<{ trip_id: string; day_id: string }>();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dateRowRef = useRef<HTMLDivElement | null>(null);
  const [selectedDayId, setSelectedDayId] = useState<number | null>(null);
  const navigate = useNavigate();

  // fetch trip details to populate date bar
  useEffect(() => {
    const fetchTrip = async () => {
      if (!trip_id) return;
      try {
        const res = await axiosInstance.get(`/api/plans/trips/${trip_id}/`);
        console.log('Fetched trip', res.data);
        setTrip(res.data);
      } catch (err) {
        console.error('Failed to fetch trip', err);
        const e = err as {
          response?: { data?: { detail?: string } };
          message?: string;
        };
        setError(
          e?.response?.data?.detail || e?.message || 'Fetch trip failed'
        );
      }
    };
    fetchTrip();
  }, [trip_id]);

  // fetch places for current day
  useEffect(() => {
    const fetchPlaces = async () => {
      if (!trip_id || !day_id) return;
      try {
        const res = await axiosInstance.get(
          `/api/plans/trips/${trip_id}/days/${day_id}/`
        );
        console.log('Fetched places for day', res.data);
        setPlaces(res.data.places || []);
        setSelectedDayId(Number(day_id));
      } catch (err) {
        console.error('Failed to fetch day places', err);
        const e = err as {
          response?: { data?: { detail?: string } };
          message?: string;
        };
        setError(
          e?.response?.data?.detail || e?.message || 'Fetch places failed'
        );
      } finally {
        setLoading(false);
      }
    };
    fetchPlaces();
  }, [trip_id, day_id]);

  // Delete place handler
  async function handleDeletePlace(placeId: number) {
    if (!trip_id || !selectedDayId) return;
    if (!window.confirm('Are you sure you want to delete this place?')) {
      return;
    }
    try {
      const res = await axiosInstance.delete(
        `/api/plans/trips/${trip_id}/days/${selectedDayId}/places/${placeId}/`
      );
      const updatedPlaces: Place[] = res.data;
      setPlaces(updatedPlaces);

      // Also update the trip state to reflect the change in its day
      setTrip((prevTrip) => {
        if (!prevTrip) return prevTrip;
        const updatedDays = prevTrip.days.map((d) =>
          d.id === selectedDayId ? { ...d, places: updatedPlaces } : d
        );
        return { ...prevTrip, days: updatedDays };
      });
    } catch (err) {
      console.error('Delete place failed', err);
      const e = err as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setError(
        e?.response?.data?.detail || e?.message || 'Delete place failed'
      );
    }
  }

  // Navigate to Add Place page
  const handleAddPlace = () => {
    if (selectedDayId) {
      navigate(`/trips/${trip_id}/days/${selectedDayId}/add-place`);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!trip) return <div>No trip found.</div>;

  return (
    <>
      <NavigationBar title={trip.name} />
      <div
        style={{
          height: 'calc(100vh - 64px)', // 64px = Navbar height
          display: 'flex',
          overflow: 'hidden', // prevent whole page scrolling
        }}
      >
        {/* Left Column — Date Bar + Place List + Add Button */}
        <div
          className="d-flex flex-column"
          style={{
            width: '35%',
            borderRight: '1px solid #e0e0e0',
            backgroundColor: '#fff',
            overflow: 'hidden', // contain inner scroll only
          }}
        >
          {/* Date bar (fixed at top) */}
          <div className="d-flex align-items-center mb-3 px-2 pt-3 flex-shrink-0">
            <Button
              variant="light"
              size="sm"
              className="me-2 d-flex align-items-center justify-content-center"
              onClick={() =>
                dateRowRef.current?.scrollBy({ left: -150, behavior: 'smooth' })
              }
            >
              <i className="bi bi-caret-left-fill fs-5"></i>
            </Button>

            <div
              ref={dateRowRef}
              className="py-2"
              style={{
                overflowX: 'auto',
                whiteSpace: 'nowrap',
                flex: 1,
                paddingBottom: '4px',
              }}
            >
              {trip.days.map((d) => (
                <div
                  key={d.id}
                  style={{ display: 'inline-block', marginRight: 8 }}
                >
                  <button
                    onClick={() => navigate(`/trips/${trip_id}/days/${d.id}`)}
                    className={`btn px-3 ${
                      Number(day_id) === d.id
                        ? 'fw-bold text-dark border-bottom border-primary'
                        : 'text-muted'
                    }`}
                    style={{
                      fontSize: 16,
                      paddingTop: 6,
                      paddingBottom: 6,
                      borderRadius: 6,
                      backgroundColor: 'transparent',
                    }}
                  >
                    {d.date}
                  </button>
                </div>
              ))}
            </div>

            <Button
              variant="light"
              size="sm"
              className="ms-2 d-flex align-items-center justify-content-center"
              onClick={() =>
                dateRowRef.current?.scrollBy({ left: 150, behavior: 'smooth' })
              }
            >
              <i className="bi bi-caret-right-fill fs-5"></i>
            </Button>
          </div>

          {/* Scrollable list */}
          <div
            className="flex-grow-1 overflow-auto px-3"
            style={{
              paddingBottom: '80px', // space for add button
            }}
          >
            {places.length > 0 ? (
              places.map((p) => (
                <PlaceCard
                  key={p.id}
                  order={p.order}
                  name={p.name}
                  address={p.address || ''}
                  notes={p.notes}
                  start_time={p.start_time}
                  end_time={p.end_time}
                  image_url={p.image_url}
                  id={p.id}
                  onDelete={handleDeletePlace}
                  trip_id={trip.id}
                  day_id={Number(day_id)}
                />
              ))
            ) : (
              <div className="text-center text-muted mt-5">
                No places added for this day.
              </div>
            )}
          </div>

          {/* Fixed bottom Add button */}
          <div
            className="p-3 border-top flex-shrink-0"
            style={{
              backgroundColor: '#fff',
              boxShadow: '0 -2px 8px rgba(0,0,0,0.05)',
              zIndex: 10,
            }}
          >
            <Button
              className="w-100 d-flex align-items-center justify-content-center"
              variant="primary"
              onClick={handleAddPlace}
            >
              <i className="bi bi-plus-circle me-2"></i> Add new place
            </Button>
          </div>
        </div>

        {/* Right Column — Map or future content */}
        <div
          style={{
            flexGrow: 1,
            backgroundColor: '#fafafa',
            overflow: 'hidden', // keep right pane static
          }}
        >
          {/* Map / Place Detail */}
          <Map places={places} />
        </div>
      </div>
    </>
  );
}
