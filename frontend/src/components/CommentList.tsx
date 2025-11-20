import { useEffect, useState } from 'react';
import type { ReactElement } from 'react';
import axiosInstance from '../api/axiosInstance';
import type { PlaceComment } from '../types/tripTypes';
import CommentCard from './CommentCard';

type Props = {
  mapboxId?: string | null;
  refreshKey?: number;
};

export default function CommentList({
  mapboxId,
  refreshKey,
}: Props): ReactElement | null {
  const [comments, setComments] = useState<PlaceComment[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!mapboxId) {
      setComments(null);
      return;
    }

    let cancelled = false;
    const fetchComments = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axiosInstance.get(
          `/api/plans/places/by-mapbox/${encodeURIComponent(mapboxId)}/comments/`
        );
        if (cancelled) return;
        setComments(res.data || []);
      } catch {
        if (cancelled) return;
        // console.error('Failed to load comments', err);
        setError('Failed to load comments');
        setComments([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchComments();
    return () => {
      cancelled = true;
    };
  }, [mapboxId, refreshKey]);

  if (!mapboxId) return null;

  if (loading) return <div className="text-muted">Loading comments…</div>;
  if (error) return <div className="text-danger">{error}</div>;

  const list = comments || [];

  if (list.length === 0)
    return <div className="text-muted">No comments yet.</div>;

  // Render a self-contained scrollable list. Parent can override sizing via CSS if needed.
  return (
    <div
      className="comment-list-scrollable"
      style={{ maxHeight: '60vh', overflowY: 'auto', paddingRight: '0.5rem' }}
      role="list"
    >
      {list.map((c) => (
        <div role="listitem" key={c.id}>
          <CommentCard comment={c} />
        </div>
      ))}
    </div>
  );
}
