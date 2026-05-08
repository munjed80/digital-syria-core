export type UserRole =
  | 'citizen'
  | 'employee'
  | 'supervisor'
  | 'admin'
  | 'super_admin'
  | 'governor'
  | 'municipality_chief'
  | 'mukhtar'
  | 'household_head';

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

// ---------------------------------------------------------------------------
// Population Registry
// ---------------------------------------------------------------------------

export type Gender = 'male' | 'female';
export type LifeStatus = 'alive' | 'deceased';
export type RelationToHead =
  | 'self'
  | 'spouse'
  | 'child'
  | 'parent'
  | 'sibling'
  | 'other';
export type HouseholdVerificationStatus = 'pending' | 'verified' | 'rejected';
export type ChangeRequestType =
  | 'birth'
  | 'death'
  | 'address_change'
  | 'correction'
  | 'add_member'
  | 'remove_member';
export type ChangeRequestStatus =
  | 'submitted'
  | 'mukhtar_review'
  | 'municipality_review'
  | 'approved'
  | 'rejected';

export interface Person {
  id: number;
  household_id: number;
  full_name: string;
  birth_date: string | null;
  gender: Gender;
  relation_to_head: RelationToHead;
  life_status: LifeStatus;
  death_date: string | null;
  national_id: string | null;
  digital_identity_ref: string | null;
  is_archived: boolean;
}

export interface Household {
  id: number;
  code: string;
  address_line: string;
  governorate_id: number;
  municipality_id: number;
  district_id: number;
  neighborhood_id: number | null;
  assigned_mukhtar_user_id: number | null;
  head_user_id: number | null;
  head_person_id: number | null;
  verification_status: HouseholdVerificationStatus;
  is_archived: boolean;
}

export interface HouseholdDetail extends Household {
  members: Person[];
}

export interface PopulationChangeRequest {
  id: number;
  request_type: ChangeRequestType;
  status: ChangeRequestStatus;
  submitted_by_user_id: number;
  household_id: number;
  target_person_id: number | null;
  payload: Record<string, unknown>;
  reason: string | null;
  mukhtar_user_id: number | null;
  mukhtar_decision_at: string | null;
  mukhtar_comment: string | null;
  municipality_user_id: number | null;
  municipality_decision_at: string | null;
  municipality_comment: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AgeGroupBreakdown {
  label: string;
  count: number;
}

export interface GenderBreakdown {
  male: number;
  female: number;
}

export interface StatusBreakdown {
  label: string;
  count: number;
}

export interface AdministrativeBreakdownItem {
  id: number;
  name_ar: string;
  households: number;
  population: number;
}

export interface PopulationStatistics {
  scope_label: string;
  total_population: number;
  total_households: number;
  verified_households: number;
  pending_households: number;
  births_last_year: number;
  deaths_last_year: number;
  age_groups: AgeGroupBreakdown[];
  gender: GenderBreakdown;
  requests_by_status: StatusBreakdown[];
  administrative_breakdown: AdministrativeBreakdownItem[];
}
