"use client";

import { useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { statusColor } from "@/lib/utils";
import type { Material, PurchaseOrder, PurchaseRequisition, Quotation, RFQ, RFQInvite, Supplier } from "@/lib/types";

export default function RFQDetailPage({ params }: { params: { rfqId: string } }) {
  const { rfqId } = params;
  const router = useRouter();

  const rfq = useApiQuery<RFQ>(`/rfqs/${rfqId}`);
  const invites = useApiQuery<RFQInvite[]>(`/rfqs/${rfqId}/invites`);
  const quotations = useApiQuery<Quotation[]>("/quotations", { rfq_id: rfqId });
  const suppliers = useApiQuery<Supplier[]>("/suppliers");
  const materials = useApiQuery<Material[]>("/materials");
  const requisition = useApiQuery<PurchaseRequisition>(
    rfq.data ? `/purchase-requisitions/${rfq.data.purchase_requisition_id}` : null,
  );

  const supplierById = useMemo(() => {
    const map = new Map<string, Supplier>();
    (suppliers.data ?? []).forEach((s) => map.set(s.id, s));
    return map;
  }, [suppliers.data]);
  const materialById = useMemo(() => {
    const map = new Map<string, Material>();
    (materials.data ?? []).forEach((m) => map.set(m.id, m));
    return map;
  }, [materials.data]);

  const invitedSupplierIds = new Set((invites.data ?? []).map((i) => i.supplier_id));

  function refetchAll() {
    rfq.refetch();
    invites.refetch();
    quotations.refetch();
  }

  async function dispatch() {
    try {
      await apiClient.post(`/rfqs/${rfqId}/dispatch`);
      refetchAll();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to dispatch RFQ");
    }
  }

  async function award(quotationItemId: string) {
    try {
      await apiClient.post(`/quotation-items/${quotationItemId}/award`);
      quotations.refetch();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to award item");
    }
  }

  async function convertToPurchaseOrders() {
    try {
      const orders = await apiClient.post<PurchaseOrder[]>(`/rfqs/${rfqId}/convert-to-purchase-orders`);
      if (orders.length > 0) router.push("/purchase-orders");
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to convert to purchase orders");
    }
  }

  const hasAwardedItems = (quotations.data ?? []).some((q) => q.items.some((i) => i.is_awarded));

  if (rfq.isLoading) return <p className="text-muted-foreground">Loading RFQ…</p>;
  if (rfq.error || !rfq.data) return <p className="text-destructive">{rfq.error ?? "RFQ not found"}</p>;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">RFQ {rfqId.slice(0, 8)}</h1>
        <Badge className={statusColor(rfq.data.status)}>{rfq.data.status}</Badge>
      </div>
      <p className="text-sm text-muted-foreground">
        Sourcing {requisition.data?.items.length ?? "…"} item(s) from purchase requisition{" "}
        {rfq.data.purchase_requisition_id.slice(0, 8)}
      </p>

      {requisition.data && (
        <Card>
          <CardHeader>
            <CardTitle>Requested Items</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Material</TableHead>
                  <TableHead>Quantity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requisition.data.items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{materialById.get(item.material_id)?.material_number ?? item.material_id}</TableCell>
                    <TableCell>{item.quantity}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <InviteSuppliersPanel
        rfqId={rfqId}
        rfqStatus={rfq.data.status}
        invites={invites.data ?? []}
        suppliers={suppliers.data ?? []}
        supplierById={supplierById}
        onInvited={refetchAll}
        onDispatch={dispatch}
      />

      {rfq.data.status === "Dispatched" && requisition.data && (
        <RecordQuotationPanel
          rfqId={rfqId}
          invitedSupplierIds={invitedSupplierIds}
          suppliers={suppliers.data ?? []}
          requisitionItems={requisition.data.items}
          materialById={materialById}
          onRecorded={refetchAll}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-foreground">
            Quotation Comparison
            {hasAwardedItems && <Button size="sm" onClick={convertToPurchaseOrders}>Convert to Purchase Orders</Button>}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(quotations.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No quotations recorded yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Material</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead>Unit Price</TableHead>
                  <TableHead>Line Total</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(quotations.data ?? []).flatMap((q) =>
                  q.items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{supplierById.get(q.supplier_id)?.name ?? q.supplier_id}</TableCell>
                      <TableCell>{materialById.get(item.material_id)?.material_number ?? item.material_id}</TableCell>
                      <TableCell>{item.quantity}</TableCell>
                      <TableCell>{item.unit_price}</TableCell>
                      <TableCell>{(item.quantity * item.unit_price).toLocaleString()}</TableCell>
                      <TableCell>
                        {item.is_awarded ? (
                          <Badge className="bg-status-success-bg text-status-success-text border-transparent">
                            Awarded
                          </Badge>
                        ) : (
                          <Button size="sm" variant="outline" onClick={() => award(item.id)}>
                            Award
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  )),
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function InviteSuppliersPanel({
  rfqId,
  rfqStatus,
  invites,
  suppliers,
  supplierById,
  onInvited,
  onDispatch,
}: {
  rfqId: string;
  rfqStatus: string;
  invites: RFQInvite[];
  suppliers: Supplier[];
  supplierById: Map<string, Supplier>;
  onInvited: () => void;
  onDispatch: () => void;
}) {
  const [supplierId, setSupplierId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post(`/rfqs/${rfqId}/invite`, { supplier_id: supplierId });
      setSupplierId("");
      onInvited();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to invite supplier");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Invited Suppliers</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {rfqStatus === "Draft" && (
          <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
            <div className="min-w-[220px]">
              <label className="mb-1 block text-sm font-medium">Supplier</label>
              <Select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required>
                <option value="">Select supplier…</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.supplier_number} — {s.name}
                  </option>
                ))}
              </Select>
            </div>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Inviting..." : "Invite"}
            </Button>
            {invites.length > 0 && (
              <Button type="button" onClick={onDispatch}>
                Dispatch RFQ
              </Button>
            )}
            {error && <p className="w-full text-sm text-destructive">{error}</p>}
          </form>
        )}
        <ul className="flex flex-wrap gap-2">
          {invites.map((i) => (
            <Badge key={i.id}>{supplierById.get(i.supplier_id)?.name ?? i.supplier_id}</Badge>
          ))}
          {invites.length === 0 && <p className="text-sm text-muted-foreground">No suppliers invited yet</p>}
        </ul>
      </CardContent>
    </Card>
  );
}

function RecordQuotationPanel({
  rfqId,
  invitedSupplierIds,
  suppliers,
  requisitionItems,
  materialById,
  onRecorded,
}: {
  rfqId: string;
  invitedSupplierIds: Set<string>;
  suppliers: Supplier[];
  requisitionItems: PurchaseRequisition["items"];
  materialById: Map<string, Material>;
  onRecorded: () => void;
}) {
  const invitedSuppliers = suppliers.filter((s) => invitedSupplierIds.has(s.id));
  const [supplierId, setSupplierId] = useState("");
  const [submittedDate, setSubmittedDate] = useState("");
  const [prices, setPrices] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post("/quotations", {
        rfq_id: rfqId,
        supplier_id: supplierId,
        submitted_date: submittedDate,
        items: requisitionItems.map((item) => ({
          pr_item_id: item.id,
          material_id: item.material_id,
          quantity: item.quantity,
          unit_price: Number(prices[item.id] ?? 0),
        })),
      });
      setSupplierId("");
      setSubmittedDate("");
      setPrices({});
      onRecorded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to record quotation");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Record Quotation</CardTitle>
      </CardHeader>
      <CardContent>
        {invitedSuppliers.length === 0 ? (
          <p className="text-sm text-muted-foreground">Invite a supplier before recording a quotation.</p>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium">Supplier</label>
                <Select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required>
                  <option value="">Select supplier…</option>
                  {invitedSuppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.supplier_number} — {s.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Submitted Date</label>
                <Input
                  type="date"
                  value={submittedDate}
                  onChange={(e) => setSubmittedDate(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              {requisitionItems.map((item) => (
                <div key={item.id} className="flex items-center gap-3">
                  <span className="min-w-[160px] text-sm">
                    {materialById.get(item.material_id)?.material_number ?? item.material_id} × {item.quantity}
                  </span>
                  <Input
                    type="number"
                    min={0.01}
                    step="0.01"
                    placeholder="Unit price"
                    value={prices[item.id] ?? ""}
                    onChange={(e) => setPrices((prev) => ({ ...prev, [item.id]: e.target.value }))}
                    className="w-32"
                    required
                  />
                </div>
              ))}
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={isSubmitting} className="self-start">
              {isSubmitting ? "Recording..." : "Record Quotation"}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
