import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { FileText } from "lucide-react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SidebarNavLink } from "@/components/sidebar-nav-link";
import { ThemeControl } from "@/components/theme-control";

describe("navigation controls", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    window.localStorage.clear();
    delete document.documentElement.dataset.theme;
  });

  it("keeps a sidebar nav hover treatment for 100ms after pointer leave", () => {
    vi.useFakeTimers();
    render(<SidebarNavLink href="/app/chat" label="Chat" icon={FileText} active={false} onNavigate={vi.fn()} />);
    const link = screen.getByRole("link", { name: "Chat" });

    fireEvent.pointerEnter(link, { pointerType: "mouse" });
    expect(link).toHaveClass("side-link-powered");
    fireEvent.pointerLeave(link, { pointerType: "mouse" });
    act(() => vi.advanceTimersByTime(99));
    expect(link).toHaveClass("side-link-powered");
    act(() => vi.advanceTimersByTime(1));
    expect(link).not.toHaveClass("side-link-powered");
  });

  it("toggles the login theme control", () => {
    render(<ThemeControl compact />);
    const control = screen.getByRole("button");

    fireEvent.click(control);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(window.localStorage.getItem("onbxrd-theme")).toBe("light");
  });
});
