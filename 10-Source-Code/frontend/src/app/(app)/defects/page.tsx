"use client";

import { useMemo } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { severityColor } from "@/lib/utils";
import type { Defect, DefectWorkflowStatus } from "@/lib/types";

const COLUMNS: DefectWorkflowStatus[] = ["Finding", "Assessment", "Approval", "Repair", "Verification", "Closed"];

// Mirrors app/modules/defect/service.py _VALID_TRANSITIONS — the API is the source of truth;
// this only decides which "advance" button to show, illegal moves are still rejected server-side.
const NEXT_STEP: Partial<Record<DefectWorkflowStatus, DefectWorkflowStatus>> = {
  Finding: "Assessment",
  Assessment: "Approval",
  Approval: "Repair",
  Repair: "Verification",
  Verification: "Closed",
};

export default function DefectsPage() {
  const defects = useApiQuery<Defect[]>("/defects", { page_size: 200 });

  const byColumn = useMemo(() => {
    const grouped: Record<DefectWorkflowStatus, Defect[]> = {
      Finding: [],
      Assessment: [],
      Approval: [],
      Repair: [],
      Verification: [],
      Closed: [],
    };
    (defects.data ?? []).forEach((d) => grouped[d.workflow_status].push(d));
    return grouped;
  }, [defects.data]);

  async function advance(defect: Defect) {
    const target = NEXT_STEP[defect.workflow_status];
    if (!target) return;
    try {
      await apiClient.put(`/defects/${defect.id}`, { target_status: target });
      defects.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to advance defect");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Defect Workflow</h1>
        <p className="text-sm text-muted-foreground">Finding → Assessment → Approval → Repair → Verification → Closed</p>
      </div>

      <div className="grid grid-cols-1 gap-3 overflow-x-auto sm:grid-cols-2 lg:grid-cols-6">
        {COLUMNS.map((column) => (
          <div key={column} className="flex min-w-[200px] flex-col gap-2">
            <div className="text-sm font-semibold text-muted-foreground">
              {column} ({byColumn[column].length})
            </div>
            {byColumn[column].map((defect) => (
              <Card key={defect.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-foreground">
                    <span className="text-sm">Defect</span>
                    <Badge className={severityColor(defect.severity)}>{defect.severity}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2 text-xs text-muted-foreground">
                  <div>Due: {defect.due_date ?? "—"}</div>
                  {defect.ffs_required && <Badge className="w-fit">FFS Required</Badge>}
                  {NEXT_STEP[defect.workflow_status] && (
                    <Button size="sm" variant="outline" onClick={() => advance(defect)}>
                      Advance to {NEXT_STEP[defect.workflow_status]}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
