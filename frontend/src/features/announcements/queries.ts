"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { archiveAnnouncement, createAnnouncement, deleteAnnouncement, fetchAnnouncement, fetchAnnouncementStatistics, fetchAnnouncements, fetchUnreadCount, markAnnouncementRead, publishAnnouncement, updateAnnouncement } from "@/lib/data";
import type { AnnouncementCreateInput, AnnouncementUpdateInput } from "@/lib/data";

export const announcementKeys = {
  all: ["announcements"] as const,
  list: (scope: "resident" | "management", filters: Record<string, unknown>) => ["announcements", "list", scope, filters] as const,
  detail: (id: string) => ["announcement", id] as const,
  unread: ["announcements", "unread-count"] as const,
  statistics: (id: string) => ["announcement", id, "statistics"] as const,
};

export function useAnnouncements(filters: Record<string, string | number | boolean | undefined> = {}, management = false) {
  const scope = management ? "management" : "resident";
  return useQuery({ queryKey: announcementKeys.list(scope, filters), queryFn: () => fetchAnnouncements(filters, management) });
}

export function useAnnouncement(id: string, management = false) {
  return useQuery({ queryKey: announcementKeys.detail(id), queryFn: () => fetchAnnouncement(id, management), enabled: Boolean(id) });
}

export function useUnreadCount() {
  return useQuery({ queryKey: announcementKeys.unread, queryFn: fetchUnreadCount });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: markAnnouncementRead,
    onSuccess: (_result, id) => {
      queryClient.invalidateQueries({ queryKey: announcementKeys.unread, exact: true });
      queryClient.invalidateQueries({ queryKey: ["announcements", "list", "resident"] });
      queryClient.invalidateQueries({ queryKey: announcementKeys.detail(id), exact: true });
    },
  });
}

export function useAnnouncementMutations(id?: string) {
  const queryClient = useQueryClient();
  const refresh = (item?: { id?: string }) => {
    if (item?.id) {
      queryClient.setQueryData(announcementKeys.detail(item.id), item);
    }
    queryClient.invalidateQueries({ queryKey: ["announcements", "list", "management"] });
    queryClient.invalidateQueries({ queryKey: ["announcements", "list", "resident"] });
    if (id) queryClient.invalidateQueries({ queryKey: announcementKeys.statistics(id), exact: true });
  };
  return {
    create: useMutation({ mutationFn: (payload: AnnouncementCreateInput) => createAnnouncement(payload), onSuccess: refresh }),
    update: useMutation({ mutationFn: (payload: AnnouncementUpdateInput) => updateAnnouncement(id ?? "", payload), onSuccess: refresh }),
    publish: useMutation({ mutationFn: (version: number) => publishAnnouncement(id ?? "", version), onSuccess: refresh }),
    archive: useMutation({ mutationFn: (version: number) => archiveAnnouncement(id ?? "", version), onSuccess: refresh }),
    remove: useMutation({ mutationFn: () => deleteAnnouncement(id ?? ""), onSuccess: () => refresh() }),
    statistics: useQuery({ queryKey: announcementKeys.statistics(id ?? ""), queryFn: () => fetchAnnouncementStatistics(id ?? ""), enabled: Boolean(id) }),
  };
}
