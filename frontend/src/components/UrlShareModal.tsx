import { useState } from 'react';
import { Modal, Button, Form, Alert, InputGroup } from 'react-bootstrap';
import axiosInstance from '../api/axiosInstance';

interface UrlShareModalProps {
  show: boolean;
  onHide: () => void;
  tripId: number | null;
}

export default function UrlShareModal({ show, onHide, tripId }: UrlShareModalProps) {
  const [permission, setPermission] = useState('read'); // Default to 'read'
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Calls the backend API to create or retrieve a ShareLink.
  const handleGenerateLink = async () => {
    if (!tripId) return;
    
    setLoading(true);
    setError(null);
    setGeneratedUrl(null);
    setCopied(false);

    try {
      // Call the new backend @action
      const response = await axiosInstance.post(
        `/api/plans/trips/${tripId}/create-link/`,
        { permission_level: permission }
      );
      // Store the returned URL to switch the modal's UI state
      setGeneratedUrl(response.data.url);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create link");
    } finally {
      setLoading(false);
    }
  };

  // Copies the generated URL to clipboard and shows "Copied!" feedback.
  const handleCopyToClipboard = () => {
    if (generatedUrl) {
      navigator.clipboard.writeText(generatedUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Resets all states to ensure the modal is clean when re-opened.
  const handleClose = () => {
    setGeneratedUrl(null);
    setError(null);
    setPermission('read');
    setCopied(false);
    onHide();
  };

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>
          <i className="bi bi-link-45deg me-2"></i>
          Share Trip Link
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        
        {/* conditional render: IF 'generatedUrl' exists, show Status A (Copy Link); ELSE, show Status B (Generate Link). */}
        {/* Status A: Show the generated link */}
        {generatedUrl ? (
          <Form.Group>
            <Form.Label>
                {`Generated Link (${permission === 'read' ? 'Read-Only' : 'Editable'})`}
            </Form.Label>
            <InputGroup>
              <Form.Control 
                type="text" 
                value={generatedUrl} 
                readOnly 
              />
              <Button variant="outline-primary" onClick={handleCopyToClipboard}>
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </InputGroup>
          </Form.Group>
        ) : (
          // Status B: Show the permission selection
          <Form>
            <Form.Group>
              <Form.Label>
                Select Permission Level
              </Form.Label>
              <Form.Select 
                value={permission} 
                onChange={(e) => setPermission(e.target.value)}
              >
                <option value="read">Read-Only (Viewer)</option>
                <option value="edit">Editable (Editor)</option>
              </Form.Select>
              <Form.Text className="text-muted">
                "Editable" permission allows others to add, delete, or modify places.
              </Form.Text>
            </Form.Group>
            <Button 
              variant="primary" 
              onClick={handleGenerateLink} 
              disabled={loading}
              className="mt-3 w-100"
            >
              {loading ? 'Generating...' : 'Generate Share Link'}
            </Button>
          </Form>
        )}
        </Modal.Body>
    </Modal>
  );
}