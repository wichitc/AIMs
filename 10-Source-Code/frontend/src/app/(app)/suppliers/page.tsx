"use client";

import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Supplier } from "@/lib/types";

export default function SuppliersPage() {
  const suppliers = useApiQuery<Supplier[]>("/suppliers");

  async function toggleBlock(supplier: Supplier) {
    const nextBlocked = !supplier.is_blocked;
    const reason = nextBlocked ? window.prompt("Block reason:") : null;
    if (nextBlocked && reason === null) return; // cancelled the prompt
    try {
      await apiClient.put(`/suppliers/${supplier.id}/block`, { is_blocked: nextBlocked, block_reason: reason || undefined });
      suppliers.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to update supplier");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Suppliers</h1>
          <p className="text-sm text-muted-foreground">Vendor master used as a source for purchase orders.</p>
        </div>
        <Link href="/suppliers/new">
          <Button>New Supplier</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Number</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Terms</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(suppliers.data ?? []).map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.supplier_number}</TableCell>
                  <TableCell>{s.name}</TableCell>
                  <TableCell className="text-muted-foreground">{s.country ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{s.email ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">{s.payment_terms ?? "—"}</TableCell>
                  <TableCell>
                    {s.is_blocked ? (
                      <Badge className="bg-status-danger-bg text-status-danger-text border-transparent" title={s.block_reason ?? undefined}>
                        Blocked
                      </Badge>
                    ) : (
                      <Badge className="bg-status-success-bg text-status-success-text border-transparent">Eligible</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button size="sm" variant={s.is_blocked ? "outline" : "destructive"} onClick={() => toggleBlock(s)}>
                      {s.is_blocked ? "Unblock" : "Block"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {suppliers.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No suppliers defined yet
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
