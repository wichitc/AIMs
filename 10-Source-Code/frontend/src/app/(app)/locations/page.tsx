"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Location } from "@/lib/types";

function formatCoord(value: number | null): string {
  return value === null ? "—" : value.toFixed(6);
}

export default function LocationsPage() {
  const locations = useApiQuery<Location[]>("/locations");

  const nameById = useMemo(() => {
    const map = new Map<string, string>();
    (locations.data ?? []).forEach((l) => map.set(l.id, l.name));
    return map;
  }, [locations.data]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Locations</h1>
          <p className="text-sm text-muted-foreground">Plant → Area → Unit hierarchy (BusinessFlow.md §1).</p>
        </div>
        <Link href="/locations/new">
          <Button>New Location</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Level</TableHead>
                <TableHead>Parent</TableHead>
                <TableHead>Latitude</TableHead>
                <TableHead>Longitude</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(locations.data ?? []).map((l) => (
                <TableRow key={l.id}>
                  <TableCell className="font-medium">{l.code}</TableCell>
                  <TableCell>{l.name}</TableCell>
                  <TableCell>
                    <Badge>{l.level}</Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {l.parent_location_id ? nameById.get(l.parent_location_id) ?? "—" : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatCoord(l.latitude)}</TableCell>
                  <TableCell className="text-muted-foreground">{formatCoord(l.longitude)}</TableCell>
                </TableRow>
              ))}
              {locations.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    No locations defined yet
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
