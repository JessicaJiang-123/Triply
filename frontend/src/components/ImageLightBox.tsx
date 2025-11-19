import { Modal } from 'react-bootstrap';
import type { ReactElement } from 'react';

type Props = {
  show: boolean;
  url?: string | null;
  onClose: () => void;
};

export default function ImageLightbox({ show, url, onClose }: Props): ReactElement {
  return (
    <Modal show={show} onHide={onClose} centered size="lg">
      <Modal.Body className="p-0 d-flex justify-content-center align-items-center" style={{ background: '#000' }}>
        {url ? (
          <img src={url} alt="Preview" style={{ maxWidth: '100%', maxHeight: '80vh', objectFit: 'contain' }} loading="lazy" />
        ) : null}
      </Modal.Body>
    </Modal>
  );
}