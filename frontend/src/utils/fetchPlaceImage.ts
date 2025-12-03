import axios from 'axios';

/**
 * Fetches a relevant image for a place or city using the Unsplash API.
 *
 * @param placeName - The name of the place or city to search for (e.g., "Paris", "Times Square")
 * @param nums - Number of images to fetch (default is 1)
 * @returns A Promise that resolves to an array of image URL strings
 */
export async function fetchPlaceImage(
  placeName: string,
  nums: number = 1
): Promise<string[]> {
  // console.log('Fetching image for place:', placeName);
  if (!placeName) return [];

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

    if (!results || results.length === 0) {
      return [];
    }

    // Extract image URLs
    const allImages = results
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .map((r: any) => r?.urls?.raw)
      .filter((url: string | undefined) => Boolean(url));

    if (allImages.length === 0) {
      return [];
    }

    // If enough images, pick `nums` random ones
    if (allImages.length >= nums) {
      const selected: string[] = [];
      const used = new Set<number>();

      while (selected.length < nums) {
        const idx = Math.floor(Math.random() * allImages.length);
        if (!used.has(idx)) {
          selected.push(allImages[idx]);
          used.add(idx);
        }
      }

      return selected;
    }

    // If fewer than `nums`, return all available
    return allImages;
  } catch {
    // console.error('Failed to fetch place image:', error);
    return [];
  }
}
