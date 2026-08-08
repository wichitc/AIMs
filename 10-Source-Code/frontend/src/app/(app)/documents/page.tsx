"use client";

import Link from "next/link";
import { useApiQuery } from "@/lib/use-api-query";
import { downloadFile, ApiError } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AimsDocument } from "@/lib/types";

function formatSize(bytes: number | null): string {
  if (bytes === null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const documents = useApiQuery<AimsDocument[]>("/documents");

  async function handleDownload(doc: AimsDocument) {
    try {
      await downloadFile(`/documents/${doc.id}/download`, doc.file_name);
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Download failed");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Document Library</h1>
          <p className="text-sm text-muted-foreground">P&IDs, drawings, certificates, and inspection reports.</p>
        </div>
        <Link href="/documents/new">
          <Button>Upload Document</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(documents.data ?? []).map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.file_name}</TableCell>
                  <TableCell>{doc.document_type}</TableCell>
                  <TableCell>v{doc.version}</TableCell>
                  <TableCell>{formatSize(doc.file_size_bytes)}</TableCell>
                  <TableCell>{new Date(doc.uploaded_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <Button size="sm" variant="outline" onClick={() => handleDownload(doc)}>
                      Download
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {documents.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    No documents uploaded yet
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
