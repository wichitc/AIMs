"use client";

import { useEffect, useState } from "react";
import { apiClient, ApiError } from "@/lib/api-client";

interface QueryState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

export function useApiQuery<T>(
  path: string | null,
  query?: Record<string, string | number | boolean | undefined>,
): QueryState<T> & { refetch: () => void } {
  const [state, setState] = useState<QueryState<T>>({ data: null, isLoading: true, error: null });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    setState((s) => ({ ...s, isLoading: true, error: null }));

    apiClient
      .get<T>(path, query)
      .then((data) => {
        if (!cancelled) setState({ data, isLoading: false, error: null });
      })
      .catch((err) => {
        if (!cancelled) {
          setState({ data: null, isLoading: false, error: err instanceof ApiError ? err.message : "Request failed" });
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, JSON.stringify(query), version]);

  return { ...state, refetch: () => setVersion((v) => v + 1) };
}
