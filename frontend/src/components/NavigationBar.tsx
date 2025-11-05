import { useContext } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Navbar, Container, Nav, Button, Image } from 'react-bootstrap';
import { AuthContext } from '../context/AuthContext';
import axiosInstance from '../api/axiosInstance';

export default function NavigationBar() {
  const { currentUser, setCurrentUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

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
    >
      <Container fluid>
        {/* Left: optional back button + Logo / Brand */}
        <div className="d-flex align-items-center">
          {location.pathname.startsWith('/trips/') && location.pathname !== '/trips' && (
            <Image
              src="/images/arrow-left-square.png"
              alt="back"
              width={22}
              height={22}
              className="me-2"
              style={{ cursor: 'pointer' }}
              onClick={() => navigate('/trips')}
            />
          )}
          <Navbar.Brand as={Link} to="/trips" className="fw-bold text-primary fs-4">
            Triply
          </Navbar.Brand>
        </div>

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
      </Container>
    </Navbar>
  );
}
