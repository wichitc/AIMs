"use client";

import { useApiQuery } from "@/lib/use-api-query";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AimsDocument } from "@/lib/types";

export default function DocumentsPage() {
  const documents = useApiQuery<AimsDocument[]>("/documents");

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Document Library</h1>
        <p className="text-sm text-muted-foreground">P&IDs, drawings, certificates, and inspection reports.</p>
      </div>

      <Card>
        <CardContent className="pt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Uploaded</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(documents.data ?? []).map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.file_name}</TableCell>
                  <TableCell>{doc.document_type}</TableCell>
                  <TableCell>v{doc.version}</TableCell>
                  <TableCell>{new Date(doc.uploaded_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
              {documents.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
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
