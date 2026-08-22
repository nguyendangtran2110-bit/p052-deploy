"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchManagementOnboarding, fetchResidentOnboarding, updateOnboardingItem } from "@/lib/data";
import type { OnboardingUpdateStatus } from "@/types";

export const onboardingKeys = {
  resident: (unitId?: string) => ["onboarding", "resident", unitId ?? "all"] as const,
  management: (filters: Record<string, unknown>) => ["onboarding", "management", filters] as const,
};

export function useResidentOnboarding(unitId?: string) {
  return useQuery({ queryKey: onboardingKeys.resident(unitId), queryFn: () => fetchResidentOnboarding(unitId) });
}

export function useUpdateOnboardingItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: OnboardingUpdateStatus }) => updateOnboardingItem(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["onboarding"] }),
  });
}

export function useManagementOnboarding(filters: { search?: string; building?: string; is_completed?: boolean; offset?: number; limit?: number } = {}) {
  return useQuery({ queryKey: onboardingKeys.management(filters), queryFn: () => fetchManagementOnboarding(filters) });
}
