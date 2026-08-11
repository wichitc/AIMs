"use client";

import { useState, type FormEvent } from "react";
import { useApiQuery } from "@/lib/use-api-query";
import { apiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { riskColor } from "@/lib/utils";
import type { Criticality } from "@/lib/types";

export function CriticalityPanel({ assetId }: { assetId: string }) {
  const history = useApiQuery<Criticality[]>(`/assets/${assetId}/criticality`);

  const [safetyScore, setSafetyScore] = useState("");
  const [environmentalScore, setEnvironmentalScore] = useState("");
  const [economicScore, setEconomicScore] = useState("");
  const [methodology, setMethodology] = useState("");
  const [assessedDate, setAssessedDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const current = (history.data ?? [])[0] ?? null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post(`/assets/${assetId}/criticality`, {
        safety_score: Number(safetyScore),
        environmental_score: Number(environmentalScore),
        economic_score: Number(economicScore),
        methodology: methodology || undefined,
        assessed_date: assessedDate,
      });
      setSafetyScore("");
      setEnvironmentalScore("");
      setEconomicScore("");
      setMethodology("");
      setAssessedDate("");
      history.refetch();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to record criticality assessment");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Current Criticality</CardTitle>
        </CardHeader>
        <CardContent>
          {current ? (
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <div className="text-muted-foreground">Level</div>
                <Badge className={riskColor(current.criticality_level)}>{current.criticality_level}</Badge>
              </div>
              <div>
                <div className="text-muted-foreground">Score</div>
                <div>{current.calculated_score}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Methodology</div>
                <div>{current.methodology ?? "—"}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Assessed</div>
                <div>{current.assessed_date}</div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No criticality assessment yet — API 580/581 recommends assessing every asset to prioritize
              inspection intervals.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>New Assessment</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="safetyScore">
                Safety (0-100)
              </label>
              <Input
                id="safetyScore"
                type="number"
                min={0}
                max={100}
                step="0.1"
                value={safetyScore}
                onChange={(e) => setSafetyScore(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="environmentalScore">
                Environmental (0-100)
              </label>
              <Input
                id="environmentalScore"
                type="number"
                min={0}
                max={100}
                step="0.1"
                value={environmentalScore}
                onChange={(e) => setEnvironmentalScore(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="economicScore">
                Economic (0-100)
              </label>
              <Input
                id="economicScore"
                type="number"
                min={0}
                max={100}
                step="0.1"
                value={economicScore}
                onChange={(e) => setEconomicScore(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="methodology">
                Methodology
              </label>
              <Input
                id="methodology"
                placeholder="e.g. API 581"
                value={methodology}
                onChange={(e) => setMethodology(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="assessedDate">
                Assessed Date
              </label>
              <Input
                id="assessedDate"
                type="date"
                value={assessedDate}
                onChange={(e) => setAssessedDate(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Record Assessment"}
            </Button>
          </form>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
          <p className="mt-2 text-xs text-muted-foreground">
            Score = Safety×0.5 + Environmental×0.3 + Economic×0.2 (safety weighted highest per API 580).
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Assessment History</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Safety</TableHead>
                <TableHead>Environmental</TableHead>
                <TableHead>Economic</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Level</TableHead>
                <TableHead>Methodology</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(history.data ?? []).map((c) => (
                <TableRow key={c.id}>
                  <TableCell>{c.assessed_date}</TableCell>
                  <TableCell>{c.safety_score}</TableCell>
                  <TableCell>{c.environmental_score}</TableCell>
                  <TableCell>{c.economic_score}</TableCell>
                  <TableCell>{c.calculated_score}</TableCell>
                  <TableCell>
                    <Badge className={riskColor(c.criticality_level)}>{c.criticality_level}</Badge>
                  </TableCell>
                  <TableCell>{c.methodology ?? "—"}</TableCell>
                </TableRow>
              ))}
              {history.data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No assessments recorded yet
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
