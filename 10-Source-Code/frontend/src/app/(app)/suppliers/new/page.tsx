"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Supplier } from "@/lib/types";

export default function NewSupplierPage() {
  const router = useRouter();

  const [supplierNumber, setSupplierNumber] = useState("");
  const [name, setName] = useState("");
  const [taxId, setTaxId] = useState("");
  const [country, setCountry] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [paymentTerms, setPaymentTerms] = useState("");
  const [currency, setCurrency] = useState("USD");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post<Supplier>("/suppliers", {
        supplier_number: supplierNumber,
        name,
        tax_id: taxId || undefined,
        country: country || undefined,
        email: email || undefined,
        phone: phone || undefined,
        address: address || undefined,
        payment_terms: paymentTerms || undefined,
        currency,
      });
      router.push("/suppliers");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create supplier");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">New Supplier</h1>
        <p className="text-sm text-muted-foreground">Register a vendor as a purchase-order source.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Supplier Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="supplierNumber">
                  Supplier Number
                </label>
                <Input
                  id="supplierNumber"
                  placeholder="e.g. SUP-001"
                  value={supplierNumber}
                  onChange={(e) => setSupplierNumber(e.target.value)}
                  maxLength={50}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="currency">
                  Currency
                </label>
                <Input
                  id="currency"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                  maxLength={3}
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
                placeholder="e.g. Rayong Valve & Fitting Co., Ltd."
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={200}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="taxId">
                  Tax ID
                </label>
                <Input id="taxId" value={taxId} onChange={(e) => setTaxId(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="country">
                  Country
                </label>
                <Input id="country" value={country} onChange={(e) => setCountry(e.target.value)} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="email">
                  Email
                </label>
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium" htmlFor="phone">
                  Phone
                </label>
                <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="address">
                Address
              </label>
              <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="paymentTerms">
                Payment Terms
              </label>
              <Input
                id="paymentTerms"
                placeholder="e.g. Net 30"
                value={paymentTerms}
                onChange={(e) => setPaymentTerms(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Supplier"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/suppliers")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
