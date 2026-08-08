"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import type { AimsDocument, Asset } from "@/lib/types";

// Matches Database.md §11.1's document_type intent (PID/Drawing/Certificate/Report/
// InspectionRecord/Photo/Other) — not DB-enforced at the moment, so the frontend is the
// only thing keeping this consistent; see Database.md vs document/models.py.
const DOCUMENT_TYPES = ["PID", "Drawing", "Certificate", "Report", "InspectionRecord", "Photo", "Other"];

// Mirrors backend/app/modules/document/router.py _ALLOWED_EXTENSIONS / _MAX_UPLOAD_BYTES —
// checked client-side too so the user gets immediate feedback instead of waiting on a
// round trip only to have the server reject it.
const ALLOWED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".dwg"];
const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

export default function NewDocumentPage() {
  const router = useRouter();
  const assets = useApiQuery<Asset[]>("/assets", { page_size: 100 });

  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0]);
  const [assetId, setAssetId] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(selected: File | null) {
    setError(null);
    if (!selected) {
      setFile(null);
      return;
    }
    const extension = "." + (selected.name.split(".").pop() ?? "").toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError(`File type '${extension}' is not allowed. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      setFile(null);
      return;
    }
    if (selected.size > MAX_UPLOAD_BYTES) {
      setError(`File exceeds the ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB upload limit`);
      setFile(null);
      return;
    }
    setFile(selected);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", documentType);
      if (assetId) formData.append("asset_id", assetId);

      await apiClient.postFormData<AimsDocument>("/documents/upload", formData);
      router.push("/documents");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload document");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Upload Document</h1>
        <p className="text-sm text-muted-foreground">
          P&IDs, drawings, certificates, and inspection reports (BRD §8). Stored on the
          backend's local volume — max 25 MB, PDF/image/Office/DWG only.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>File Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="file">
                File
              </label>
              <input
                id="file"
                type="file"
                accept={ALLOWED_EXTENSIONS.join(",")}
                onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
                className="flex w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm shadow-sm file:mr-3 file:rounded file:border-0 file:bg-muted file:px-2 file:py-1 file:text-sm"
                required
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="documentType">
                Document Type
              </label>
              <Select id="documentType" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                {DOCUMENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="asset">
                Related Asset (optional)
              </label>
              <Select id="asset" value={assetId} onChange={(e) => setAssetId(e.target.value)}>
                <option value="">None</option>
                {(assets.data ?? []).map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.tag_number} — {a.name}
                  </option>
                ))}
              </Select>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="mt-2 flex gap-2">
              <Button type="submit" disabled={isSubmitting || !file}>
                {isSubmitting ? "Uploading..." : "Upload"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.push("/documents")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
