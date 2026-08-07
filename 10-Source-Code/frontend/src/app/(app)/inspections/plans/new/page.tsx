"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Asset, InspectionPlan } from "@/lib/types";

const INSPECTION_TYPES = ["Visual", "UT", "RT", "MT", "PT", "PMI", "Other"];
const BASES: { value: InspectionPlan["basis"]; label: string }[] = [
  { value: "RBI", label: "Risk Based Inspection" },
  { value: "FixedInterval", label: "Fixed Interval" },
  { value: "Regulatory", label: "Regulatory" },
];

export default function NewInspectionPlanPage() {
  const router = useRouter();
  const assets = useApiQuery<Asset[]>("/assets", { page_size: 100 });

  const [assetId, setAssetId] = useState("");
  const [planCode, setPlanCode] = useState("");
  const [applicableCode, setApplicableCode] = useState("");
  const [inspectionType, setInspectionType] = useState(INSPECTION_TYPES[0]);
  const [basis, setBasis] = useState<InspectionPlan["basis"]>("FixedInterval");
  const [frequencyMonths, setFrequencyMonths] = useState("12");
  const [nextDueDate, setNextDueDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<InspectionPlan>("/inspection-plans", {
        asset_id: assetId,
        plan_code: planCode,
        applicable_code: applicableCode || undefined,
        inspection_type: inspectionType,
        basis,
        frequency_months: Number(frequencyMonths),
        next_due_date: nextDueDate,
      });
      router.push("/inspections/new");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create inspection plan");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noAssetsAvailable = !assets.isLoading && (assets.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Inspection Plan</h1>
        <p className="text-sm text-muted-foreground">
          Defines applicable code, type, and interval for an asset — a schedulable inspection
          references a plan (FR-08).
        </p>
      </div>

      {noAssetsAvailable && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No assets exist yet —{" "}
            <a href="/assets/new" className="underline">
              register one first
            </a>
            .
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Plan Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="asset">
                Asset
              </label>
              <Select id="asset" value={assetId} onChange={(e) => setAssetId(e.target.value)} required>
                <option value="">Select asset…</option>
                {(assets.data ?? []).map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.tag_number} — {a.name}
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="planCode">
                  Plan Code
                </label>
                <Input
                  id="planCode"
                  placeholder="e.g. IP-V101-001"
                  value={planCode}
                  onChange={(e) => setPlanCode(e.target.value)}
                  maxLength={50}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="applicableCode">
                  Applicable Code
                </label>
                <Input
                  id="applicableCode"
                  placeholder="e.g. API 510"
                  value={applicableCode}
                  onChange={(e) => setApplicableCode(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="inspectionType">
                  Inspection Type
                </label>
                <Select
                  id="inspectionType"
                  value={inspectionType}
                  onChange={(e) => setInspectionType(e.target.value)}
                >
                  {INSPECTION_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="basis">
                  Basis
                </label>
                <Select
                  id="basis"
                  value={basis}
                  onChange={(e) => setBasis(e.target.value as InspectionPlan["basis"])}
                >
                  {BASES.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="frequency">
                  Frequency (months)
                </label>
                <Input
                  id="frequency"
                  type="number"
                  min={1}
                  value={frequencyMonths}
                  onChange={(e) => setFrequencyMonths(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="nextDueDate">
                  Next Due Date
                </label>
                <Input
                  id="nextDueDate"
                  type="date"
                  value={nextDueDate}
                  onChange={(e) => setNextDueDate(e.target.value)}
                  required
                />
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || noAssetsAvailable}>
                {isSubmitting ? "Creating..." : "Create Plan"}
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
