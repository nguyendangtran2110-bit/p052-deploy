import accountsFixture from "@/mock-data/accounts.json";
import notificationsFixture from "@/mock-data/notifications.json";
import residentContentFixture from "@/mock-data/resident-content.json";
import residentsFixture from "@/mock-data/residents.json";
import ticketsFixture from "@/mock-data/tickets.json";
import { demoNotificationScopePolicy, demoScopePolicy, demoTicketScopePolicy } from "@/src/mock/demo-scope-policy";

export type Role = "resident" | "manager";
export type TicketStatus = "Pending" | "Resolving" | "Resolved" | "Denied";
export type TicketUrgency = "Low" | "Normal" | "High";
export type Theme = "light" | "dark";

export type DemoAccount = {
  id: string;
  username: string;
  passphrase: string;
  role: Role;
  name: string;
  label: string;
  building: string;
  floors: string[];
};

export type Ticket = {
  id: string;
  ownerId: string;
  subject: string;
  content: string;
  urgency: TicketUrgency;
  status: TicketStatus;
  building: string;
  floor: string;
  room: string;
  submittedAt: string;
  denialReason?: string;
};

export type ResidentProfile = {
  id: string;
  name: string;
  building: string;
  floor: string;
  room: string;
  onboarding: string;
  state: string;
};

export type Notification = {
  id: string;
  accountIds: string[];
  building: string;
  floor: string;
  title: string;
  body: string;
  unread: boolean;
  time: string;
  relatedTicketId?: string;
};

export type OnboardingStep = {
  title: string;
  state: "Completed" | "Current" | "Pending";
  detail: string;
};

export type Benefit = {
  title: string;
  category: string;
  body: string;
};

export type FixtureBundle = {
  accounts: DemoAccount[];
  tickets: Ticket[];
  residentProfiles: ResidentProfile[];
  notifications: Notification[];
  onboardingSteps: OnboardingStep[];
  benefits: Benefit[];
};

function fixtureError(path: string): never {
  throw new Error(`Invalid mock fixture at ${path}.`);
}

function recordAt(value: unknown, path: string, keys: readonly string[]): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) fixtureError(path);
  const record = value as Record<string, unknown>;
  if (Object.keys(record).some((key) => !keys.includes(key))) fixtureError(`${path}.keys`);
  return record;
}

function arrayAt(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) fixtureError(path);
  return value;
}

function stringAt(value: unknown, path: string, maxLength = 1800): string {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > maxLength) fixtureError(path);
  return value;
}

function stringArrayAt(value: unknown, path: string): string[] {
  const values = arrayAt(value, path).map((item, index) => stringAt(item, `${path}[${index}]`, 120));
  if (values.length === 0 || new Set(values).size !== values.length) fixtureError(path);
  return values;
}

function enumAt<const T extends string>(value: unknown, path: string, allowed: readonly T[]): T {
  if (typeof value !== "string" || !allowed.includes(value as T)) fixtureError(path);
  return value as T;
}

function booleanAt(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") fixtureError(path);
  return value;
}

function optionalStringAt(value: unknown, path: string, maxLength = 1800): string | undefined {
  return value === undefined ? undefined : stringAt(value, path, maxLength);
}

function uniqueBy(items: Array<{ id: string }>, path: string): void {
  if (new Set(items.map((item) => item.id)).size !== items.length) fixtureError(`${path}.id`);
}

function uniqueStrings(values: readonly string[], path: string): void {
  if (new Set(values).size !== values.length) fixtureError(path);
}

function accountAt(value: unknown, path: string): DemoAccount {
  const record = recordAt(value, path, ["id", "username", "passphrase", "role", "name", "label", "building", "floors"]);
  return {
    id: stringAt(record.id, `${path}.id`, 120),
    username: stringAt(record.username, `${path}.username`, 120),
    passphrase: stringAt(record.passphrase, `${path}.passphrase`, 120),
    role: enumAt(record.role, `${path}.role`, ["resident", "manager"]),
    name: stringAt(record.name, `${path}.name`, 160),
    label: stringAt(record.label, `${path}.label`, 200),
    building: stringAt(record.building, `${path}.building`, 160),
    floors: stringArrayAt(record.floors, `${path}.floors`),
  };
}

function ticketAt(value: unknown, path: string): Ticket {
  const record = recordAt(value, path, ["id", "ownerId", "subject", "content", "urgency", "status", "building", "floor", "room", "submittedAt", "denialReason"]);
  const submittedAt = stringAt(record.submittedAt, `${path}.submittedAt`, 40);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(submittedAt) || Number.isNaN(Date.parse(submittedAt))) {
    fixtureError(`${path}.submittedAt`);
  }
  const denialReason = optionalStringAt(record.denialReason, `${path}.denialReason`);
  const status = enumAt(record.status, `${path}.status`, ["Pending", "Resolving", "Resolved", "Denied"]);
  if ((status === "Denied") !== Boolean(denialReason)) fixtureError(`${path}.denialReason`);
  return {
    id: stringAt(record.id, `${path}.id`, 120),
    ownerId: stringAt(record.ownerId, `${path}.ownerId`, 120),
    subject: stringAt(record.subject, `${path}.subject`, 120),
    content: stringAt(record.content, `${path}.content`),
    urgency: enumAt(record.urgency, `${path}.urgency`, ["Low", "Normal", "High"]),
    status,
    building: stringAt(record.building, `${path}.building`, 160),
    floor: stringAt(record.floor, `${path}.floor`, 40),
    room: stringAt(record.room, `${path}.room`, 80),
    submittedAt,
    ...(denialReason ? { denialReason } : {}),
  };
}

function residentProfileAt(value: unknown, path: string): ResidentProfile {
  const record = recordAt(value, path, ["id", "name", "building", "floor", "room", "onboarding", "state"]);
  return {
    id: stringAt(record.id, `${path}.id`, 120),
    name: stringAt(record.name, `${path}.name`, 160),
    building: stringAt(record.building, `${path}.building`, 160),
    floor: stringAt(record.floor, `${path}.floor`, 40),
    room: stringAt(record.room, `${path}.room`, 80),
    onboarding: stringAt(record.onboarding, `${path}.onboarding`, 120),
    state: stringAt(record.state, `${path}.state`, 80),
  };
}

function notificationAt(value: unknown, path: string): Notification {
  const record = recordAt(value, path, ["id", "accountIds", "building", "floor", "title", "body", "unread", "time", "relatedTicketId"]);
  const relatedTicketId = optionalStringAt(record.relatedTicketId, `${path}.relatedTicketId`, 120);
  return {
    id: stringAt(record.id, `${path}.id`, 120),
    accountIds: stringArrayAt(record.accountIds, `${path}.accountIds`),
    building: stringAt(record.building, `${path}.building`, 160),
    floor: stringAt(record.floor, `${path}.floor`, 40),
    title: stringAt(record.title, `${path}.title`, 160),
    body: stringAt(record.body, `${path}.body`),
    unread: booleanAt(record.unread, `${path}.unread`),
    time: stringAt(record.time, `${path}.time`, 120),
    ...(relatedTicketId ? { relatedTicketId } : {}),
  };
}

function onboardingStepAt(value: unknown, path: string): OnboardingStep {
  const record = recordAt(value, path, ["title", "state", "detail"]);
  return {
    title: stringAt(record.title, `${path}.title`, 160),
    state: enumAt(record.state, `${path}.state`, ["Completed", "Current", "Pending"]),
    detail: stringAt(record.detail, `${path}.detail`),
  };
}

function benefitAt(value: unknown, path: string): Benefit {
  const record = recordAt(value, path, ["title", "category", "body"]);
  return {
    title: stringAt(record.title, `${path}.title`, 160),
    category: stringAt(record.category, `${path}.category`, 120),
    body: stringAt(record.body, `${path}.body`),
  };
}

export function validateFixtureBundle(input: unknown): FixtureBundle {
  const bundle = recordAt(input, "bundle", ["accounts", "tickets", "residentProfiles", "notifications", "onboardingSteps", "benefits"]);
  const accounts = arrayAt(bundle.accounts, "accounts").map((item, index) => accountAt(item, `accounts[${index}]`));
  const tickets = arrayAt(bundle.tickets, "tickets").map((item, index) => ticketAt(item, `tickets[${index}]`));
  const residentProfiles = arrayAt(bundle.residentProfiles, "residentProfiles").map((item, index) => residentProfileAt(item, `residentProfiles[${index}]`));
  const notifications = arrayAt(bundle.notifications, "notifications").map((item, index) => notificationAt(item, `notifications[${index}]`));
  const onboardingSteps = arrayAt(bundle.onboardingSteps, "onboardingSteps").map((item, index) => onboardingStepAt(item, `onboardingSteps[${index}]`));
  const benefits = arrayAt(bundle.benefits, "benefits").map((item, index) => benefitAt(item, `benefits[${index}]`));

  uniqueBy(accounts, "accounts");
  if (new Set(accounts.map((account) => account.username)).size !== accounts.length) fixtureError("accounts.username");
  uniqueBy(tickets, "tickets");
  uniqueBy(residentProfiles, "residentProfiles");
  uniqueBy(notifications, "notifications");
  if (benefits.length === 0) fixtureError("benefits.empty");
  uniqueStrings(onboardingSteps.map((step) => step.title), "onboardingSteps.title");
  uniqueStrings(benefits.map((benefit) => benefit.title), "benefits.title");
  uniqueStrings(benefits.map((benefit) => benefitKey(benefit.title)), "benefits.slug");

  const residents = accounts.filter((account) => account.role === "resident");
  const managers = accounts.filter((account) => account.role === "manager");
  if (residents.length !== 3 || managers.length !== 3) fixtureError("accounts.roleCounts");
  if (accounts.length !== Object.keys(demoScopePolicy).length) fixtureError("accounts.scopePolicyCoverage");
  for (const [index, account] of accounts.entries()) {
    const policy = demoScopePolicy[account.id];
    if (!policy || account.role !== policy.role || account.building !== policy.building || !sameStrings(account.floors, policy.floors)) {
      fixtureError(`accounts[${index}].scopePolicy`);
    }
  }
  const accountById = new Map(accounts.map((account) => [account.id, account]));
  const ticketById = new Map(tickets.map((ticket) => [ticket.id, ticket]));
  const profileById = new Map(residentProfiles.map((profile) => [profile.id, profile]));

  for (const [index, profile] of residentProfiles.entries()) {
    const account = accountById.get(profile.id);
    if (!account || account.role !== "resident") fixtureError(`residentProfiles[${index}].id`);
    if (account.building !== profile.building || !account.floors.includes(profile.floor)) fixtureError(`residentProfiles[${index}].location`);
  }
  if (residents.some((resident) => !profileById.has(resident.id))) fixtureError("residentProfiles.coverage");

  if (tickets.length !== Object.keys(demoTicketScopePolicy).length) fixtureError("tickets.scopePolicyCoverage");
  for (const [index, ticket] of tickets.entries()) {
    const policy = demoTicketScopePolicy[ticket.id as keyof typeof demoTicketScopePolicy];
    if (!policy || ticket.ownerId !== policy.ownerId || ticket.building !== policy.building || ticket.floor !== policy.floor || ticket.room !== policy.room) {
      fixtureError(`tickets[${index}].scopePolicy`);
    }
    const owner = accountById.get(ticket.ownerId);
    const profile = profileById.get(ticket.ownerId);
    if (!owner || owner.role !== "resident") fixtureError(`tickets[${index}].ownerId`);
    if (!profile || ticket.building !== owner.building || !owner.floors.includes(ticket.floor) || ticket.room !== profile.room) {
      fixtureError(`tickets[${index}].location`);
    }
  }

  if (notifications.length !== Object.keys(demoNotificationScopePolicy).length) fixtureError("notifications.scopePolicyCoverage");
  for (const [index, notification] of notifications.entries()) {
    const policy = demoNotificationScopePolicy[notification.id as keyof typeof demoNotificationScopePolicy];
    if (!policy || notification.building !== policy.building || notification.floor !== policy.floor || !sameStrings(notification.accountIds, policy.accountIds) || notification.relatedTicketId !== ("relatedTicketId" in policy ? policy.relatedTicketId : undefined)) {
      fixtureError(`notifications[${index}].scopePolicy`);
    }
    for (const accountId of notification.accountIds) {
      const account = accountById.get(accountId);
      if (!account) fixtureError(`notifications[${index}].accountIds`);
      if (account.building !== notification.building || (!account.floors.includes("ALL_FLOORS") && !account.floors.includes(notification.floor))) {
        fixtureError(`notifications[${index}].scope`);
      }
    }
    if (notification.relatedTicketId) {
      const relatedTicket = ticketById.get(notification.relatedTicketId);
      if (!relatedTicket) fixtureError(`notifications[${index}].relatedTicketId`);
      if (relatedTicket.building !== notification.building || relatedTicket.floor !== notification.floor) {
        fixtureError(`notifications[${index}].relatedTicketScope`);
      }
      for (const accountId of notification.accountIds) {
        const account = accountById.get(accountId)!;
        if (account.role === "resident" && relatedTicket.ownerId !== account.id) {
          fixtureError(`notifications[${index}].relatedTicketAudience`);
        }
      }
    }
  }

  return { accounts, tickets, residentProfiles, notifications, onboardingSteps, benefits };
}

function sameStrings(actual: readonly string[], expected: readonly string[]) {
  return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function benefitKey(title: string) {
  return title.toLowerCase().replaceAll(" ", "-");
}

function fixtureCollection(source: unknown, file: string, key: string, allowedKeys: readonly string[] = [key]): unknown {
  const wrapper = recordAt(source, file, allowedKeys);
  return wrapper[key];
}

const fixtureBundle = validateFixtureBundle({
  accounts: fixtureCollection(accountsFixture, "accounts.json", "accounts"),
  tickets: fixtureCollection(ticketsFixture, "tickets.json", "tickets"),
  residentProfiles: fixtureCollection(residentsFixture, "residents.json", "residentProfiles"),
  notifications: fixtureCollection(notificationsFixture, "notifications.json", "notifications"),
  onboardingSteps: fixtureCollection(residentContentFixture, "resident-content.json", "onboardingSteps", ["onboardingSteps", "benefits"]),
  benefits: fixtureCollection(residentContentFixture, "resident-content.json", "benefits", ["onboardingSteps", "benefits"]),
});

export const demoAccounts = fixtureBundle.accounts;
export const tickets = fixtureBundle.tickets;
export const residentProfiles = fixtureBundle.residentProfiles;
export const notifications = fixtureBundle.notifications;
export const onboardingSteps = fixtureBundle.onboardingSteps;
export const benefits = fixtureBundle.benefits;

export function accountByUsername(username: string) {
  return demoAccounts.find((account) => account.username === username);
}

export function ticketsForAccount(account: DemoAccount) {
  if (account.role === "resident") return tickets.filter((ticket) => ticket.ownerId === account.id);
  return tickets.filter((ticket) => {
    if (ticket.building !== account.building) return false;
    return account.floors.includes("ALL_FLOORS") || account.floors.includes(ticket.floor);
  });
}

export function ticketForAccount(account: DemoAccount, ticketId: string) {
  return ticketsForAccount(account).find((ticket) => ticket.id === ticketId);
}

export function notificationsForAccount(account: DemoAccount) {
  return notifications.filter((notification) => notification.accountIds.includes(account.id));
}
