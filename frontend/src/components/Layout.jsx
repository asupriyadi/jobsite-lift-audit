import React from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROLE_LABELS } from "@/lib/meta";
import {
  SquaresFour, ClipboardText, Plus, Wrench, Users, SignOut, Elevator,
} from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";

const NAV = [
  { to: "/", label: "Dashboard", icon: SquaresFour, roles: null },
  { to: "/inspections/new", label: "Inspeksi Baru", icon: Plus, roles: ["technician", "supervisor", "head_maintenance", "admin"] },
  { to: "/inspections", label: "Riwayat SIR", icon: ClipboardText, roles: null },
  { to: "/spare-parts", label: "Spare Part", icon: Wrench, roles: null },
  { to: "/users", label: "Pengguna", icon: Users, roles: ["admin"] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const can = (roles) => !roles || roles.includes(user.role) || user.role === "admin";

  const doLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top bar */}
      <header className="sticky top-0 z-40 border-b border-border bg-primary text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent">
              <Elevator size={20} weight="fill" className="text-white" />
            </div>
            <div className="leading-tight">
              <p className="font-head text-sm font-extrabold tracking-tight">FUJITEC SIR</p>
              <p className="text-[10px] text-white/60">Service Inspection Report</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-semibold">{user.name}</p>
              <p className="text-[10px] text-white/60">{ROLE_LABELS[user.role]}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={doLogout} data-testid="logout-btn"
              className="text-white hover:bg-white/10 hover:text-white">
              <SignOut size={18} />
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl">
        {/* Sidebar (desktop) */}
        <aside className="hidden w-56 shrink-0 border-r border-border p-3 md:block">
          <nav className="flex flex-col gap-1">
            {NAV.filter((n) => can(n.roles)).map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                data-testid={`nav-${n.label.toLowerCase().replace(/\s+/g, "-")}`}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive ? "bg-primary text-white" : "text-slate-600 hover:bg-secondary"
                  }`
                }
              >
                <n.icon size={18} />
                {n.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 p-4 pb-24 md:p-6">
          <Outlet />
        </main>
      </div>

      {/* Bottom nav (mobile) */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-border bg-white md:hidden">
        {NAV.filter((n) => can(n.roles)).slice(0, 5).map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.to === "/"}
            data-testid={`mnav-${n.label.toLowerCase().replace(/\s+/g, "-")}`}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-medium transition-colors ${
                isActive ? "text-accent" : "text-slate-400"
              }`
            }
          >
            <n.icon size={20} />
            {n.label.split(" ")[0]}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
