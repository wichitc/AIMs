"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import type { Material, PurchaseRequisition, PurchaseRequisitionStatus } from "@/lib/types";

interface UserOption {
  id: string;
  username: string;
  full_name: string;
}

const COLUMNS: PurchaseRequisitionStatus[] = ["Draft", "Submitted", "Approved", "Rejected", "Withdrawn"];

export default function PurchaseRequisitionsPage() {
  const { user: currentUser } = useAuth();
  const requisitions = useApiQuery<PurchaseRequisition[]>("/purchase-requisitions", { page_size: 200 });
  const users = useApiQuery<UserOption[]>("/users", { page_size: 100 });
  const materials = useApiQuery<Material[]>("/materials");
  const [busyId, setBusyId] = useState<string | null>(null);

  const userById = useMemo(() => {
    const map = new Map<string, UserOption>();
    (users.data ?? []).forEach((u) => map.set(u.id, u));
    return map;
  }, [users.data]);

  const materialById = useMemo(() => {
    const map = new Map<string, Material>();
    (materials.data ?? []).forEach((m) => map.set(m.id, m));
    return map;
  }, [materials.data]);

  const byColumn = useMemo(() => {
    const grouped: Record<PurchaseRequisitionStatus, PurchaseRequisition[]> = {
      Draft: [],
      Submitted: [],
      Approved: [],
      Rejected: [],
      Withdrawn: [],
    };
    (requisitions.data ?? []).forEach((r) => grouped[r.status].push(r));
    return grouped;
  }, [requisitions.data]);

  async function act(id: string, action: "submit" | "approve" | "reject" | "withdraw") {
    setBusyId(id);
    try {
      const reason = action === "reject" ? window.prompt("Rejection reason (optional):") ?? undefined : undefined;
      await apiClient.post(`/purchase-requisitions/${id}/${action}`, action === "reject" ? { reason } : undefined);
      requisitions.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : `Failed to ${action} purchase requisition`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Purchase Requisitions</h1>
          <p className="text-sm text-muted-foreground">
            Demand capture and single-step approval — Draft → Submitted → Approved/Rejected.
          </p>
        </div>
        <Link href="/purchase-requisitions/new">
          <Button>New Requisition</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-3 overflow-x-auto sm:grid-cols-2 lg:grid-cols-5">
        {COLUMNS.map((column) => (
          <div key={column} className="flex min-w-[220px] flex-col gap-2">
            <div className="text-sm font-semibold text-muted-foreground">
              {column} ({byColumn[column].length})
            </div>
            {byColumn[column].map((r) => {
              const totalEstimate = r.items.reduce((sum, i) => sum + (i.estimated_price ?? 0) * i.quantity, 0);
              const isRequester = currentUser?.id === r.requester_id;
              return (
                <Card key={r.id}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between text-foreground">
                      <span className="text-sm">{userById.get(r.requester_id)?.full_name ?? "—"}</span>
                      <Badge>{r.items.length} item{r.items.length === 1 ? "" : "s"}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-2 text-xs text-muted-foreground">
                    <ul className="list-disc pl-4">
                      {r.items.map((item) => (
                        <li key={item.id}>
                          {materialById.get(item.material_id)?.material_number ?? item.material_id} × {item.quantity}
                        </li>
                      ))}
                    </ul>
                    {totalEstimate > 0 && <div>Est. total: {totalEstimate.toLocaleString()}</div>}
                    <div>Requested: {r.requested_date}</div>
                    {r.decision_reason && <div>Reason: {r.decision_reason}</div>}
                    <div className="flex flex-wrap gap-2">
                      {r.status === "Draft" && isRequester && (
                        <Button size="sm" variant="outline" disabled={busyId === r.id} onClick={() => act(r.id, "submit")}>
                          Submit
                        </Button>
                      )}
                      {(r.status === "Draft" || r.status === "Submitted") && isRequester && (
                        <Button size="sm" variant="destructive" disabled={busyId === r.id} onClick={() => act(r.id, "withdraw")}>
                          Withdraw
                        </Button>
                      )}
                      {r.status === "Submitted" && !isRequester && (
                        <>
                          <Button size="sm" onClick={() => act(r.id, "approve")} disabled={busyId === r.id}>
                            Approve
                          </Button>
                          <Button size="sm" variant="destructive" disabled={busyId === r.id} onClick={() => act(r.id, "reject")}>
                            Reject
                          </Button>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {byColumn[column].length === 0 && <p className="text-xs text-muted-foreground">No requisitions</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
