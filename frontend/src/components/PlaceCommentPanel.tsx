import type { ReactElement } from 'react';
import PlaceImagePreview from './PlaceImagePreview';

type Props = {
	mapboxId?: string | null;
	placeName?: string;
};

export default function PlaceCommentPanel({ mapboxId, placeName }: Props): ReactElement | null {
	return <PlaceImagePreview mapboxId={mapboxId} placeName={placeName} />;
}
