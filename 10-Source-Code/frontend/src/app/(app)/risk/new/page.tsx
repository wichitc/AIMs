"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Asset, Equipment, RiskAssessment } from "@/lib/types";

const METHODOLOGIES: { value: RiskAssessment["methodology"]; label: string }[] = [
  { value: "Qualitative", label: "Qualitative" },
  { value: "SemiQuantitative", label: "Semi-Quantitative" },
  { value: "Quantitative", label: "Quantitative (API 581)" },
];
const COF_LEVELS = ["Low", "Medium", "High", "Critical"];

export default function NewRiskAssessmentPage() {
  const router = useRouter();
  const assets = useApiQuery<Asset[]>("/assets", { page_size: 100 });

  const [assetId, setAssetId] = useState("");
  const [equipmentId, setEquipmentId] = useState("");
  const [methodology, setMethodology] = useState<RiskAssessment["methodology"]>("SemiQuantitative");
  const [pofScore, setPofScore] = useState("2.5");
  const [cofFinancial, setCofFinancial] = useState("");
  const [cofSafety, setCofSafety] = useState("");
  const [cofEnvironmental, setCofEnvironmental] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const equipment = useApiQuery<Equipment[]>(assetId ? `/assets/${assetId}/equipment` : null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const assessment = await apiClient.post<RiskAssessment>("/risk-assessments", {
        asset_id: assetId,
        equipment_id: equipmentId || undefined,
        methodology,
        pof_score: Number(pofScore),
        cof_financial: cofFinancial ? Number(cofFinancial) : undefined,
        cof_safety: cofSafety || undefined,
        cof_environmental: cofEnvironmental || undefined,
      });
      void assessment;
      router.push("/risk");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create risk assessment");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noAssetsAvailable = !assets.isLoading && (assets.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Risk Assessment</h1>
        <p className="text-sm text-muted-foreground">
          POF/COF are combined server-side into a risk score, rank, and recommended
          re-inspection interval — those fields are never client-supplied (FR-13/14/15).
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
          <CardTitle>Assessment Inputs</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="asset">
                  Asset
                </label>
                <Select
                  id="asset"
                  value={assetId}
                  onChange={(e) => {
                    setAssetId(e.target.value);
                    setEquipmentId("");
                  }}
                  required
                >
                  <option value="">Select asset…</option>
                  {(assets.data ?? []).map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.tag_number} — {a.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="equipment">
                  Component (optional)
                </label>
                <Select
                  id="equipment"
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  disabled={!assetId}
                >
                  <option value="">Whole asset</option>
                  {(equipment.data ?? []).map((eq) => (
                    <option key={eq.id} value={eq.id}>
                      {eq.tag_number} — {eq.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="methodology">
                Methodology
              </label>
              <Select
                id="methodology"
                value={methodology}
                onChange={(e) => setMethodology(e.target.value as RiskAssessment["methodology"])}
              >
                {METHODOLOGIES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="pofScore">
                Probability of Failure Score (0–5)
              </label>
              <Input
                id="pofScore"
                type="number"
                min={0}
                max={5}
                step="0.1"
                value={pofScore}
                onChange={(e) => setPofScore(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="cofFinancial">
                  COF — Financial ($)
                </label>
                <Input
                  id="cofFinancial"
                  type="number"
                  step="1000"
                  value={cofFinancial}
                  onChange={(e) => setCofFinancial(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="cofSafety">
                  COF — Safety
                </label>
                <Select id="cofSafety" value={cofSafety} onChange={(e) => setCofSafety(e.target.value)}>
                  <option value="">Not assessed</option>
                  {COF_LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="cofEnvironmental">
                  COF — Environmental
                </label>
                <Select
                  id="cofEnvironmental"
                  value={cofEnvironmental}
                  onChange={(e) => setCofEnvironmental(e.target.value)}
                >
                  <option value="">Not assessed</option>
                  {COF_LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              The higher (worse) of Safety/Environmental governs the consequence category — see
              AI-Copilot-Design.md-adjacent logic in app/modules/rbi/service.py.
            </p>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || noAssetsAvailable}>
                {isSubmitting ? "Calculating..." : "Create Assessment"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/risk")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
