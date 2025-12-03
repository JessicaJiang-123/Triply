import type { Dispatch, ReactElement, SetStateAction } from 'react';
import PlaceCommentPanel from '../components/PlaceCommentPanel';
import MapComponent from '../components/MapComponent';
import type { Place, Trip } from '../types/tripTypes';

type PlanMapCommentPanelProps = {
  selectedPlaceId: number | null;
  selectedMapboxId: string | null;
  setSelectedMapboxId: Dispatch<SetStateAction<string | null>>;
  places: Place[];
  trip: Trip;
  displayedRoutes: [number, number][][];
};

export default function PlanMapCommentPanel({
  selectedPlaceId,
  selectedMapboxId,
  setSelectedMapboxId,
  places,
  trip,
  displayedRoutes,
}: PlanMapCommentPanelProps): ReactElement {
  return (
    <>
      {/* Map / Place Detail */}
      {selectedMapboxId ? (
        <div className="w-100">
          <PlaceCommentPanel
            mapboxId={selectedMapboxId}
            placeName={(() => {
              const place = places.find(
                (p) =>
                  p.mapbox_id === selectedMapboxId && p.id === selectedPlaceId
              );
              return place?.name || place?.address || '';
            })()}
            onClose={() => setSelectedMapboxId(null)}
          />
        </div>
      ) : (
        <MapComponent
          places={places}
          center={[trip.longitude, trip.latitude]}
          routes={displayedRoutes}
        />
      )}
    </>
  );
}
