"use client";

import { useState, type FormEvent } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { AddEquipmentForm } from "@/components/asset/AddEquipmentForm";
import { CorrosionPanel } from "@/components/asset/CorrosionPanel";
import { CriticalityPanel } from "@/components/asset/CriticalityPanel";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Asset, AssetStatus, Equipment, RiskAssessment } from "@/lib/types";

const ASSET_STATUSES: AssetStatus[] = [
  "Design",
  "Construction",
  "Commissioning",
  "Operating",
  "Inactive",
  "Decommissioned",
];

function EditAssetForm({ asset, onSaved, onCancel }: { asset: Asset; onSaved: () => void; onCancel: () => void }) {
  const [name, setName] = useState(asset.name);
  const [status, setStatus] = useState<AssetStatus>(asset.status);
  const [designPressure, setDesignPressure] = useState(asset.design_pressure_bar?.toString() ?? "");
  const [designTemperature, setDesignTemperature] = useState(asset.design_temperature_c?.toString() ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.put(`/assets/${asset.id}`, {
        name,
        status,
        design_pressure_bar: designPressure === "" ? undefined : Number(designPressure),
        design_temperature_c: designTemperature === "" ? undefined : Number(designTemperature),
      });
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update asset");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="editName">
          Name
        </label>
        <Input id="editName" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="editStatus">
          Status
        </label>
        <Select id="editStatus" value={status} onChange={(e) => setStatus(e.target.value as AssetStatus)}>
          {ASSET_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="editDesignPressure">
          Design Pressure (bar)
        </label>
        <Input
          id="editDesignPressure"
          type="number"
          step="0.1"
          value={designPressure}
          onChange={(e) => setDesignPressure(e.target.value)}
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium" htmlFor="editDesignTemperature">
          Design Temperature (°C)
        </label>
        <Input
          id="editDesignTemperature"
          type="number"
          step="0.1"
          value={designTemperature}
          onChange={(e) => setDesignTemperature(e.target.value)}
        />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving..." : "Save"}
      </Button>
      <Button type="button" variant="outline" onClick={onCancel}>
        Cancel
      </Button>
      {error && <p className="w-full text-sm text-destructive">{error}</p>}
    </form>
  );
}

export default function AssetDetailPage({ params }: { params: { assetId: string } }) {
  const { assetId } = params;
  const asset = useApiQuery<Asset>(`/assets/${assetId}`);
  const equipment = useApiQuery<Equipment[]>(`/assets/${assetId}/equipment`);
  const risks = useApiQuery<RiskAssessment[]>("/risk-assessments", { asset_id: assetId });
  const [showAddEquipment, setShowAddEquipment] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  if (asset.isLoading) return <p className="text-muted-foreground">Loading asset…</p>;
  if (asset.error || !asset.data) return <p className="text-destructive">{asset.error ?? "Asset not found"}</p>;

  const data = asset.data;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">{data.tag_number}</h1>
        <Badge className={statusColor(data.status)}>{data.status}</Badge>
      </div>
      <p className="text-sm text-muted-foreground">{data.name}</p>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="equipment">Equipment</TabsTrigger>
          <TabsTrigger value="corrosion">Corrosion</TabsTrigger>
          <TabsTrigger value="criticality">Criticality</TabsTrigger>
          <TabsTrigger value="risk">Risk</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardContent className="flex flex-col gap-4 pt-4">
              {isEditing ? (
                <EditAssetForm
                  asset={data}
                  onSaved={() => {
                    setIsEditing(false);
                    asset.refetch();
                  }}
                  onCancel={() => setIsEditing(false)}
                />
              ) : (
                <>
                  <div className="flex justify-end">
                    <Button size="sm" variant="outline" onClick={() => setIsEditing(true)}>
                      Edit
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
                    <div>
                      <div className="text-muted-foreground">Design Code</div>
                      <div>{data.design_code ?? "—"}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Install Date</div>
                      <div>{data.install_date ?? "—"}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Status</div>
                      <div>{data.status}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Design Pressure</div>
                      <div>{data.design_pressure_bar != null ? `${data.design_pressure_bar} bar` : "—"}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Design Temperature</div>
                      <div>{data.design_temperature_c != null ? `${data.design_temperature_c} °C` : "—"}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Material</div>
                      <div>{data.material ?? "—"}</div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="equipment">
          <div className="mb-3 flex justify-end">
            {!showAddEquipment && (
              <Button size="sm" onClick={() => setShowAddEquipment(true)}>
                Add Component
              </Button>
            )}
          </div>

          {showAddEquipment && (
            <div className="mb-3">
              <AddEquipmentForm
                assetId={assetId}
                existingEquipment={equipment.data ?? []}
                onCreated={() => {
                  setShowAddEquipment(false);
                  equipment.refetch();
                }}
                onCancel={() => setShowAddEquipment(false)}
              />
            </div>
          )}

          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tag Number</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>CML</TableHead>
                    <TableHead>Nominal (mm)</TableHead>
                    <TableHead>Min. Required (mm)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(equipment.data ?? []).map((eq) => (
                    <TableRow key={eq.id}>
                      <TableCell>{eq.tag_number}</TableCell>
                      <TableCell>{eq.level}</TableCell>
                      <TableCell>{eq.name}</TableCell>
                      <TableCell>{eq.cml_number ?? "—"}</TableCell>
                      <TableCell>{eq.nominal_thickness_mm ?? "—"}</TableCell>
                      <TableCell>{eq.minimum_required_thickness_mm ?? "—"}</TableCell>
                    </TableRow>
                  ))}
                  {equipment.data?.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground">
                        No components registered
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="corrosion">
          <CorrosionPanel equipment={equipment.data ?? []} />
        </TabsContent>

        <TabsContent value="criticality">
          <CriticalityPanel assetId={assetId} />
        </TabsContent>

        <TabsContent value="risk">
          <Card>
            <CardContent className="pt-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Assessment</TableHead>
                    <TableHead>POF</TableHead>
                    <TableHead>Risk Score</TableHead>
                    <TableHead>Rank</TableHead>
                    <TableHead>Next Inspection</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(risks.data ?? []).map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.methodology}</TableCell>
                      <TableCell>{r.pof_score}</TableCell>
                      <TableCell>{r.risk_score}</TableCell>
                      <TableCell>
                        <Badge>{r.risk_rank}</Badge>
                      </TableCell>
                      <TableCell>{r.next_inspection_date ?? "—"}</TableCell>
                    </TableRow>
                  ))}
                  {risks.data?.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        No risk assessments yet
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents">
          <Card>
            <CardContent className="pt-4 text-sm text-muted-foreground">
              See the <a className="text-primary hover:underline" href="/documents">Document Library</a> filtered
              by this asset.
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
