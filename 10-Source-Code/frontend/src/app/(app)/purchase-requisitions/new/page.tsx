"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Material, PurchaseRequisition } from "@/lib/types";

interface DraftItem {
  materialId: string;
  quantity: string;
  estimatedPrice: string;
}

function emptyItem(): DraftItem {
  return { materialId: "", quantity: "", estimatedPrice: "" };
}

export default function NewPurchaseRequisitionPage() {
  const router = useRouter();
  const materials = useApiQuery<Material[]>("/materials");

  const [requestedDate, setRequestedDate] = useState("");
  const [requiredDate, setRequiredDate] = useState("");
  const [items, setItems] = useState<DraftItem[]>([emptyItem()]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateItem(index: number, patch: Partial<DraftItem>) {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  function addItem() {
    setItems((prev) => [...prev, emptyItem()]);
  }

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<PurchaseRequisition>("/purchase-requisitions", {
        requested_date: requestedDate,
        required_date: requiredDate || undefined,
        items: items.map((item) => ({
          material_id: item.materialId,
          quantity: Number(item.quantity),
          estimated_price: item.estimatedPrice === "" ? undefined : Number(item.estimatedPrice),
        })),
      });
      router.push("/purchase-requisitions");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create purchase requisition");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noMaterialsAvailable = !materials.isLoading && (materials.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Purchase Requisition</h1>
        <p className="text-sm text-muted-foreground">Capture demand for one or more materials.</p>
      </div>

      {noMaterialsAvailable && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            No materials exist yet —{" "}
            <a href="/materials/new" className="underline">
              create one first
            </a>
            .
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Requisition Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="requestedDate">
                  Requested Date
                </label>
                <Input
                  id="requestedDate"
                  type="date"
                  value={requestedDate}
                  onChange={(e) => setRequestedDate(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="requiredDate">
                  Required Date
                </label>
                <Input
                  id="requiredDate"
                  type="date"
                  value={requiredDate}
                  onChange={(e) => setRequiredDate(e.target.value)}
                />
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <div className="text-sm font-medium">Items</div>
              {items.map((item, index) => (
                <div key={index} className="flex flex-wrap items-end gap-2 rounded-md border border-border p-3">
                  <div className="min-w-[200px] flex-1">
                    <label className="mb-1 block text-xs font-medium">Material</label>
                    <Select
                      value={item.materialId}
                      onChange={(e) => updateItem(index, { materialId: e.target.value })}
                      required
                    >
                      <option value="">Select material…</option>
                      {(materials.data ?? []).map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.material_number} — {m.name}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium">Quantity</label>
                    <Input
                      type="number"
                      min={0.001}
                      step="0.001"
                      value={item.quantity}
                      onChange={(e) => updateItem(index, { quantity: e.target.value })}
                      className="w-24"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium">Est. Price</label>
                    <Input
                      type="number"
                      min={0}
                      step="0.01"
                      value={item.estimatedPrice}
                      onChange={(e) => updateItem(index, { estimatedPrice: e.target.value })}
                      className="w-28"
                    />
                  </div>
                  {items.length > 1 && (
                    <Button type="button" variant="outline" size="sm" onClick={() => removeItem(index)}>
                      Remove
                    </Button>
                  )}
                </div>
              ))}
              <Button type="button" variant="outline" size="sm" onClick={addItem} className="self-start">
                Add Item
              </Button>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Requisition"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/purchase-requisitions")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
