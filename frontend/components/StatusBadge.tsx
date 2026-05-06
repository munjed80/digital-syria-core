import type { RequestStatus } from '../lib/types';
import { STATUS_BADGE_CLASSES, STATUS_LABELS_AR } from '../lib/services-meta';

export default function StatusBadge({ status }: { status: RequestStatus }) {
  return (
    <span className={`badge ${STATUS_BADGE_CLASSES[status]}`}>
      {STATUS_LABELS_AR[status]}
    </span>
  );
}
