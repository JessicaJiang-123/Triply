import { useEffect, useState } from 'react';
import type { ReactElement } from 'react';
import { useParams } from 'react-router-dom';
import NavigationBar from '../components/NavigationBar';
import { Container, Button } from 'react-bootstrap';
import PlaceCard from '../components/PlaceCard';
import { useRef } from 'react';

type Place = {
  id: number;
  name: string;
  category?: string;
  start_time?: string;
  end_time?: string;
  notes?: string;
  order?: number;
  image_url?: string;
  address?: string;
};

type Day = {
  id: number;
  date: string;
  order: number;
  places: Place[];
};

type Trip = {
  id: number;
  name: string;
  destination_city: string;
  start_date: string;
  end_date: string;
  days: Day[];
};

// (If you want local mock data, use src/mocks/mockPlaces.ts)


export default function PlanDetailPage(): ReactElement {
  const { id } = useParams();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dateRowRef = useRef<HTMLDivElement | null>(null);
  const [selectedDay, setSelectedDay] = useState<string>('');
  const [selectedDayId, setSelectedDayId] = useState<number | null>(null);

  // helper to get places for selected day
  const selectedPlaces: Place[] = (() => {
    if (!trip) return [];
    const d = trip.days.find((x) => x.date === selectedDay) || trip.days[0];
    return d ? d.places : [];
  })();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetch(`/api/plans/${id}/`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setTrip(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  // set default selected day when trip loads
  useEffect(() => {
    if (trip && trip.days && trip.days.length > 0) {
      setSelectedDay(trip.days[0].date);
      setSelectedDayId(trip.days[0].id);
    }
  }, [trip]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!trip) return <div>No trip found.</div>;

  return (
      <>
          <NavigationBar />
          <Container fluid>
            <div className="row g-0">
              <div className="col-md-5 p-0" style={{ borderRight: '1px solid #eee', minHeight: '80vh', overflowY: 'auto' }}>
            {/* Date bar */}
            <div className="d-flex align-items-center mb-3">
              <Button variant="light" size="sm" className="me-2" onClick={() => {
                const el = dateRowRef.current;
                if (el) el.scrollBy({ left: -150, behavior: 'smooth' });
              }}>◀</Button>

              <div
                ref={dateRowRef}
                style={{ overflowX: 'auto', whiteSpace: 'nowrap', flex: 1 }}
                className="py-2"
              >
                {trip.days.map((d) => (
                  <div key={d.id} style={{ display: 'inline-block', marginRight: 8 }}>
                    <button
                      onClick={() => {
                        setSelectedDay(d.date);
                        setSelectedDayId(d.id);
                      }}
                      className={`btn btn-link px-3 ${selectedDay === d.date ? 'fw-bold text-dark' : 'text-muted'}`}
                      style={{ display: 'inline-block' }}
                    >
                      <div style={{ fontSize: 12 }}>{d.date}</div>
                    </button>
                    
                  </div>
                ))}
              </div>

              <Button variant="light" size="sm" className="ms-2" onClick={() => {
                const el = dateRowRef.current;
                if (el) el.scrollBy({ left: 150, behavior: 'smooth' });
              }}>▶</Button>
            </div>

            {/* Places for selected day */}
            <div>
              {selectedPlaces.map((p) => (
                <PlaceCard
                  key={p.id}
                  order={p.order}
                  name={p.name}
                  notes={p.notes}
                  start_time={p.start_time}
                  end_time={p.end_time}
                  image_url={p.image_url}
                />
              ))}
              </div>
              {/* Inline add link with icon */}
              <div className="mt-4 d-flex justify-content-center">
                <a
                  className="d-inline-flex align-items-center text-dark"
                  href={selectedDayId ? `/trips/${id}/days/${selectedDayId}/add-place` : '#'}
                  style={{ fontSize: 18, textDecoration: 'none', color: '#000' }}
                >
                  <img src="/images/add_circle.png" alt="add" width={24} height={24} className="me-2" />
                  <span style={{ color: '#000' }}>Add new place</span>
                </a>
              </div>
              </div>
              <div className="col-md-7" style={{ minHeight: '80vh' }}>
                {/* right column intentionally left blank (map or secondary content can go here) */}
              </div>
            </div>
          </Container>
      </>
  );
}
