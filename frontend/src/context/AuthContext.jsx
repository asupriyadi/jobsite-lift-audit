import React, { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null=loading, false=unauth, obj=auth
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (window.location.hash?.includes("session_id=")) {
      setReady(true);
      return; // AuthCallback will handle the Google session exchange
    }
    const token = localStorage.getItem("sir_token");
    if (!token) {
      setUser(false);
      setReady(true);
      return;
    }
    api
      .get("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("sir_token");
        setUser(false);
      })
      .finally(() => setReady(true));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("sir_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (payload) => {
    const { data } = await api.post("/auth/register", payload);
    localStorage.setItem("sir_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  const googleSession = async (sessionId) => {
    const { data } = await api.post("/auth/google-session", { session_id: sessionId });
    localStorage.setItem("sir_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("sir_token");
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, ready, login, register, googleSession, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
