"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/assets", label: "Asset Register", icon: Boxes },
  { href: "/inspections", label: "Inspections", icon: ClipboardCheck },
  { href: "/risk", label: "Risk (RBI)", icon: ShieldAlert },
  { href: "/defects", label: "Defects", icon: Wrench },
  { href: "/maintenance", label: "Maintenance", icon: Hammer },
  { href: "/materials", label: "Materials", icon: PackageSearch },
  { href: "/suppliers", label: "Suppliers", icon: Truck },
  { href: "/sourcing", label: "Sourcing", icon: Route },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/copilot", label: "AI Copilot", icon: Sparkles },
  { href: "/audit-log", label: "Audit Log", icon: History },
  { href: "/admin", label: "Admin", icon: Users },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card md:flex">
        <div className="flex h-16 items-center gap-2 border-b border-border px-6 font-semibold text-foreground">
          <ShieldCheck className="h-6 w-6 text-accent" aria-hidden />
          AIMS
        </div>
        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
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
          })}
        </nav>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-border bg-card md:hidden">
        {NAV_ITEMS.slice(0, 5).map((item) => {
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
