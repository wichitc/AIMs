"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Boxes,
  ClipboardCheck,
  ShieldAlert,
  ShieldCheck,
  Wrench,
  Hammer,
  FileText,
  Sparkles,
  Users,
  History,
  PackageSearch,
  Truck,
  Route,
  FileSpreadsheet,
  Send,
  ShoppingCart,
  Warehouse,
  BookmarkCheck,
  ArrowLeftRight,
  ChevronDown,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavLeaf {
  href: string;
  label: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  icon: LucideIcon;
  items: NavLeaf[];
}

type NavEntry = NavLeaf | NavGroup;

function isGroup(entry: NavEntry): entry is NavGroup {
  return "items" in entry;
}

const NAV_ITEMS: NavEntry[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  {
    label: "Asset Integrity",
    icon: Boxes,
    items: [
      { href: "/assets", label: "Asset Register", icon: Boxes },
      { href: "/inspections", label: "Inspections", icon: ClipboardCheck },
      { href: "/risk", label: "Risk (RBI)", icon: ShieldAlert },
      { href: "/defects", label: "Defects", icon: Wrench },
      { href: "/maintenance", label: "Maintenance", icon: Hammer },
    ],
  },
  {
    label: "Purchasing",
    icon: ShoppingCart,
    items: [
      { href: "/materials", label: "Materials", icon: PackageSearch },
      { href: "/suppliers", label: "Suppliers", icon: Truck },
      { href: "/sourcing", label: "Sourcing", icon: Route },
      { href: "/purchase-requisitions", label: "Purchase Requisitions", icon: FileSpreadsheet },
      { href: "/rfqs", label: "RFQs", icon: Send },
      { href: "/purchase-orders", label: "Purchase Orders", icon: ShoppingCart },
    ],
  },
  {
    label: "Inventory",
    icon: Warehouse,
    items: [
      { href: "/stock", label: "Stock", icon: Warehouse },
      { href: "/reservations", label: "Reservations", icon: BookmarkCheck },
      { href: "/stock-transfers", label: "Stock Transfers", icon: ArrowLeftRight },
    ],
  },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/copilot", label: "AI Copilot", icon: Sparkles },
  { href: "/audit-log", label: "Audit Log", icon: History },
  { href: "/admin", label: "Admin", icon: Users },
];

// Flat subset for the mobile bottom nav — a collapsible tree doesn't fit that layout.
const MOBILE_NAV_ITEMS: NavLeaf[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/assets", label: "Asset Register", icon: Boxes },
  { href: "/inspections", label: "Inspections", icon: ClipboardCheck },
  { href: "/risk", label: "Risk (RBI)", icon: ShieldAlert },
  { href: "/defects", label: "Defects", icon: Wrench },
];

const COLLAPSE_STORAGE_KEY = "aims_sidebar_collapsed_groups";

function NavLink({ item, active }: { item: NavLeaf; active: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Icon className="h-4 w-4" aria-hidden />
      {item.label}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  // Loaded after mount (not in the initial state) so the client's hydration render matches
  // the server's — both start with everything expanded, then this syncs in the saved state.
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(COLLAPSE_STORAGE_KEY);
      if (raw) setCollapsedGroups(JSON.parse(raw));
    } catch {
      // ignore malformed storage
    }
  }, []);

  function toggleGroup(label: string) {
    setCollapsedGroups((prev) => {
      const next = { ...prev, [label]: !prev[label] };
      window.localStorage.setItem(COLLAPSE_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card md:flex">
        <div className="flex h-16 items-center gap-2 border-b border-border px-6 font-semibold text-foreground">
          <ShieldCheck className="h-6 w-6 text-accent" aria-hidden />
          AIMS
        </div>
        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((entry) => {
            if (!isGroup(entry)) {
              return <NavLink key={entry.href} item={entry} active={pathname.startsWith(entry.href)} />;
            }

            const groupHasActiveItem = entry.items.some((item) => pathname.startsWith(item.href));
            // The group holding the current page always stays open, even if the user
            // previously collapsed it — otherwise the active link would vanish on navigation.
            const isCollapsed = !groupHasActiveItem && (collapsedGroups[entry.label] ?? false);
            const GroupIcon = entry.icon;

            return (
              <div key={entry.label}>
                <button
                  type="button"
                  onClick={() => toggleGroup(entry.label)}
                  aria-expanded={!isCollapsed}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )}
                >
                  <GroupIcon className="h-4 w-4" aria-hidden />
                  <span className="flex-1 text-left">{entry.label}</span>
                  {isCollapsed ? (
                    <ChevronRight className="h-4 w-4" aria-hidden />
                  ) : (
                    <ChevronDown className="h-4 w-4" aria-hidden />
                  )}
                </button>
                {!isCollapsed && (
                  <div className="ml-4 flex flex-col gap-1 border-l border-border pl-3 pt-1">
                    {entry.items.map((item) => (
                      <NavLink key={item.href} item={item} active={pathname.startsWith(item.href)} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-border bg-card md:hidden">
        {MOBILE_NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium",
                active ? "text-primary" : "text-muted-foreground",
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
