"use client";

import { useState, type FormEvent } from "react";
import { apiClient, ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ChecklistResultForm({ inspectionId, onSubmitted }: { inspectionId: string; onSubmitted: () => void }) {
  const [checklistItem, setChecklistItem] = useState("");
  const [resultStatus, setResultStatus] = useState<"Pass" | "Fail" | "NA">("Pass");
  const [remarks, setRemarks] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post(`/inspections/${inspectionId}/results`, {
        checklist_item: checklistItem,
        result_status: resultStatus,
        remarks: remarks || undefined,
      });
      setChecklistItem("");
      setRemarks("");
      onSubmitted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to submit result");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add Checklist Result</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <Input
            placeholder="Checklist item (e.g. 'External visual - shell corrosion')"
            value={checklistItem}
            onChange={(e) => setChecklistItem(e.target.value)}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <Select value={resultStatus} onChange={(e) => setResultStatus(e.target.value as typeof resultStatus)}>
              <option value="Pass">Pass</option>
              <option value="Fail">Fail</option>
              <option value="NA">N/A</option>
            </Select>
          </div>
          <Input placeholder="Remarks (optional)" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          {error && <p className="text-sm text-destructive">{error}</p>}
          {/* Large tap target — this form is the primary mobile/field-inspector surface (UIUX.md §3.4/§4) */}
          <Button type="submit" size="lg" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Save Result"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export function FindingForm({
  inspectionId,
  equipmentId,
  onSubmitted,
}: {
  inspectionId: string;
  equipmentId: string;
  onSubmitted: () => void;
}) {
  const [findingType, setFindingType] = useState("Corrosion");
  const [severity, setSeverity] = useState<"Low" | "Medium" | "High" | "Critical">("Medium");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post(`/inspections/${inspectionId}/findings`, {
        equipment_id: equipmentId,
        finding_type: findingType,
        severity,
        description,
      });
      setDescription("");
      onSubmitted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to raise finding");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Raise Finding</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <Select value={findingType} onChange={(e) => setFindingType(e.target.value)}>
              <option value="Corrosion">Corrosion</option>
              <option value="Crack">Crack</option>
              <option value="Leak">Leak</option>
              <option value="CoatingFailure">Coating Failure</option>
              <option value="Deformation">Deformation</option>
              <option value="Other">Other</option>
            </Select>
            <Select value={severity} onChange={(e) => setSeverity(e.target.value as typeof severity)}>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </Select>
          </div>
          <Input
            placeholder="Describe the finding"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" variant="destructive" size="lg" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Raise Finding"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
