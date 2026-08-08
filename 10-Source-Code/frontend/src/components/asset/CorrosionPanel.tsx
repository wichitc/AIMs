"use client";

import { useState, type FormEvent } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { CorrosionRecord, Equipment, ThicknessRecord } from "@/lib/types";

export function CorrosionPanel({ equipment }: { equipment: Equipment[] }) {
  // Thickness readings are only meaningful at the CML / Inspection Point level, not the
  // Component level above it — matches Database.md §7.1 (thickness_record.equipment_id
  // references equipment where level='InspectionPoint').
  const inspectionPoints = equipment.filter((e) => e.level === "InspectionPoint");

  const [selectedId, setSelectedId] = useState("");
  const thickness = useApiQuery<ThicknessRecord[]>(
    selectedId ? `/equipment/${selectedId}/thickness-records` : null,
  );
  const corrosion = useApiQuery<CorrosionRecord[]>(
    selectedId ? `/equipment/${selectedId}/corrosion-records` : null,
  );

  const [readingDate, setReadingDate] = useState("");
  const [thicknessMm, setThicknessMm] = useState("");
  const [method, setMethod] = useState<"UT" | "RT">("UT");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);

  async function handleAddReading(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post(`/equipment/${selectedId}/thickness-records`, {
        reading_date: readingDate,
        measured_thickness_mm: Number(thicknessMm),
        measurement_method: method,
      });
      setReadingDate("");
      setThicknessMm("");
      thickness.refetch();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add reading");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCalculate() {
    setCalcError(null);
    setIsCalculating(true);
    try {
      await apiClient.post(`/equipment/${selectedId}/corrosion-records/calculate`);
      corrosion.refetch();
    } catch (err) {
      setCalcError(err instanceof ApiError ? err.message : "Failed to calculate corrosion rate");
    } finally {
      setIsCalculating(false);
    }
  }

  if (inspectionPoints.length === 0) {
    return (
      <Card>
        <CardContent className="pt-4 text-sm text-muted-foreground">
          No Inspection Points (CMLs) registered on this asset yet — add one from the Equipment tab
          (level = Inspection Point) before recording thickness readings.
        </CardContent>
      </Card>
    );
  }

  const latestCorrosion = (corrosion.data ?? [])[0] ?? null;

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="pt-4">
          <label className="mb-1 block text-sm font-medium" htmlFor="cml">
            Inspection Point (CML)
          </label>
          <Select id="cml" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            <option value="">Select CML…</option>
            {inspectionPoints.map((eq) => (
              <option key={eq.id} value={eq.id}>
                {eq.tag_number} — {eq.name} {eq.cml_number ? `(${eq.cml_number})` : ""}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {selectedId && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Add Thickness Reading</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddReading} className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium" htmlFor="readingDate">
                    Reading Date
                  </label>
                  <Input
                    id="readingDate"
                    type="date"
                    value={readingDate}
                    onChange={(e) => setReadingDate(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium" htmlFor="thicknessMm">
                    Thickness (mm)
                  </label>
                  <Input
                    id="thicknessMm"
                    type="number"
                    step="0.001"
                    value={thicknessMm}
                    onChange={(e) => setThicknessMm(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium" htmlFor="method">
                    Method
                  </label>
                  <Select id="method" value={method} onChange={(e) => setMethod(e.target.value as "UT" | "RT")}>
                    <option value="UT">UT</option>
                    <option value="RT">RT</option>
                  </Select>
                </div>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Saving..." : "Add Reading"}
                </Button>
              </form>
              {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Thickness History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Thickness (mm)</TableHead>
                    <TableHead>Method</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(thickness.data ?? []).map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.reading_date}</TableCell>
                      <TableCell>{r.measured_thickness_mm}</TableCell>
                      <TableCell>{r.measurement_method}</TableCell>
                    </TableRow>
                  ))}
                  {thickness.data?.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground">
                        No readings yet
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-foreground">
                Corrosion Rate & Remaining Life
                <Button
                  size="sm"
                  onClick={handleCalculate}
                  disabled={isCalculating || (thickness.data ?? []).length < 2}
                >
                  {isCalculating ? "Calculating..." : "Calculate"}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {(thickness.data ?? []).length < 2 && (
                <p className="mb-2 text-xs text-muted-foreground">
                  At least 2 thickness readings are required to calculate a rate.
                </p>
              )}
              {calcError && <p className="mb-2 text-sm text-destructive">{calcError}</p>}
              {latestCorrosion ? (
                <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
                  <div>
                    <div className="text-muted-foreground">Governing Rate</div>
                    <div>{latestCorrosion.governing_rate_mm_yr} mm/yr</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Remaining Life</div>
                    <div>{latestCorrosion.remaining_life_years} years</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Next Inspection</div>
                    <div>{latestCorrosion.next_inspection_date}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Short-Term Rate</div>
                    <div>{latestCorrosion.short_term_rate_mm_yr ?? "—"} mm/yr</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Long-Term Rate</div>
                    <div>{latestCorrosion.long_term_rate_mm_yr ?? "—"} mm/yr</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Basis</div>
                    <div>{latestCorrosion.calculation_basis ?? "—"}</div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No calculation yet.</p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
