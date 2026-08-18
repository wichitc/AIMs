"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Location, Material, PurchaseOrder, Supplier } from "@/lib/types";

export default function NewGoodsReceiptPage() {
  const router = useRouter();
  const orders = useApiQuery<PurchaseOrder[]>("/purchase-orders", { status: "Sent", page_size: 100 });
  const materials = useApiQuery<Material[]>("/materials");
  const suppliers = useApiQuery<Supplier[]>("/suppliers");
  const locations = useApiQuery<Location[]>("/locations");

  const [orderId, setOrderId] = useState("");
  const [quantities, setQuantities] = useState<Record<string, string>>({});
  const [locationByItem, setLocationByItem] = useState<Record<string, string>>({});
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [errorByItem, setErrorByItem] = useState<Record<string, string>>({});

  const materialById = useMemo(() => {
    const map = new Map<string, Material>();
    (materials.data ?? []).forEach((m) => map.set(m.id, m));
    return map;
  }, [materials.data]);
  const supplierById = useMemo(() => {
    const map = new Map<string, Supplier>();
    (suppliers.data ?? []).forEach((s) => map.set(s.id, s));
    return map;
  }, [suppliers.data]);

  const selectedOrder = (orders.data ?? []).find((o) => o.id === orderId) ?? null;

  async function postReceipt(poItemId: string) {
    const quantity = Number(quantities[poItemId] ?? 0);
    const storageLocationId = locationByItem[poItemId];
    setErrorByItem((prev) => ({ ...prev, [poItemId]: "" }));
    if (!quantity || quantity <= 0) {
      setErrorByItem((prev) => ({ ...prev, [poItemId]: "Enter a quantity greater than zero" }));
      return;
    }
    if (!storageLocationId) {
      setErrorByItem((prev) => ({ ...prev, [poItemId]: "Select a storage location" }));
      return;
    }
    setBusyItemId(poItemId);
    try {
      await apiClient.post("/goods-receipts", {
        po_item_id: poItemId,
        storage_location_id: storageLocationId,
        quantity,
      });
      setQuantities((prev) => ({ ...prev, [poItemId]: "" }));
      orders.refetch();
    } catch (err) {
      setErrorByItem((prev) => ({
        ...prev,
        [poItemId]: err instanceof ApiError ? err.message : "Failed to post goods receipt",
      }));
    } finally {
      setBusyItemId(null);
    }
  }

  const noSentOrders = !orders.isLoading && (orders.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Post Goods Receipt</h1>
        <p className="text-sm text-muted-foreground">
          Receive delivery against a sent purchase order — posts an immutable material document
          and updates stock.
        </p>
      </div>

      {noSentOrders && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No Sent purchase orders yet — a PO must be approved and sent before goods can be received.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Purchase Order</CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={orderId} onChange={(e) => setOrderId(e.target.value)}>
            <option value="">Select a sent purchase order…</option>
            {(orders.data ?? []).map((o) => (
              <option key={o.id} value={o.id}>
                {o.id.slice(0, 8)} — {supplierById.get(o.supplier_id)?.name ?? o.supplier_id}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {selectedOrder && (
        <Card>
          <CardHeader>
            <CardTitle>Items</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Material</TableHead>
                  <TableHead>Ordered</TableHead>
                  <TableHead>Received</TableHead>
                  <TableHead>Open</TableHead>
                  <TableHead>Qty to Receive</TableHead>
                  <TableHead>Storage Location</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {selectedOrder.items.map((item) => {
                  const open = item.quantity - item.received_quantity;
                  return (
                    <TableRow key={item.id}>
                      <TableCell>{materialById.get(item.material_id)?.material_number ?? item.material_id}</TableCell>
                      <TableCell>{item.quantity}</TableCell>
                      <TableCell>{item.received_quantity}</TableCell>
                      <TableCell>{open}</TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          min={0}
                          max={open}
                          step="0.001"
                          disabled={open <= 0}
                          value={quantities[item.id] ?? ""}
                          onChange={(e) => setQuantities((prev) => ({ ...prev, [item.id]: e.target.value }))}
                          className="w-24"
                        />
                      </TableCell>
                      <TableCell>
                        <Select
                          value={locationByItem[item.id] ?? ""}
                          onChange={(e) => setLocationByItem((prev) => ({ ...prev, [item.id]: e.target.value }))}
                          disabled={open <= 0}
                        >
                          <option value="">Select…</option>
                          {(locations.data ?? []).map((loc) => (
                            <option key={loc.id} value={loc.id}>
                              {loc.code} — {loc.name}
                            </option>
                          ))}
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          disabled={open <= 0 || busyItemId === item.id}
                          onClick={() => postReceipt(item.id)}
                        >
                          {busyItemId === item.id ? "Posting..." : "Post"}
                        </Button>
                        {errorByItem[item.id] && (
                          <p className="mt-1 text-xs text-destructive">{errorByItem[item.id]}</p>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <div className="mt-4">
              <Button variant="outline" onClick={() => router.push("/stock")}>
                View Stock Overview
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
