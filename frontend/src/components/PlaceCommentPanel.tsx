import type { ReactElement } from 'react';
import PlaceImagePreview from './PlaceImagePreview';
import CommentList from './CommentList';

type Props = {
	mapboxId?: string | null;
	placeName?: string;
	onClose?: () => void;
};

export default function PlaceCommentPanel({ mapboxId, placeName, onClose }: Props): ReactElement | null {
	if (!mapboxId) return null;

	return (
		<div
			style={{
				position: 'fixed',
				top: 80,
				right: 24,
				width: '48vw',
				maxWidth: 720,
				zIndex: 1100,
			}}
		>
			<div className="d-flex justify-content-between align-items-start mb-2">
				<div className="fw-semibold">{placeName || 'Place'}</div>
				<button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
			</div>

			<PlaceImagePreview mapboxId={mapboxId} placeName={placeName} />

			<div style={{ marginTop: 12 }}>
				<h5 className="mb-3">Real Comments</h5>
				<CommentList mapboxId={mapboxId} />
			</div>
		</div>
	);
}
