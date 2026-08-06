"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { apiClient, setToken } from "@/lib/api-client";
import type { CurrentUser } from "@/lib/types";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: CurrentUser;
}

interface AuthContextValue {
  user: CurrentUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (code: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem("aims_user") : null;
    if (stored) setUser(JSON.parse(stored));
    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const result = await apiClient.post<LoginResponse>("/auth/login", { username, password });
      setToken(result.access_token);
      window.localStorage.setItem("aims_user", JSON.stringify(result.user));
      setUser(result.user);
      router.push("/dashboard");
    },
    [router],
  );

  const logout = useCallback(() => {
    setToken(null);
    window.localStorage.removeItem("aims_user");
    setUser(null);
    router.push("/login");
  }, [router]);

  const hasPermission = useCallback(
    (_code: string) => {
      // Permission codes live in the JWT, not the /login response body — this checks
      // presence of a session as a placeholder gate; server-side RBAC is the real enforcement.
      return user !== null;
    },
    [user],
  );

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
