import { useEffect, useState } from 'react';
import type { ReactElement } from 'react';
import axiosInstance from '../api/axiosInstance';
import type { CommentImage } from '../types/tripTypes';

type ImagePreviewProps = {
    mapboxId?: string | null;
    placeName?: string;
};

export default function PlaceImagePreview({
    mapboxId,
}: ImagePreviewProps): ReactElement | null {
    const [images, setImages] = useState<CommentImage[] | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!mapboxId) {
            setImages(null);
            return;
        }

        let mounted = true;
        const fetchImages = async () => {
            setLoading(true);
            try {
                const res = await axiosInstance.get(
                    `/api/plans/places/by-mapbox/${encodeURIComponent(mapboxId)}/comment-images/`
                );
                if (!mounted) return;
                // Map backend response into CommentImage[] safely
                const raw = res.data || [];
                const imgsUnfiltered: Array<CommentImage | null> = raw.map(
                    (it: unknown) => {
                        if (it && typeof it === 'object') {
                            const o = it as Record<string, unknown>;
                            const id = typeof o.id === 'number' ? o.id : -1;
                            const url = typeof o.image_url === 'string' ? o.image_url : '';
                            const created_at =
                                typeof o.created_at === 'string' ? o.created_at : '';
                            return { id, image_url: url, created_at } as CommentImage;
                        }
                        return null;
                    }
                );
                const imgs: CommentImage[] = imgsUnfiltered.filter(
                    (v): v is CommentImage => !!v && v.image_url !== ''
                );
                setImages(imgs);
            } catch (err) {
                console.error('Failed to fetch comment images', err);
                if (!mounted) return;
                setImages([]);
            } finally {
                if (mounted) setLoading(false);
            }
        };

        fetchImages();

        return () => {
            mounted = false;
        };

    }, [mapboxId]);

    // When images === null => no mapboxId selected; render nothing
    if (!mapboxId) return null;

    // Loading state: show place name and spinner-like text
    if (loading) {
        return (
            <div>
                <div className="text-muted">Loading images…</div>
            </div>
        );
    }

    const list = images || [];

    // If no images found, render
    if (list.length === 0) {
        return <div className="text-muted">Waiting for your images!</div>;
    }

    // Render horizontal image strip (inline within panel)
    return (
        <div>
            {/* Image strip: use Bootstrap utilities for layout and spacing */}
            <div
                className="d-flex gap-3 flex-nowrap p-2 bg-white rounded"
                style={{
                    overflowX: 'auto',
                    WebkitOverflowScrolling: 'touch',
                    background: 'rgba(255,255,255,0.95)',
                    boxShadow: '0 6px 20px rgba(0,0,0,0.04)',
                }}
            >
                {list.map((img, idx) => (
                    <div
                        key={img.id || idx}
                        className="flex-shrink-0 rounded overflow-hidden"
                        style={{ minWidth: 240, height: 160 }}
                    >
                        <img
                            src={img.image_url}
                            alt={`place-img-${img.id || idx}`}
                            className="img-fluid h-100 w-100"
                            style={{ objectFit: 'cover' }}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
