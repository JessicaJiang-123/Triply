import axios from 'axios';

export async function getCoordinatesFromAddress(
  address: string
): Promise<[number, number]> {
  const accessToken = import.meta.env.VITE_MAPBOX_TOKEN;
  const encodedAddress = encodeURIComponent(address);
  const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodedAddress}.json?access_token=${accessToken}`;

  const response = await axios.get(url);

  if (!response.data.features || response.data.features.length === 0) {
    throw new Error('Address could not be geocoded.');
  }

  return response.data.features[0].center;
}
