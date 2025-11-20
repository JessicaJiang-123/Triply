import axios from 'axios';

// Default image URL to use if no relevant image is found
const defaultImage =
  'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg';

/**
 * Fetches a relevant image for a place or city using the Unsplash API.
 *
 * @param placeName - The name of the place or city to search for (e.g., "Paris", "Times Square")
 * @returns A Promise that resolves to an image URL string
 */
export async function fetchPlaceImage(placeName: string): Promise<string> {
  // console.log('Fetching image for place:', placeName);
  if (!placeName) return defaultImage;

  const accessKey = import.meta.env.VITE_UNSPLASH_ACCESS_KEY;
  const url = 'https://api.unsplash.com/search/photos';

  try {
    const response = await axios.get(url, {
      params: {
        query: placeName,
        client_id: accessKey,
        orientation: 'landscape',
        per_page: 10,
      },
    });

    const results = response.data?.results;

    if (results && results.length > 0) {
      // pick a random image from the list
      const randomIndex = Math.floor(Math.random() * results.length);
      const imageUrl = results[randomIndex]?.urls?.raw || results[0]?.urls?.raw;
      return imageUrl;
    }
    return defaultImage;
  } catch {
    // console.error('Failed to fetch place image:', error);
    return defaultImage;
  }
}
