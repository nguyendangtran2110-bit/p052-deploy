"use client";

import { Building2, Plus } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, Input, PageHeader, Select } from "@/components/ui";
import { useManagementMutations, useUnits } from "@/features/management/queries";
import { useUiStore } from "@/stores/ui-store";

export default function UnitsPage() {
  const [showForm, setShowForm] = useState(false);
  const units = useUnits({ offset: 0, limit: 100 });
  const mutations = useManagementMutations();
  const showToast = useUiStore((state) => state.showToast);
  const [form, setForm] = useState({ project_code: "", building: "", floor: "", unit_number: "" });
  async function create() {
    if (!form.project_code || !form.building || !form.unit_number) return showToast({ tone: "error", message: "Project, building và unit number là bắt buộc." });
    try { await mutations.createUnit.mutateAsync({ ...form, floor: form.floor || null }); setShowForm(false); setForm({ project_code: "", building: "", floor: "", unit_number: "" }); showToast({ tone: "success", message: "Unit đã được tạo." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tạo unit." }); }
  }
  return <AppShell><PageHeader eyebrow="Management / Units" title="Units" description="Danh sách unit phục vụ resident profile, ticket routing và announcement audience. API hỗ trợ offset/limit, không có search text." actions={<Button onClick={() => setShowForm((value) => !value)}><Plus size={16} /> Tạo unit</Button>} />{showForm && <div style={{ marginBottom: 18 }}><Card><div className="section-heading"><div><h2>Tạo unit</h2><p>POST /units với project_code, building, floor và unit_number.</p></div><Building2 size={18} color="#087f77" /></div><div className="form-grid form-grid-two"><Input label="Project code" value={form.project_code} onChange={(event) => setForm({ ...form, project_code: event.target.value })} /><Input label="Building" value={form.building} onChange={(event) => setForm({ ...form, building: event.target.value })} /><Input label="Floor" value={form.floor} onChange={(event) => setForm({ ...form, floor: event.target.value })} /><Input label="Unit number" value={form.unit_number} onChange={(event) => setForm({ ...form, unit_number: event.target.value })} /></div><div className="form-actions"><Button variant="ghost" onClick={() => setShowForm(false)}>Hủy</Button><Button onClick={() => void create()} disabled={mutations.createUnit.isPending}>Tạo unit</Button></div></Card></div>}<Card padding={false}><div className="filter-bar" style={{ margin: 16 }}><span className="form-help">Đang hiển thị danh sách server với limit 100.</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Unit</th><th>Project</th><th>Floor</th><th>Status</th><th>Updated</th></tr></thead><tbody>{(units.data ?? []).map((unit) => <tr key={unit.id}><td><div style={{ display: "flex", alignItems: "center", gap: 9 }}><div className="file-icon"><Building2 size={14} /></div><div><div className="row-title">{unit.unit_number}</div><div className="row-subtitle">Tòa {unit.building}</div></div></div></td><td>{unit.project_code}</td><td>{unit.floor ?? "—"}</td><td><Badge tone={unit.is_active ? "success" : "neutral"}>{unit.is_active ? "Active" : "Inactive"}</Badge></td><td>{new Date(unit.updated_at).toLocaleDateString("vi-VN")}</td></tr>)}</tbody></table></div>{units.isError && <div className="error-state">Không thể tải units.</div>}{!units.isLoading && !units.data?.length && <div className="empty-state"><p>Chưa có unit.</p></div>}</Card></AppShell>;
}
