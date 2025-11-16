import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axiosInstance from '../api/axiosInstance';
import { Alert, Container } from 'react-bootstrap';

/**
 * A "loader" or "bridge" that handles the logic for a public share URL.
 */
export default function PublicTripLoader() {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!uuid) {
      setError('No share token provided in URL.');
      setLoading(false);
      return;
    }

    const fetchLinkInfo = async () => {
      try {
        const response = await axiosInstance.get(
          `/api/plans/public/link-info/${uuid}/`
        );
        const { trip_id, firstDayId, permission_level } = response.data;

        if (!trip_id || !firstDayId) {
          throw new Error("Invalid trip data received from server.");
        }

        // Inject the uuid as the 'X-Share-Token' header
        // All future axios requests will now carry this header automatically.
        axiosInstance.defaults.headers.common['X-Share-Token'] = uuid;
        
        // Store the permission level in localStorage
        localStorage.setItem('share_permission', permission_level);
        localStorage.setItem('active_share_token', uuid);

        // Redirect to the actual PlanDetailPage
        setLoading(false);
        navigate(`/trips/${trip_id}/days/${firstDayId}`, { replace: true });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } catch (err: any) {
        console.error("Failed to fetch share link info:", err);
        setError(err.response?.data?.detail || "This share link is invalid or has expired.");
        setLoading(false);
      }
    };

    fetchLinkInfo();
  }, [uuid, navigate]);

  if (loading) {
    return (
      <Container className="text-center mt-5">
        <h1>Loading Shared Trip...</h1>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="text-center mt-5">
        <Alert variant="danger">
          <h1>Error</h1>
          <p>{error}</p>
        </Alert>
      </Container>
    );
  }

  return null;
}