import type { Metadata } from "next";
import "@fontsource/be-vietnam-pro/400.css";
import "@fontsource/be-vietnam-pro/500.css";
import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/700.css";
import "./globals.css";
import { Providers } from "@/app/providers";

export const metadata: Metadata = {
  title: "OnBxrd · Resident operations",
  description: "Không gian cư dân và console vận hành cho khu căn hộ OnBxrd.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{ __html: `(() => { try { const stored = localStorage.getItem('onbxrd-theme'); const theme = stored === 'dark' || stored === 'light' ? stored : (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); document.documentElement.dataset.theme = theme; } catch {} })();` }} /></head><body><Providers>{children}</Providers></body></html>;
}
