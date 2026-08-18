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
  latitude: number | null;
  longitude: number | null;
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
  design_pressure_bar: number | null;
  design_temperature_c: number | null;
  material: string | null;
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
  nominal_thickness_mm: number | null;
  minimum_required_thickness_mm: number | null;
}

export type CriticalityLevel = "Low" | "Medium" | "High" | "VeryHigh";

export interface Criticality {
  id: string;
  asset_id: string;
  safety_score: number;
  environmental_score: number;
  economic_score: number;
  calculated_score: number;
  criticality_level: CriticalityLevel;
  methodology: string | null;
  assessed_date: string;
}

export type InspectionStatus = "Planned" | "InProgress" | "Completed" | "Overdue" | "Cancelled";

export interface InspectionPlan {
  id: string;
  asset_id: string;
  equipment_id: string | null;
  plan_code: string;
  applicable_code: string | null;
  inspection_type: string;
  basis: "RBI" | "FixedInterval" | "Regulatory";
  frequency_months: number;
  next_due_date: string;
  status: "Active" | "Suspended" | "Retired";
}

export interface Inspection {
  id: string;
  inspection_plan_id: string;
  asset_id: string;
  equipment_id: string | null;
  inspector_id: string;
  inspection_type: string;
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
  defect_type: string;
  workflow_status: DefectWorkflowStatus;
  severity: FindingSeverity;
  ffs_required: boolean;
  assigned_to: string | null;
  due_date: string | null;
  closed_date: string | null;
}

export interface MaintenanceOrder {
  id: string;
  equipment_id: string;
  defect_id: string | null;
  order_type: "Corrective" | "Preventive" | "Predictive";
  description: string;
  status: "Open" | "InProgress" | "Completed" | "Cancelled";
  priority: "Low" | "Medium" | "High" | "Urgent";
  scheduled_date: string | null;
  completed_date: string | null;
  assigned_to: string | null;
  cost_estimate: number | null;
}

// Purchasing & Inventory (SAP MM-inspired, see 01 SAP MM/docs) — Stage 1: master data.
export type MaterialType = "SparePart" | "Consumable" | "RawMaterial" | "Service";

export interface Material {
  id: string;
  org_id: string;
  material_number: string;
  name: string;
  description: string | null;
  material_type: MaterialType;
  material_group: string | null;
  base_uom: string;
  moving_average_price: number | null;
  min_stock_level: number | null;
  is_active: boolean;
}

export interface Supplier {
  id: string;
  org_id: string;
  supplier_number: string;
  name: string;
  tax_id: string | null;
  country: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  payment_terms: string | null;
  currency: string;
  is_active: boolean;
  is_blocked: boolean;
  block_reason: string | null;
}

export interface PurchasingInfoRecord {
  id: string;
  org_id: string;
  material_id: string;
  supplier_id: string;
  price: number;
  lead_time_days: number | null;
  valid_from: string | null;
  valid_to: string | null;
  is_active: boolean;
}

export interface SourceListEntry {
  id: string;
  org_id: string;
  material_id: string;
  supplier_id: string;
  is_fixed: boolean;
  is_blocked: boolean;
  valid_from: string | null;
  valid_to: string | null;
}

export interface QuotaArrangement {
  id: string;
  org_id: string;
  material_id: string;
  supplier_id: string;
  quota_percentage: number;
  valid_from: string | null;
  valid_to: string | null;
}

export interface SourceCandidate {
  supplier_id: string;
  rank: number;
  reason: string;
  price: number | null;
}

export type PurchaseRequisitionStatus = "Draft" | "Submitted" | "Approved" | "Rejected" | "Withdrawn";

export interface PurchaseRequisitionItem {
  id: string;
  line_no: number;
  material_id: string;
  quantity: number;
  estimated_price: number | null;
  required_date: string | null;
}

export interface PurchaseRequisition {
  id: string;
  org_id: string;
  requester_id: string;
  status: PurchaseRequisitionStatus;
  requested_date: string;
  required_date: string | null;
  maintenance_order_id: string | null;
  defect_id: string | null;
  decision_by: string | null;
  decision_at: string | null;
  decision_reason: string | null;
  items: PurchaseRequisitionItem[];
}

export type RFQStatus = "Draft" | "Dispatched" | "Closed";

export interface RFQ {
  id: string;
  org_id: string;
  purchase_requisition_id: string;
  status: RFQStatus;
  deadline: string | null;
}

export interface RFQInvite {
  id: string;
  rfq_id: string;
  supplier_id: string;
  dispatched_at: string | null;
}

export interface QuotationItem {
  id: string;
  pr_item_id: string;
  material_id: string;
  quantity: number;
  unit_price: number;
  is_awarded: boolean;
}

export interface Quotation {
  id: string;
  org_id: string;
  rfq_id: string;
  supplier_id: string;
  submitted_date: string;
  items: QuotationItem[];
}

export type PurchaseOrderStatus = "Draft" | "Approved" | "Sent" | "Cancelled";

export interface PurchaseOrderItem {
  id: string;
  line_no: number;
  material_id: string;
  quantity: number;
  unit_price: number;
  received_quantity: number;
  pr_item_id: string | null;
}

export interface PurchaseOrder {
  id: string;
  org_id: string;
  supplier_id: string;
  purchase_requisition_id: string | null;
  rfq_id: string | null;
  status: PurchaseOrderStatus;
  order_date: string;
  approved_by: string | null;
  confirmed_date: string | null;
  confirmed_by_supplier: boolean;
  items: PurchaseOrderItem[];
}

export interface MaterialDocumentItem {
  id: string;
  line_no: number;
  material_id: string;
  storage_location_id: string;
  quantity: number;
  unit_price: number;
  po_item_id: string | null;
}

export interface MaterialDocument {
  id: string;
  org_id: string;
  movement_type: string;
  posted_date: string;
  reference_type: string | null;
  reference_id: string | null;
  reversal_of_id: string | null;
  items: MaterialDocumentItem[];
}

export interface StockBalance {
  id: string;
  material_id: string;
  storage_location_id: string;
  quantity: number;
  value: number;
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
