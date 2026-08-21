"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createManagementAccount, createAnnouncement, createResident, createUnit, deleteManagementAccount, deleteResidentAccount, fetchDashboard, fetchHandoffs, fetchKnowledge, fetchManagementAccounts, fetchResident, fetchResidents, fetchUnits, updateKnowledgeStatus, uploadKnowledge, updateManagementAccount, updateResident } from "@/lib/data";
import type { KnowledgeFilters } from "@/types";

export const managementKeys = {
  dashboard: ["management", "dashboard"] as const,
  handoffs: (filters: Record<string, unknown> = {}) => ["management", "handoffs", filters] as const,
  residents: (filters: Record<string, unknown> = {}) => ["management", "residents", filters] as const,
  resident: (id: string) => ["management", "resident", id] as const,
  accounts: (filters: Record<string, unknown> = {}) => ["management", "accounts", filters] as const,
  knowledge: (filters: Record<string, unknown> = {}) => ["knowledge", "documents", filters] as const,
  knowledgeDetail: (id: string) => ["knowledge", "document", id] as const,
  units: (filters: Record<string, unknown> = {}) => ["units", filters] as const,
};

export const useDashboard = () => useQuery({ queryKey: managementKeys.dashboard, queryFn: fetchDashboard });
export const useHandoffs = (filters: Record<string, string | number | undefined> = {}) => useQuery({ queryKey: managementKeys.handoffs(filters), queryFn: () => fetchHandoffs(filters) });
export const useResidents = (filters: { search?: string; is_active?: boolean; offset?: number; limit?: number } = {}) => useQuery({ queryKey: managementKeys.residents(filters), queryFn: () => fetchResidents(filters) });
export const useResident = (id: string) => useQuery({ queryKey: managementKeys.resident(id), queryFn: () => fetchResident(id), enabled: Boolean(id) });
export const useManagementAccounts = (filters: { status?: string; management_role?: string; offset?: number; limit?: number } = {}, enabled = true) => useQuery({ queryKey: managementKeys.accounts(filters), queryFn: () => fetchManagementAccounts(filters), enabled });
export const useKnowledge = (filters: KnowledgeFilters = {}) => useQuery({ queryKey: managementKeys.knowledge(filters as Record<string, unknown>), queryFn: () => fetchKnowledge(filters) });
export const useKnowledgeDocument = (id: string) => useQuery({ queryKey: managementKeys.knowledgeDetail(id), queryFn: () => import("@/lib/data").then(({ fetchKnowledgeDocument }) => fetchKnowledgeDocument(id)), enabled: Boolean(id) });
export const useUnits = (filters: { project_code?: string; building?: string; is_active?: boolean; offset?: number; limit?: number } = {}) => useQuery({ queryKey: managementKeys.units(filters), queryFn: () => fetchUnits(filters) });

export function useManagementMutations() {
  const queryClient = useQueryClient();
  const invalidateDashboard = () => queryClient.invalidateQueries({ queryKey: managementKeys.dashboard, exact: true });
  const invalidateResidents = (id?: string) => {
    queryClient.invalidateQueries({ queryKey: ["management", "residents"] });
    if (id) queryClient.invalidateQueries({ queryKey: managementKeys.resident(id), exact: true });
    invalidateDashboard();
  };
  const invalidateAccounts = () => {
    queryClient.invalidateQueries({ queryKey: ["management", "accounts"] });
    invalidateDashboard();
  };
  const invalidateKnowledge = (id?: string) => {
    queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
    if (id) queryClient.invalidateQueries({ queryKey: managementKeys.knowledgeDetail(id), exact: true });
    invalidateDashboard();
  };
  const invalidateUnits = () => {
    queryClient.invalidateQueries({ queryKey: ["units"] });
    invalidateDashboard();
  };
  return {
    createAccount: useMutation({ mutationFn: createManagementAccount, onSuccess: invalidateAccounts }),
    updateAccount: useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) => updateManagementAccount(id, payload), onSuccess: invalidateAccounts }),
    deleteAccount: useMutation({ mutationFn: deleteManagementAccount, onSuccess: invalidateAccounts }),
    createResident: useMutation({ mutationFn: createResident, onSuccess: () => invalidateResidents() }),
    updateResident: useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) => updateResident(id, payload), onSuccess: (_resident, variables) => invalidateResidents(variables.id) }),
    deleteResidentAccount: useMutation({ mutationFn: deleteResidentAccount, onSuccess: (_result, id) => invalidateResidents(id) }),
    uploadDocument: useMutation({ mutationFn: ({ file, metadata }: { file: File; metadata: { title: string; version: string; document_type: string; project_code?: string; building?: string; effective_date?: string } }) => uploadKnowledge(file, metadata), onSuccess: () => invalidateKnowledge() }),
    updateKnowledgeStatus: useMutation({ mutationFn: ({ id, status }: { id: string; status: "pending" | "indexing" | "indexed" | "failed" | "archived" }) => updateKnowledgeStatus(id, status), onSuccess: (_document, variables) => invalidateKnowledge(variables.id) }),
    createAnnouncement: useMutation({ mutationFn: createAnnouncement, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["announcements", "list", "management"] }) }),
    createUnit: useMutation({ mutationFn: createUnit, onSuccess: invalidateUnits }),
  };
}
