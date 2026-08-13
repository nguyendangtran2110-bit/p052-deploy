import Link from "next/link";
import { ThemeButton } from "@/src/components/theme-button";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="public-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="public-topbar">
        <Link className="brand" href="/login"><span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><span>OnBxrd</span></Link>
        <ThemeButton />
      </header>
      <main id="main-content" tabIndex={-1}>{children}</main>
    </div>
  );
}
