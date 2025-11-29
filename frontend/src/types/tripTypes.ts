// Define TypeScript types for Trip, Day, Place, and RouteSegment

export type SimpleUser = {
  id: number;
  username: string;
  email: string;
};

export type CurrentUser = SimpleUser & {
  is_authenticated: boolean;
  picture?: string;
};

export type UnsplashImage = {
  unsplash_url: string;
  local_image_url?: string;
};

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
  unsplash_image?: UnsplashImage;
  address?: string;
  mapbox_id?: string;
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
  unsplash_image?: UnsplashImage;
  firstDayId?: number;
  owner: SimpleUser;
  shared_users: SimpleUser[];
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

export type SharedPlace = {
  mapbox_id: string;
  name: string;
};

export type PlaceComment = {
  id: number;
  mapbox_id: string;
  text: string;
  created_at: string;
  author: { id: number; username: string; avatar: string } | null;
  images?: CommentImage[];
};

export type CommentImage = {
  id: number;
  mapbox_id: string;
  comment_id: number;
  image_url: string;
  created_at: string;
  uploaded_by?: { id: number; username: string } | null;
};
