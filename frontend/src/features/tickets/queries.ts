"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignTicket,
  createTicket,
  fetchConversationById,
  fetchTicket,
  fetchTicketConversation,
  fetchTickets,
  sendManagementMessage,
  sendTicketMessage,
  takeoverConversation,
  handbackConversation,
  updateTicketStatus,
} from "@/lib/data";
import type { CreateTicketInput } from "@/lib/data";

export const ticketKeys = {
  all: ["tickets"] as const,
  list: (filters: Record<string, unknown>) => ["tickets", "list", filters] as const,
  detail: (id: string) => ["ticket", id] as const,
  ticketConversation: (ticketId: string) => ["ticket", ticketId, "conversation"] as const,
  conversation: (conversationId: string) => ["conversation", conversationId] as const,
};

export function useTickets(filters: Record<string, string | number | boolean | undefined> = {}) {
  return useQuery({ queryKey: ticketKeys.list(filters), queryFn: () => fetchTickets(filters) });
}

export function useTicket(id: string) {
  return useQuery({ queryKey: ticketKeys.detail(id), queryFn: () => fetchTicket(id), enabled: Boolean(id) });
}

export function useConversation(ticketId: string) {
  return useQuery({ queryKey: ticketKeys.ticketConversation(ticketId), queryFn: () => fetchTicketConversation(ticketId), enabled: Boolean(ticketId) });
}

export function useConversationById(conversationId: string | undefined) {
  return useQuery({ queryKey: ticketKeys.conversation(conversationId ?? ""), queryFn: () => fetchConversationById(conversationId!), enabled: Boolean(conversationId) });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateTicketInput & { idempotencyKey?: string }) => {
      const { idempotencyKey, ...payload } = input;
      return createTicket(payload, idempotencyKey);
    },
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ticketKeys.all });
      queryClient.setQueryData(ticketKeys.detail(ticket.id), ticket);
    },
  });
}

export function useSendTicketMessage(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { message: string; conversation_id?: string; unit_id?: string; attachment_ids?: string[] }) => sendTicketMessage(ticketId, payload),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ticketKeys.ticketConversation(ticketId), exact: true });
      queryClient.invalidateQueries({ queryKey: ticketKeys.detail(ticketId), exact: true });
      if (response.conversation_id) queryClient.invalidateQueries({ queryKey: ticketKeys.conversation(response.conversation_id), exact: true });
    },
  });
}

export function useManagementConversationActions(ticketId: string, conversationId?: string) {
  const queryClient = useQueryClient();
  const refresh = (response?: { conversation_id?: string }) => {
    const id = response?.conversation_id ?? conversationId;
    if (id) {
      queryClient.invalidateQueries({ queryKey: ticketKeys.conversation(id), exact: true });
      queryClient.invalidateQueries({ queryKey: ticketKeys.ticketConversation(ticketId), exact: true });
    }
    if (ticketId) queryClient.invalidateQueries({ queryKey: ticketKeys.detail(ticketId), exact: true });
    queryClient.invalidateQueries({ queryKey: ticketKeys.all });
    queryClient.invalidateQueries({ queryKey: ["management", "handoffs"] });
    queryClient.invalidateQueries({ queryKey: ["management", "dashboard"], exact: true });
  };
  const requireConversation = () => {
    if (!conversationId) throw new Error("Conversation chưa sẵn sàng.");
    return conversationId;
  };
  return {
    takeover: useMutation({ mutationFn: (version: number) => takeoverConversation(requireConversation(), version), onSuccess: refresh }),
    handback: useMutation({ mutationFn: ({ version, note }: { version: number; note?: string }) => handbackConversation(requireConversation(), version, note), onSuccess: refresh }),
    send: useMutation({ mutationFn: ({ message, version, attachment_ids }: { message: string; version: number; attachment_ids?: string[] }) => sendManagementMessage(requireConversation(), { message, conversation_version: version, attachment_ids }), onSuccess: () => refresh() }),
    assign: useMutation({ mutationFn: ({ assignee, dueAt }: { assignee: string | null; dueAt?: string | null }) => assignTicket(ticketId, assignee, dueAt ?? null), onSuccess: refresh }),
    status: useMutation({ mutationFn: ({ status, comment }: { status: string; comment?: string }) => updateTicketStatus(ticketId, status, comment), onSuccess: refresh }),
  };
}
