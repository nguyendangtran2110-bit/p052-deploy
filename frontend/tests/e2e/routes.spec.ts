import { expect, test } from "@playwright/test";

const publicRoutes = ["/login", "/register", "/recovery"];
const residentRoutes = [
  "/resident/onboarding",
  "/resident/benefits",
  "/resident/assistant",
  "/resident/tickets",
  "/resident/tickets/new",
  "/resident/tickets/TKT-LGN-1042",
  "/resident/notifications",
  "/resident/profile",
];
const managerRoutes = [
  "/manager/dashboard",
  "/manager/residents",
  "/manager/onboarding",
  "/manager/tickets",
  "/manager/tickets/TKT-LGN-1042",
  "/manager/notifications",
  "/manager/profile",
];

async function fillAndSubmitDemo(page: import("@playwright/test").Page, name: RegExp) {
  await page.goto("/login");
  await page.getByRole("button", { name }).click();
  await expect(page.getByLabel("Username")).not.toHaveValue("");
  await expect(page.getByLabel("Passphrase")).not.toHaveValue("");
  await page.getByRole("button", { name: /^Sign in$/ }).click();
  await expect(page).toHaveURL(/\/(?:resident\/onboarding|manager\/dashboard)$/);
}

async function sendHomieMessage(page: import("@playwright/test").Page, message: string, response: Record<string, unknown>, status = 200) {
  await page.route("**/api/rag/chat", async (route) => {
    await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(response) });
  });
  await page.getByRole("button", { name: "Homie Agent" }).click();
  await page.getByLabel("Message").fill(message);
  await page.getByRole("button", { name: "Send" }).click();
}

test("public landing and authentication routes render and theme switches", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "A more settled start to building life." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in to OnBxrd" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Create an account" }).first()).toBeVisible();
  for (const route of publicRoutes) {
    await page.goto(route);
    await expect(page.locator("h1").first()).toBeVisible();
  }
  await page.goto("/login");
  const initialTheme = await page.locator("html").getAttribute("data-theme");
  const nextTheme = initialTheme === "dark" ? "light" : "dark";
  await page.getByRole("button", { name: new RegExp(`switch to ${nextTheme} theme`, "i") }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", nextTheme);
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", nextTheme);
  await expect(page).toHaveTitle("Sign in · OnBxrd");
  await expect(page.getByRole("link", { name: "Back to OnBxrd home" })).toHaveAttribute("href", "/");
});

test("the account card opens the role profile and the wordmark returns to the landing page", async ({ page }) => {
  await fillAndSubmitDemo(page, /Avery Lagoon/);
  await expect(page.getByRole("link", { name: "Open profile for Avery Lagoon" })).toHaveAttribute("href", "/resident/profile");
  await page.getByRole("link", { name: "Open profile for Avery Lagoon" }).click();
  await expect(page).toHaveURL(/\/resident\/profile$/);
  await expect(page.getByRole("heading", { name: "Preferences" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Verified contact" })).toBeVisible();
  await expect(page.getByRole("link", { name: "OnBxrd" }).first()).toHaveAttribute("href", "/");
});

test("Homie Agent is a keyboard-accessible non-modal workside panel in both protected role shells", async ({ page }) => {
  await fillAndSubmitDemo(page, /Avery Lagoon/);
  const residentLauncher = page.getByRole("button", { name: "Homie Agent" });
  await residentLauncher.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Homie Agent workside panel")).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Homie Agent" })).toHaveCount(0);
  await expect(page.getByLabel("Message")).toBeFocused();
  await expect(page.getByLabel("Homie Agent workside panel")).toBeVisible();
  await residentLauncher.click();
  await expect(page.getByLabel("Homie Agent workside panel")).toHaveCount(0);

  await fillAndSubmitDemo(page, /Drew Eight/);
  await page.getByRole("button", { name: "Homie Agent" }).click();
  await expect(page.getByLabel("Homie Agent workside panel")).toBeVisible();
  await expect(page.getByRole("link", { name: /manual ticket/i })).toHaveCount(0);
});

test("Homie Agent remains usable at 320px without horizontal overflow", async ({ page }) => {
  await fillAndSubmitDemo(page, /Avery Lagoon/);
  await page.setViewportSize({ width: 320, height: 800 });
  await page.getByRole("button", { name: "Homie Agent" }).click();
  await expect(page.getByLabel("Homie Agent workside panel")).toBeVisible();
  await expect(page.getByLabel("Message")).toBeVisible();
  await expect(page.getByRole("button", { name: "Send" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
});

test("Resident Homie Agent proposal and unavailable fallback preserve the safe ticket paths", async ({ page }) => {
  await fillAndSubmitDemo(page, /Avery Lagoon/);
  await sendHomieMessage(page, "The lobby door is broken", {
    answer: "I can suggest fields for your review.",
    citations: [{ source_file: "handbook.pdf", section_title: "Support requests" }],
    proposal: { subject: "Broken lobby door", content: "The lobby door is broken.", urgency: "High" },
  });
  await page.getByRole("button", { name: "Review ticket fields" }).click();
  await expect(page).toHaveURL(/\/resident\/tickets\/new$/);
  await expect(page.getByLabel("Homie Agent workside panel")).toBeVisible();
  await expect(page.getByText("Broken lobby door")).toBeVisible();

  await page.goto("/resident/onboarding");
  await sendHomieMessage(page, "Can you help?", { code: "rag_backend_unavailable", message: "Unavailable" }, 503);
  await page.getByRole("link", { name: /manual ticket/i }).click();
  await expect(page).toHaveURL(/\/resident\/tickets\/new\?intent=new$/);
  await expect(page.getByLabel("Homie Agent workside panel")).toBeVisible();
});

test("public skip navigation and benefit tabs are keyboard complete", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator("#login-title")).toBeVisible();
  await page.getByRole("link", { name: "Skip to content" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  await fillAndSubmitDemo(page, /Avery Lagoon/);
  await page.goto("/resident/benefits");
  const tabs = page.getByRole("tab");
  await tabs.first().focus();
  await page.keyboard.press("ArrowRight");
  await expect(tabs.nth(1)).toBeFocused();
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("End");
  await expect(tabs.last()).toBeFocused();
  await page.keyboard.press("Home");
  await expect(tabs.first()).toBeFocused();
});

test("major stage and in-place dialog changes move focus safely", async ({ page }) => {
  await page.goto("/register");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Confirm your building identity" })).toBeFocused();
  await page.getByLabel("Building-issued resident ID").fill("SYN-RES-FOCUS");
  await page.getByLabel("Username").fill("synthetic-focus");
  await page.getByLabel("Passphrase").fill("synthetic-passphrase");
  await page.getByLabel("Contact for verification").fill("synthetic-contact");
  await page.getByRole("button", { name: "Send verification" }).click();
  await expect(page.getByRole("heading", { name: "Enter your verification code" })).toBeFocused();

  await page.goto("/recovery");
  await page.getByLabel("Username or building-issued ID").fill("synthetic-focus");
  await page.getByRole("button", { name: "Start recovery" }).click();
  await expect(page.getByRole("heading", { name: "Verify your recovery request" })).toBeFocused();
  await page.getByLabel("One-time code").fill("123456");
  await page.getByLabel("New passphrase").fill("synthetic-passphrase");
  await page.getByRole("button", { name: "Complete recovery" }).click();
  await expect(page.getByRole("heading", { name: "Recovery flow complete" })).toBeFocused();

  await fillAndSubmitDemo(page, /Avery Lagoon/);
  await page.goto("/resident/tickets/new");
  await expect(page.getByText("Saved", { exact: true })).toBeVisible();
  await page.getByLabel("Subject").fill("Accessible stage focus");
  await page.getByLabel("Content").fill("Review and submission stages move focus to their new headings.");
  await page.getByLabel("Content").blur();
  await expect(page.getByText("Saved", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review ticket" }).click();
  await expect(page.locator(".review-card h2")).toBeFocused();

  await fillAndSubmitDemo(page, /Drew Eight/);
  await page.goto("/manager/tickets/TKT-LGN-1042");
  await expect(page.getByText("Ticket is already Resolving. Current state refreshed without another transition.")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("button", { name: "Zalo" })).toBeEnabled();
  await page.getByRole("button", { name: "Zalo" }).click();
  await page.getByRole("button", { name: "Use Notify instead" }).click();
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Notify this resident" })).toBeFocused();
});

test("all 18 approved routes render in the correct role shell", async ({ page }) => {
  test.setTimeout(60_000);
  for (const route of publicRoutes) {
    await page.goto(route);
    await expect(page.locator("#main-content")).toBeVisible();
  }

  await fillAndSubmitDemo(page, /Avery Lagoon/);
  for (const route of residentRoutes) {
    await page.goto(route);
    await expect(page.locator("#main-content")).toBeVisible();
    await expect(page.locator("#main-content h1").first()).toBeVisible();
  }

  await fillAndSubmitDemo(page, /Drew Eight/);
  for (const route of managerRoutes) {
    await page.goto(route);
    await expect(page.locator("#main-content")).toBeVisible();
    await expect(page.locator("#main-content h1").first()).toBeVisible();
  }
});

test("resident demo remains account scoped", async ({ page }) => {
  await fillAndSubmitDemo(page, /Avery Lagoon/);
  await expect(page).toHaveURL(/resident\/onboarding/);
  await expect(page).toHaveTitle("Resident onboarding · OnBxrd");
  await expect(page.locator("h1")).toBeFocused();
  await page.reload();
  await expect(page).toHaveURL(/resident\/onboarding/);
  await page.goto("/resident/tickets");
  await expect(page.getByText("TKT-LGN-1042")).toBeVisible();
  await expect(page.getByText("TKT-EMB-2017")).toHaveCount(0);
});

test("manager exact scope excludes other floors", async ({ page }) => {
  await fillAndSubmitDemo(page, /Drew Eight/);
  await expect(page).toHaveURL(/manager\/dashboard/);
  await page.getByRole("link", { name: "Tickets" }).click();
  await expect(page).toHaveURL(/manager\/tickets/);
  await expect(page).toHaveTitle("Manager ticket queue · OnBxrd");
  await expect(page.locator("h1")).toBeFocused();
  await expect(page.getByText("TKT-LGN-1042")).toBeVisible();
  await expect(page.getByText("TKT-EMB-2017")).toHaveCount(0);
});

test("manager ticket open exposes actions only after a safe result and recovers from unavailable", async ({ page }) => {
  await fillAndSubmitDemo(page, /Drew Eight/);
  await page.goto("/manager/tickets/TKT-LGN-1042");

  await expect(page.getByText("Opening ticket and refreshing the current server state.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Zalo" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Mark resolved" })).toBeDisabled();
  await expect(page.getByText("Ticket is already Resolving. Current state refreshed without another transition.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Zalo" })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Mark resolved" })).toBeEnabled();

  await page.getByRole("button", { name: "Simulate open unavailable" }).click();
  await expect(page.getByText("Ticket open is unavailable. No transition was claimed and the observed state remains unchanged.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Zalo" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Retry open" })).toBeVisible();
  await page.getByRole("button", { name: "Retry open" }).click();
  await expect(page.getByText("Ticket is already Resolving. Current state refreshed without another transition.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Zalo" })).toBeEnabled();
});

test("manager Pending ticket transitions only after the open command completes", async ({ page }) => {
  await fillAndSubmitDemo(page, /Emery Harbor/);
  await page.goto("/manager/tickets/TKT-EMB-2017");

  await expect(page.getByText("Opening ticket and refreshing the current server state.")).toBeVisible();
  await expect(page.getByText("Pending", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Notify resident" })).toBeDisabled();
  await expect(page.getByText("Ticket opened and moved from Pending to Resolving.")).toBeVisible();
  await expect(page.getByText("Resolving", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Notify resident" })).toBeEnabled();
});

test("manager notification audience resets when the authenticated account changes", async ({ page }) => {
  await fillAndSubmitDemo(page, /Emery Harbor/);
  await page.goto("/manager/notifications");
  await page.getByRole("button", { name: "Compose" }).click();
  await page.getByLabel("Audience").selectOption("building");
  await expect(page.getByLabel("Audience")).toHaveValue("building");

  await fillAndSubmitDemo(page, /Drew Eight/);
  await page.goto("/manager/notifications");
  await page.getByRole("button", { name: "Compose" }).click();
  await expect(page.getByLabel("Audience")).toHaveValue("floor");
  await expect(page.getByLabel("Audience").locator('option[value="building"]')).toHaveCount(0);
});

test("resident notification reads survive reload and unavailable keeps the item unread", async ({ page }, testInfo) => {
  const dark = testInfo.project.name.includes("dark");
  const demo = dark ? /Blake Ember/ : /Avery Lagoon/;
  const heading = dark ? "Ticket received" : "Ticket status changed";
  const ticketId = dark ? "TKT-EMB-2017" : "TKT-LGN-1042";

  await fillAndSubmitDemo(page, demo);
  await page.goto("/resident/notifications");

  const notification = page.getByRole("article").filter({ has: page.getByRole("heading", { name: heading }) });
  await page.getByRole("button", { name: "Simulate next read unavailable" }).click();
  await notification.getByRole("button", { name: "Open ticket and mark read" }).click();
  await expect(page.getByText("Mark as read is unavailable. The notification remains unread; retry when ready.")).toBeVisible();
  await expect(notification.getByText("Unread", { exact: true })).toBeVisible();

  await notification.getByRole("button", { name: "Open ticket and mark read" }).click();
  await expect(page).toHaveURL(new RegExp(`/resident/tickets/${ticketId}$`));
  await page.goto("/resident/notifications");
  await expect(notification.getByText("Unread", { exact: true })).toHaveCount(0);
  await expect(notification.getByRole("button", { name: "Open ticket", exact: true })).toBeVisible();
  await page.reload();
  await expect(notification.getByText("Unread", { exact: true })).toHaveCount(0);
  await expect(notification.getByRole("button", { name: "Open ticket", exact: true })).toBeVisible();
});

test("360px and 320 CSS px reflow keep ticket work and account controls usable", async ({ page }) => {
  await fillAndSubmitDemo(page, /Avery Lagoon/);
  for (const width of [360, 320]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/resident/tickets/new");
    await expect(page.getByLabel("Subject")).toBeVisible();
    await expect(page.getByRole("button", { name: "Review ticket" })).toBeVisible();
    await expect(page.getByRole("button", { name: /switch to .* theme/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  }
});

test("reduced motion removes animated transforms and smooth scrolling", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/login");
  const motion = await page.locator(".reveal").first().evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      animationDuration: style.animationDuration,
      transform: style.transform,
      scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
    };
  });
  expect(Number.parseFloat(motion.animationDuration)).toBeLessThanOrEqual(0.001);
  expect(motion.transform).toBe("none");
  expect(motion.scrollBehavior).toBe("auto");
});

test("all six synthetic identities retain distinct exact ticket scope", async ({ page }) => {
  const cases = [
    { name: /Avery Lagoon/, route: "/resident/tickets", visible: ["TKT-LGN-1042", "TKT-LGN-0981"], hidden: "TKT-EMB-2017" },
    { name: /Blake Ember/, route: "/resident/tickets", visible: ["TKT-EMB-2017", "TKT-EMB-1940"], hidden: "TKT-LGN-1042" },
    { name: /Casey Harbor/, route: "/resident/tickets", visible: ["TKT-HBR-3308", "TKT-HBR-3241"], hidden: "TKT-LGN-1042" },
    { name: /Drew Eight/, route: "/manager/tickets", visible: ["TKT-LGN-1042", "TKT-LGN-0981"], hidden: "TKT-EMB-2017" },
    { name: /Emery Harbor/, route: "/manager/tickets", visible: ["TKT-LGN-1042", "TKT-EMB-2017"], hidden: "TKT-HBR-3308" },
    { name: /Finley Orchard/, route: "/manager/tickets", visible: ["TKT-HBR-3308", "TKT-HBR-3241"], hidden: "TKT-LGN-1042" },
  ];

  for (const demo of cases) {
    await fillAndSubmitDemo(page, demo.name);
    await page.goto(demo.route);
    for (const ticketId of demo.visible) await expect(page.getByText(ticketId)).toBeVisible();
    await expect(page.getByText(demo.hidden)).toHaveCount(0);
  }
});

test("invalid credentials never establish a session", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("resident.lagoon");
  await page.getByLabel("Passphrase").fill("NOT-THE-DEMO-PASSPHRASE");
  await page.getByRole("button", { name: /^Sign in$/ }).click();
  await expect(page.locator(".error-summary[role='alert']")).toContainText("Sign-in unsuccessful");
  await page.goto("/resident/onboarding");
  await expect(page).toHaveURL(/\/login\?returnTo=/);
});

test("scope loss purges the manager session and protected composer state", async ({ page }) => {
  await fillAndSubmitDemo(page, /Drew Eight/);
  await page.goto("/manager/notifications");
  await page.getByRole("button", { name: "Compose" }).click();
  await page.getByLabel("Subject").fill("Synthetic floor update");
  await page.getByLabel("Content").fill("Synthetic protected campaign content");
  await page.getByRole("button", { name: "Simulate scope loss" }).click();
  await expect(page).toHaveURL(/\/login\?reason=scope-changed/);
  await expect(page.getByText("Synthetic protected campaign content")).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem("onbxrd-demo-principal"))).toBeNull();
  await page.goBack();
  await expect(page).toHaveURL(/\/login\?returnTo=/);
  await expect(page.getByText("Synthetic protected campaign content")).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem("onbxrd-demo-principal"))).toBeNull();

  await fillAndSubmitDemo(page, /Drew Eight/);
  await page.goto("/manager/notifications");
  await page.getByRole("button", { name: "Compose" }).click();
  await expect(page.getByLabel("Subject")).toHaveValue("");
  await expect(page.getByLabel("Content")).toHaveValue("");
  await expect(page.getByText("Synthetic protected campaign content")).toHaveCount(0);
});

test("resident draft and submitted tickets remain durable without browser content persistence", async ({ browser }) => {
  const firstContext = await browser.newContext();
  const firstPage = await firstContext.newPage();
  await fillAndSubmitDemo(firstPage, /Avery Lagoon/);
  await firstPage.goto("/resident/tickets/new");
  await expect(firstPage.getByText("Saved", { exact: true })).toBeVisible();
  await firstPage.getByLabel("Subject").fill("Durable browser-boundary request");
  await firstPage.getByLabel("Content").fill("This synthetic draft must survive a new browser context through the mock server boundary.");
  await firstPage.getByLabel("Content").blur();
  await expect(firstPage.getByText("Saving…", { exact: true })).toBeVisible();
  await expect(firstPage.getByText("Saved", { exact: true })).toBeVisible();
  const browserStorage = await firstPage.evaluate(() => ({ local: JSON.stringify(localStorage), session: JSON.stringify(sessionStorage) }));
  expect(browserStorage.local).not.toContain("Durable browser-boundary request");
  expect(browserStorage.session).not.toContain("Durable browser-boundary request");
  await firstContext.close();

  const secondContext = await browser.newContext();
  const secondPage = await secondContext.newPage();
  await fillAndSubmitDemo(secondPage, /Avery Lagoon/);
  await secondPage.goto("/resident/tickets/new");
  await expect(secondPage.getByText("Saved", { exact: true })).toBeVisible();
  await expect(secondPage.getByLabel("Subject")).toHaveValue("Durable browser-boundary request");
  await expect(secondPage.getByRole("dialog", { name: "Continue your active draft?" })).toHaveCount(0);
  await secondPage.getByRole("button", { name: "Review ticket" }).click();
  await secondPage.getByRole("button", { name: "Submit ticket" }).click();
  await expect(secondPage.getByRole("heading", { name: "Ticket submitted" })).toBeVisible();
  const createdId = await secondPage.locator(".durable-result dd").first().textContent();
  expect(createdId).toMatch(/^TKT-DEMO-\d+$/);
  await secondPage.reload();
  await secondPage.goto("/resident/tickets");
  await expect(secondPage.getByText(createdId!)).toBeVisible();
  await secondPage.goto(`/resident/tickets/${createdId}`);
  await expect(secondPage.getByText("This synthetic draft must survive a new browser context through the mock server boundary.")).toBeVisible();
});

test("outcome unknown retries the same durable submission", async ({ page }) => {
  await fillAndSubmitDemo(page, /Blake Ember/);
  await page.goto("/resident/tickets/new");
  await expect(page.getByText("Saved", { exact: true })).toBeVisible();
  await page.getByLabel("Subject").fill("[simulate outcome unknown] durable retry");
  await page.getByLabel("Content").fill("The first response is ambiguous but the same idempotency key returns one ticket.");
  await page.getByLabel("Content").blur();
  await expect(page.getByText("Saving…", { exact: true })).toBeVisible();
  await expect(page.getByText("Saved", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review ticket" }).click();
  await page.getByRole("button", { name: "Submit ticket" }).click();
  await expect(page.getByText("Submission outcome unknown")).toBeVisible();
  const metadata = await page.evaluate(() => sessionStorage.getItem("onbxrd-submit-attempt"));
  expect(metadata).not.toContain("durable retry");
  expect(metadata).not.toContain("first response is ambiguous");
  await page.getByRole("button", { name: "Retry same submission" }).click();
  await expect(page.getByRole("heading", { name: "Ticket submitted" })).toBeVisible();
});
