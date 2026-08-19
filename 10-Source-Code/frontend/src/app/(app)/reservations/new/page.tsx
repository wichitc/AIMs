"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Location, Material, Reservation } from "@/lib/types";

export default function NewReservationPage() {
  const router = useRouter();
  const materials = useApiQuery<Material[]>("/materials");
  const locations = useApiQuery<Location[]>("/locations");

  const [materialId, setMaterialId] = useState("");
  const [storageLocationId, setStorageLocationId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [purpose, setPurpose] = useState("");
  const [requiredDate, setRequiredDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<Reservation>("/reservations", {
        material_id: materialId,
        storage_location_id: storageLocationId,
        quantity: Number(quantity),
        purpose: purpose || undefined,
        required_date: requiredDate || undefined,
      });
      router.push("/reservations");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create reservation");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Reservation</h1>
        <p className="text-sm text-muted-foreground">Reserve stock ahead of an intended Goods Issue.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reservation Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="material">
                Material
              </label>
              <Select id="material" value={materialId} onChange={(e) => setMaterialId(e.target.value)} required>
                <option value="">Select material…</option>
                {(materials.data ?? []).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.material_number} — {m.name}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="location">
                Storage Location
              </label>
              <Select
                id="location"
                value={storageLocationId}
                onChange={(e) => setStorageLocationId(e.target.value)}
                required
              >
                <option value="">Select location…</option>
                {(locations.data ?? []).map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.code} — {loc.name}
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="quantity">
                  Quantity
                </label>
                <Input
                  id="quantity"
                  type="number"
                  min={0.001}
                  step="0.001"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
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

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="purpose">
                Purpose
              </label>
              <Input
                id="purpose"
                placeholder="e.g. Maintenance Order MO-2026-004"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Reservation"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/reservations")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
