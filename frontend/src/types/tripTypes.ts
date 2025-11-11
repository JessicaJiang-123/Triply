// Define TypeScript types for Trip, Day, Place, and RouteSegment

export type Place = {
  id: number;
  name: string;
  category?: string;
  start_time?: string;
  end_time?: string;
  notes?: string;
  order: number;
  latitude?: number;
  longitude?: number;
  image_url?: string;
  address?: string;
};

export type Day = {
  id: number;
  date: string;
  order: number;
  places: Place[];
  routes?: RouteSegment[];
};

export type Trip = {
  id: number;
  name: string;
  destination_city: string;
  latitude?: number;
  longitude?: number;
  start_date: string;
  end_date: string;
  days: Day[];
  share_uuid: string;
  image_url?: string;
  firstDayId?: number;
};

export type RouteSegment = {
  id: number;
  route_id: string;
  from_place_name: string;
  to_place_name: string;
  distance_km: number;
  travel_time_min: number;
  coordinates: [number, number][];
};
