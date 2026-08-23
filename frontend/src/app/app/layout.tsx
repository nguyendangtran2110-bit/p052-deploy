import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";

// Keep the resident workspace mounted while its child routes change.
export default function ResidentLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
