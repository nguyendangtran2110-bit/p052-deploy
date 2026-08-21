"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, BookOpen, Bot, Building2, ChevronDown, FileText, Home, LayoutDashboard, LifeBuoy, LogOut, Menu, MessageCircle, Megaphone, Settings, Shield, UserCog, Users, X } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Button, IconButton, WorkspaceLoading, cn } from "@/components/ui";
import { ConnectionPill, ToastViewport } from "@/components/feedback";
import { USE_MOCKS } from "@/lib/api-client";
import { clearSession, getAccount, getAccessToken, getRefreshToken, subscribeToAuthChanges } from "@/lib/auth-session";
import { logoutSession } from "@/lib/data";
import { disconnectRealtime, connectRealtime, type RealtimeEvent, type RealtimeState } from "@/lib/realtime";
import { queryClient } from "@/lib/query-client";
import { initials } from "@/lib/format";
import { aiChatKeys } from "@/features/ai-chat/queries";
import { useUiStore } from "@/stores/ui-store";
import type { Account } from "@/types";

const residentNav = [
  { href: "/app", label: "Tổng quan", icon: Home },
  { href: "/app/chat", label: "Hỏi chatbot", icon: MessageCircle },
  { href: "/app/tickets", label: "Tickets", icon: FileText },
  { href: "/app/announcements", label: "Thông báo", icon: Bell },
  { href: "/app/profile", label: "Tài khoản", icon: Settings },
];

const managementNav = [
  { href: "/management", label: "Dashboard", icon: LayoutDashboard },
  { href: "/management/tickets", label: "Ticket queue", icon: FileText },
  { href: "/management/conversations", label: "Handoff", icon: MessageCircle },
  { href: "/management/assistant", label: "AI announcement assistant", icon: Bot },
  { href: "/management/residents", label: "Residents", icon: Users },
  { href: "/management/announcements", label: "Announcements", icon: Megaphone },
  { href: "/management/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/management/units", label: "Units", icon: Building2 },
];

function eventId(event: RealtimeEvent, ...keys: string[]) {
  for (const key of keys) {
    const value = event.data[key];
    if (typeof value === "string" && value) return value;
  }
  return undefined;
}

function invalidateForRealtimeEvent(event: RealtimeEvent) {
  const conversationId = eventId(event, "conversation_id");
  const ticketId = eventId(event, "ticket_id");
  const announcementId = eventId(event, "announcement_id");
  const workflowId = eventId(event, "workflow_id");

  if (event.event.startsWith("conversation.")) {
    if (conversationId) {
      queryClient.invalidateQueries({ queryKey: ["conversation", conversationId], exact: true });
      queryClient.invalidateQueries({ queryKey: ["ticket", conversationId, "conversation"], exact: true });
      queryClient.invalidateQueries({ queryKey: aiChatKeys.residentConversation(conversationId), exact: true });
      queryClient.invalidateQueries({ queryKey: aiChatKeys.managerConversation(conversationId), exact: true });
    }
    if (ticketId) {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId], exact: true });
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId, "conversation"], exact: true });
    }
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
    queryClient.invalidateQueries({ queryKey: ["management", "handoffs"] });
    queryClient.invalidateQueries({ queryKey: ["management", "dashboard"], exact: true });
  }

  if (event.event.startsWith("ticket.")) {
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
    if (ticketId) {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId], exact: true });
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId, "conversation"], exact: true });
    }
    queryClient.invalidateQueries({ queryKey: ["management", "dashboard"], exact: true });
  }

  if (workflowId) {
    queryClient.invalidateQueries({ queryKey: aiChatKeys.workflow(workflowId), exact: true });
    queryClient.invalidateQueries({ queryKey: aiChatKeys.all });
  }

  if (event.event.startsWith("announcement.")) {
    if (announcementId) {
      queryClient.invalidateQueries({ queryKey: ["announcement", announcementId], exact: false });
      queryClient.invalidateQueries({ queryKey: ["announcement", announcementId, "statistics"], exact: true });
    }
    queryClient.invalidateQueries({ queryKey: ["announcements", "list"] });
    queryClient.invalidateQueries({ queryKey: ["announcements", "unread-count"], exact: true });
  }
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isManagement = pathname.startsWith("/management");
  const [account, setAccountState] = useState<Account | null>(USE_MOCKS ? getAccount() : null);
  const [hydrated, setHydrated] = useState(USE_MOCKS);
  const [connection, setConnection] = useState<RealtimeState>(USE_MOCKS ? "connected" : "offline");
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);
  const showToast = useUiStore((state) => state.showToast);

  useEffect(() => {
    const syncAccount = () => {
      const current = getAccount();
      setAccountState(current);
      setHydrated(true);
      if (!USE_MOCKS && !current) router.replace("/login");
      if (!USE_MOCKS && isManagement && current?.role !== "management") router.replace("/app");
    };
    syncAccount();
    return subscribeToAuthChanges(syncAccount);
  }, [isManagement, router]);

  useEffect(() => {
    if (USE_MOCKS) return;
    if (!account || !getAccessToken()) {
      setConnection("offline");
      return;
    }
    return connectRealtime((state, event) => {
      setConnection(state);
      if (event) {
        invalidateForRealtimeEvent(event);
        if (event.event === "conversation.message.created") showToast({ tone: "info", message: "Có cập nhật mới trong conversation." });
      }
    });
  }, [account, showToast]);

  const actor = account;
  const navItems = useMemo(() => {
    if (!isManagement) return residentNav;
    const canUseAssistant = ["manager", "admin"].includes(actor?.management_profile?.management_role ?? "");
    const visibleManagementNav = canUseAssistant ? managementNav : managementNav.filter((item) => item.href !== "/management/assistant");
    return actor?.management_profile?.management_role === "admin"
      ? [...visibleManagementNav, { href: "/management/accounts", label: "Management accounts", icon: UserCog }]
      : visibleManagementNav;
  }, [actor?.management_profile?.management_role, isManagement]);
  const roleLabel = actor?.role === "management" ? actor.management_profile?.management_role ?? "management" : "Resident";
  const displayName = actor?.role === "management" ? actor.management_profile?.full_name ?? actor.email : actor?.email ?? "Đang tải phiên";
  const activeHref = useMemo(() => navItems.find((item) => item.href !== "/app" && item.href !== "/management" && pathname.startsWith(item.href))?.href ?? (isManagement ? "/management" : "/app"), [isManagement, navItems, pathname]);

  async function handleLogout() {
    try {
      await logoutSession(getRefreshToken());
    } catch {
      // Logout is best-effort; local credentials must still be removed.
    }
    disconnectRealtime();
    queryClient.clear();
    clearSession();
    showToast({ tone: "success", message: "Bạn đã đăng xuất." });
    router.replace("/login");
  }

  if (!hydrated) return <WorkspaceLoading />;

  return <div className={cn("app-frame", isManagement && "management-frame")}>
    <aside className={cn("sidebar", sidebarOpen && "sidebar-open")}>
      <div className="brand"><div className="brand-mark">O</div><div><strong>OnBxrd</strong><span>{isManagement ? "Operations" : "Resident space"}</span></div><IconButton label="Đóng menu" className="mobile-only close-sidebar" onClick={() => setSidebarOpen(false)}><X size={18} /></IconButton></div>
      <div className="workspace-switcher"><div className="workspace-icon">{isManagement ? <Shield size={16} /> : <Home size={16} />}</div><div><span>Workspace</span><strong>{isManagement ? "Management" : "Resident workspace"}</strong></div><ChevronDown size={15} /></div>
      <nav className="side-nav" aria-label="Điều hướng chính">{navItems.map((item) => { const Icon = item.icon; return <Link key={item.href} href={item.href} onClick={() => setSidebarOpen(false)} className={cn("side-link", activeHref === item.href && "side-link-active")}><Icon size={18} /><span>{item.label}</span></Link>; })}</nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-help"><LifeBuoy size={19} /><div><strong>Cần hỗ trợ?</strong><span>Trung tâm vận hành</span></div></div>
      <div className="sidebar-user"><div className="avatar avatar-small">{initials(displayName)}</div><div className="user-copy"><strong>{displayName}</strong><span>{roleLabel}</span></div><IconButton label="Đăng xuất" onClick={handleLogout}><LogOut size={16} /></IconButton></div>
    </aside>
    {sidebarOpen && <button className="sidebar-overlay mobile-only" aria-label="Đóng menu" onClick={() => setSidebarOpen(false)} />}
    <main className="app-main">
      <header className="topbar"><div className="topbar-left"><IconButton label="Mở menu" className="mobile-only" onClick={() => setSidebarOpen(true)}><Menu size={20} /></IconButton><div className="mobile-brand"><div className="brand-mark">O</div><strong>OnBxrd</strong></div><ConnectionPill state={connection} /></div><div className="topbar-actions"><button className="notification-button" aria-label="Thông báo"><Bell size={19} /><span /></button><div className="topbar-profile"><div className="avatar avatar-small">{initials(displayName)}</div><span>{displayName}</span><ChevronDown size={15} /></div></div></header>
      <div className="page-content">{children}</div>
    </main>
    <ToastViewport />
    {!isManagement && <nav className="bottom-nav mobile-only" aria-label="Điều hướng mobile">{residentNav.map((item) => { const Icon = item.icon; return <Link key={item.href} href={item.href} className={cn(pathname === item.href || (item.href !== "/app" && pathname.startsWith(item.href)) ? "bottom-link-active" : "")}><Icon size={19} /><span>{item.label === "Tổng quan" ? "Home" : item.label.split(" ")[0]}</span></Link>; })}</nav>}
    {USE_MOCKS && <div className="demo-banner">Demo data · kết nối API thật khi tắt <code>NEXT_PUBLIC_USE_MOCKS</code></div>}
  </div>;
}
