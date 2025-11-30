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
      style={{
        height: '100%',
        position: 'relative',
        overflowY: 'auto',
      }}
    >
      <button
        type="button"
        onClick={onClose}
        style={{
          position: 'sticky',
          top: 4,
          right: 4,
          alignSelf: 'flex-end',
          padding: '4px 8px',
          border: '1px solid #ccc',
          borderRadius: 6,
          background: 'transparent',
          zIndex: 20,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = '#e9ecef';
          e.currentTarget.style.borderColor = '#999';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.borderColor = '#ccc';
        }}
      >
        <i className="bi bi-x-lg"></i>
      </button>

      <div className="mb-0 fw-bold fs-4 mb-2">{placeName || 'Place'}</div>

      <PlaceImagePreview
        mapboxId={mapboxId}
        placeName={placeName}
        refreshKey={refresh}
      />

      <div style={{ marginTop: 12 }} className="d-flex flex-column flex-grow-1">
        <h5 className="mb-3">Real Comments</h5>
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 120 }}>
          <CommentList mapboxId={mapboxId} refreshKey={refresh} />
        </div>
      </div>

      {/* absolutely positioned add comment form centered at bottom */}
      <div
        style={{
          position: 'sticky',
          bottom: 12,
          width: '100%',
          paddingLeft: 12,
          paddingRight: 12,
        }}
      >
        <div style={{ maxWidth: maxWidth, margin: '0 auto' }}>
          <AddCommentForm
            mapboxId={mapboxId}
            onPosted={() => {
              // bump refreshKey in parent to make CommentList refetch
              setRefresh((r) => r + 1);
            }}
          />
        </div>
      </div>
    </div>
  );
}
