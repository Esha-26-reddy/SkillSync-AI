import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import client from "../api/client";

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [form, setForm] = useState({ name: "", email: "", github_username: "", title: "" });
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  function load() {
    client.get("/employees").then((res) => setEmployees(res.data));
  }

  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      await client.post("/employees", form);
      setForm({ name: "", email: "", github_username: "", title: "" });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create employee.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Remove this employee?")) return;
    await client.delete(`/employees/${id}`);
    load();
  }

  return (
    <Layout>
      <div className="page-header">
        <div>
          <div className="eyebrow">Talent</div>
          <h1>Employees</h1>
          <p className="subtitle">Add employees, then sync their GitHub activity and mock Jira/ServiceNow work to build their Verified Skill Graph.</p>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Add an employee</div>
          {error && <div className="error-banner">{error}</div>}
          <form onSubmit={handleCreate}>
            <label>Full name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            <label>Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            <label>Job title (optional)</label>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <label>GitHub username (optional, needed for sync)</label>
            <input value={form.github_username} onChange={(e) => setForm({ ...form, github_username: e.target.value })} placeholder="e.g. octocat" />
            <button className="btn btn-primary" disabled={creating}>{creating ? "Adding..." : "Add employee"}</button>
          </form>
        </div>

        <div className="card">
          <div className="card-title">All employees ({employees.length})</div>
          {employees.length === 0 ? (
            <div className="empty-state">No employees yet.</div>
          ) : (
            employees.map((e) => (
              <div key={e.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                <div>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{e.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{e.title || e.email}</div>
                </div>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <Link to={`/employees/${e.id}`}>View graph</Link>
                  <button className="btn btn-ghost" style={{ padding: "4px 8px" }} onClick={() => handleDelete(e.id)}>Remove</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}
