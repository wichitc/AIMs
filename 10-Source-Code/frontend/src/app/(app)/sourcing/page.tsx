"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type {
  Material,
  PurchasingInfoRecord,
  QuotaArrangement,
  SourceCandidate,
  SourceListEntry,
  Supplier,
} from "@/lib/types";

export default function SourcingPage() {
  const materials = useApiQuery<Material[]>("/materials");
  const suppliers = useApiQuery<Supplier[]>("/suppliers");
  const [materialId, setMaterialId] = useState("");

  const infoRecords = useApiQuery<PurchasingInfoRecord[]>(
    materialId ? "/purchasing-info-records" : null,
    materialId ? { material_id: materialId } : undefined,
  );
  const sourceList = useApiQuery<SourceListEntry[]>(
    materialId ? "/source-list-entries" : null,
    materialId ? { material_id: materialId } : undefined,
  );
  const quotas = useApiQuery<QuotaArrangement[]>(
    materialId ? "/quota-arrangements" : null,
    materialId ? { material_id: materialId } : undefined,
  );

  const supplierById = useMemo(() => {
    const map = new Map<string, Supplier>();
    (suppliers.data ?? []).forEach((s) => map.set(s.id, s));
    return map;
  }, [suppliers.data]);

  const [candidates, setCandidates] = useState<SourceCandidate[] | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

  async function runSimulation() {
    setSimError(null);
    setIsSimulating(true);
    try {
      const result = await apiClient.get<SourceCandidate[]>("/source-determination", { material_id: materialId });
      setCandidates(result);
    } catch (err) {
      setSimError(err instanceof ApiError ? err.message : "Failed to run source determination");
    } finally {
      setIsSimulating(false);
    }
  }

  function refetchAll() {
    infoRecords.refetch();
    sourceList.refetch();
    quotas.refetch();
    setCandidates(null);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Sourcing</h1>
        <p className="text-sm text-muted-foreground">
          Purchasing info records, source list, and quota arrangements — the deterministic
          eligible-source engine explains exactly why each candidate was chosen.
        </p>
      </div>

      <Card>
        <CardContent className="pt-4">
          <label className="mb-1 block text-sm font-medium" htmlFor="material">
            Material
          </label>
          <Select
            id="material"
            value={materialId}
            onChange={(e) => {
              setMaterialId(e.target.value);
              setCandidates(null);
            }}
          >
            <option value="">Select material…</option>
            {(materials.data ?? []).map((m) => (
              <option key={m.id} value={m.id}>
                {m.material_number} — {m.name}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      {materialId && (
        <>
          <InfoRecordPanel
            materialId={materialId}
            records={infoRecords.data ?? []}
            suppliers={suppliers.data ?? []}
            supplierById={supplierById}
            onCreated={refetchAll}
          />
          <SourceListPanel
            materialId={materialId}
            entries={sourceList.data ?? []}
            suppliers={suppliers.data ?? []}
            supplierById={supplierById}
            onCreated={refetchAll}
          />
          <QuotaPanel
            materialId={materialId}
            quotas={quotas.data ?? []}
            suppliers={suppliers.data ?? []}
            supplierById={supplierById}
            onCreated={refetchAll}
          />

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-foreground">
                Source Determination
                <Button size="sm" onClick={runSimulation} disabled={isSimulating}>
                  {isSimulating ? "Running..." : "Run Simulation"}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {simError && <p className="mb-2 text-sm text-destructive">{simError}</p>}
              {candidates === null ? (
                <p className="text-sm text-muted-foreground">Run the simulation to see ranked, explainable candidates.</p>
              ) : candidates.length === 0 ? (
                <p className="text-sm text-muted-foreground">No eligible source found for this material.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rank</TableHead>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Price</TableHead>
                      <TableHead>Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {candidates.map((c) => (
                      <TableRow key={c.supplier_id}>
                        <TableCell>
                          <Badge>{c.rank}</Badge>
                        </TableCell>
                        <TableCell>{supplierById.get(c.supplier_id)?.name ?? c.supplier_id}</TableCell>
                        <TableCell>{c.price ?? "—"}</TableCell>
                        <TableCell className="text-muted-foreground">{c.reason}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function SupplierSelect({
  suppliers,
  value,
  onChange,
}: {
  suppliers: Supplier[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <Select value={value} onChange={(e) => onChange(e.target.value)} required>
      <option value="">Select supplier…</option>
      {suppliers.map((s) => (
        <option key={s.id} value={s.id}>
          {s.supplier_number} — {s.name}
        </option>
      ))}
    </Select>
  );
}

function InfoRecordPanel({
  materialId,
  records,
  suppliers,
  supplierById,
  onCreated,
}: {
  materialId: string;
  records: PurchasingInfoRecord[];
  suppliers: Supplier[];
  supplierById: Map<string, Supplier>;
  onCreated: () => void;
}) {
  const [supplierId, setSupplierId] = useState("");
  const [price, setPrice] = useState("");
  const [leadTimeDays, setLeadTimeDays] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/purchasing-info-records", {
        material_id: materialId,
        supplier_id: supplierId,
        price: Number(price),
        lead_time_days: leadTimeDays === "" ? undefined : Number(leadTimeDays),
      });
      setSupplierId("");
      setPrice("");
      setLeadTimeDays("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add info record");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Purchasing Info Records</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Supplier</label>
            <SupplierSelect suppliers={suppliers} value={supplierId} onChange={setSupplierId} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="infoPrice">
              Price
            </label>
            <Input id="infoPrice" type="number" min={0.01} step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="leadTime">
              Lead Time (days)
            </label>
            <Input
              id="leadTime"
              type="number"
              min={0}
              value={leadTimeDays}
              onChange={(e) => setLeadTimeDays(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Adding..." : "Add"}
          </Button>
          {error && <p className="w-full text-sm text-destructive">{error}</p>}
        </form>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Supplier</TableHead>
              <TableHead>Price</TableHead>
              <TableHead>Lead Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {records.map((r) => (
              <TableRow key={r.id}>
                <TableCell>{supplierById.get(r.supplier_id)?.name ?? r.supplier_id}</TableCell>
                <TableCell>{r.price}</TableCell>
                <TableCell>{r.lead_time_days != null ? `${r.lead_time_days} days` : "—"}</TableCell>
              </TableRow>
            ))}
            {records.length === 0 && (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  No info records yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function SourceListPanel({
  materialId,
  entries,
  suppliers,
  supplierById,
  onCreated,
}: {
  materialId: string;
  entries: SourceListEntry[];
  suppliers: Supplier[];
  supplierById: Map<string, Supplier>;
  onCreated: () => void;
}) {
  const [supplierId, setSupplierId] = useState("");
  const [isFixed, setIsFixed] = useState(false);
  const [isBlocked, setIsBlocked] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/source-list-entries", {
        material_id: materialId,
        supplier_id: supplierId,
        is_fixed: isFixed,
        is_blocked: isBlocked,
      });
      setSupplierId("");
      setIsFixed(false);
      setIsBlocked(false);
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add source list entry");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Source List</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Supplier</label>
            <SupplierSelect suppliers={suppliers} value={supplierId} onChange={setSupplierId} />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isFixed} onChange={(e) => setIsFixed(e.target.checked)} />
            Fixed source
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isBlocked} onChange={(e) => setIsBlocked(e.target.checked)} />
            Blocked
          </label>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Adding..." : "Add"}
          </Button>
          {error && <p className="w-full text-sm text-destructive">{error}</p>}
        </form>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Supplier</TableHead>
              <TableHead>Fixed</TableHead>
              <TableHead>Blocked</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((e) => (
              <TableRow key={e.id}>
                <TableCell>{supplierById.get(e.supplier_id)?.name ?? e.supplier_id}</TableCell>
                <TableCell>{e.is_fixed ? "Yes" : "No"}</TableCell>
                <TableCell>{e.is_blocked ? "Yes" : "No"}</TableCell>
              </TableRow>
            ))}
            {entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  No source list entries yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function QuotaPanel({
  materialId,
  quotas,
  suppliers,
  supplierById,
  onCreated,
}: {
  materialId: string;
  quotas: QuotaArrangement[];
  suppliers: Supplier[];
  supplierById: Map<string, Supplier>;
  onCreated: () => void;
}) {
  const [supplierId, setSupplierId] = useState("");
  const [quotaPercentage, setQuotaPercentage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/quota-arrangements", {
        material_id: materialId,
        supplier_id: supplierId,
        quota_percentage: Number(quotaPercentage),
      });
      setSupplierId("");
      setQuotaPercentage("");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add quota arrangement");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quota Arrangements</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Supplier</label>
            <SupplierSelect suppliers={suppliers} value={supplierId} onChange={setSupplierId} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="quotaPct">
              Quota %
            </label>
            <Input
              id="quotaPct"
              type="number"
              min={1}
              max={100}
              step="1"
              value={quotaPercentage}
              onChange={(e) => setQuotaPercentage(e.target.value)}
              required
            />
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Adding..." : "Add"}
          </Button>
          {error && <p className="w-full text-sm text-destructive">{error}</p>}
        </form>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Supplier</TableHead>
              <TableHead>Quota</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {quotas.map((q) => (
              <TableRow key={q.id}>
                <TableCell>{supplierById.get(q.supplier_id)?.name ?? q.supplier_id}</TableCell>
                <TableCell>{q.quota_percentage}%</TableCell>
              </TableRow>
            ))}
            {quotas.length === 0 && (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
                  No quota arrangements yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
