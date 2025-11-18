import { Card } from 'react-bootstrap';
import { useState, type ReactElement } from 'react';
import type { CommentImage, PlaceComment } from '../types/tripTypes';


type CommentCardProps = {
  comment: PlaceComment;
};

export default function CommentCard({
  comment,
}: CommentCardProps): ReactElement {
  

  const authorName = comment.author?.username ?? 'Someone';
  const text = comment.text;
  const createdAt = comment.created_at;
  const images: CommentImage[] = comment.images ?? [];

  // Formt date (fallbck to raw strng if parsing fail)
  let dateLabel = createdAt;
  try {
    const d = new Date(createdAt);
    if (!Number.isNaN(d.getTime())) {
      dateLabel = d.toLocaleDateString(undefined, { year: 'numeric', month: 'numeric', day: 'numeric' });
    }
  } catch {
    // leave createdAt as-is
  }
  // determine avatar src: prefer comment author's picture, else null
  const avatarSrc = comment.author?.picture ?? null;
  const [avatarLoadFailed, setAvatarLoadFailed] = useState(false);

  return (
    <Card className="mb-3">
      <Card.Body>
        {/* Header: avatar + author name */}
        <div className="d-flex align-items-center mb-2">
          {/* avatar */}
          <div
            className="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center me-3"
            style={{ width: 40, height: 40, flex: '0 0 auto', overflow: 'hidden' }}
            aria-hidden
          >
            {avatarSrc && !avatarLoadFailed ? (
              <img
                src={avatarSrc}
                alt={`${authorName} avatar`}
                className="w-100 h-100"
                style={{ objectFit: 'cover', borderRadius: '50%', display: 'block' }}
                onError={() => {
                  // mark failed so React will render the initials fallback
                  setAvatarLoadFailed(true);
                }}
                onLoad={() => setAvatarLoadFailed(false)}
              />
            ) : (
              // initials fallback
              <div style={{ width: 40, height: 40, lineHeight: '40px', textAlign: 'center' }}>
                {authorName.charAt(0).toUpperCase()}
              </div>
            )}
          </div>

          <div className="flex-grow-1">
            <div className="fw-semibold">{authorName}</div>
            <div className="text-muted small">&nbsp;</div>
          </div>
        </div>

  {/* Comment text */}
  <div className="mb-2 text-break" style={{ wordBreak: 'break-word' }}>{text}</div>

        {/* Thumbnails */}
        {images.length > 0 && (
          <div className="d-flex align-items-start mb-1">
            {images.map((img, idx) => (
              <div
                key={img.id}
                className={idx === 0 ? 'me-2' : ''}
                style={{ width: 150, height: 100, borderRadius: 12, overflow: 'hidden' }}
              >
                <img
                  src={img.image_url}
                  alt={`Comment image ${img.id}`}
                  className="w-100 h-100"
                  style={{ objectFit: 'cover', display: 'block' }}
                />
              </div>
            ))}
          </div>
        )}

        {/* Date */}
        <div className="text-muted small">{dateLabel}</div>
      </Card.Body>
    </Card>
  );
}