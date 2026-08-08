"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { MaintenanceOrder } from "@/lib/types";

type Status = MaintenanceOrder["status"];

const COLUMNS: Status[] = ["Open", "InProgress", "Completed", "Cancelled"];

const PRIORITY_COLOR: Record<MaintenanceOrder["priority"], string> = {
  Low: "bg-slate-100 text-slate-800 border-slate-200",
  Medium: "bg-amber-100 text-amber-800 border-amber-200",
  High: "bg-orange-100 text-orange-800 border-orange-200",
  Urgent: "bg-red-100 text-red-800 border-red-200",
};

export default function MaintenancePage() {
  const orders = useApiQuery<MaintenanceOrder[]>("/maintenance-orders", { page_size: 200 });

  const byColumn = useMemo(() => {
    const grouped: Record<Status, MaintenanceOrder[]> = { Open: [], InProgress: [], Completed: [], Cancelled: [] };
    (orders.data ?? []).forEach((o) => grouped[o.status].push(o));
    return grouped;
  }, [orders.data]);

  async function transition(order: MaintenanceOrder, status: Status) {
    try {
      await apiClient.put(`/maintenance-orders/${order.id}`, {
        status,
        completed_date: status === "Completed" ? new Date().toISOString().slice(0, 10) : undefined,
      });
      orders.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to update maintenance order");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Maintenance Orders</h1>
          <p className="text-sm text-muted-foreground">Corrective, preventive, and predictive work orders.</p>
        </div>
        <Link href="/maintenance/new">
          <Button>New Maintenance Order</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-3 overflow-x-auto sm:grid-cols-2 lg:grid-cols-4">
        {COLUMNS.map((column) => (
          <div key={column} className="flex min-w-[220px] flex-col gap-2">
            <div className="text-sm font-semibold text-muted-foreground">
              {column} ({byColumn[column].length})
            </div>
            {byColumn[column].map((order) => (
              <Card key={order.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-foreground">
                    <span className="text-sm">{order.order_type}</span>
                    <Badge className={PRIORITY_COLOR[order.priority]}>{order.priority}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2 text-xs text-muted-foreground">
                  <div>Scheduled: {order.scheduled_date ?? "—"}</div>
                  {order.completed_date && <div>Completed: {order.completed_date}</div>}
                  {order.defect_id && (
                    <Badge className="w-fit bg-blue-100 text-blue-800 border-blue-200">From Defect</Badge>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {order.status === "Open" && (
                      <Button size="sm" variant="outline" onClick={() => transition(order, "InProgress")}>
                        Start
                      </Button>
                    )}
                    {order.status === "InProgress" && (
                      <Button size="sm" variant="outline" onClick={() => transition(order, "Completed")}>
                        Mark Completed
                      </Button>
                    )}
                    {(order.status === "Open" || order.status === "InProgress") && (
                      <Button size="sm" variant="destructive" onClick={() => transition(order, "Cancelled")}>
                        Cancel
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            {byColumn[column].length === 0 && (
              <p className="text-xs text-muted-foreground">No orders</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
