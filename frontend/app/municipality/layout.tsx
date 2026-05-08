import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function MunicipalityLayout({ children }: { children: ReactNode }) {
  return (
    <PortalShell
      allowedRoles={['municipality_chief', 'governor', 'super_admin', 'admin']}
    >
      {children}
    </PortalShell>
  );
}
