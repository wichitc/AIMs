"use client";

import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4">
      <div className="text-sm text-muted-foreground">Enterprise Asset Integrity Management System</div>
      <div className="flex items-center gap-3">
        {user && <span className="text-sm font-medium">{user.full_name}</span>}
        <Button variant="ghost" size="sm" onClick={logout}>
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </header>
  );
}
