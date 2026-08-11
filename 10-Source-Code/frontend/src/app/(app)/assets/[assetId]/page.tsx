"use client";

import { useState } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { AddEquipmentForm } from "@/components/asset/AddEquipmentForm";
import { CorrosionPanel } from "@/components/asset/CorrosionPanel";
import { CriticalityPanel } from "@/components/asset/CriticalityPanel";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Asset, Equipment, RiskAssessment } from "@/lib/types";

export default function AssetDetailPage({ params }: { params: { assetId: string } }) {
  const { assetId } = params;
  const asset = useApiQuery<Asset>(`/assets/${assetId}`);
  const equipment = useApiQuery<Equipment[]>(`/assets/${assetId}/equipment`);
  const risks = useApiQuery<RiskAssessment[]>("/risk-assessments", { asset_id: assetId });
  const [showAddEquipment, setShowAddEquipment] = useState(false);

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
            <CardContent className="grid grid-cols-2 gap-4 pt-4 text-sm md:grid-cols-3">
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
