import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function GovernorLayout({ children }: { children: ReactNode }) {
  return (
    <PortalShell allowedRoles={['governor', 'super_admin', 'admin']}>
      {children}
    </PortalShell>
  );
}
