"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Location, Material, StockTransfer } from "@/lib/types";

export default function StockTransfersPage() {
  const transfers = useApiQuery<StockTransfer[]>("/stock-transfers");
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

  async function receive(transferId: string) {
    try {
      await apiClient.post(`/stock-transfers/${transferId}/receive`);
      transfers.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to receive transfer");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Stock Transfers</h1>
        <p className="text-sm text-muted-foreground">
          Move stock between locations — one-step completes immediately, two-step holds the
          quantity in transit until received.
        </p>
      </div>

      <TransferForm materials={materials.data ?? []} locations={locations.data ?? []} onPosted={transfers.refetch} />

      <Card>
        <CardHeader>
          <CardTitle>Transfers</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Material</TableHead>
                <TableHead>From</TableHead>
                <TableHead>To</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Mode</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(transfers.data ?? []).map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{materialById.get(t.material_id)?.material_number ?? t.material_id}</TableCell>
                  <TableCell>{locationById.get(t.source_location_id)?.name ?? t.source_location_id}</TableCell>
                  <TableCell>{locationById.get(t.destination_location_id)?.name ?? t.destination_location_id}</TableCell>
                  <TableCell>{t.quantity}</TableCell>
                  <TableCell>{t.transfer_mode}</TableCell>
                  <TableCell>
                    <Badge className={statusColor(t.status)}>{t.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {t.status === "InTransit" && (
                      <Button size="sm" onClick={() => receive(t.id)}>
                        Receive
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {transfers.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No transfers yet
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

function TransferForm({
  materials,
  locations,
  onPosted,
}: {
  materials: Material[];
  locations: Location[];
  onPosted: () => void;
}) {
  const [mode, setMode] = useState<"OneStep" | "TwoStep">("OneStep");
  const [materialId, setMaterialId] = useState("");
  const [sourceLocationId, setSourceLocationId] = useState("");
  const [destinationLocationId, setDestinationLocationId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const path = mode === "OneStep" ? "/stock-transfers/one-step" : "/stock-transfers/issue";
      await apiClient.post(path, {
        material_id: materialId,
        source_location_id: sourceLocationId,
        destination_location_id: destinationLocationId,
        quantity: Number(quantity),
      });
      setMaterialId("");
      setSourceLocationId("");
      setDestinationLocationId("");
      setQuantity("");
      onPosted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to post transfer");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Transfer</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium">Mode</label>
            <Select value={mode} onChange={(e) => setMode(e.target.value as "OneStep" | "TwoStep")}>
              <option value="OneStep">One-step</option>
              <option value="TwoStep">Two-step (issue now, receive later)</option>
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Material</label>
            <Select value={materialId} onChange={(e) => setMaterialId(e.target.value)} required>
              <option value="">Select…</option>
              {materials.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.material_number}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">From</label>
            <Select value={sourceLocationId} onChange={(e) => setSourceLocationId(e.target.value)} required>
              <option value="">Select…</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.code}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">To</label>
            <Select value={destinationLocationId} onChange={(e) => setDestinationLocationId(e.target.value)} required>
              <option value="">Select…</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.code}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Quantity</label>
            <Input
              type="number"
              min={0.001}
              step="0.001"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-28"
              required
            />
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Posting..." : "Post Transfer"}
          </Button>
          {error && <p className="w-full text-sm text-destructive">{error}</p>}
        </form>
      </CardContent>
    </Card>
  );
}
