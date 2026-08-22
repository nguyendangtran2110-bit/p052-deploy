import Link from "next/link";
import { ArrowRight, UserRound } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card, EmptyState, PageHeader } from "@/components/ui";

export default function ManagementProfilePage() {
  return <AppShell><PageHeader eyebrow="Management / Profile" title="Management profile" description="Account profile editing remains governed by the live management API and is not available on this branch." /><Card><EmptyState icon={<UserRound size={22} />} title="Profile editing is unavailable" description="Your current session and authorization remain unchanged. Use the existing account controls to sign out or return to work." action={<Link className="button button-outline" href="/management">Back to work home <ArrowRight size={15} /></Link>} /></Card></AppShell>;
}
