import { createContext, useContext, useState } from "react";
import client from "../api/client";

const TOKEN_KEY = "skillsync_token";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));

  async function login(username, password) {
    // Backend uses FastAPI's OAuth2PasswordRequestForm, which expects
    // application/x-www-form-urlencoded, not JSON.
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await client.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem(TOKEN_KEY, res.data.access_token);
    setToken(res.data.access_token);
  }

  async function register(username, password, role) {
    const res = await client.post("/auth/register", { username, password, role });
    localStorage.setItem(TOKEN_KEY, res.data.access_token);
    setToken(res.data.access_token);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
