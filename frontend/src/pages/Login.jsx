import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { apiError } from "@/lib/api";
import { ROLE_LABELS } from "@/lib/meta";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Elevator, SpinnerGap } from "@phosphor-icons/react";
import { toast } from "sonner";

const DEMO = [
  ["Teknisi", "teknisi@fujitec.com", "teknisi123"],
  ["Supervisor", "supervisor@fujitec.com", "super123"],
  ["Kepala Maint.", "kepala@fujitec.com", "kepala123"],
  ["Sales", "sales@fujitec.com", "sales123"],
  ["Inventory", "inventory@fujitec.com", "inv123"],
  ["Customer", "customer@fujitec.com", "cust123"],
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      toast.error(apiError(err.response?.data?.detail) || "Login gagal");
    } finally {
      setLoading(false);
    }
  };

  const quick = (em, pw) => {
    setEmail(em);
    setPassword(pw);
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left visual */}
      <div className="relative hidden lg:block">
        <img
          src="https://images.unsplash.com/photo-1621905251918-48416bd8575a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400"
          alt="Teknisi lift"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-primary/80" />
        <div className="relative flex h-full flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-accent">
              <Elevator size={22} weight="fill" />
            </div>
            <span className="font-head text-lg font-extrabold tracking-tight">FUJITEC SIR</span>
          </div>
          <div>
            <h1 className="font-head text-4xl font-extrabold leading-tight tracking-tight">
              Service Inspection Report
            </h1>
            <p className="mt-3 max-w-md text-white/70">
              Digitalisasi pemeriksaan unit lift di jobsite — checklist 1M / 3M / 12M,
              foto bukti, tanda tangan digital, dan tracking spare part terpusat.
            </p>
          </div>
          <p className="text-xs text-white/40">PT. Fujitec Indonesia · REXIA / ZEXIA</p>
        </div>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm">
          <div className="mb-6 lg:hidden">
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-md bg-primary">
              <Elevator size={24} weight="fill" className="text-white" />
            </div>
          </div>
          <p className="overline text-accent">Masuk Akun</p>
          <h2 className="font-head mt-1 text-2xl font-extrabold tracking-tight text-primary">
            Selamat datang kembali
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">Masuk untuk mengisi & memantau laporan SIR.</p>

          <form onSubmit={submit} className="mt-6 space-y-4" data-testid="login-form">
            <div>
              <Label className="text-xs">Email</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                required data-testid="login-email" placeholder="nama@fujitec.com" className="mt-1" />
            </div>
            <div>
              <Label className="text-xs">Password</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                required data-testid="login-password" placeholder="••••••" className="mt-1" />
            </div>
            <Button type="submit" disabled={loading} data-testid="login-submit"
              className="w-full bg-primary hover:bg-primary/90">
              {loading ? <SpinnerGap size={18} className="mr-2 animate-spin" /> : null}
              Masuk
            </Button>
          </form>

          <div className="mt-6">
            <p className="overline mb-2 text-muted-foreground">Akun Demo (klik untuk isi)</p>
            <div className="grid grid-cols-2 gap-1.5">
              {DEMO.map(([role, em, pw]) => (
                <button
                  key={em}
                  type="button"
                  onClick={() => quick(em, pw)}
                  data-testid={`demo-${role}`}
                  className="rounded-md border border-border bg-white px-2.5 py-1.5 text-left text-[11px] hover:border-accent"
                >
                  <span className="font-semibold text-primary">{role}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
