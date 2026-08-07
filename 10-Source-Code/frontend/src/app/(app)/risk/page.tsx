"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { RiskMatrix } from "@/components/risk/RiskMatrix";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { riskColor } from "@/lib/utils";
import type { RiskAssessment } from "@/lib/types";

export default function RiskPage() {
  const risks = useApiQuery<RiskAssessment[]>("/risk-assessments", { page_size: 200 });
  const [cellFilter, setCellFilter] = useState<{ pof: string; cof: string } | null>(null);

  async function approve(assessment: RiskAssessment) {
    try {
      await apiClient.post(`/risk-assessments/${assessment.id}/approve`);
      risks.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to approve assessment");
    }
  }

  const filtered = useMemo(() => {
    const items = risks.data ?? [];
    const ranked = [...items].sort((a, b) => b.risk_score - a.risk_score);
    if (!cellFilter) return ranked.slice(0, 20);
    return ranked.filter((r) => r.pof_category === cellFilter.pof && r.cof_category === cellFilter.cof);
  }, [risks.data, cellFilter]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Risk Based Inspection</h1>
          <p className="text-sm text-muted-foreground">5×5 POF × COF risk matrix and ranked asset exposure.</p>
        </div>
        <Link href="/risk/new">
          <Button>New Assessment</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Risk Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <RiskMatrix assessments={risks.data ?? []} onCellClick={(pof, cof) => setCellFilter({ pof, cof })} />
          {cellFilter && (
            <button
              className="mt-2 text-xs text-primary hover:underline"
              onClick={() => setCellFilter(null)}
              type="button"
            >
              Clear cell filter (POF {cellFilter.pof} / COF {cellFilter.cof})
            </button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{cellFilter ? "Filtered Assessments" : "Top 20 Highest-Risk Assessments"}</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Methodology</TableHead>
                <TableHead>Risk Score</TableHead>
                <TableHead>Rank</TableHead>
                <TableHead>Next Inspection</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.methodology}</TableCell>
                  <TableCell>{r.risk_score}</TableCell>
                  <TableCell>
                    <Badge className={riskColor(r.risk_rank)}>{r.risk_rank}</Badge>
                  </TableCell>
                  <TableCell>{r.next_inspection_date ?? "—"}</TableCell>
                  <TableCell>{r.status}</TableCell>
                  <TableCell>
                    {r.status !== "Approved" && (
                      <Button size="sm" variant="outline" onClick={() => approve(r)}>
                        Approve
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    No risk assessments in this selection
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
