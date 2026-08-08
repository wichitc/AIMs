// Mirrors app/modules/*/schemas.py on the backend. Keep in sync with API-Spec.md.

export interface ResponseEnvelope<T> {
  success: boolean;
  data: T | null;
  meta?: { page: number; page_size: number; total: number } | null;
  error?: { code: string; message: string; details?: unknown[] } | null;
}

export interface CurrentUser {
  id: string;
  org_id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
}

export interface Location {
  id: string;
  parent_location_id: string | null;
  level: "Plant" | "Area" | "Unit";
  name: string;
  code: string;
}

export interface AssetClass {
  id: string;
  name: string;
  code: string;
  category: string;
  description: string | null;
}

export type AssetStatus =
  | "Design"
  | "Construction"
  | "Commissioning"
  | "Operating"
  | "Inactive"
  | "Decommissioned";

export interface Asset {
  id: string;
  location_id: string;
  asset_class_id: string;
  tag_number: string;
  name: string;
  status: AssetStatus;
  design_code: string | null;
  install_date: string | null;
}

export interface Equipment {
  id: string;
  asset_id: string;
  parent_equipment_id: string | null;
  level: "Component" | "InspectionPoint";
  tag_number: string;
  name: string;
  cml_number: string | null;
}

export type CriticalityLevel = "Low" | "Medium" | "High" | "VeryHigh";

export interface Criticality {
  id: string;
  asset_id: string;
  calculated_score: number;
  criticality_level: CriticalityLevel;
  assessed_date: string;
}

export type InspectionStatus = "Planned" | "InProgress" | "Completed" | "Overdue" | "Cancelled";

export interface InspectionPlan {
  id: string;
  asset_id: string;
  plan_code: string;
  inspection_type: string;
  basis: "RBI" | "FixedInterval" | "Regulatory";
  next_due_date: string;
  status: "Active" | "Suspended" | "Retired";
}

export interface Inspection {
  id: string;
  inspection_plan_id: string;
  asset_id: string;
  inspector_id: string;
  status: InspectionStatus;
  scheduled_date: string;
  actual_date: string | null;
}

export interface InspectionResult {
  id: string;
  checklist_item: string;
  result_status: "Pass" | "Fail" | "NA";
  recorded_at: string;
}

export type FindingSeverity = "Low" | "Medium" | "High" | "Critical";

export interface Finding {
  id: string;
  inspection_id: string;
  equipment_id: string;
  finding_type: string;
  severity: FindingSeverity;
  status: "Open" | "UnderAssessment" | "Closed";
  raised_date: string;
}

export type RiskRank = "Low" | "Medium" | "High" | "VeryHigh";

export interface RiskAssessment {
  id: string;
  asset_id: string;
  methodology: "Qualitative" | "SemiQuantitative" | "Quantitative";
  pof_score: number;
  pof_category: string | null;
  cof_category: string | null;
  risk_score: number;
  risk_rank: RiskRank;
  recommended_interval_months: number | null;
  next_inspection_date: string | null;
  status: "Draft" | "PendingApproval" | "Approved";
}

export interface ThicknessRecord {
  id: string;
  equipment_id: string;
  reading_date: string;
  measured_thickness_mm: number;
  measurement_method: "UT" | "RT";
}

export interface CorrosionRecord {
  id: string;
  equipment_id: string;
  short_term_rate_mm_yr: number | null;
  long_term_rate_mm_yr: number | null;
  governing_rate_mm_yr: number;
  remaining_life_years: number;
  next_inspection_date: string;
  calculation_basis: string | null;
}

export type DefectWorkflowStatus =
  | "Finding"
  | "Assessment"
  | "Approval"
  | "Repair"
  | "Verification"
  | "Closed";

export interface Defect {
  id: string;
  finding_id: string;
  equipment_id: string;
  workflow_status: DefectWorkflowStatus;
  severity: FindingSeverity;
  ffs_required: boolean;
  due_date: string | null;
  closed_date: string | null;
}

export interface MaintenanceOrder {
  id: string;
  equipment_id: string;
  defect_id: string | null;
  order_type: "Corrective" | "Preventive" | "Predictive";
  status: "Open" | "InProgress" | "Completed" | "Cancelled";
  priority: "Low" | "Medium" | "High" | "Urgent";
  scheduled_date: string | null;
  completed_date: string | null;
}

export interface AimsDocument {
  id: string;
  asset_id: string | null;
  document_type: string;
  file_name: string;
  version: number;
  file_size_bytes: number | null;
  uploaded_at: string;
}

// AI Engine service (ai-service) — separate base URL, see lib/api-client.ts aiApiClient.
export interface SourceRef {
  type: string;
  id: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceRef[];
}
