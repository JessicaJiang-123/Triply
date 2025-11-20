import { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Navbar,
  Container,
  Nav,
  Button,
  Image,
  Tooltip,
  OverlayTrigger,
} from 'react-bootstrap';
import { AuthContext } from '../context/AuthContext';
import axiosInstance from '../api/axiosInstance';

type NavigationBarProps = {
  title?: string;
};

export default function NavigationBar({ title }: NavigationBarProps) {
  const { currentUser, setCurrentUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await axiosInstance.post('/api/user/logout/');
      setCurrentUser(null);
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <Navbar
      bg="light"
      expand="md"
      sticky="top"
      className="border-bottom shadow-sm px-3 w-100"
      style={{ minHeight: '64px' }} // Fixed height for consistency
    >
      <Container fluid>
        {/* Left: Brand + Optional Title */}
        <div className="d-flex align-items-center gap-3">
          <OverlayTrigger
            placement="bottom"
            overlay={
              <Tooltip id="tooltip-triply">
                Click to go back to the travel plan page
              </Tooltip>
            }
          >
            <Navbar.Brand
              as={Link}
              to="/trips"
              className="fw-bold text-primary fs-4 mb-0"
              style={{ cursor: 'pointer' }}
            >
              Triply
            </Navbar.Brand>
          </OverlayTrigger>

          {title && (
            <span className="fw-semibold text-secondary fs-5">{title}</span>
          )}
        </div>

        <Navbar.Toggle aria-controls="user-nav-content" />
        <Navbar.Collapse id="user-nav-content" className="justify-content-end">
          {/* Right: User info & Logout */}
          {currentUser && (
            <Nav className="ms-auto align-items-center">
              <span className="me-2 text-dark">
                Welcome, <strong>{currentUser.username}</strong>
              </span>
              <Image
                src={currentUser.picture}
                alt="User avatar"
                roundedCircle
                width={36}
                height={36}
                className="me-3 border border-primary"
                referrerPolicy="no-referrer"
              />
              <Button variant="outline-danger" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </Nav>
          )}
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
