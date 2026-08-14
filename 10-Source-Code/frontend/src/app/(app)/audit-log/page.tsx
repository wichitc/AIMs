"use client";

import { useMemo, useState } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  timestamp: string;
}

interface UserOption {
  id: string;
  username: string;
  full_name: string;
}

const ENTITY_TYPES = [
  "Asset",
  "Location",
  "AssetClass",
  "Equipment",
  "Criticality",
  "InspectionPlan",
  "Inspection",
  "Finding",
  "Defect",
  "MaintenanceOrder",
  "RiskAssessment",
  "Document",
  "ThicknessRecord",
  "User",
  "Role",
  "Organization",
  "Material",
  "Supplier",
  "PurchasingInfoRecord",
  "SourceListEntry",
  "QuotaArrangement",
  "PurchaseRequisition",
];

const ACTION_COLOR: Record<string, string> = {
  Create: "bg-status-success-bg text-status-success-text border-transparent",
  Update: "bg-status-warning-bg text-status-warning-text border-transparent",
  Delete: "bg-status-danger-bg text-status-danger-text border-transparent",
  Approve: "bg-status-info-bg text-status-info-text border-transparent",
};

function formatValue(value: Record<string, unknown> | null): string {
  if (!value) return "—";
  return Object.entries(value)
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join(", ");
}

export default function AuditLogPage() {
  const [entityType, setEntityType] = useState("");
  const [entityId, setEntityId] = useState("");
  const [userId, setUserId] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const users = useApiQuery<UserOption[]>("/users", { page_size: 100 });
  const logs = useApiQuery<AuditLogEntry[]>("/audit-logs", {
    entity_type: entityType || undefined,
    entity_id: entityId || undefined,
    user_id: userId || undefined,
    page,
    page_size: pageSize,
  });

  const userById = useMemo(() => {
    const map = new Map<string, UserOption>();
    (users.data ?? []).forEach((u) => map.set(u.id, u));
    return map;
  }, [users.data]);

  function applyFilters() {
    setPage(1);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Audit Log</h1>
        <p className="text-sm text-muted-foreground">
          Every create/update/delete recorded across the system (ISO 55001 traceability requirement).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="entityType">
              Entity Type
            </label>
            <Select
              id="entityType"
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All types</option>
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="entityId">
              Entity ID
            </label>
            <Input
              id="entityId"
              placeholder="uuid…"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
              onBlur={applyFilters}
              onKeyDown={(e) => e.key === "Enter" && applyFilters()}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="userId">
              User
            </label>
            <Select
              id="userId"
              value={userId}
              onChange={(e) => {
                setUserId(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All users</option>
              {(users.data ?? []).map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.username})
                </option>
              ))}
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Events</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(logs.data ?? []).map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</TableCell>
                  <TableCell>
                    {log.user_id ? (userById.get(log.user_id)?.full_name ?? log.user_id) : "System"}
                  </TableCell>
                  <TableCell>
                    <Badge className={ACTION_COLOR[log.action] ?? ""}>{log.action}</Badge>
                  </TableCell>
                  <TableCell>
                    {log.entity_type}
                    <div className="text-xs text-muted-foreground">{log.entity_id}</div>
                  </TableCell>
                  <TableCell className="max-w-md truncate text-xs text-muted-foreground" title={formatValue(log.new_value ?? log.old_value)}>
                    {formatValue(log.new_value ?? log.old_value)}
                  </TableCell>
                </TableRow>
              ))}
              {logs.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No audit events match this filter
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <div className="mt-3 flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Page {page}
              {logs.meta ? ` of ${Math.max(1, Math.ceil(logs.meta.total / pageSize))} · ${logs.meta.total} total` : ""}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                className="rounded-md border border-border px-2 py-1 disabled:opacity-50"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <button
                type="button"
                className="rounded-md border border-border px-2 py-1 disabled:opacity-50"
                disabled={logs.meta ? page * pageSize >= logs.meta.total : true}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
