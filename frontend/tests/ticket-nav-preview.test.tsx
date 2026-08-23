import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FileText } from "lucide-react";
import { TicketNavPreview } from "@/components/ticket-nav-preview";

const { useTickets } = vi.hoisted(() => ({ useTickets: vi.fn() }));

vi.mock("@/features/tickets/queries", () => ({ useTickets }));

const ticket = {
  id: "ticket-42",
  title: "Leaking faucet in kitchen",
  status: "in_progress",
  priority: "high",
};

describe("TicketNavPreview", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("opens immediately with compact ticket metadata and links to the existing detail route", () => {
    Object.defineProperty(window, "matchMedia", { configurable: true, value: () => ({ matches: true }) });
    useTickets.mockReturnValue({ data: { items: [ticket] }, isLoading: false, isError: false });

    render(<TicketNavPreview href="/app/tickets" label="Tickets" icon={FileText} active={false} onNavigate={vi.fn()} />);
    fireEvent.pointerEnter(screen.getByRole("link", { name: "Tickets" }));

    expect(screen.getByRole("region", { name: "Tickets preview" })).toBeInTheDocument();
    expect(screen.getByText(ticket.title)).toBeInTheDocument();
    expect(screen.getByText("Đang xử lý")).toBeInTheDocument();
    expect(screen.getByText("Cao")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /leaking faucet/i })).toHaveAttribute("href", "/app/tickets/ticket-42");
  });

  it("uses the existing management detail route for a manager ticket", () => {
    Object.defineProperty(window, "matchMedia", { configurable: true, value: () => ({ matches: true }) });
    useTickets.mockReturnValue({ data: { items: [ticket] }, isLoading: false, isError: false });

    render(<TicketNavPreview href="/management/tickets" label="Ticket queue" icon={FileText} active={false} onNavigate={vi.fn()} />);
    fireEvent.pointerEnter(screen.getByRole("link", { name: "Ticket queue" }));

    expect(screen.getByRole("link", { name: /leaking faucet/i })).toHaveAttribute("href", "/management/tickets/ticket-42");
  });
});
