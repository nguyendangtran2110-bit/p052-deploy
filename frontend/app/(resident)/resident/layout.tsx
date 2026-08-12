import { AppShell } from "@/src/components/app-shell";

export default function ResidentLayout({ children }: { children: React.ReactNode }) {
  return <AppShell role="resident">{children}</AppShell>;
}
