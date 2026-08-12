"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { apiRequest, isApiError, USE_MOCKS } from "@/lib/api-client";
import { bootstrapSession, clearSession, setAccount } from "@/lib/auth-session";
import { queryClient } from "@/lib/query-client";
import type { Account, TokenResponse } from "@/types";
import { WorkspaceLoading } from "@/components/ui";

export function Providers({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(USE_MOCKS);

  useEffect(() => {
    if (USE_MOCKS) return;
    let active = true;
    void (async () => {
      const account = await bootstrapSession((refreshToken) =>
        apiRequest<TokenResponse>("/auth/refresh", {
          method: "POST",
          body: JSON.stringify({ refresh_token: refreshToken }),
          skipRefresh: true,
        }),
      );
      if (account) {
        try {
          const current = await apiRequest<Account>("/auth/me");
          setAccount(current);
        } catch (error) {
          if (isApiError(error) && error.status !== 0) clearSession();
          else setAccount(account);
        }
      }
      if (active) setReady(true);
    })();
    return () => { active = false; };
  }, []);

  if (!ready) return <WorkspaceLoading />;
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
