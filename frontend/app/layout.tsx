import type { Metadata } from "next";
import { headers } from "next/headers";
import Script from "next/script";
import { AppProviders } from "@/src/components/providers";
import "@fontsource/be-vietnam-pro/400.css";
import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/700.css";
import "@/src/styles/globals.css";

export const metadata: Metadata = {
  title: { default: "OnBxrd", template: "%s · OnBxrd" },
  description: "Synthetic demonstration of the OnBxrd resident and manager frontend.",
};

export const dynamic = "force-dynamic";

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const nonce = (await headers()).get("x-nonce") ?? undefined;
  return (
    <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning>
      <head><Script nonce={nonce} src="/theme-bootstrap.js" strategy="beforeInteractive" /></head>
      <body>
        <div hidden dangerouslySetInnerHTML={{ __html: `<!--
THESIS: Quiet Signal turns resident help and manager operations into one exact signal path and refuses the generic KPI dashboard.
OWN-WORLD: Mineral canvas, solid paper surfaces, Lagoon and Harbor fields, Ember endpoints, stair-step forms, and a precise animated signal line.
STORY: People identify scope, understand state, review consequential actions, and retain a durable result.
FIRST VIEWPORT: A stable role rail frames a title-first task surface; the primary action sits beside or directly after the heading.
FORM: Approved Quiet Signal operational register, position 1; inherited canonical direction seed QS-APPROVED-2026-08.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
-->` }} />
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
