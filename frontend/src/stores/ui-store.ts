import { create } from "zustand";

interface UiState {
  sidebarOpen: boolean;
  toast: { tone: "success" | "error" | "info"; message: string } | null;
  setSidebarOpen: (open: boolean) => void;
  showToast: (toast: NonNullable<UiState["toast"]>) => void;
  clearToast: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  toast: null,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  showToast: (toast) => set({ toast }),
  clearToast: () => set({ toast: null }),
}));
