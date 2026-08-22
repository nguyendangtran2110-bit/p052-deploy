import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card, EmptyState, PageHeader } from "@/components/ui";

export default function ResidentBenefitsPage() {
  return <AppShell><PageHeader eyebrow="Resident space / Benefits" title="Benefits for your home" description="Building-specific benefits will be shown here when they are available from your account scope." /><Card><EmptyState icon={<Sparkles size={22} />} title="No benefits published" description="OnBxrd has not received approved benefits for this building yet. This page does not invent availability or eligibility." action={<Link className="button button-outline" href="/app/profile">Review your profile <ArrowRight size={15} /></Link>} /></Card></AppShell>;
}
