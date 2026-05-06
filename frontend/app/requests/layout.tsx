import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function RequestsLayout({ children }: { children: ReactNode }) {
  return <PortalShell>{children}</PortalShell>;
}
