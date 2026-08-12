import { beforeEach, describe, expect, it } from "vitest";
import { markNotificationRead, notificationSnapshot, resetNotificationService } from "@/src/mock/notification-service";
import { GET, POST } from "@/app/api/v1/resident/notifications/route";

const lagoonId = "demo-resident-lagoon";
const emberId = "demo-resident-ember";

beforeEach(() => resetNotificationService());

describe("resident notification read state", () => {
  it("keeps read state across snapshots and isolates it by account", () => {
    const lagoonNotification = notificationSnapshot(lagoonId)!.find((item) => item.unread)!;

    expect(markNotificationRead(lagoonId, lagoonNotification.id)?.find((item) => item.id === lagoonNotification.id)?.unread).toBe(false);
    expect(notificationSnapshot(lagoonId)?.find((item) => item.id === lagoonNotification.id)?.unread).toBe(false);
    expect(notificationSnapshot(emberId)?.find((item) => item.id === lagoonNotification.id)).toBeUndefined();
  });

  it("marks reads idempotently and rejects foreign notification ids", () => {
    const notificationId = notificationSnapshot(lagoonId)!.find((item) => item.unread)!.id;

    const first = markNotificationRead(lagoonId, notificationId);
    const replay = markNotificationRead(lagoonId, notificationId);

    expect(first).toEqual(replay);
    expect(markNotificationRead(emberId, notificationId)).toBeNull();
  });
});

describe("resident notification route", () => {
  it("derives the account from the authenticated principal header", async () => {
    const response = GET(new Request("http://localhost/api/v1/resident/notifications?accountId=demo-resident-ember", {
      headers: { "X-OnBxrd-Demo-Principal": lagoonId },
    }));
    const body = await response.json() as { notifications: Array<{ id: string }> };

    expect(response.status).toBe(200);
    expect(body.notifications).toEqual(notificationSnapshot(lagoonId));
    expect(body.notifications).not.toEqual(notificationSnapshot(emberId));
  });

  it("returns unavailable without changing durable read state", async () => {
    const notificationId = notificationSnapshot(lagoonId)!.find((item) => item.unread)!.id;
    const response = await POST(new Request("http://localhost/api/v1/resident/notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-OnBxrd-Demo-Principal": lagoonId },
      body: JSON.stringify({ notificationId, simulateUnavailable: true }),
    }));

    expect(response.status).toBe(503);
    expect(notificationSnapshot(lagoonId)?.find((item) => item.id === notificationId)?.unread).toBe(true);
  });
});
