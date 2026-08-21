"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAIWorkflow, fetchConversationById, fetchManagerAssistantConversation } from "@/lib/data";

export const aiChatKeys = {
  all: ["ai-chat"] as const,
  residentConversation: (conversationId: string) => ["ai-chat", "resident-conversation", conversationId] as const,
  managerConversation: (conversationId: string) => ["ai-chat", "manager-conversation", conversationId] as const,
  workflow: (workflowId: string) => ["ai-chat", "workflow", workflowId] as const,
};

export function useResidentAssistantConversation(conversationId?: string) {
  return useQuery({
    queryKey: aiChatKeys.residentConversation(conversationId ?? ""),
    queryFn: () => fetchConversationById(conversationId!),
    enabled: Boolean(conversationId),
  });
}

export function useManagerAssistantConversation(conversationId?: string) {
  return useQuery({
    queryKey: aiChatKeys.managerConversation(conversationId ?? ""),
    queryFn: () => fetchManagerAssistantConversation(conversationId!),
    enabled: Boolean(conversationId),
  });
}

export function useAIWorkflow(workflowId?: string) {
  return useQuery({
    queryKey: aiChatKeys.workflow(workflowId ?? ""),
    queryFn: () => fetchAIWorkflow(workflowId!),
    enabled: Boolean(workflowId),
  });
}
