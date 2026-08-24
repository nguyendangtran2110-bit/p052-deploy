"use client";

import { Plus, ShieldCheck, UserCog } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge, Button, Card, Input, PageHeader, Select } from "@/components/ui";
import { useManagementAccounts, useManagementMutations } from "@/features/management/queries";
import { fetchAccount } from "@/lib/data";
import { formatDate, initials, label } from "@/lib/format";
import type { ManagementRole } from "@/types";
import { useUiStore } from "@/stores/ui-store";

export default function AccountsPage() {
  const auth = useQuery({ queryKey: ["auth", "me"], queryFn: fetchAccount });
  const isAdmin = auth.data?.role === "management" && auth.data.management_profile?.management_role === "admin";
  const [filters, setFilters] = useState({ status: "", management_role: "" });
  const accounts = useManagementAccounts({ status: filters.status || undefined, management_role: filters.management_role || undefined }, isAdmin);
  const mutations = useManagementMutations();
  const showToast = useUiStore((state) => state.showToast);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", employee_code: "", password: "", management_role: "manager" as ManagementRole });
  async function create() {
    if (!form.email || !form.full_name || !form.employee_code || form.password.length < 12) return showToast({ tone: "error", message: "Nhập đủ email, họ tên, employee code và password tối thiểu 12 ký tự." });
    try { await mutations.createAccount.mutateAsync(form); setShowForm(false); setForm({ email: "", full_name: "", employee_code: "", password: "", management_role: "manager" }); showToast({ tone: "success", message: "Management account đã được tạo." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể tạo account." }); }
  }
  async function toggleStatus(id: string, status: "active" | "disabled") {
    try { await mutations.updateAccount.mutateAsync({ id, payload: { status } }); showToast({ tone: "success", message: "Account status đã cập nhật." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể cập nhật account." }); }
  }
  async function remove(id: string) {
    if (!window.confirm("Xóa management account này?")) return;
    try { await mutations.deleteAccount.mutateAsync(id); showToast({ tone: "success", message: "Account đã được xóa." }); }
    catch (error) { showToast({ tone: "error", message: error instanceof Error ? error.message : "Không thể xóa account." }); }
  }
  if (!isAdmin && !auth.isLoading) return <div className="error-state">Chỉ admin mới được quản lý management accounts.</div>;
  return <><PageHeader eyebrow="Management / Accounts" title="Management accounts" description="Chỉ admin được tạo, đổi role, disable hoặc xóa management account. Role mặc định khi tạo mới là manager." actions={<Button onClick={() => setShowForm((value) => !value)}><Plus size={16} /> Tạo account</Button>} />{showForm && <div style={{ marginBottom: 18 }}><Card><div className="section-heading"><div><h2>Tạo management account</h2><p>Password chỉ tồn tại trong state tới thời điểm submit.</p></div><UserCog size={18} color="var(--primary)" /></div><div className="form-grid form-grid-two"><Input label="Họ tên" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} /><Input label="Employee code" value={form.employee_code} onChange={(event) => setForm({ ...form, employee_code: event.target.value })} /><Input label="Email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /><Input label="Password" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /><Select label="Management role" value={form.management_role} onChange={(event) => setForm({ ...form, management_role: event.target.value as ManagementRole })}><option value="manager">Manager</option><option value="staff">Staff</option><option value="admin">Admin</option></Select></div><div className="form-actions" style={{ marginTop: 16 }}><Button variant="ghost" onClick={() => setShowForm(false)}>Hủy</Button><Button onClick={() => void create()} disabled={mutations.createAccount.isPending}>Tạo account</Button></div></Card></div>}<Card padding={false}><div className="filter-bar" style={{ margin: 16 }}><Select aria-label="Status" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">Mọi status</option><option value="active">Active</option><option value="disabled">Disabled</option></Select><Select aria-label="Role" value={filters.management_role} onChange={(event) => setFilters({ ...filters, management_role: event.target.value })}><option value="">Mọi role</option><option value="admin">Admin</option><option value="manager">Manager</option><option value="staff">Staff</option></Select><ShieldCheck size={16} color="var(--primary)" /><span className="form-help">Filter status/role được gửi server; backend chưa có search text.</span></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Account</th><th>Role</th><th>Status</th><th>Email verified</th><th>Last login</th><th>Actions</th></tr></thead><tbody>{(accounts.data?.items ?? []).map((account) => <tr key={account.id}><td><div style={{ display: "flex", alignItems: "center", gap: 9 }}><div className="avatar avatar-small">{initials(account.management_profile?.full_name)}</div><div><div className="row-title">{account.management_profile?.full_name ?? "—"}</div><div className="row-subtitle">{account.email} · {account.management_profile?.employee_code}</div></div></div></td><td><Badge tone={account.management_profile?.management_role === "admin" ? "purple" : account.management_profile?.management_role === "manager" ? "info" : "neutral"}>{label(account.management_profile?.management_role)}</Badge></td><td><Badge tone={account.status === "active" ? "success" : "danger"}>{label(account.status)}</Badge></td><td>{account.email_verified_at ? <span style={{ color: "var(--success)" }}>Đã xác thực</span> : <span style={{ color: "var(--muted)" }}>Chưa xác thực</span>}</td><td>{formatDate(account.last_login_at)}</td><td><div style={{ display: "flex", gap: 6 }}>{account.status === "active" ? <Button size="sm" variant="outline" onClick={() => void toggleStatus(account.id, "disabled")} disabled={mutations.updateAccount.isPending}>Disable</Button> : <Button size="sm" variant="outline" onClick={() => void toggleStatus(account.id, "active")} disabled={mutations.updateAccount.isPending}>Enable</Button>}<Button size="sm" variant="danger" onClick={() => void remove(account.id)} disabled={mutations.deleteAccount.isPending}>Delete</Button></div></td></tr>)}</tbody></table></div>{!accounts.isLoading && !accounts.data?.items.length && <div className="empty-state"><p>Không có account phù hợp filter server.</p></div>}</Card></>;
}
