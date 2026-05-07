import { ReactNode } from 'react';

import PortalShell from '../../components/PortalShell';

export default function AdminLayout({ children }: { children: ReactNode }) {
  // Frontend role gating is a UX convenience; backend RBAC remains the source
  // of truth. Admin-only endpoints (e.g. audit logs) are enforced server-side.
  return (
    <PortalShell allowedRoles={['admin']}>{children}</PortalShell>
  );
}
