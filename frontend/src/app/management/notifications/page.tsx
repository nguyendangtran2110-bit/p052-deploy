import Link from "next/link";
import { ArrowRight, Bell } from "lucide-react";
import { Card, EmptyState, PageHeader } from "@/components/ui";

export default function ManagementNotificationsPage() {
  return <><PageHeader eyebrow="Management / Notifications" title="Notifications" description="A scoped inbox and campaign composer will appear here when the live notification contract is enabled." /><Card><EmptyState icon={<Bell size={22} />} title="Notifications are unavailable" description="No live management notification data is connected on this branch, so nothing is fabricated or sent from this page." action={<Link className="button button-outline" href="/management/announcements">Open announcements <ArrowRight size={15} /></Link>} /></Card></>;
}
