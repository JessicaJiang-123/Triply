import type { ReactElement } from 'react';
import PlaceImagePreview from './PlaceImagePreview';
import CommentList from './CommentList';
import AddCommentForm from './AddCommentForm';
import { useState } from 'react';

type Props = {
  mapboxId?: string | null;
  placeName?: string;
  onClose?: () => void;
  maxWidth?: number;
};

export default function PlaceCommentPanel({
  mapboxId,
  placeName,
  onClose,
  maxWidth = 720,
}: Props): ReactElement | null {
  const [refresh, setRefresh] = useState(0);
  if (!mapboxId) return null;

  return (
    <div
      className="p-3 d-flex flex-column"
      style={{ height: '100%', position: 'relative' }}
    >
      <div className="d-flex justify-content-between align-items-start mb-2">
        <div className="mb-0 fw-bold fs-4">{placeName || 'Place'}</div>
        <button
          type="button"
          className="btn-close"
          aria-label="Close"
          onClick={onClose}
        ></button>
      </div>

      <PlaceImagePreview mapboxId={mapboxId} placeName={placeName} />

      <div style={{ marginTop: 12 }} className="d-flex flex-column">
        <h5 className="mb-3">Real Comments</h5>
        {/* make the comment list take the remaining space and scroll */}
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 120 }}>
          <CommentList mapboxId={mapboxId} refreshKey={refresh} />
        </div>
      </div>

      {/* absolutely positioned add comment form centered at bottom */}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          bottom: 12,
          transform: 'translateX(-50%)',
          width: '100%',
          paddingLeft: 12,
          paddingRight: 12,
        }}
      >
        <div style={{ maxWidth: maxWidth, margin: '0 auto' }}>
          <AddCommentForm
            mapboxId={mapboxId}
            onPosted={() => {
              // bump refreshKey in parent to make CommentList and Image Preview refetch
              setRefresh((r) => r + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}
