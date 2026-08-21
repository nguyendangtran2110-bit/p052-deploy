"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchResidentProfile } from "@/lib/data";

export const residentKeys = { profile: ["resident", "profile"] as const };
export function useResidentProfile() {
  return useQuery({ queryKey: residentKeys.profile, queryFn: fetchResidentProfile });
}
