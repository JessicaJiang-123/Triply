import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // e.g. http://localhost:8000
  withCredentials: true, // allow sending cookies
});

function getCSRFToken(): string | null {
  const match = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
  return match ? match[2] : null;
}

axiosInstance.interceptors.request.use((config) => {
  // Add CSRF token to non-GET requests
  if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(config.method || '')) {
    const token = getCSRFToken();
    if (token) config.headers['X-CSRFToken'] = token;
  }
  return config;
});

export default axiosInstance;
