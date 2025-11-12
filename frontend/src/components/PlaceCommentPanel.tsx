import type { ReactElement } from 'react';
import PlaceImagePreview from './PlaceImagePreview';
import CommentList from './CommentList';
import AddCommentForm from './AddCommentForm';

type Props = {
	mapboxId?: string | null;
	placeName?: string;
	onClose?: () => void;
};

export default function PlaceCommentPanel({ mapboxId, placeName, onClose }: Props): ReactElement | null {
	if (!mapboxId) return null;

	return (
		<div className="p-3 d-flex flex-column" style={{ height: '100%', position: 'relative' }}>
			<div className="d-flex justify-content-between align-items-start mb-2">
				<div className="fw-semibold">{placeName || 'Place'}</div>
				<button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
			</div>

			<PlaceImagePreview mapboxId={mapboxId} placeName={placeName} />

			<div style={{ marginTop: 12 }} className="d-flex flex-column" >
				<h5 className="mb-3">Real Comments</h5>
				{/* make the comment list take the remaining space and scroll */}
				<div style={{ flex: 1, overflowY: 'auto' }}>
					<CommentList mapboxId={mapboxId} />
				</div>
			</div>

			{/* fixed add comment form at bottom */}
			<div style={{ position: 'sticky', bottom: 0, background: 'white', paddingTop: 12 }}>
				<AddCommentForm mapboxId={mapboxId} onPosted={() => { /* could refresh list via event or refetch in CommentList */ }} />
			</div>
		</div>
	);
}
