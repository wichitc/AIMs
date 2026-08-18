"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Location, Material, StockBalance } from "@/lib/types";

export default function StockPage() {
  const balances = useApiQuery<StockBalance[]>("/stock-balances");
  const materials = useApiQuery<Material[]>("/materials");
  const locations = useApiQuery<Location[]>("/locations");

  const materialById = useMemo(() => {
    const map = new Map<string, Material>();
    (materials.data ?? []).forEach((m) => map.set(m.id, m));
    return map;
  }, [materials.data]);
  const locationById = useMemo(() => {
    const map = new Map<string, Location>();
    (locations.data ?? []).forEach((l) => map.set(l.id, l));
    return map;
  }, [locations.data]);

  const nonZero = (balances.data ?? []).filter((b) => b.quantity !== 0);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Stock Overview</h1>
          <p className="text-sm text-muted-foreground">
            Current balances by material and storage location — the derived running total of the
            immutable stock ledger.
          </p>
        </div>
        <Link href="/goods-receipts/new">
          <Button>Post Goods Receipt</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Material</TableHead>
                <TableHead>Storage Location</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Avg. Price</TableHead>
                <TableHead>Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {nonZero.map((b) => {
                const material = materialById.get(b.material_id);
                return (
                  <TableRow key={b.id}>
                    <TableCell>{material ? `${material.material_number} — ${material.name}` : b.material_id}</TableCell>
                    <TableCell>
                      {locationById.get(b.storage_location_id)?.name ?? b.storage_location_id}
                    </TableCell>
                    <TableCell>
                      {b.quantity} {material?.base_uom ?? ""}
                    </TableCell>
                    <TableCell>{material?.moving_average_price ?? "—"}</TableCell>
                    <TableCell>
                      <Badge>{b.value.toLocaleString()}</Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
              {nonZero.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">
                    No stock on hand yet
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
