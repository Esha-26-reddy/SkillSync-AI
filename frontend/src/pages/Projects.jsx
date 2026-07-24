import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import client from "../api/client";

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [skillsText, setSkillsText] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  function load() {
    client.get("/projects").then((res) => setProjects(res.data));
  }

  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      const required_skills = skillsText.split(",").map((s) => s.trim()).filter(Boolean);
      await client.post("/projects", { name, description, required_skills });
      setName(""); setDescription(""); setSkillsText("");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create project.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this project?")) return;
    await client.delete(`/projects/${id}`);
    load();
  }

  return (
    <Layout>
      <div className="page-header">
        <div>
          <div className="eyebrow">Project Staffing</div>
          <h1>Projects & Matching</h1>
          <p className="subtitle">Describe what a project needs. SkillSync AI forms a Shadow Squad from verified internal talent and a Bridge Learning Plan for any gaps.</p>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">New project requirement</div>
          {error && <div className="error-banner">{error}</div>}
          <form onSubmit={handleCreate}>
            <label>Project name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
            <label>Description (optional)</label>
            <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
            <label>Required skills (comma-separated)</label>
            <input
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              placeholder="e.g. python, react, docker, security"
              required
            />
            <button className="btn btn-primary" disabled={creating}>{creating ? "Creating..." : "Create project"}</button>
          </form>
        </div>

        <div className="card">
          <div className="card-title">All projects ({projects.length})</div>
          {projects.length === 0 ? (
            <div className="empty-state">No projects yet.</div>
          ) : (
            projects.map((p) => (
              <div key={p.id} style={{ padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{p.name}</div>
                  <div style={{ display: "flex", gap: 12 }}>
                    <Link to={`/projects/${p.id}`}>View match &rarr;</Link>
                    <button className="btn btn-ghost" style={{ padding: "4px 8px" }} onClick={() => handleDelete(p.id)}>Delete</button>
                  </div>
                </div>
                <div style={{ marginTop: 6 }}>
                  {p.required_skills.map((s) => <span key={s} className="pill" style={{ marginRight: 6 }}>{s}</span>)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}
