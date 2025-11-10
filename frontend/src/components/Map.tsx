import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Place } from '../types/tripTypes';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import MapboxDirections from '@mapbox/mapbox-gl-directions/dist/mapbox-gl-directions.js';
import '@mapbox/mapbox-gl-directions/dist/mapbox-gl-directions.css';

type MapProps = {
  places: Place[];
};

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || '';

const Map: React.FC<MapProps> = ({ places }) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize map only once
    if (!mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [-79.94237, 40.4435], // TODO: Center on the destination city
        zoom: 14,
      });

      mapRef.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
      mapRef.current.addControl(new MapboxDirections({
        accessToken: mapboxgl.accessToken,
      }), 'top-right');
      const geolocateControl = new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
        showUserHeading: true,
        showUserLocation: true
      });
      mapRef.current.addControl(geolocateControl, 'bottom-left');
    }

    const map = mapRef.current;

    // Wait until map is ready
    map.on('load', () => {
      // Remove existing markers if any
      const markers = document.getElementsByClassName('mapbox-marker');
      while (markers.length > 0) {
        markers[0].remove();
      }

      // Filter valid coordinates
      const validPlaces = places.filter(
        (p) => p.latitude !== undefined && p.longitude !== undefined
      );

      // Add each place as a marker
      validPlaces.forEach((place) => {
        const el = document.createElement('div');
        el.className = 'mapbox-marker';
        el.style.width = '24px';
        el.style.height = '24px';
        el.style.backgroundImage =
          'url("data:image/svg+xml;utf8,<svg xmlns=%27http://www.w3.org/2000/svg%27 width=%2722%27 height=%2722%27 fill=%27%23c41230%27 class=%27bi bi-geo-alt-fill%27 viewBox=%270 0 16 16%27><path d=%27M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10m0-7a3 3 0 1 1 0-6 3 3 0 0 1 0 6%27/></svg>")';
        el.style.backgroundSize = 'contain';
        el.style.backgroundRepeat = 'no-repeat';
        el.style.cursor = 'pointer';

        const popupContent = `
          <div style="font-family: Poppins, sans-serif; font-size: 13px;">
            <strong>${place.name}</strong>
            ${place.category ? `<br/><em>${place.category}</em>` : ''}
            ${place.address ? `<br/>${place.address}` : ''}
          </div>
        `;

        const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(popupContent);

        new mapboxgl.Marker(el)
          .setLngLat([place.longitude!, place.latitude!])
          .setPopup(popup)
          .addTo(map);
      });

      // Fit map to bounds if we have valid coordinates
      if (validPlaces.length > 0) {
        const bounds = new mapboxgl.LngLatBounds();
        validPlaces.forEach((p) => bounds.extend([p.longitude!, p.latitude!]));
        map.fitBounds(bounds, { padding: 50, maxZoom: 16 });
      }
    });

    // Cleanup when unmounting
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [places]);

  return (
    <div
      ref={mapContainerRef}
      id="map"
      style={{
        width: '100%',
        height: '100%',
        border: '1px solid #e0e0e0',
      }}
    />
  );
};

export default Map;
