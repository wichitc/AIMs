"use client";

import { useMemo } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { riskColor, statusColor } from "@/lib/utils";
import type { Asset, Inspection, RiskAssessment } from "@/lib/types";

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const assets = useApiQuery<Asset[]>("/assets", { page_size: 100 });
  const risks = useApiQuery<RiskAssessment[]>("/risk-assessments", { page_size: 100 });
  const inspections = useApiQuery<Inspection[]>("/inspections", { status: "Planned", page_size: 10 });

  const riskDistribution = useMemo(() => {
    const buckets: Record<string, number> = { Low: 0, Medium: 0, High: 0, VeryHigh: 0 };
    (risks.data ?? []).forEach((r) => {
      buckets[r.risk_rank] = (buckets[r.risk_rank] ?? 0) + 1;
    });
    return buckets;
  }, [risks.data]);

  const overdueCount = (inspections.data ?? []).filter((i) => i.status === "Overdue").length;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Executive Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Asset integrity KPIs across the organization (BRD §7).
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Assets" value={String(assets.data?.length ?? "—")} />
        <StatCard label="Overdue Inspections" value={String(overdueCount)} />
        <StatCard label="High/VeryHigh Risk Assets" value={String(riskDistribution.High + riskDistribution.VeryHigh)} />
        <StatCard label="Risk Assessments Logged" value={String(risks.data?.length ?? "—")} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Risk Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {(Object.entries(riskDistribution) as [keyof typeof riskDistribution, number][]).map(([rank, count]) => (
              <Badge key={rank} className={riskColor(rank as never)}>
                {rank}: {count}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Inspections Due Soon</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scheduled Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(inspections.data ?? []).map((i) => (
                <TableRow key={i.id}>
                  <TableCell>{i.scheduled_date}</TableCell>
                  <TableCell>
                    <Badge className={statusColor(i.status)}>{i.status}</Badge>
                  </TableCell>
                </TableRow>
              ))}
              {inspections.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={2} className="text-center text-muted-foreground">
                    No upcoming inspections
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
