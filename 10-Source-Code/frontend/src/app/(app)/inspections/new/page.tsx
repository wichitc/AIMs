"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Asset, Inspection, InspectionPlan } from "@/lib/types";

interface UserOption {
  id: string;
  username: string;
  full_name: string;
}

export default function NewInspectionPage() {
  const router = useRouter();
  const plans = useApiQuery<InspectionPlan[]>("/inspection-plans", { page_size: 100 });
  const assets = useApiQuery<Asset[]>("/assets", { page_size: 100 });
  const users = useApiQuery<UserOption[]>("/users", { page_size: 100 });

  const assetById = useMemo(() => {
    const map = new Map<string, Asset>();
    (assets.data ?? []).forEach((a) => map.set(a.id, a));
    return map;
  }, [assets.data]);

  const [inspectionPlanId, setInspectionPlanId] = useState("");
  const [inspectorId, setInspectorId] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedPlan = (plans.data ?? []).find((p) => p.id === inspectionPlanId) ?? null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedPlan) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const inspection = await apiClient.post<Inspection>("/inspections", {
        inspection_plan_id: selectedPlan.id,
        asset_id: selectedPlan.asset_id,
        inspector_id: inspectorId,
        inspection_type: selectedPlan.inspection_type,
        scheduled_date: scheduledDate,
      });
      router.push(`/inspections/${inspection.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to schedule inspection");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noPlansAvailable = !plans.isLoading && (plans.data ?? []).length === 0;
  const noInspectorsAvailable = !users.isLoading && (users.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Schedule Inspection</h1>
        <p className="text-sm text-muted-foreground">
          Create an inspection instance from an existing plan and assign an inspector (FR-09).
        </p>
      </div>

      {noPlansAvailable && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No inspection plans exist yet —{" "}
            <a href="/inspections/plans/new" className="underline">
              create one first
            </a>
            .
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Inspection Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="plan">
                Inspection Plan
              </label>
              <Select
                id="plan"
                value={inspectionPlanId}
                onChange={(e) => setInspectionPlanId(e.target.value)}
                required
              >
                <option value="">Select plan…</option>
                {(plans.data ?? []).map((p) => {
                  const asset = assetById.get(p.asset_id);
                  return (
                    <option key={p.id} value={p.id}>
                      {p.plan_code} — {asset ? asset.tag_number : p.asset_id} ({p.inspection_type})
                    </option>
                  );
                })}
              </Select>
              {selectedPlan && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Basis: {selectedPlan.basis} · Code: {selectedPlan.applicable_code ?? "—"} · Next due:{" "}
                  {selectedPlan.next_due_date ?? "—"}
                </p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="inspector">
                Inspector
              </label>
              <Select id="inspector" value={inspectorId} onChange={(e) => setInspectorId(e.target.value)} required>
                <option value="">Select inspector…</option>
                {(users.data ?? []).map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} ({u.username})
                  </option>
                ))}
              </Select>
              {noInspectorsAvailable && (
                <p className="mt-1 text-xs text-destructive">No users exist to assign as inspector.</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="scheduledDate">
                Scheduled Date
              </label>
              <Input
                id="scheduledDate"
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                required
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || !selectedPlan || noInspectorsAvailable}>
                {isSubmitting ? "Scheduling..." : "Schedule Inspection"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/inspections")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
