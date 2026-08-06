"use client";

import { useMemo } from "react";
import { cn, riskColor, type RiskRank } from "@/lib/utils";
import type { RiskAssessment } from "@/lib/types";

const POF_CATEGORIES = ["1", "2", "3", "4", "5"]; // low -> high probability of failure
const COF_CATEGORIES = ["E", "D", "C", "B", "A"]; // top row = highest consequence

const RANK_ORDER: RiskRank[] = ["Low", "Medium", "High", "VeryHigh"];

interface Cell {
  pof: string;
  cof: string;
  count: number;
  dominantRank: RiskRank | null;
}

export function RiskMatrix({
  assessments,
  onCellClick,
}: {
  assessments: RiskAssessment[];
  onCellClick?: (pof: string, cof: string) => void;
}) {
  const cells = useMemo(() => {
    const grid = new Map<string, Cell>();
    for (const pof of POF_CATEGORIES) {
      for (const cof of COF_CATEGORIES) {
        grid.set(`${pof}-${cof}`, { pof, cof, count: 0, dominantRank: null });
      }
    }
    for (const a of assessments) {
      if (!a.pof_category || !a.cof_category) continue;
      const key = `${a.pof_category}-${a.cof_category}`;
      const cell = grid.get(key);
      if (!cell) continue;
      cell.count += 1;
      if (!cell.dominantRank || RANK_ORDER.indexOf(a.risk_rank) > RANK_ORDER.indexOf(cell.dominantRank)) {
        cell.dominantRank = a.risk_rank;
      }
    }
    return grid;
  }, [assessments]);

  return (
    <div className="inline-grid grid-cols-[auto_repeat(5,minmax(48px,1fr))] gap-1 text-xs">
      <div />
      {POF_CATEGORIES.map((pof) => (
        <div key={pof} className="text-center font-medium text-muted-foreground">
          POF {pof}
        </div>
      ))}
      {COF_CATEGORIES.map((cof) => (
        <div key={cof} className="contents">
          <div className="flex items-center justify-end pr-2 font-medium text-muted-foreground">COF {cof}</div>
          {POF_CATEGORIES.map((pof) => {
            const cell = cells.get(`${pof}-${cof}`)!;
            return (
              <button
                key={pof}
                type="button"
                onClick={() => onCellClick?.(pof, cof)}
                className={cn(
                  "flex h-12 items-center justify-center rounded-md border font-semibold",
                  cell.dominantRank ? riskColor(cell.dominantRank) : "border-border bg-muted/30 text-muted-foreground",
                )}
              >
                {cell.count || ""}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
