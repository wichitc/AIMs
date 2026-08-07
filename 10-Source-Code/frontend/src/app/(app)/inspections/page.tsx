"use client";

import { useState } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Inspection, InspectionStatus } from "@/lib/types";

const STATUSES: (InspectionStatus | "All")[] = ["All", "Planned", "InProgress", "Completed", "Overdue", "Cancelled"];

export default function InspectionsPage() {
  const [status, setStatus] = useState<string>("All");
  const inspections = useApiQuery<Inspection[]>("/inspections", {
    status: status === "All" ? undefined : status,
    page_size: 100,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Inspections</h1>
          <p className="text-sm text-muted-foreground">Scheduled, in-progress, and completed inspections.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-40">
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Link href="/inspections/plans/new">
            <Button variant="outline">New Plan</Button>
          </Link>
          <Link href="/inspections/new">
            <Button>Schedule Inspection</Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scheduled Date</TableHead>
                <TableHead>Actual Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(inspections.data ?? []).map((i) => (
                <TableRow key={i.id}>
                  <TableCell>
                    <Link href={`/inspections/${i.id}`} className="font-medium text-primary hover:underline">
                      {i.scheduled_date}
                    </Link>
                  </TableCell>
                  <TableCell>{i.actual_date ?? "—"}</TableCell>
                  <TableCell>
                    <Badge className={statusColor(i.status)}>{i.status}</Badge>
                  </TableCell>
                </TableRow>
              ))}
              {inspections.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No inspections found
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
