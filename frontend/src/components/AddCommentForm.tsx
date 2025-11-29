import { useState } from 'react';
import type { ReactElement } from 'react';
import { Button, InputGroup, FormControl } from 'react-bootstrap';
import axiosInstance from '../api/axiosInstance';

type Props = {
  mapboxId?: string | null;
  onPosted?: () => void;
};

export default function AddCommentForm({
  mapboxId,
  onPosted,
}: Props): ReactElement | null {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  if (!mapboxId) return null;

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!text.trim() && imageUrls.length === 0) return;
    setLoading(true);
    setError(null);
    setUploadError(null);
    try {
      await axiosInstance.post(
        `/api/plans/places/by-mapbox/${encodeURIComponent(mapboxId)}/comments/`,
        {
          text: text.trim(),
          image_urls: imageUrls,
        }
      );
      setText('');
      setImageUrls([]);
      onPosted?.();
    } catch {
      // console.error('Failed to post comment', err);
      setError('Failed to post comment');
    } finally {
      setLoading(false);
    }
  };

  const handleFilesSelected = async (files?: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploadError(null);
    setUploading(true);
    try {
      const maxFiles = Math.max(0, 3 - imageUrls.length);
      const toUpload = Array.from(files).slice(0, maxFiles);
      // client-side validation: type and size (5MB)
      const MAX_SIZE = 5 * 1024 * 1024;
      for (const f of toUpload) {
        if (!f.type.startsWith('image/')) {
          setUploadError('Only image files are allowed');
          setUploading(false);
          return;
        }
        if (f.size > MAX_SIZE) {
          setUploadError('Each image must be smaller than 5MB');
          setUploading(false);
          return;
        }
      }
      if (toUpload.length === 0) {
        setUploadError('You can only attach up to 3 images per comment.');
        return;
      }

      const form = new FormData();
      toUpload.forEach((f) => form.append('images', f));
      // include mapbox_id so backend can attach to place if no comment yet
      form.append('mapbox_id', mapboxId || '');

      const resp = await axiosInstance.post(
        '/api/plans/comments/upload-images/',
        form,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      );

      // response expected shape: { images: Array<string | { image_url: string }> }
      const imgs = resp.data?.images || [];
      const urls = imgs
        .map((i: unknown) => {
          if (typeof i === 'string') return i;
          if (
            i &&
            typeof i === 'object' &&
            'image_url' in (i as Record<string, unknown>)
          ) {
            const obj = i as Record<string, unknown>;
            const v = obj['image_url'];
            return typeof v === 'string' ? v : undefined;
          }
          return undefined;
        })
        .filter(Boolean) as string[];
      setImageUrls((s) => [...s, ...urls].slice(0, 3));
    } catch {
      // console.error('Upload failed', err);
      setUploadError('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-3">
      <InputGroup>
        <FormControl
          placeholder="Leave your comments here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading}
        />
        <label className="btn btn-light mb-0" title="Upload image">
          <i className="bi bi-image" />
          <input
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            multiple
            onClick={(e) => {
              // prevent opening file picker when already at limit and show an error
              if (imageUrls.length >= 3) {
                e.preventDefault();
                setUploadError('You can only upload up to 3 images');
                return;
              }
              // clear previous upload errors when user intentionally opens picker
              setUploadError(null);
            }}
            onChange={(e) => handleFilesSelected(e.target.files)}
            disabled={uploading || loading}
          />
        </label>
        <Button
          variant="primary"
          type="submit"
          disabled={loading || (!text.trim() && imageUrls.length === 0)}
        >
          {loading ? 'Posting…' : 'Post'}
        </Button>
      </InputGroup>

      {uploading && <div className="small text-muted mt-2">Uploading…</div>}
      {uploadError && (
        <div className="text-danger small mt-2">{uploadError}</div>
      )}

      {imageUrls.length > 0 && (
        <div className="d-flex gap-2 mt-2">
          {imageUrls.map((u, idx) => (
            <div
              key={idx}
              style={{
                width: 80,
                height: 60,
                overflow: 'hidden',
                borderRadius: 8,
                position: 'relative',
              }}
            >
              <img
                src={u}
                alt={`img-${idx}`}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              <button
                type="button"
                className="btn-close"
                aria-label={`Remove image ${idx + 1}`}
                style={{ position: 'absolute', top: 4, right: 4 }}
                onClick={() =>
                  setImageUrls((s) => s.filter((_, i) => i !== idx))
                }
              />
            </div>
          ))}
        </div>
      )}
      {error && <div className="text-danger small mt-2">{error}</div>}
    </form>
  );
}
