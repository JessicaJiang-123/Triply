import axios from 'axios';
import mapboxgl from 'mapbox-gl';

/** Type for a route info returned from Mapbox Directions API */
export type RouteInfo = {
  id: string; // unique identifier for the route
  coordinates: [number, number][]; // array of [lng, lat] (route coordinates)
  duration: number; // seconds
  distance: number; // meters
};

/**
 * Fetches a route between two coordinates using Mapbox Directions API.
 * Returns coordinates, duration, and distance.
 */
export async function getRouteBetweenPoints(
  id: string,
  origin: [number, number],
  destination: [number, number]
): Promise<RouteInfo | null> {
  try {
    const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${origin[0]},${origin[1]};${destination[0]},${destination[1]}`;
    const params = {
      geometries: 'geojson',
      access_token: mapboxgl.accessToken,
    };

    const response = await axios.get(url, { params });

    if (!response.data?.routes?.length) {
      // console.warn('No routes found between points:', origin, destination);
      return null;
    }

    const route = response.data.routes[0];
    const coordinates: [number, number][] = route.geometry.coordinates;
    const duration: number = route.duration; // in seconds
    const distance: number = route.distance; // in meters

    return { id, coordinates, duration, distance };
  } catch {
    // console.error('Failed to fetch route info:', error);
    return null;
  }
}
