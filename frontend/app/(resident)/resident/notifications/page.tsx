"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BellIcon } from "@/src/components/icons";
import { Button, PageHeader } from "@/src/components/primitives";
import { useApp } from "@/src/components/providers";

type NotificationItem = {
  id: string;
  title: string;
  body: string;
  time: string;
  unread: boolean;
  relatedTicketId?: string;
};

export default function ResidentNotificationsPage() {
  const { account } = useApp();
  const router = useRouter();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [failNextRead, setFailNextRead] = useState(false);

  const load = useCallback(async () => {
    if (!account) return;
    setLoading(true);
    const response = await fetch("/api/v1/resident/notifications", {
      cache: "no-store",
      headers: { "X-OnBxrd-Demo-Principal": account.id },
    });
    if (response.ok) {
      setItems((await response.json() as { notifications: NotificationItem[] }).notifications);
      setError("");
    } else {
      setError("Notifications are unavailable. Your existing read state was not changed.");
    }
    setLoading(false);
  }, [account]);

  useEffect(() => {
    const loadTimer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(loadTimer);
  }, [load]);

  const markRead = async (item: NotificationItem, openRelated = false) => {
    if (!account) return;
    setError("");
    const response = await fetch("/api/v1/resident/notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-OnBxrd-Demo-Principal": account.id },
      body: JSON.stringify({ notificationId: item.id, simulateUnavailable: failNextRead }),
    });
    setFailNextRead(false);
    if (!response.ok) {
      setError("Mark as read is unavailable. The notification remains unread; retry when ready.");
      return;
    }
    setItems((await response.json() as { notifications: NotificationItem[] }).notifications);
    if (openRelated && item.relatedTicketId) router.push(`/resident/tickets/${item.relatedTicketId}`);
  };

  return <div className="page manager-page">
    <PageHeader title="Notifications" description="Building updates and ticket activity, kept in a durable history." action={<Button kind="quiet" onClick={() => setFailNextRead(true)} disabled={failNextRead}>Simulate next read unavailable</Button>} />
    {error ? <div className="notice" role="alert"><strong>Notification update failed</strong><span>{error}</span><Button kind="quiet" onClick={() => void load()}>Reload notifications</Button></div> : null}
    {loading ? <div className="route-pending" role="status">Loading notifications…</div> : <div className="notification-list reveal reveal-2">{items.map((item) => <article className={item.unread ? "notification unread" : "notification"} key={item.id}><span className="notification-icon"><BellIcon /></span><div><div className="notification-heading"><h2>{item.title}</h2>{item.unread ? <span className="unread-label">Unread</span> : null}</div><p>{item.body}</p><small>{item.time}</small></div>{item.relatedTicketId ? <Button kind="quiet" onClick={() => void markRead(item, true)}>Open ticket{item.unread ? " and mark read" : ""}</Button> : item.unread ? <Button kind="quiet" onClick={() => void markRead(item)}>Mark as read</Button> : <span className="read-label">Read</span>}</article>)}</div>}
  </div>;
}
