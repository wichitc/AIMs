"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Defect, Finding, FindingSeverity } from "@/lib/types";

interface UserOption {
  id: string;
  username: string;
  full_name: string;
}

export default function NewDefectPage() {
  const router = useRouter();
  // Only Open findings are eligible — one already escalated to a defect shouldn't be
  // escalated again (FR-21 workflow starts once, at Finding -> Assessment).
  const findings = useApiQuery<Finding[]>("/findings", { status: "Open", page_size: 100 });
  const users = useApiQuery<UserOption[]>("/users", { page_size: 100 });

  const [findingId, setFindingId] = useState("");
  const [defectType, setDefectType] = useState("");
  const [severity, setSeverity] = useState<FindingSeverity>("Medium");
  const [ffsRequired, setFfsRequired] = useState(false);
  const [assignedTo, setAssignedTo] = useState("");
  const [dueDate, setDueDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedFinding = (findings.data ?? []).find((f) => f.id === findingId) ?? null;

  function handleFindingChange(id: string) {
    setFindingId(id);
    const finding = (findings.data ?? []).find((f) => f.id === id);
    if (finding) {
      setDefectType(finding.finding_type);
      setSeverity(finding.severity);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedFinding) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const defect = await apiClient.post<Defect>("/defects", {
        finding_id: selectedFinding.id,
        equipment_id: selectedFinding.equipment_id,
        defect_type: defectType,
        severity,
        ffs_required: ffsRequired,
        assigned_to: assignedTo || undefined,
        due_date: dueDate || undefined,
      });
      void defect;
      router.push("/defects");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create defect");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noFindingsAvailable = !findings.isLoading && (findings.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Escalate Finding to Defect</h1>
        <p className="text-sm text-muted-foreground">
          Starts the defect workflow: Finding → Assessment → Approval → Repair → Verification → Closed (FR-21).
        </p>
      </div>

      {noFindingsAvailable && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No open findings exist yet — raise one from an in-progress inspection first.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Defect Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="finding">
                Finding
              </label>
              <Select id="finding" value={findingId} onChange={(e) => handleFindingChange(e.target.value)} required>
                <option value="">Select finding…</option>
                {(findings.data ?? []).map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.finding_type} — {f.severity} ({f.raised_date})
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="defectType">
                  Defect Type
                </label>
                <Input
                  id="defectType"
                  value={defectType}
                  onChange={(e) => setDefectType(e.target.value)}
                  maxLength={50}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="severity">
                  Severity
                </label>
                <Select id="severity" value={severity} onChange={(e) => setSeverity(e.target.value as FindingSeverity)}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="assignedTo">
                  Assign To
                </label>
                <Select id="assignedTo" value={assignedTo} onChange={(e) => setAssignedTo(e.target.value)}>
                  <option value="">Unassigned</option>
                  {(users.data ?? []).map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.username})
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="dueDate">
                  Due Date
                </label>
                <Input id="dueDate" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={ffsRequired}
                onChange={(e) => setFfsRequired(e.target.checked)}
                className="h-4 w-4 rounded border-border"
              />
              Fitness-For-Service assessment required (API 579)
            </label>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || !selectedFinding}>
                {isSubmitting ? "Creating..." : "Create Defect"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/defects")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
