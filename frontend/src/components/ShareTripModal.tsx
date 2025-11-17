import { useState } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';
import axiosInstance from '../api/axiosInstance';


interface ShareModalProps {
  show: boolean;  // show: controls whether the modal is visible
  onHide: () => void;  // onHide: function to call to hide the modal
  tripId: number | null;
}

export default function ShareTripModal({ show, onHide, tripId }: ShareModalProps) {

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tripId || !email) return;

    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      // sent POST request to '/api/plans/trips/{tripId}/share/' with body: { email: email }
      const response = await axiosInstance.post(
        `/api/plans/trips/${tripId}/share/`,
        { email: email }
      );
      
      setSuccessMsg(response.data.message || 'Trip shared successfully!');
      setEmail('');

      setTimeout(() => {
        onHide();
        setSuccessMsg(null);
      }, 2000);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      console.error('Failed to share trip:', err);
      setError(err.response?.data?.detail || 'Failed to share trip. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (loading) return; 

    setEmail('');
    setError(null);
    setSuccessMsg(null);
    onHide();
  };

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>
          <i className="bi bi-share-fill me-2"></i>
          Share Your Travel Plan
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        {/* status A: show success message */}
        {successMsg && (
          <Alert variant="success">{successMsg}</Alert>
        )}

        {/* status B: show email form (default) */}
        {!successMsg && (
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="shareEmail">
              <Form.Label>Enter the email of the user you want to share with:</Form.Label>
              <Form.Control
                type="email"
                placeholder="friend@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Form.Group>

            {/* status C: show error message */}
            {error && <Alert variant="danger" className="mt-3">{error}</Alert>}
            
            <div className="text-end mt-4">
              <Button variant="outline-secondary" onClick={handleClose} className="me-2">
                Cancel
              </Button>
              <Button variant="primary" type="submit" disabled={loading}>
                {loading ? 'Sharing...' : 'Share'}
              </Button>
            </div>
          </Form>
        )}
      </Modal.Body>
    </Modal>
  );
}