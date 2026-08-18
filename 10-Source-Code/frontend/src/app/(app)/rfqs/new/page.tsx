"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Material, PurchaseRequisition, RFQ } from "@/lib/types";

export default function NewRFQPage() {
  const router = useRouter();
  const requisitions = useApiQuery<PurchaseRequisition[]>("/purchase-requisitions", { page_size: 200 });
  const materials = useApiQuery<Material[]>("/materials");

  const approvedRequisitions = useMemo(
    () => (requisitions.data ?? []).filter((r) => r.status === "Approved"),
    [requisitions.data],
  );
  const materialById = useMemo(() => {
    const map = new Map<string, Material>();
    (materials.data ?? []).forEach((m) => map.set(m.id, m));
    return map;
  }, [materials.data]);

  const [requisitionId, setRequisitionId] = useState("");
  const [deadline, setDeadline] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRequisition = approvedRequisitions.find((r) => r.id === requisitionId) ?? null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const rfq = await apiClient.post<RFQ>("/rfqs", {
        purchase_requisition_id: requisitionId,
        deadline: deadline || undefined,
      });
      router.push(`/rfqs/${rfq.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create RFQ");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noApprovedRequisitions = !requisitions.isLoading && approvedRequisitions.length === 0;

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New RFQ</h1>
        <p className="text-sm text-muted-foreground">Source an approved purchase requisition through supplier bids.</p>
      </div>

      {noApprovedRequisitions && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No Approved purchase requisitions yet — a requisition must be submitted and approved first.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>RFQ Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="requisition">
                Purchase Requisition
              </label>
              <Select
                id="requisition"
                value={requisitionId}
                onChange={(e) => setRequisitionId(e.target.value)}
                required
              >
                <option value="">Select approved requisition…</option>
                {approvedRequisitions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.id.slice(0, 8)} — {r.items.length} item{r.items.length === 1 ? "" : "s"} ({r.requested_date})
                  </option>
                ))}
              </Select>
              {selectedRequisition && (
                <ul className="mt-2 list-disc pl-4 text-xs text-muted-foreground">
                  {selectedRequisition.items.map((item) => (
                    <li key={item.id}>
                      {materialById.get(item.material_id)?.material_number ?? item.material_id} × {item.quantity}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="deadline">
                Deadline
              </label>
              <Input id="deadline" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || !requisitionId}>
                {isSubmitting ? "Creating..." : "Create RFQ"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/rfqs")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
