"use client";

import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { RFQ } from "@/lib/types";

export default function RFQsPage() {
  const rfqs = useApiQuery<RFQ[]>("/rfqs");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">RFQs</h1>
          <p className="text-sm text-muted-foreground">
            Request for quotation — solicit and compare supplier offers against an approved requisition.
          </p>
        </div>
        <Link href="/rfqs/new">
          <Button>New RFQ</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Deadline</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(rfqs.data ?? []).map((r) => (
                <TableRow key={r.id}>
                  <TableCell>
                    <Badge className={statusColor(r.status)}>{r.status}</Badge>
                  </TableCell>
                  <TableCell>{r.deadline ?? "—"}</TableCell>
                  <TableCell>
                    <Link href={`/rfqs/${r.id}`} className="text-sm text-primary hover:underline">
                      Open
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {rfqs.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground">
                    No RFQs yet
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
