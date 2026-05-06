import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function ServicesLayout({ children }: { children: ReactNode }) {
  return <PortalShell>{children}</PortalShell>;
}
