"use client";

import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Material } from "@/lib/types";

export default function MaterialsPage() {
  const materials = useApiQuery<Material[]>("/materials");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Materials</h1>
          <p className="text-sm text-muted-foreground">
            Spare-part and consumable catalog used by purchase requisitions and stock.
          </p>
        </div>
        <Link href="/materials/new">
          <Button>New Material</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Number</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>UoM</TableHead>
                <TableHead>Avg. Price</TableHead>
                <TableHead>Min. Stock</TableHead>
                <TableHead>Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(materials.data ?? []).map((m) => (
                <TableRow key={m.id}>
                  <TableCell className="font-medium">{m.material_number}</TableCell>
                  <TableCell>{m.name}</TableCell>
                  <TableCell>
                    <Badge>{m.material_type}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{m.material_group ?? "—"}</TableCell>
                  <TableCell>{m.base_uom}</TableCell>
                  <TableCell>{m.moving_average_price ?? "—"}</TableCell>
                  <TableCell>{m.min_stock_level ?? "—"}</TableCell>
                  <TableCell>{m.is_active ? "Yes" : "No"}</TableCell>
                </TableRow>
              ))}
              {materials.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">
                    No materials defined yet
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
