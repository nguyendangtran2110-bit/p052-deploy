import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";

// Keep the management workspace mounted while its child routes change.
export default function ManagementLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
