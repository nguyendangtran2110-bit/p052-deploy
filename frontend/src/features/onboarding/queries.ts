"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchOnboarding, fetchOnboardingProgress, updateOnboardingItem } from "@/lib/data";
import type { OnboardingItemStatus } from "@/types";

export const onboardingKeys = {
  resident: (unitId?: string) => ["onboarding", "resident", unitId ?? "all"] as const,
  management: (filters: Record<string, unknown> = {}) => ["onboarding", "management", filters] as const,
};

export function useOnboarding(unitId?: string) {
  return useQuery({
    queryKey: onboardingKeys.resident(unitId),
    queryFn: () => fetchOnboarding(unitId),
  });
}

export function useUpdateOnboardingItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, status }: { itemId: string; status: OnboardingItemStatus }) => updateOnboardingItem(itemId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["onboarding", "resident"] });
      queryClient.invalidateQueries({ queryKey: ["onboarding", "management"] });
    },
  });
}

export function useOnboardingProgress(filters: Record<string, string | number | boolean | undefined> = {}) {
  return useQuery({
    queryKey: onboardingKeys.management(filters),
    queryFn: () => fetchOnboardingProgress(filters),
  });
}
