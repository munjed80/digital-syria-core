import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function EmployeeLayout({ children }: { children: ReactNode }) {
  // Frontend role gating is a UX convenience; backend RBAC remains the source
  // of truth for every action exposed under this section.
  return (
    <PortalShell allowedRoles={['employee', 'supervisor', 'admin']}>
      {children}
    </PortalShell>
  );
}
