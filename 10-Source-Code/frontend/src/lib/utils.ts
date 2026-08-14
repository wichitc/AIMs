import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type RiskRank = "Low" | "Medium" | "High" | "VeryHigh";
export type Severity = "Low" | "Medium" | "High" | "Critical";

export function riskColor(rank: RiskRank): string {
  switch (rank) {
    case "Low":
      return "bg-status-success-bg text-status-success-text border-transparent";
    case "Medium":
      return "bg-status-warning-bg text-status-warning-text border-transparent";
    case "High":
      return "bg-status-warning-bg text-status-warning-text border-transparent";
    case "VeryHigh":
      return "bg-status-danger-bg text-status-danger-text border-transparent";
  }
}

export function severityColor(severity: Severity): string {
  switch (severity) {
    case "Low":
      return "bg-status-success-bg text-status-success-text border-transparent";
    case "Medium":
      return "bg-status-warning-bg text-status-warning-text border-transparent";
    case "High":
      return "bg-status-warning-bg text-status-warning-text border-transparent";
    case "Critical":
      return "bg-status-danger-bg text-status-danger-text border-transparent";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "Completed":
    case "Closed":
    case "Approved":
    case "Active":
      return "bg-status-success-bg text-status-success-text border-transparent";
    case "InProgress":
    case "Repair":
    case "Assessment":
      return "bg-status-info-bg text-status-info-text border-transparent";
    case "Overdue":
    case "Cancelled":
      return "bg-status-danger-bg text-status-danger-text border-transparent";
    default:
      return "bg-status-neutral-bg text-status-neutral-text border-transparent";
  }
}
