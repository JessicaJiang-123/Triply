import type { ReactElement, Dispatch, SetStateAction, RefObject } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import PlaceCard from '../components/PlaceCard';
import type { Place, RouteSegment, Trip } from '../types/tripTypes';

type PlanPlacesPanelProps = {
  dateRowRef: RefObject<HTMLDivElement | null>;
  trip: Trip;
  trip_id: string | undefined;
  day_id: string | undefined;
  places: Place[];
  routes: RouteSegment[];
  isOwner: boolean;
  handleAddPlace: () => void;
  handleDeletePlace: (id: number, mapbox_id: string) => Promise<void>;
  selectedRouteId: string | null;
  setSelectedRouteId: Dispatch<SetStateAction<string | null>>;
  setSelectedMapboxId: Dispatch<SetStateAction<string | null>>;
  handleShare: () => void;
};

export default function PlanPlacesPanel({
  dateRowRef,
  trip,
  trip_id,
  day_id,
  places,
  routes,
  isOwner,
  handleAddPlace,
  handleDeletePlace,
  selectedRouteId,
  setSelectedRouteId,
  setSelectedMapboxId,
  handleShare,
}: PlanPlacesPanelProps): ReactElement {
  const navigate = useNavigate();

  return (
    <>
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
            <div key={d.id} style={{ display: 'inline-block', marginRight: 8 }}>
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

        {/* Share Button */}
        {isOwner && (
          <Button
            variant="light"
            size="sm"
            // ... (other props)
            onClick={handleShare}
            title="Share your travel plan"
          >
            <i className="bi bi-share-fill fs-5 text-primary"></i>
          </Button>
        )}
      </div>

      {/* Scrollable list */}
      <div
        className="flex-grow-1 overflow-auto px-3"
        style={{
          paddingBottom: '80px', // space for add button
        }}
      >
        {places.length > 0 ? (
          places.map((p, index) => (
            <div key={p.id} style={{ marginBottom: '1rem' }}>
              <PlaceCard
                order={p.order}
                name={p.name}
                address={p.address || ''}
                notes={p.notes}
                start_time={p.start_time}
                end_time={p.end_time}
                image_url={p.unsplash_image?.local_image_url || p.image_url}
                id={p.id}
                mapbox_id={p.mapbox_id}
                mapbox_supported={p.mapbox_supported}
                onPreviewComments={
                  (mbid: string) => {
                    setSelectedRouteId(null);
                    setSelectedMapboxId(mbid)
                  }
                }
                onDelete={handleDeletePlace}
                trip_id={trip.id}
                day_id={Number(day_id)}
                isOwner={isOwner}
              />
              {/* Clickable distance + duration line */}
              {index < routes.length && (
                <div
                  onClick={() => {
                    setSelectedMapboxId(null);
                    setSelectedRouteId((prev) =>
                      prev === routes[index].route_id
                        ? null
                        : routes[index].route_id
                    )
                  }
                  }
                  className={`text-center small my-2 py-1 rounded ${
                    selectedRouteId === routes[index].route_id
                      ? 'border border-primary'
                      : 'border border-transparent text-muted'
                  }`}
                  style={{
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <i className="bi bi-arrow-down-short me-1"></i>
                  {routes[index].distance_km.toFixed(1)} km ·{' '}
                  {Math.round(routes[index].travel_time_min)} min
                  <i className="bi bi-car-front-fill ms-2 text-secondary"></i>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center text-muted mt-5">
            No places added for this day.
          </div>
        )}
      </div>

      {/* Fixed bottom Add button */}
      {isOwner && (
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
      )}
    </>
  );
}
