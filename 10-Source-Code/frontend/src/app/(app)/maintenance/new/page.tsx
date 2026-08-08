"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Asset, Defect, Equipment, MaintenanceOrder } from "@/lib/types";

interface UserOption {
  id: string;
  username: string;
  full_name: string;
}

const ORDER_TYPES: MaintenanceOrder["order_type"][] = ["Corrective", "Preventive", "Predictive"];
const PRIORITIES: MaintenanceOrder["priority"][] = ["Low", "Medium", "High", "Urgent"];

export default function NewMaintenanceOrderPage() {
  const router = useRouter();
  const assets = useApiQuery<Asset[]>("/assets", { page_size: 100 });
  // Orders are most often raised to execute an already-approved repair — scope the
  // optional defect link to ones sitting in Repair (see defect/service.py _VALID_TRANSITIONS
  // and the Kanban board's Approval -> Repair step).
  const repairDefects = useApiQuery<Defect[]>("/defects", { workflow_status: "Repair", page_size: 100 });
  const users = useApiQuery<UserOption[]>("/users", { page_size: 100 });

  const [assetId, setAssetId] = useState("");
  const [equipmentId, setEquipmentId] = useState("");
  const [defectId, setDefectId] = useState("");
  const [orderType, setOrderType] = useState<MaintenanceOrder["order_type"]>("Corrective");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<MaintenanceOrder["priority"]>("Medium");
  const [scheduledDate, setScheduledDate] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [costEstimate, setCostEstimate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const equipment = useApiQuery<Equipment[]>(assetId ? `/assets/${assetId}/equipment` : null);

  function handleDefectChange(id: string) {
    setDefectId(id);
    const defect = (repairDefects.data ?? []).find((d) => d.id === id);
    if (defect) {
      setEquipmentId(defect.equipment_id);
      setOrderType("Corrective");
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<MaintenanceOrder>("/maintenance-orders", {
        equipment_id: equipmentId,
        defect_id: defectId || undefined,
        order_type: orderType,
        description,
        priority,
        scheduled_date: scheduledDate || undefined,
        assigned_to: assignedTo || undefined,
        cost_estimate: costEstimate ? Number(costEstimate) : undefined,
      });
      router.push("/maintenance");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create maintenance order");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noAssetsAvailable = !assets.isLoading && (assets.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Maintenance Order</h1>
        <p className="text-sm text-muted-foreground">
          Schedule corrective, preventive, or predictive work against a piece of equipment.
        </p>
      </div>

      {noAssetsAvailable && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No assets exist yet —{" "}
            <a href="/assets/new" className="underline">
              register one first
            </a>
            .
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Order Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="defect">
                Link to Approved Repair (optional)
              </label>
              <Select id="defect" value={defectId} onChange={(e) => handleDefectChange(e.target.value)}>
                <option value="">None — standalone order</option>
                {(repairDefects.data ?? []).map((d) => (
                  <option key={d.id} value={d.id}>
                    Defect {d.id.slice(0, 8)} — {d.severity}
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="asset">
                  Asset
                </label>
                <Select
                  id="asset"
                  value={assetId}
                  onChange={(e) => {
                    setAssetId(e.target.value);
                    setEquipmentId("");
                  }}
                  disabled={!!defectId}
                  required={!defectId}
                >
                  <option value="">Select asset…</option>
                  {(assets.data ?? []).map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.tag_number} — {a.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="equipment">
                  Equipment / Component
                </label>
                <Select
                  id="equipment"
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  disabled={!!defectId || !assetId}
                  required
                >
                  <option value="">Select equipment…</option>
                  {(equipment.data ?? []).map((eq) => (
                    <option key={eq.id} value={eq.id}>
                      {eq.tag_number} — {eq.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="orderType">
                  Order Type
                </label>
                <Select
                  id="orderType"
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value as MaintenanceOrder["order_type"])}
                >
                  {ORDER_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="priority">
                  Priority
                </label>
                <Select
                  id="priority"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as MaintenanceOrder["priority"])}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="description">
                Description
              </label>
              <Input
                id="description"
                placeholder="e.g. Re-torque nozzle N2 bolting per finding"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="scheduledDate">
                  Scheduled Date
                </label>
                <Input
                  id="scheduledDate"
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="assignedTo">
                  Assign To
                </label>
                <Select id="assignedTo" value={assignedTo} onChange={(e) => setAssignedTo(e.target.value)}>
                  <option value="">Unassigned</option>
                  {(users.data ?? []).map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.username})
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="costEstimate">
                  Cost Estimate
                </label>
                <Input
                  id="costEstimate"
                  type="number"
                  step="100"
                  value={costEstimate}
                  onChange={(e) => setCostEstimate(e.target.value)}
                />
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || !equipmentId}>
                {isSubmitting ? "Creating..." : "Create Order"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/maintenance")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
