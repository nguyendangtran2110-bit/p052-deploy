"use client";

import { useApp } from "@/src/components/providers";
import { PageHeader } from "@/src/components/primitives";
import { ProfileUI } from "@/src/components/profile-ui";

export default function ResidentProfilePage() {
  const { account } = useApp();
  return <div className="page"><PageHeader title="Profile and preferences" description="Verified identity stays separate from the details and preferences you can control." />{account ? <ProfileUI account={account} /> : null}</div>;
}
