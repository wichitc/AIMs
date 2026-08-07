"use client";

import { useState } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { AssetTree } from "@/components/asset/AssetTree";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Asset, Location } from "@/lib/types";

export default function AssetsPage() {
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const locations = useApiQuery<Location[]>("/locations");
  const assets = useApiQuery<Asset[]>("/assets", {
    location_id: selectedLocationId ?? undefined,
    page_size: 100,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Asset Register</h1>
          <p className="text-sm text-muted-foreground">Plant → Area → Unit → Equipment → Component hierarchy.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/locations/new">
            <Button variant="outline">New Location</Button>
          </Link>
          <Link href="/asset-classes/new">
            <Button variant="outline">New Asset Class</Button>
          </Link>
          <Link href="/assets/new">
            <Button>New Asset</Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-[240px_1fr]">
        <Card>
          <CardContent className="pt-4">
            {locations.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading locations…</p>
            ) : (
              <AssetTree
                locations={locations.data ?? []}
                selectedId={selectedLocationId}
                onSelect={setSelectedLocationId}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tag Number</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Design Code</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(assets.data ?? []).map((asset) => (
                  <TableRow key={asset.id}>
                    <TableCell>
                      <Link href={`/assets/${asset.id}`} className="font-medium text-primary hover:underline">
                        {asset.tag_number}
                      </Link>
                    </TableCell>
                    <TableCell>{asset.name}</TableCell>
                    <TableCell>
                      <Badge className={statusColor(asset.status)}>{asset.status}</Badge>
                    </TableCell>
                    <TableCell>{asset.design_code ?? "—"}</TableCell>
                  </TableRow>
                ))}
                {assets.data?.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      No assets found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
