import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("sir_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const fileUrl = (fileId) => `${API}/files/${fileId}`;
export const pdfUrl = (id) => `${API}/inspections/${id}/pdf`;

export async function openInspectionPdf(id) {
  const { data } = await api.get(`/inspections/${id}/pdf-token`);
  window.open(`${API}/inspections/${id}/pdf?auth=${data.token}`, "_blank");
}

export async function openReportPdf(id) {
  const { data } = await api.get(`/reports/${id}/pdf-token`);
  window.open(`${API}/reports/${id}/pdf?auth=${data.token}`, "_blank");
}

export async function downloadExcel() {
  const res = await api.get(`/export/excel`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const a = document.createElement("a");
  a.href = url;
  a.download = "fujitec-reports.xlsx";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export function apiError(detail) {
  if (detail == null) return "Terjadi kesalahan. Coba lagi.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export default api;
