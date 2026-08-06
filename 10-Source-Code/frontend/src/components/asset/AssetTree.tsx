"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { Location } from "@/lib/types";

interface AssetTreeProps {
  locations: Location[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

interface TreeNode extends Location {
  children: TreeNode[];
}

function buildTree(locations: Location[]): TreeNode[] {
  const nodeMap = new Map<string, TreeNode>(locations.map((l) => [l.id, { ...l, children: [] }]));
  const roots: TreeNode[] = [];

  nodeMap.forEach((node) => {
    if (node.parent_location_id && nodeMap.has(node.parent_location_id)) {
      nodeMap.get(node.parent_location_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  });

  return roots;
}

function TreeItem({
  node,
  depth,
  selectedId,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}) {
  return (
    <div>
      <button
        type="button"
        onClick={() => onSelect(node.id)}
        style={{ paddingLeft: `${depth * 14 + 8}px` }}
        className={cn(
          "flex w-full items-center gap-2 rounded-md py-1.5 pr-2 text-left text-sm hover:bg-muted",
          selectedId === node.id && "bg-primary/10 font-medium text-primary",
        )}
      >
        <span className="text-xs uppercase text-muted-foreground">{node.level}</span>
        {node.name}
      </button>
      {node.children.map((child) => (
        <TreeItem key={child.id} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </div>
  );
}

export function AssetTree({ locations, selectedId, onSelect }: AssetTreeProps) {
  const tree = useMemo(() => buildTree(locations), [locations]);

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={() => onSelect(null)}
        className={cn(
          "rounded-md px-2 py-1.5 text-left text-sm font-medium hover:bg-muted",
          selectedId === null && "bg-primary/10 text-primary",
        )}
      >
        All Locations
      </button>
      {tree.map((node) => (
        <TreeItem key={node.id} node={node} depth={0} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </div>
  );
}
