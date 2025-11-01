import { FcGoogle } from 'react-icons/fc';

type Props = {
  label: string;
  href?: string;
  onClick?: () => void;
};

const googleIcon = <FcGoogle size={24} />;

export default function OAuthButton({ label, href, onClick }: Props) {
  const content = (
    <div
      className="oauth-btn"
      role={href ? 'link' : 'button'}
      aria-label={label}
      tabIndex={0}
    >
      {googleIcon}
      <span>{label}</span>
    </div>
  );

  if (href) {
    return (
      <a href={href} className="text-decoration-none" onClick={onClick}>
        {content}
      </a>
    );
  }

  return (
    <button className="btn btn-link p-0" onClick={onClick}>
      {content}
    </button>
  );
}
