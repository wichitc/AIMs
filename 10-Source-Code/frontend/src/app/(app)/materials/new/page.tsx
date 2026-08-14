"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Material, MaterialType } from "@/lib/types";

const MATERIAL_TYPES: MaterialType[] = ["SparePart", "Consumable", "RawMaterial", "Service"];

export default function NewMaterialPage() {
  const router = useRouter();

  const [materialNumber, setMaterialNumber] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [materialType, setMaterialType] = useState<MaterialType>("SparePart");
  const [materialGroup, setMaterialGroup] = useState("");
  const [baseUom, setBaseUom] = useState("EA");
  const [minStockLevel, setMinStockLevel] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<Material>("/materials", {
        material_number: materialNumber,
        name,
        description: description || undefined,
        material_type: materialType,
        material_group: materialGroup || undefined,
        base_uom: baseUom,
        min_stock_level: minStockLevel === "" ? undefined : Number(minStockLevel),
      });
      router.push("/materials");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create material");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Material</h1>
        <p className="text-sm text-muted-foreground">Add a spare-part or consumable to the catalog.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Material Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="materialNumber">
                  Material Number
                </label>
                <Input
                  id="materialNumber"
                  placeholder="e.g. MAT-001"
                  value={materialNumber}
                  onChange={(e) => setMaterialNumber(e.target.value)}
                  maxLength={50}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="baseUom">
                  Base UoM
                </label>
                <Input
                  id="baseUom"
                  placeholder="e.g. EA"
                  value={baseUom}
                  onChange={(e) => setBaseUom(e.target.value)}
                  maxLength={10}
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="name">
                Name
              </label>
              <Input
                id="name"
                placeholder="e.g. Gasket, 6-inch ANSI 150#"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={200}
                required
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="description">
                Description
              </label>
              <Input
                id="description"
                placeholder="Optional"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="materialType">
                  Type
                </label>
                <Select
                  id="materialType"
                  value={materialType}
                  onChange={(e) => setMaterialType(e.target.value as MaterialType)}
                >
                  {MATERIAL_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="materialGroup">
                  Group
                </label>
                <Input
                  id="materialGroup"
                  placeholder="Optional, e.g. Gaskets & Seals"
                  value={materialGroup}
                  onChange={(e) => setMaterialGroup(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="minStockLevel">
                Minimum Stock Level
              </label>
              <Input
                id="minStockLevel"
                type="number"
                min={0}
                step="0.001"
                placeholder="Optional"
                value={minStockLevel}
                onChange={(e) => setMinStockLevel(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Material"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/materials")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
