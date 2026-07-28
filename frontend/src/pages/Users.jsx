import React, { useEffect, useState } from "react";
import api, { apiError } from "@/lib/api";
import { ROLE_LABELS } from "@/lib/meta";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { UserPlus, Trash } from "@phosphor-icons/react";
import { toast } from "sonner";

const ROLES = Object.keys(ROLE_LABELS);

export default function Users() {
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "technician" });

  const load = () => api.get("/users").then((r) => setUsers(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const create = async () => {
    try {
      await api.post("/users", form);
      toast.success("Pengguna dibuat");
      setOpen(false);
      setForm({ name: "", email: "", password: "", role: "technician" });
      load();
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail));
    }
  };

  const del = async (id) => {
    if (!window.confirm("Hapus pengguna?")) return;
    await api.delete(`/users/${id}`);
    load();
  };

  return (
    <div className="space-y-5" data-testid="users-page">
      <div className="flex items-end justify-between">
        <div>
          <p className="overline text-accent">Administrasi</p>
          <h1 className="font-head text-2xl font-extrabold tracking-tight text-primary">Manajemen Pengguna</h1>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-user" className="bg-accent hover:bg-accent/90"><UserPlus size={16} className="mr-1" /> Tambah</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Tambah Pengguna</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div><Label className="text-xs">Nama</Label><Input value={form.name} data-testid="user-name" onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1" /></div>
              <div><Label className="text-xs">Email</Label><Input type="email" value={form.email} data-testid="user-email" onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1" /></div>
              <div><Label className="text-xs">Password</Label><Input type="password" value={form.password} data-testid="user-password" onChange={(e) => setForm({ ...form, password: e.target.value })} className="mt-1" /></div>
              <div>
                <Label className="text-xs">Role</Label>
                <select value={form.role} data-testid="user-role" onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="mt-1 h-10 w-full rounded-md border border-input bg-white px-3 text-sm">
                  {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                </select>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={create} data-testid="save-user" className="bg-primary">Simpan</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-2.5 md:grid-cols-2">
        {users.map((u) => (
          <Card key={u.id} className="flex items-center justify-between border-border p-4" data-testid={`user-${u.id}`}>
            <div>
              <p className="font-semibold text-primary">{u.name}</p>
              <p className="text-[11px] text-muted-foreground">{u.email}</p>
              <span className="mt-1 inline-block rounded bg-secondary px-1.5 py-0.5 text-[10px] font-semibold text-primary">{ROLE_LABELS[u.role]}</span>
            </div>
            {u.role !== "admin" && (
              <Button variant="ghost" size="icon" onClick={() => del(u.id)} data-testid={`del-user-${u.id}`} className="text-red-500">
                <Trash size={16} />
              </Button>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
