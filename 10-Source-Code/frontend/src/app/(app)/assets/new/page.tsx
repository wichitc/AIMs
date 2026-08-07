"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Asset, AssetClass, Location } from "@/lib/types";

export default function NewAssetPage() {
  const router = useRouter();
  const locations = useApiQuery<Location[]>("/locations");
  const assetClasses = useApiQuery<AssetClass[]>("/asset-classes");

  // Assets are registered at the Unit level per the Plant > Area > Unit > Equipment
  // hierarchy (BusinessFlow.md §1) — Plant/Area nodes are containers, not asset owners.
  const unitLocations = (locations.data ?? []).filter((l) => l.level === "Unit");

  const [locationId, setLocationId] = useState("");
  const [assetClassId, setAssetClassId] = useState("");
  const [tagNumber, setTagNumber] = useState("");
  const [name, setName] = useState("");
  const [designCode, setDesignCode] = useState("");
  const [designPressure, setDesignPressure] = useState("");
  const [designTemperature, setDesignTemperature] = useState("");
  const [material, setMaterial] = useState("");
  const [installDate, setInstallDate] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const asset = await apiClient.post<Asset>("/assets", {
        location_id: locationId,
        asset_class_id: assetClassId,
        tag_number: tagNumber,
        name,
        design_code: designCode || undefined,
        design_pressure_bar: designPressure ? Number(designPressure) : undefined,
        design_temperature_c: designTemperature ? Number(designTemperature) : undefined,
        material: material || undefined,
        install_date: installDate || undefined,
      });
      router.push(`/assets/${asset.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create asset");
    } finally {
      setIsSubmitting(false);
    }
  }

  const noUnitsAvailable = !locations.isLoading && unitLocations.length === 0;
  const noClassesAvailable = !assetClasses.isLoading && (assetClasses.data ?? []).length === 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Asset</h1>
        <p className="text-sm text-muted-foreground">Register a new tagged asset (FR-04).</p>
      </div>

      {(noUnitsAvailable || noClassesAvailable) && (
        <Card className="border-destructive/50">
          <CardContent className="pt-4 text-sm text-destructive">
            {noUnitsAvailable && (
              <p>
                No Unit-level locations exist yet —{" "}
                <a href="/locations/new" className="underline">
                  create one first
                </a>
                .
              </p>
            )}
            {noClassesAvailable && (
              <p>
                No asset classes exist yet —{" "}
                <a href="/asset-classes/new" className="underline">
                  create one first
                </a>
                .
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Asset Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="location">
                  Location (Unit)
                </label>
                <Select
                  id="location"
                  value={locationId}
                  onChange={(e) => setLocationId(e.target.value)}
                  required
                >
                  <option value="">Select unit…</option>
                  {unitLocations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name} ({l.code})
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="assetClass">
                  Asset Class
                </label>
                <Select
                  id="assetClass"
                  value={assetClassId}
                  onChange={(e) => setAssetClassId(e.target.value)}
                  required
                >
                  <option value="">Select class…</option>
                  {(assetClasses.data ?? []).map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.category})
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="tagNumber">
                  Tag Number
                </label>
                <Input
                  id="tagNumber"
                  placeholder="e.g. V-101"
                  value={tagNumber}
                  onChange={(e) => setTagNumber(e.target.value)}
                  maxLength={50}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="name">
                  Name
                </label>
                <Input
                  id="name"
                  placeholder="e.g. Feed Surge Vessel"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={200}
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="designCode">
                Design Code
              </label>
              <Input
                id="designCode"
                placeholder="e.g. ASME VIII Div.1"
                value={designCode}
                onChange={(e) => setDesignCode(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="designPressure">
                  Design Pressure (bar)
                </label>
                <Input
                  id="designPressure"
                  type="number"
                  step="0.01"
                  value={designPressure}
                  onChange={(e) => setDesignPressure(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="designTemperature">
                  Design Temp. (°C)
                </label>
                <Input
                  id="designTemperature"
                  type="number"
                  step="0.01"
                  value={designTemperature}
                  onChange={(e) => setDesignTemperature(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="installDate">
                  Install Date
                </label>
                <Input
                  id="installDate"
                  type="date"
                  value={installDate}
                  onChange={(e) => setInstallDate(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="material">
                Material
              </label>
              <Input
                id="material"
                placeholder="e.g. SA-516-70"
                value={material}
                onChange={(e) => setMaterial(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || noUnitsAvailable || noClassesAvailable}>
                {isSubmitting ? "Creating..." : "Create Asset"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/assets")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
