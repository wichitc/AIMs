"use client";

import { useState, type FormEvent } from "react";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Equipment } from "@/lib/types";

export function AddEquipmentForm({
  assetId,
  existingEquipment,
  onCreated,
  onCancel,
}: {
  assetId: string;
  existingEquipment: Equipment[];
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [level, setLevel] = useState<"Component" | "InspectionPoint">("Component");
  const [parentEquipmentId, setParentEquipmentId] = useState("");
  const [tagNumber, setTagNumber] = useState("");
  const [name, setName] = useState("");
  const [cmlNumber, setCmlNumber] = useState("");
  const [nominalThickness, setNominalThickness] = useState("");
  const [minRequiredThickness, setMinRequiredThickness] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inspection Points nest under a Component — matches Database.md §4.4's self-referencing
  // equipment hierarchy (Component > InspectionPoint).
  const components = existingEquipment.filter((e) => e.level === "Component");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<Equipment>(`/assets/${assetId}/equipment`, {
        level,
        parent_equipment_id: level === "InspectionPoint" ? parentEquipmentId || undefined : undefined,
        tag_number: tagNumber,
        name,
        cml_number: cmlNumber || undefined,
        nominal_thickness_mm: nominalThickness ? Number(nominalThickness) : undefined,
        minimum_required_thickness_mm: minRequiredThickness ? Number(minRequiredThickness) : undefined,
      });
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add equipment");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add Component / Inspection Point</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="eq-level">
                Level
              </label>
              <Select
                id="eq-level"
                value={level}
                onChange={(e) => setLevel(e.target.value as "Component" | "InspectionPoint")}
              >
                <option value="Component">Component</option>
                <option value="InspectionPoint">Inspection Point (CML)</option>
              </Select>
            </div>
            {level === "InspectionPoint" && (
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="eq-parent">
                  Parent Component
                </label>
                <Select id="eq-parent" value={parentEquipmentId} onChange={(e) => setParentEquipmentId(e.target.value)}>
                  <option value="">None (directly on asset)</option>
                  {components.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.tag_number} — {c.name}
                    </option>
                  ))}
                </Select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="eq-tag">
                Tag Number
              </label>
              <Input
                id="eq-tag"
                placeholder="e.g. SHELL-1 or CML-01"
                value={tagNumber}
                onChange={(e) => setTagNumber(e.target.value)}
                maxLength={50}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="eq-name">
                Name
              </label>
              <Input
                id="eq-name"
                placeholder="e.g. Shell Course 1"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={200}
                required
              />
            </div>
          </div>

          {level === "InspectionPoint" && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="eq-cml">
                  CML Number
                </label>
                <Input id="eq-cml" placeholder="e.g. CML-01" value={cmlNumber} onChange={(e) => setCmlNumber(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="eq-nominal">
                  Nominal Thickness (mm)
                </label>
                <Input
                  id="eq-nominal"
                  type="number"
                  step="0.01"
                  value={nominalThickness}
                  onChange={(e) => setNominalThickness(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="eq-minreq">
                  Min. Required Thickness (mm)
                </label>
                <Input
                  id="eq-minreq"
                  type="number"
                  step="0.01"
                  value={minRequiredThickness}
                  onChange={(e) => setMinRequiredThickness(e.target.value)}
                />
              </div>
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="mt-1 flex gap-2">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding..." : "Add"}
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
