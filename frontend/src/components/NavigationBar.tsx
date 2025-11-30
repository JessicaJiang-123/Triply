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
    } catch {
      // console.error('Logout failed:', error);
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

          {/* Hide title on mobile */}
          {title && (
            <span className="fw-semibold text-secondary fs-5 d-none d-md-inline">
              {title}
            </span>
          )}
        </div>

        <Navbar.Toggle aria-controls="user-nav-content" />
        <Navbar.Collapse id="user-nav-content" className="justify-content-end">
          {/* Right: User info & Logout */}
          {currentUser && (
            <>
              {/* Desktop layout (inline) */}
              <Nav className="ms-auto align-items-center d-none d-md-flex">
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

                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={handleLogout}
                >
                  Logout
                </Button>
              </Nav>

              {/* Mobile layout (stacked, centered) */}
              <Nav className="d-flex flex-column d-md-none mt-3 text-center w-100">
                {/* Line 1: Welcome */}
                <span className="text-dark mb-2 w-100">
                  Welcome, <strong>{currentUser.username}</strong>
                </span>

                {/* Line 2: Avatar + Logout (centered row) */}
                <div className="d-flex justify-content-center align-items-center w-100">
                  <Image
                    src={currentUser.picture}
                    alt="User avatar"
                    roundedCircle
                    width={40}
                    height={40}
                    className="me-3 border border-primary"
                    referrerPolicy="no-referrer"
                  />

                  <Button
                    variant="outline-danger"
                    size="sm"
                    onClick={handleLogout}
                  >
                    Logout
                  </Button>
                </div>
              </Nav>
            </>
          )}
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
