import { create } from 'zustand';

export const useUIStore = create((set) => ({
  inspectorOpen: false,
  selectedDeliveryId: null,
  sidebarCollapsed: false,

  openInspector: (deliveryId) =>
    set({
      inspectorOpen: true,
      selectedDeliveryId: deliveryId,
    }),

  closeInspector: () =>
    set({
      inspectorOpen: false,
      selectedDeliveryId: null,
    }),

  toggleSidebar: () =>
    set((state) => ({
      sidebarCollapsed: !state.sidebarCollapsed,
    })),
}));

