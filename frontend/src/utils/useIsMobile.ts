import { useEffect, useState } from 'react';

export function useIsMobile() {
  const getValue = () => window.innerWidth < 768; // match Bootstrap "md"

  const [isMobile, setIsMobile] = useState(getValue);

  useEffect(() => {
    const handleResize = () => setIsMobile(getValue());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return isMobile;
}
