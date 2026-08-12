"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { BellIcon, ChatIcon, GiftIcon, HomeIcon, MoonIcon, StepsIcon, SunIcon, TicketIcon, UserIcon, UsersIcon } from "@/src/components/icons";
import { useApp } from "@/src/components/providers";
import { logout } from "@/src/lib/session";
import type { Role } from "@/src/mock/data";

const residentNavigation = [
  { href: "/resident/onboarding", label: "Onboarding", icon: StepsIcon },
  { href: "/resident/benefits", label: "Benefits", icon: GiftIcon },
  { href: "/resident/assistant", label: "Assistant", icon: ChatIcon },
  { href: "/resident/tickets", label: "Tickets", icon: TicketIcon },
  { href: "/resident/notifications", label: "Notifications", icon: BellIcon },
  { href: "/resident/profile", label: "Profile", icon: UserIcon },
];

const managerNavigation = [
  { href: "/manager/dashboard", label: "Work home", icon: HomeIcon },
  { href: "/manager/residents", label: "Residents", icon: UsersIcon },
  { href: "/manager/onboarding", label: "Onboarding", icon: StepsIcon },
  { href: "/manager/tickets", label: "Tickets", icon: TicketIcon },
  { href: "/manager/notifications", label: "Notifications", icon: BellIcon },
  { href: "/manager/profile", label: "Profile", icon: UserIcon },
];

export function AppShell({ role, children }: { role: Role; children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { account, theme, setTheme } = useApp();
  const navigation = role === "resident" ? residentNavigation : managerNavigation;

  useEffect(() => {
    if (!account) router.replace(`/login?returnTo=${encodeURIComponent(pathname)}`);
    else if (account.role !== role) router.replace(account.role === "resident" ? "/resident/onboarding" : "/manager/dashboard");
  }, [account, pathname, role, router]);

  if (!account || account.role !== role) {
    return <main className="route-pending" aria-live="polite"><span className="static-spinner" />Confirming your session…</main>;
  }

  return (
    <div className={`app-shell app-shell-${role}`}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className="sidebar">
        <Link className="brand" href={role === "resident" ? "/resident/onboarding" : "/manager/dashboard"}>
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>OnBxrd</span>
        </Link>
        <div className="scope-card">
          <span>{role === "resident" ? "Resident space" : "Manager space"}</span>
          <strong>{account.building}</strong>
          <small>{account.floors.includes("ALL_FLOORS") ? "All assigned floors" : `Floor ${account.floors.join(", ")}`}</small>
        </div>
        <nav aria-label={`${role} navigation`}>
          {navigation.map(({ href, label, icon: Icon }) => {
            const current = pathname === href || (href.endsWith("/tickets") && pathname.startsWith(`${href}/`));
            return <Link key={href} href={href} aria-current={current ? "page" : undefined} className={current ? "nav-link current" : "nav-link"}><Icon />{label}</Link>;
          })}
        </nav>
        <div className="sidebar-footer">
          <button className="theme-toggle" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}>
            {theme === "light" ? <MoonIcon /> : <SunIcon />}
            <span>{theme === "light" ? "Dark theme" : "Light theme"}</span>
          </button>
          <div className="account-plate">
            <span className="avatar">{account.name.slice(0, 1)}</span>
            <span><strong>{account.name}</strong><small>Synthetic demo</small></span>
          </div>
          <button className="logout-button" onClick={() => { logout(); router.replace("/login"); }}>Sign out</button>
        </div>
      </aside>
      <div className="compact-account-actions" aria-label="Account controls">
        <button className="theme-toggle" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}>
          {theme === "light" ? <MoonIcon /> : <SunIcon />}
        </button>
        <button className="logout-button" onClick={() => { logout(); router.replace("/login"); }}>Sign out</button>
      </div>
      <main id="main-content" className="app-main" tabIndex={-1}>{children}</main>
    </div>
  );
}
