import { Card } from 'react-bootstrap';
import { useState, type ReactElement } from 'react';
import type { CommentImage, PlaceComment } from '../types/tripTypes';
import ImageLightbox from './ImageLightBox';

type CommentCardProps = {
  comment: PlaceComment;
};

export default function CommentCard({
  comment,
}: CommentCardProps): ReactElement {
  const authorName = comment.author?.username ?? 'Someone';
  const [avatarFailed, setAvatarFailed] = useState(false);
  const authorAvatar = comment.author?.avatar ?? null;
  const text = comment.text;
  const createdAt = comment.created_at;
  const images: CommentImage[] = comment.images ?? [];
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);

  // Format date (fallback to raw string if parsing fails)
  let dateLabel = createdAt;
  try {
    const d = new Date(createdAt);
    if (!Number.isNaN(d.getTime())) {
      dateLabel = d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
      });
    }
  } catch {
    // leave createdAt as-is
  }
  return (
    <Card className="mb-3">
      <Card.Body>
        {/* Header: avatar + author name */}
        <div className="d-flex align-items-center mb-2">
          {/* avatar */}
          <div
            className="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center me-3"
            style={{ width: 40, height: 40, flex: '0 0 auto' }}
            aria-hidden
          >
            {authorAvatar && !avatarFailed ? (
              <img
                src={authorAvatar}
                alt="User avatar"
                className="w-100 h-100"
                style={{
                  objectFit: 'cover',
                  borderRadius: '50%',
                  display: 'block',
                }}
                onError={() => setAvatarFailed(true)}
                onLoad={() => setAvatarFailed(false)}
              />
            ) : (
              // initials fallback
              <div
                style={{
                  width: 40,
                  height: 40,
                  lineHeight: '40px',
                  textAlign: 'center',
                }}
              >
                {authorName ? authorName.charAt(0).toUpperCase() : '?'}
              </div>
            )}
          </div>

          {/* author name */}
          <div>
            <div className="fw-semibold">{authorName}</div>
          </div>
        </div>

        {/* Comment text */}
        <div className="mb-2 text-break" style={{ wordBreak: 'break-word' }}>
          {text}
        </div>

        {/* Thumbnails */}
        {images.length > 0 && (
          <div className="d-flex align-items-start mb-1">
            {images.map((img) => (
              <div
                key={img.id}
                style={{
                  flex: '0 0 auto',
                  width: 150,
                  height: 100,
                  borderRadius: 12,
                  overflow: 'hidden',
                  position: 'relative',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                  background: '#f6f6f6',
                  marginRight: 12,
                }}
              >
                <img
                  src={img.image_url}
                  alt={`Comment image ${img.id}`}
                  className="w-100 h-100"
                  style={{
                    objectFit: 'cover',
                    display: 'block',
                    cursor: 'pointer',
                  }}
                  onClick={() => setLightboxUrl(img.image_url)}
                  loading="lazy"
                />
              </div>
            ))}
          </div>
        )}

        {/* Date */}
        <div className="text-muted small">{dateLabel}</div>
      </Card.Body>
      {/* render Lightbox */}
      <ImageLightbox
        show={!!lightboxUrl}
        url={lightboxUrl}
        onClose={() => setLightboxUrl(null)}
      />
    </Card>
  );
}
