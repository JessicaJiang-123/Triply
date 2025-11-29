export default function NotFoundPage() {
  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#fafafa',
        color: '#333',
      }}
    >
      <h1 style={{ fontSize: '64px', marginBottom: '10px' }}>404</h1>
      <p style={{ fontSize: '20px', marginBottom: '20px' }}>Page Not Found</p>
      <a href="/trips" style={{ color: '#0d6efd', fontSize: '18px' }}>
        Go back to homepage
      </a>
    </div>
  );
}
