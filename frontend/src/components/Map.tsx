import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Place } from '../types/tripTypes';

type MapProps = {
  places: Place[];
  center?: [number | undefined, number | undefined];
  routes?: [number, number][][];
};

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || '';

const Map: React.FC<MapProps> = ({ places, center, routes }) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  // Function to get user's current coordinates
  async function getUserCoordinates(): Promise<[number, number]> {
    if (!('geolocation' in navigator)) {
      throw new Error('Geolocation is not supported by this browser.');
    }

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { longitude, latitude } = pos.coords;
          console.log('User coordinates:', longitude, latitude);
          resolve([longitude, latitude]);
        },
        (err) => {
          reject(
            new Error(
              `Failed to get user location: ${err.message || 'Unknown error'}`
            )
          );
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    });
  }

  useEffect(() => {
    async function initMap() {
      if (!mapContainerRef.current || mapRef.current) return;

      // Determine initial center of the map
      let initialCenter: [number, number];
      if (
        center &&
        typeof center[0] === 'number' &&
        typeof center[1] === 'number'
      ) {
        initialCenter = [center[0], center[1]] as [number, number];
      } else {
        try {
          initialCenter = await getUserCoordinates();
        } catch (error) {
          console.warn(
            'Failed to get user location, fallback to [0, 0]:',
            error
          );
          initialCenter = [0, 0];
        }
      }

      // Initialize map
      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: initialCenter,
        zoom: 12,
      });
      mapRef.current = map;

      map.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
      const geolocateControl = new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
        showUserHeading: true,
        showUserLocation: true,
      });
      map.addControl(geolocateControl, 'bottom-left');

      // Wait until map is ready
      map.on('load', async () => {
        // Remove existing markers
        const markers = document.getElementsByClassName('mapbox-marker');
        while (markers.length > 0) {
          markers[0].remove();
        }

        // Remove existing route layers/sources
        map
          .getStyle()
          .layers?.filter((layer) => layer.id.startsWith('route-'))
          .forEach((layer) => {
            if (map.getLayer(layer.id)) map.removeLayer(layer.id);
            if (map.getSource(layer.id)) map.removeSource(layer.id);
          });

        // Filter valid coordinates
        const validPlaces = places.filter(
          (p) => p.latitude !== undefined && p.longitude !== undefined
        );

        // Add each place as a marker
        validPlaces.forEach((place) => {
          const el = document.createElement('div');
          el.className = 'mapbox-marker';
          el.style.width = '28px';
          el.style.height = '28px';
          el.style.borderRadius = '50%';
          el.style.backgroundColor = '#c41230';
          el.style.display = 'flex';
          el.style.alignItems = 'center';
          el.style.justifyContent = 'center';
          el.style.color = 'white';
          el.style.fontWeight = '600';
          el.style.fontSize = '13px';
          el.style.border = '2px solid white';
          el.style.boxShadow = '0 0 3px rgba(0,0,0,0.3)';
          el.style.cursor = 'pointer';
          el.innerText = place.order?.toString() || '?';

          const popupContent = `
            <div style="font-family: Poppins, sans-serif; font-size: 13px;">
              <strong>${place.order}. ${place.name}</strong>
              ${place.address ? `<br/>${place.address}` : ''}
            </div>
          `;

          const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(
            popupContent
          );

          new mapboxgl.Marker(el)
            .setLngLat([place.longitude!, place.latitude!])
            .setPopup(popup)
            .addTo(map);
        });

        // Add route layers for each route in props
        if (routes && routes.length > 0) {
          routes.forEach((coords, idx) => {
            const routeId = `route-${idx}`;

            map.addSource(routeId, {
              type: 'geojson',
              data: {
                type: 'Feature',
                properties: {},
                geometry: {
                  type: 'LineString',
                  coordinates: coords,
                },
              },
            });

            map.addLayer({
              id: routeId,
              type: 'line',
              source: routeId,
              layout: {
                'line-join': 'round',
                'line-cap': 'round',
              },
              paint: {
                'line-color': '#007cbf',
                'line-width': 4,
                'line-opacity': 0.75,
              },
            });
          });
        }

        // Fit bounds to all markers and routes
        const bounds = new mapboxgl.LngLatBounds();

        validPlaces.forEach((p) => bounds.extend([p.longitude!, p.latitude!]));

        routes?.forEach((route) => {
          route.forEach((coord) => bounds.extend(coord));
        });

        if (!bounds.isEmpty()) {
          map.fitBounds(bounds, { padding: 50, maxZoom: 15 });
        }
      });
    }

    initMap();

    // Cleanup when unmounting
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [places, center, routes]);

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
