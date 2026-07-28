import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-center" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="inspections" element={<InspectionList />} />
            <Route
              path="inspections/new"
              element={
                <ProtectedRoute roles={["technician", "supervisor", "head_maintenance", "admin"]}>
                  <NewInspection />
                </ProtectedRoute>
              }
            />
            <Route path="inspections/:id" element={<InspectionDetail />} />
            <Route path="spare-parts" element={<SpareParts />} />
            <Route path="users" element={<ProtectedRoute roles={["admin"]}><Users /></ProtectedRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
