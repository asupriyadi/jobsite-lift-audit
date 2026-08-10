import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import NewInspection from "@/pages/NewInspection";
import InspectionList from "@/pages/InspectionList";
import InspectionDetail from "@/pages/InspectionDetail";
import SpareParts from "@/pages/SpareParts";
import Users from "@/pages/Users";
import NewReportChooser from "@/pages/NewReportChooser";
import NewECR from "@/pages/NewECR";
import NewHOR from "@/pages/NewHOR";
import ReportsList from "@/pages/ReportsList";
import ReportDetail from "@/pages/ReportDetail";

function AuthCallback() {
  const { googleSession } = useAuth();
  const navigate = useNavigate();
  const done = useRef(false);
  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const sid = new URLSearchParams(window.location.hash.replace("#", "")).get("session_id");
    if (!sid) { navigate("/login", { replace: true }); return; }
    googleSession(sid)
      .then(() => navigate("/", { replace: true }))
      .catch(() => navigate("/login", { replace: true }));
    // eslint-disable-next-line
  }, []);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="animate-pulse text-sm text-muted-foreground">Menyelesaikan login Google…</div>
    </div>
  );
}

function RootRoutes() {
  const location = useLocation();
  if (location.hash?.includes("session_id=")) return <AuthCallback />;
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="inspections" element={<InspectionList />} />
        <Route
          path="reports/new"
          element={
            <ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}>
              <NewReportChooser />
            </ProtectedRoute>
          }
        />
        <Route
          path="inspections/new"
          element={
            <ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}>
              <NewInspection />
            </ProtectedRoute>
          }
        />
        <Route
          path="inspections/:id/edit"
          element={
            <ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}>
              <NewInspection />
            </ProtectedRoute>
          }
        />
        <Route path="inspections/:id" element={<InspectionDetail />} />
        <Route path="reports" element={<ReportsList />} />
        <Route path="reports/ecr/new" element={<ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}><NewECR /></ProtectedRoute>} />
        <Route path="reports/ecr/:id/edit" element={<ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}><NewECR /></ProtectedRoute>} />
        <Route path="reports/hor/new" element={<ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}><NewHOR /></ProtectedRoute>} />
        <Route path="reports/hor/:id/edit" element={<ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}><NewHOR /></ProtectedRoute>} />
        <Route path="reports/:id" element={<ReportDetail />} />
        <Route path="spare-parts" element={<SpareParts />} />
        <Route path="users" element={<ProtectedRoute roles={["admin"]}><Users /></ProtectedRoute>} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-center" richColors />
      <BrowserRouter>
        <RootRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
