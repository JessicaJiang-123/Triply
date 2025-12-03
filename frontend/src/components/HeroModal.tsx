import OAuthButton from './OAuthButton';
import '../css/HeroModal.css';

export default function HeroModal() {
  const DEBUG = import.meta.env.VITE_DEBUG === 'true';

  // OAuth endpoints
  let googleHref = '';
  if (DEBUG) {
    googleHref = `${import.meta.env.VITE_API_BASE_URL || ''}/oauth/login/google-oauth2/`;
  } else {
    googleHref = '/oauth/login/google-oauth2/';
  }

  return (
    <div className="hero-wrapper">
      <div
        className="hero-background"
        style={{ backgroundImage: `url('/login_bg.jpg')` }}
      />
      <div className="hero-overlay" />

      <div className="glass-card text-white">
        <div className="text-center mb-3">
          <div className="brand">Triply</div>
          <div className="gradient-title">Welcome to Triply</div>
          <div className="subtitle">AI powered trip planner</div>
        </div>

        <div className="d-grid gap-2">
          <div className="btn-gap">
            <OAuthButton label="Continue with Google" href={googleHref} />
          </div>
        </div>
      </div>
    </div>
  );
}
