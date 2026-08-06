"use client";

import { useState } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { ChecklistResultForm, FindingForm } from "@/components/inspection/InspectionChecklistForm";
import { statusColor } from "@/lib/utils";
import type { Equipment, Inspection } from "@/lib/types";

export default function InspectionDetailPage({ params }: { params: { inspectionId: string } }) {
  const { inspectionId } = params;
  const inspection = useApiQuery<Inspection>(`/inspections/${inspectionId}`);
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string>("");
  const [completeError, setCompleteError] = useState<string | null>(null);
  const [isCompleting, setIsCompleting] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);

  const equipment = useApiQuery<Equipment[]>(
    inspection.data ? `/assets/${inspection.data.asset_id}/equipment` : null,
  );

  async function handleComplete() {
    setCompleteError(null);
    setIsCompleting(true);
    try {
      await apiClient.post(`/inspections/${inspectionId}/complete`);
      inspection.refetch();
    } catch (err) {
      setCompleteError(err instanceof ApiError ? err.message : "Failed to complete inspection");
    } finally {
      setIsCompleting(false);
    }
  }

  if (inspection.isLoading) return <p className="text-muted-foreground">Loading inspection…</p>;
  if (inspection.error || !inspection.data) {
    return <p className="text-destructive">{inspection.error ?? "Inspection not found"}</p>;
  }

  const data = inspection.data;
  const isEditable = data.status !== "Completed" && data.status !== "Cancelled";

  return (
    <div className="flex flex-col gap-4 pb-20 md:pb-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Inspection — {data.scheduled_date}</h1>
          <Badge className={statusColor(data.status)}>{data.status}</Badge>
        </div>
        {isEditable && (
          <Button onClick={handleComplete} disabled={isCompleting}>
            {isCompleting ? "Completing..." : "Complete Inspection"}
          </Button>
        )}
      </div>
      {completeError && <p className="text-sm text-destructive">{completeError}</p>}

      {isEditable && (
        <>
          <ChecklistResultForm
            inspectionId={inspectionId}
            onSubmitted={() => setLastSavedAt(new Date().toLocaleTimeString())}
          />

          <Card>
            <CardHeader>
              <CardTitle>Component / Inspection Point</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedEquipmentId} onChange={(e) => setSelectedEquipmentId(e.target.value)}>
                <option value="">Select equipment…</option>
                {(equipment.data ?? []).map((eq) => (
                  <option key={eq.id} value={eq.id}>
                    {eq.tag_number} — {eq.name}
                  </option>
                ))}
              </Select>
            </CardContent>
          </Card>

          {selectedEquipmentId && (
            <FindingForm
              inspectionId={inspectionId}
              equipmentId={selectedEquipmentId}
              onSubmitted={() => setLastSavedAt(new Date().toLocaleTimeString())}
            />
          )}

          {lastSavedAt && <p className="text-xs text-muted-foreground">Last saved at {lastSavedAt}</p>}
        </>
      )}
    </div>
  );
}
