// Define TypeScript types for Trip, Day, and Place

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
  mapbox_id?: string;
};

export type Day = {
  id: number;
  date: string;
  order: number;
  places: Place[];
};

export type Trip = {
  id: number;
  name: string;
  destination_city: string;
  start_date: string;
  end_date: string;
  days: Day[];
  share_uuid: string;
  image_url?: string;
  firstDayId?: number;
};

export type SharedPlace = {
  mapbox_id: string;
  name: string;
  latitude?: number;
  longitude?: number;
}

export type PlaceComment = {
  id: number;
  mapbox_id: string;
  text: string;
  created_at: string;
  author: { id: number; username: string; } | null;
  images?: CommentImage[];
};

export type CommentImage = {
  id: number;
  mapbox_id: string;
  comment_id: number;
  image_url: string;
  created_at: string;
  uploaded_by?: { id: number; username: string; } | null;
}