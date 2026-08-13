"use client";

import { useApp } from "@/src/components/providers";
import { PageHeader } from "@/src/components/primitives";
import { ProfileUI } from "@/src/components/profile-ui";

export default function ManagerProfilePage() {
  const { account } = useApp();
  return <div className="page"><PageHeader title="Manager profile" description="Your current assignment pairs are visible and read-only. Registry changes are applied outside OnBxrd." />{account ? <ProfileUI account={account} /> : null}</div>;
}
