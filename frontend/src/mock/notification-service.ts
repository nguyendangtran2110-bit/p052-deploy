import { demoAccounts, notificationsForAccount } from "@/src/mock/data";

const readByAccount = new Map<string, Set<string>>();

export function notificationSnapshot(accountId: string) {
  const account = demoAccounts.find((candidate) => candidate.id === accountId && candidate.role === "resident");
  if (!account) return null;
  const readIds = readByAccount.get(accountId) ?? new Set<string>();
  return notificationsForAccount(account).map((notification) => ({
    ...notification,
    unread: notification.unread && !readIds.has(notification.id),
  }));
}

export function markNotificationRead(accountId: string, notificationId: string) {
  const snapshot = notificationSnapshot(accountId);
  if (!snapshot?.some((notification) => notification.id === notificationId)) return null;
  const readIds = readByAccount.get(accountId) ?? new Set<string>();
  readIds.add(notificationId);
  readByAccount.set(accountId, readIds);
  return notificationSnapshot(accountId);
}

export function resetNotificationService() {
  readByAccount.clear();
}
