"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { Location } from "@/lib/types";

// Plant is top-level (no parent); Area sits under a Plant; Unit sits under an Area or
// directly under a Plant — matches the Plant > Area > Unit hierarchy in BusinessFlow.md §1.
const VALID_PARENT_LEVELS: Record<string, string[]> = {
  Plant: [],
  Area: ["Plant"],
  Unit: ["Plant", "Area"],
};

export default function NewLocationPage() {
  const router = useRouter();
  const locations = useApiQuery<Location[]>("/locations");

  const [level, setLevel] = useState<"Plant" | "Area" | "Unit">("Plant");
  const [parentLocationId, setParentLocationId] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eligibleParents = (locations.data ?? []).filter((l) =>
    VALID_PARENT_LEVELS[level].includes(l.level),
  );

  function handleLevelChange(next: "Plant" | "Area" | "Unit") {
    setLevel(next);
    setParentLocationId(""); // previous selection may not be a valid parent for the new level
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<Location>("/locations", {
        level,
        parent_location_id: parentLocationId || undefined,
        name,
        code,
        latitude: latitude ? Number(latitude) : undefined,
        longitude: longitude ? Number(longitude) : undefined,
      });
      router.push("/locations");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create location");
    } finally {
      setIsSubmitting(false);
    }
  }

  const requiresParent = VALID_PARENT_LEVELS[level].length > 0;

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Location</h1>
        <p className="text-sm text-muted-foreground">
          Add a node to the Plant → Area → Unit hierarchy.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Location Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="level">
                Level
              </label>
              <Select
                id="level"
                value={level}
                onChange={(e) => handleLevelChange(e.target.value as "Plant" | "Area" | "Unit")}
              >
                <option value="Plant">Plant</option>
                <option value="Area">Area</option>
                <option value="Unit">Unit</option>
              </Select>
            </div>

            {requiresParent && (
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="parent">
                  Parent ({VALID_PARENT_LEVELS[level].join(" or ")})
                </label>
                <Select
                  id="parent"
                  value={parentLocationId}
                  onChange={(e) => setParentLocationId(e.target.value)}
                  required
                >
                  <option value="">Select parent…</option>
                  {eligibleParents.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.level}: {l.name} ({l.code})
                    </option>
                  ))}
                </Select>
                {eligibleParents.length === 0 && !locations.isLoading && (
                  <p className="mt-1 text-xs text-destructive">
                    No {VALID_PARENT_LEVELS[level].join("/")} exists yet — create one first.
                  </p>
                )}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="name">
                  Name
                </label>
                <Input
                  id="name"
                  placeholder="e.g. Crude Distillation Unit 200"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={200}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="code">
                  Code
                </label>
                <Input
                  id="code"
                  placeholder="e.g. CDU-200"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  maxLength={50}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="latitude">
                  Latitude (optional)
                </label>
                <Input
                  id="latitude"
                  type="number"
                  step="0.000001"
                  placeholder="e.g. 12.682400"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="longitude">
                  Longitude (optional)
                </label>
                <Input
                  id="longitude"
                  type="number"
                  step="0.000001"
                  placeholder="e.g. 101.147800"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                />
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button
                type="submit"
                disabled={isSubmitting || (requiresParent && eligibleParents.length === 0)}
              >
                {isSubmitting ? "Creating..." : "Create Location"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/locations")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
