export type UserRole = 'citizen' | 'employee' | 'supervisor' | 'admin';

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ServiceItem {
  id: number;
  code: string;
  title_ar: string;
  description_ar: string;
  is_active: boolean;
  created_at?: string | null;
}

export type RequestStatus =
  | 'submitted'
  | 'under_review'
  | 'in_progress'
  | 'resolved'
  | 'rejected';

export interface ServiceRequest {
  id: number;
  citizen_id: number;
  service_id: number;
  title: string;
  description: string;
  current_status: RequestStatus;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface StatusHistoryEntry {
  id: number;
  old_status: RequestStatus;
  new_status: RequestStatus;
  comment?: string | null;
  created_at?: string | null;
}

export interface InternalNote {
  id: number;
  note: string;
  created_at?: string | null;
}

export interface ServiceRequestDetail extends ServiceRequest {
  status_history: StatusHistoryEntry[];
  internal_notes: InternalNote[];
}
