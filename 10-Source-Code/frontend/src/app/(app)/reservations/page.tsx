"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Location, Material, Reservation } from "@/lib/types";

export default function ReservationsPage() {
  const reservations = useApiQuery<Reservation[]>("/reservations");
  const materials = useApiQuery<Material[]>("/materials");
  const locations = useApiQuery<Location[]>("/locations");
  const [issueQty, setIssueQty] = useState<Record<string, string>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [errorByReservation, setErrorByReservation] = useState<Record<string, string>>({});

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

  async function issue(reservation: Reservation) {
    const quantity = Number(issueQty[reservation.id] ?? 0);
    setErrorByReservation((prev) => ({ ...prev, [reservation.id]: "" }));
    if (!quantity || quantity <= 0) {
      setErrorByReservation((prev) => ({ ...prev, [reservation.id]: "Enter a quantity greater than zero" }));
      return;
    }
    setBusyId(reservation.id);
    try {
      await apiClient.post("/goods-issues", { reservation_id: reservation.id, quantity });
      setIssueQty((prev) => ({ ...prev, [reservation.id]: "" }));
      reservations.refetch();
    } catch (err) {
      setErrorByReservation((prev) => ({
        ...prev,
        [reservation.id]: err instanceof ApiError ? err.message : "Failed to post goods issue",
      }));
    } finally {
      setBusyId(null);
    }
  }

  async function cancel(reservation: Reservation) {
    try {
      await apiClient.post(`/reservations/${reservation.id}/cancel`);
      reservations.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to cancel reservation");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Reservations</h1>
          <p className="text-sm text-muted-foreground">
            Dated availability reservations — Goods Issue only consumes unrestricted stock through one of these.
          </p>
        </div>
        <Link href="/reservations/new">
          <Button>New Reservation</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Material</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Issued</TableHead>
                <TableHead>Purpose</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(reservations.data ?? []).map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{materialById.get(r.material_id)?.material_number ?? r.material_id}</TableCell>
                  <TableCell>{locationById.get(r.storage_location_id)?.name ?? r.storage_location_id}</TableCell>
                  <TableCell>{r.quantity}</TableCell>
                  <TableCell>{r.issued_quantity}</TableCell>
                  <TableCell className="text-muted-foreground">{r.purpose ?? "—"}</TableCell>
                  <TableCell>
                    <Badge className={statusColor(r.status)}>{r.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {r.status === "Open" && (
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          min={0}
                          max={r.quantity - r.issued_quantity}
                          step="0.001"
                          placeholder="Qty"
                          value={issueQty[r.id] ?? ""}
                          onChange={(e) => setIssueQty((prev) => ({ ...prev, [r.id]: e.target.value }))}
                          className="w-20"
                        />
                        <Button size="sm" disabled={busyId === r.id} onClick={() => issue(r)}>
                          Issue
                        </Button>
                        {r.issued_quantity === 0 && (
                          <Button size="sm" variant="destructive" onClick={() => cancel(r)}>
                            Cancel
                          </Button>
                        )}
                      </div>
                    )}
                    {errorByReservation[r.id] && (
                      <p className="mt-1 text-xs text-destructive">{errorByReservation[r.id]}</p>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {reservations.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No reservations yet
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
