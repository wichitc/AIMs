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
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "Medium":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "High":
      return "bg-orange-100 text-orange-800 border-orange-200";
    case "VeryHigh":
      return "bg-red-100 text-red-800 border-red-200";
  }
}

export function severityColor(severity: Severity): string {
  switch (severity) {
    case "Low":
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "Medium":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "High":
      return "bg-orange-100 text-orange-800 border-orange-200";
    case "Critical":
      return "bg-red-100 text-red-800 border-red-200";
  }
}

export function statusColor(status: string): string {
  switch (status) {
    case "Completed":
    case "Closed":
    case "Approved":
    case "Active":
      return "bg-emerald-100 text-emerald-800 border-emerald-200";
    case "InProgress":
    case "Repair":
    case "Assessment":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "Overdue":
    case "Cancelled":
      return "bg-red-100 text-red-800 border-red-200";
    default:
      return "bg-slate-100 text-slate-800 border-slate-200";
  }
}
