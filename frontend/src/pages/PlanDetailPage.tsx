import { useContext, useEffect, useState } from 'react';
import type { ReactElement } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../api/axiosInstance';
import NavigationBar from '../components/NavigationBar';
import { useRef } from 'react';
import type { Place, RouteSegment, Trip } from '../types/tripTypes';
import ShareTripModal from '../components/ShareTripModal';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { useIsMobile } from '../utils/useIsMobile';
import PlanMapCommentPanel from '../components/PlanMapCommentPanel';
import PlanPlacesPanel from '../components/PlanPlacesPanel';

export default function PlanDetailPage(): ReactElement {
  const { trip_id, day_id } = useParams<{ trip_id: string; day_id: string }>();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [routes, setRoutes] = useState<RouteSegment[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [selectedMapboxId, setSelectedMapboxId] = useState<string | null>(null);
  const [selectedPlaceId, setSelectedPlaceId] = useState<number | null>(null);
  const [loadingTrip, setLoadingTrip] = useState(true);
  const [loadingPlaces, setLoadingPlaces] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dateRowRef = useRef<HTMLDivElement | null>(null);
  const [selectedDayId, setSelectedDayId] = useState<number | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const { currentUser } = useContext(AuthContext);
  const isMobile = useIsMobile();
  const navigate = useNavigate();

  // fetch trip details to populate date bar
  useEffect(() => {
    const fetchTrip = async () => {
      if (!trip_id) return;
      try {
        const res = await axiosInstance.get(`/api/plans/trips/${trip_id}/`);
        // console.log('Fetched trip', res.data);
        setTrip(res.data);
      } catch (err) {
        // console.error('Failed to fetch trip', err);
        if (axios.isAxiosError(err) && err.response) {
          const status = err.response.status;
          const detail =
            err.response.data?.detail || 'Fetch trip details failed';
          setError(`${detail} (${status})`);
        } else {
          setError('Fetch trip details failed');
        }
      } finally {
        setLoadingTrip(false);
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
        // console.log('Fetched places for day', res.data);
        const fetchedPlaces: Place[] = res.data.places || [];
        const fetchedRoutes: RouteSegment[] = res.data.routes || [];
        setPlaces(fetchedPlaces);
        setRoutes(fetchedRoutes);
        setSelectedDayId(Number(day_id));
        setSelectedRouteId(null);
        setSelectedMapboxId(null);
        setSelectedPlaceId(null);
      } catch (err) {
        // console.error('Failed to fetch day places', err);
        if (axios.isAxiosError(err) && err.response) {
          const status = err.response.status;
          const detail = err.response.data?.detail || 'Fetch day places failed';
          setError(`${detail} (${status})`);
        } else {
          setError('Fetch day places failed');
        }
      } finally {
        setLoadingPlaces(false);
      }
    };
    fetchPlaces();
  }, [trip_id, day_id]);

  // Delete place handler
  async function handleDeletePlace(placeId: number, mapboxId?: string | null) {
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

      // Re-fetch routes after deletion
      const routesRes = await axiosInstance.get(
        `/api/plans/trips/${trip_id}/days/${selectedDayId}/`
      );
      setRoutes(routesRes.data.routes || []);

      // Also update the trip state to reflect the change in its day
      setTrip((prevTrip) => {
        if (!prevTrip) return prevTrip;
        const updatedDays = prevTrip.days.map((d) =>
          d.id === selectedDayId ? { ...d, places: updatedPlaces } : d
        );
        return { ...prevTrip, days: updatedDays };
      });

      // If the deleted place was being viewed in the comment panel, close it
      if (mapboxId && selectedMapboxId === mapboxId && selectedPlaceId === placeId) {
        setSelectedMapboxId(null);
        setSelectedPlaceId(null);
      }
    } catch (err) {
      // console.error('Delete place failed', err);
      if (axios.isAxiosError(err) && err.response) {
        setError(err.response.data.detail || 'Delete place failed');
      } else {
        setError('Delete place failed');
      }
    }
  }

  // Navigate to Add Place page
  const handleAddPlace = () => {
    if (selectedDayId) {
      navigate(`/trips/${trip_id}/days/${selectedDayId}/add-place`);
    }
  };

  const handleShare = () => {
    setShowShareModal(true);
  };

  /** Determine which routes to show on the map */
  const displayedRoutes =
    selectedRouteId !== null
      ? routes
          .filter((r) => r.route_id === selectedRouteId)
          .map((r) => r.coordinates)
      : routes.map((r) => r.coordinates);

  const isOwner = currentUser ? currentUser.id === trip?.owner.id : false;

  if (loadingTrip || loadingPlaces) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!trip) return <div>404 Not Found: Trip does not exist</div>;

  return (
    <>
      <NavigationBar title={trip.name} />

      {isMobile ? (
        <div
          className="d-flex d-md-none flex-column"
          style={{
            height: 'calc(100vh - 64px)', // 64px = Navbar height
            overflow: 'hidden', // prevent whole page scrolling
          }}
        >
          {/* Top Panel — Map / Comment Panel */}
          <div
            style={{
              flexGrow: 1,
              backgroundColor: '#fafafa',
              overflow: 'auto',
              display: 'flex',
              maxHeight: '40%',
            }}
          >
            <PlanMapCommentPanel
              selectedPlaceId={selectedPlaceId}
              selectedMapboxId={selectedMapboxId}
              setSelectedMapboxId={setSelectedMapboxId}
              places={places}
              trip={trip}
              displayedRoutes={displayedRoutes}
            />
          </div>

          {/* Bottom Panel — Date Bar + Place List + Add Button */}
          <div
            className="d-flex flex-column"
            style={{
              height: '60%',
              borderTop: '1px solid #e0e0e0',
              backgroundColor: '#fff',
              overflow: 'hidden',
            }}
          >
            <PlanPlacesPanel
              dateRowRef={dateRowRef}
              trip={trip}
              trip_id={trip_id}
              day_id={day_id}
              places={places}
              routes={routes}
              isOwner={isOwner}
              handleAddPlace={handleAddPlace}
              handleDeletePlace={handleDeletePlace}
              selectedRouteId={selectedRouteId}
              setSelectedRouteId={setSelectedRouteId}
              setSelectedMapboxId={setSelectedMapboxId}
              setSelectedPlaceId={setSelectedPlaceId}
              handleShare={handleShare}
            />
          </div>
        </div>
      ) : (
        <div
          className="d-none d-md-flex"
          style={{
            height: 'calc(100vh - 64px)', // 64px = Navbar height
            overflow: 'hidden', // prevent whole page scrolling
          }}
        >
          {/* Left Column — Date Bar + Place List + Add Button */}
          <div
            className="d-flex flex-column"
            style={{
              width: '40%',
              borderRight: '1px solid #e0e0e0',
              backgroundColor: '#fff',
              overflow: 'hidden', // contain inner scroll only
            }}
          >
            <PlanPlacesPanel
              dateRowRef={dateRowRef}
              trip={trip}
              trip_id={trip_id}
              day_id={day_id}
              places={places}
              routes={routes}
              isOwner={isOwner}
              handleAddPlace={handleAddPlace}
              handleDeletePlace={handleDeletePlace}
              selectedRouteId={selectedRouteId}
              setSelectedRouteId={setSelectedRouteId}
              setSelectedMapboxId={setSelectedMapboxId}
              setSelectedPlaceId={setSelectedPlaceId}
              handleShare={handleShare}
            />
          </div>

          {/* Right Column — Map / Comment Panel */}
          <div
            style={{
              flexGrow: 1,
              backgroundColor: '#fafafa',
              overflow: 'hidden', // keep right pane static
              display: 'flex',
              maxWidth: '60%',
            }}
          >
            <PlanMapCommentPanel
              selectedPlaceId={selectedPlaceId}
              selectedMapboxId={selectedMapboxId}
              setSelectedMapboxId={setSelectedMapboxId}
              places={places}
              trip={trip}
              displayedRoutes={displayedRoutes}
            />
          </div>
        </div>
      )}

      {/* Share Trip Modal */}
      <ShareTripModal
        show={showShareModal}
        onHide={() => setShowShareModal(false)}
        tripId={trip ? trip.id : null}
      />
    </>
  );
}
