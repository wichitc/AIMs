"use client";

import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AssetClass } from "@/lib/types";

export default function AssetClassesPage() {
  const assetClasses = useApiQuery<AssetClass[]>("/asset-classes");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Asset Classes</h1>
          <p className="text-sm text-muted-foreground">
            Taxonomy used to classify assets (e.g. Pressure Vessel, Piping) — see Database.md §4.2.
          </p>
        </div>
        <Link href="/asset-classes/new">
          <Button>New Asset Class</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(assetClasses.data ?? []).map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.code}</TableCell>
                  <TableCell>{c.name}</TableCell>
                  <TableCell>
                    <Badge>{c.category}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{c.description ?? "—"}</TableCell>
                </TableRow>
              ))}
              {assetClasses.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No asset classes defined yet
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
