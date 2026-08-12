import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function IconBase({ children, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

export const HomeIcon = (props: IconProps) => <IconBase {...props}><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></IconBase>;
export const StepsIcon = (props: IconProps) => <IconBase {...props}><path d="M5 18h4v-4h4v-4h6"/><path d="M5 6h.01"/><path d="M5 10h.01"/><path d="M5 14h.01"/></IconBase>;
export const GiftIcon = (props: IconProps) => <IconBase {...props}><path d="M3 9h18v12H3z"/><path d="M12 9v12"/><path d="M3 13h18"/><path d="M12 9H7.5a2.5 2.5 0 1 1 2.2-3.7L12 9Z"/><path d="M12 9h4.5a2.5 2.5 0 1 0-2.2-3.7L12 9Z"/></IconBase>;
export const ChatIcon = (props: IconProps) => <IconBase {...props}><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4Z"/><path d="M8 9h8M8 13h5"/></IconBase>;
export const TicketIcon = (props: IconProps) => <IconBase {...props}><path d="M4 5h16v5a2 2 0 0 0 0 4v5H4v-5a2 2 0 0 0 0-4Z"/><path d="M9 8v8"/></IconBase>;
export const BellIcon = (props: IconProps) => <IconBase {...props}><path d="M18 8a6 6 0 1 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></IconBase>;
export const UserIcon = (props: IconProps) => <IconBase {...props}><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></IconBase>;
export const UsersIcon = (props: IconProps) => <IconBase {...props}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></IconBase>;
export const ArrowIcon = (props: IconProps) => <IconBase {...props}><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></IconBase>;
export const CheckIcon = (props: IconProps) => <IconBase {...props}><path d="m5 12 4 4L19 6"/></IconBase>;
export const MoonIcon = (props: IconProps) => <IconBase {...props}><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"/></IconBase>;
export const SunIcon = (props: IconProps) => <IconBase {...props}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></IconBase>;
export const SearchIcon = (props: IconProps) => <IconBase {...props}><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></IconBase>;
export const ShieldIcon = (props: IconProps) => <IconBase {...props}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></IconBase>;
export const ExternalIcon = (props: IconProps) => <IconBase {...props}><path d="M14 3h7v7"/><path d="m10 14 11-11"/><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/></IconBase>;
