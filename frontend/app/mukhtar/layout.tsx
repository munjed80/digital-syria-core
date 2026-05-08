import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function MukhtarLayout({ children }: { children: ReactNode }) {
  return (
    <PortalShell allowedRoles={['mukhtar', 'super_admin', 'admin']}>
      {children}
    </PortalShell>
  );
}
