import type { Role } from "@/src/mock/data";

type DemoScopePolicy = {
  role: Role;
  building: string;
  floors: readonly string[];
};

export const demoScopePolicy: Readonly<Record<string, DemoScopePolicy>> = Object.freeze({
  "demo-resident-lagoon": { role: "resident", building: "Harbor House", floors: ["08"] },
  "demo-resident-ember": { role: "resident", building: "Harbor House", floors: ["11"] },
  "demo-resident-harbor": { role: "resident", building: "Orchard Annex", floors: ["03"] },
  "demo-manager-eight": { role: "manager", building: "Harbor House", floors: ["08"] },
  "demo-manager-harbor": { role: "manager", building: "Harbor House", floors: ["ALL_FLOORS"] },
  "demo-manager-orchard": { role: "manager", building: "Orchard Annex", floors: ["03"] },
});

export const demoTicketScopePolicy = Object.freeze({
  "TKT-LGN-1042": { ownerId: "demo-resident-lagoon", building: "Harbor House", floor: "08", room: "0812" },
  "TKT-LGN-0981": { ownerId: "demo-resident-lagoon", building: "Harbor House", floor: "08", room: "0812" },
  "TKT-EMB-2017": { ownerId: "demo-resident-ember", building: "Harbor House", floor: "11", room: "1104" },
  "TKT-EMB-1940": { ownerId: "demo-resident-ember", building: "Harbor House", floor: "11", room: "1104" },
  "TKT-HBR-3308": { ownerId: "demo-resident-harbor", building: "Orchard Annex", floor: "03", room: "0306" },
  "TKT-HBR-3241": { ownerId: "demo-resident-harbor", building: "Orchard Annex", floor: "03", room: "0306" },
});

export const demoNotificationScopePolicy = Object.freeze({
  "NTF-LGN-01": { accountIds: ["demo-resident-lagoon", "demo-manager-eight", "demo-manager-harbor"], building: "Harbor House", floor: "08", relatedTicketId: "TKT-LGN-1042" },
  "NTF-EMB-01": { accountIds: ["demo-resident-ember", "demo-manager-harbor"], building: "Harbor House", floor: "11", relatedTicketId: "TKT-EMB-2017" },
  "NTF-HBR-01": { accountIds: ["demo-resident-harbor", "demo-manager-orchard"], building: "Orchard Annex", floor: "03" },
  "NTF-LGN-02": { accountIds: ["demo-resident-lagoon"], building: "Harbor House", floor: "08" },
});
