"use client";

import { useMemo, useState } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Material, PurchaseOrder, PurchaseOrderStatus, Supplier } from "@/lib/types";

const COLUMNS: PurchaseOrderStatus[] = ["Draft", "Approved", "Sent", "Cancelled"];

export default function PurchaseOrdersPage() {
  const orders = useApiQuery<PurchaseOrder[]>("/purchase-orders", { page_size: 200 });
  const suppliers = useApiQuery<Supplier[]>("/suppliers");
  const materials = useApiQuery<Material[]>("/materials");
  const [busyId, setBusyId] = useState<string | null>(null);

  const supplierById = useMemo(() => {
    const map = new Map<string, Supplier>();
    (suppliers.data ?? []).forEach((s) => map.set(s.id, s));
    return map;
  }, [suppliers.data]);
  const materialById = useMemo(() => {
    const map = new Map<string, Material>();
    (materials.data ?? []).forEach((m) => map.set(m.id, m));
    return map;
  }, [materials.data]);

  const byColumn = useMemo(() => {
    const grouped: Record<PurchaseOrderStatus, PurchaseOrder[]> = {
      Draft: [],
      Approved: [],
      Sent: [],
      Cancelled: [],
    };
    (orders.data ?? []).forEach((o) => grouped[o.status].push(o));
    return grouped;
  }, [orders.data]);

  async function approve(id: string) {
    setBusyId(id);
    try {
      await apiClient.post(`/purchase-orders/${id}/approve`);
      orders.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to approve purchase order");
    } finally {
      setBusyId(null);
    }
  }

  async function send(id: string) {
    setBusyId(id);
    try {
      await apiClient.post(`/purchase-orders/${id}/send`);
      orders.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to send purchase order");
    } finally {
      setBusyId(null);
    }
  }

  async function confirm(id: string) {
    const confirmedDate = window.prompt("Confirmed date (YYYY-MM-DD):", new Date().toISOString().slice(0, 10));
    if (!confirmedDate) return;
    setBusyId(id);
    try {
      await apiClient.post(`/purchase-orders/${id}/confirm`, { confirmed_date: confirmedDate });
      orders.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to confirm purchase order");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Purchase Orders</h1>
        <p className="text-sm text-muted-foreground">
          Formalized supplier commitments, converted from awarded quotation items.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 overflow-x-auto sm:grid-cols-2 lg:grid-cols-4">
        {COLUMNS.map((column) => (
          <div key={column} className="flex min-w-[240px] flex-col gap-2">
            <div className="text-sm font-semibold text-muted-foreground">
              {column} ({byColumn[column].length})
            </div>
            {byColumn[column].map((order) => {
              const total = order.items.reduce((sum, i) => sum + i.quantity * i.unit_price, 0);
              return (
                <Card key={order.id}>
                  <CardHeader>
                    <CardTitle className="text-sm text-foreground">
                      {supplierById.get(order.supplier_id)?.name ?? order.supplier_id}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-2 text-xs text-muted-foreground">
                    <ul className="list-disc pl-4">
                      {order.items.map((item) => (
                        <li key={item.id}>
                          {materialById.get(item.material_id)?.material_number ?? item.material_id} × {item.quantity} @{" "}
                          {item.unit_price}
                        </li>
                      ))}
                    </ul>
                    <div>Total: {total.toLocaleString()}</div>
                    <div>Order date: {order.order_date}</div>
                    {order.confirmed_by_supplier && (
                      <Badge className="w-fit bg-status-success-bg text-status-success-text border-transparent">
                        Confirmed {order.confirmed_date}
                      </Badge>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {order.status === "Draft" && (
                        <Button size="sm" variant="outline" disabled={busyId === order.id} onClick={() => approve(order.id)}>
                          Approve
                        </Button>
                      )}
                      {order.status === "Approved" && (
                        <Button size="sm" variant="outline" disabled={busyId === order.id} onClick={() => send(order.id)}>
                          Send
                        </Button>
                      )}
                      {order.status === "Sent" && !order.confirmed_by_supplier && (
                        <Button size="sm" variant="outline" disabled={busyId === order.id} onClick={() => confirm(order.id)}>
                          Record Confirmation
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {byColumn[column].length === 0 && <p className="text-xs text-muted-foreground">No orders</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
