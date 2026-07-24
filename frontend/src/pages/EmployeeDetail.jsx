import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Layout from "../components/Layout";
import ConfidenceRing from "../components/ConfidenceRing";
import client from "../api/client";

export default function EmployeeDetail() {
  const { id } = useParams();
  const [employee, setEmployee] = useState(null);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const [githubForm, setGithubForm] = useState({ github_username: "", repo: "", max_items: 50 });
  const [mockForm, setMockForm] = useState({ num_jira_tickets: 10, num_servicenow_tickets: 5 });

  function load() {
    client.get(`/employees/${id}`).then((res) => {
      setEmployee(res.data);
      setGithubForm((f) => ({ ...f, github_username: res.data.github_username || "" }));
    });
  }

  useEffect(load, [id]);

  async function handleGithubSync(e) {
    e.preventDefault();
    setError("");
    setSyncing(true);
    try {
      await client.post("/github/sync", { employee_id: id, ...githubForm });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "GitHub sync failed. Check the repo name and your GITHUB_TOKEN.");
    } finally {
      setSyncing(false);
    }
  }

  async function handleMockSeed(e) {
    e.preventDefault();
    setError("");
    setSeeding(true);
    try {
      await client.post("/mock-data/seed", { employee_id: id, ...mockForm });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not seed mock data.");
    } finally {
      setSeeding(false);
    }
  }

  if (!employee) {
    return (
      <Layout>
        <p style={{ color: "var(--text-muted)" }}><span className="loading-dot" /> Loading...</p>
      </Layout>
    );
  }

  const sortedSkills = [...(employee.skills || [])].sort((a, b) => b.confidence_score - a.confidence_score);
  const activeSkill = selectedSkill
    ? sortedSkills.find((s) => s.skill === selectedSkill)
    : sortedSkills[0];

  return (
    <Layout>
      <div className="page-header">
        <div>
          <div className="eyebrow">Verified Skill Graph</div>
          <h1>{employee.name}</h1>
          <p className="subtitle">{employee.title || employee.email}</p>
        </div>
        <Link to="/employees" className="btn btn-secondary">&larr; Back to employees</Link>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Sync real GitHub activity</div>
          <form onSubmit={handleGithubSync}>
            <label>GitHub username</label>
            <input value={githubForm.github_username} onChange={(e) => setGithubForm({ ...githubForm, github_username: e.target.value })} required />
            <label>Repository (owner/repo)</label>
            <input value={githubForm.repo} onChange={(e) => setGithubForm({ ...githubForm, repo: e.target.value })} placeholder="e.g. facebook/react" required />
            <button className="btn btn-primary" disabled={syncing}>{syncing ? "Syncing commits & PRs..." : "Sync GitHub"}</button>
          </form>
        </div>

        <div className="card">
          <div className="card-title">Seed mock Jira / ServiceNow work</div>
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: -8, marginBottom: 12 }}>
            Simulates ticket history since this demo doesn't have live Jira/ServiceNow credentials.
          </p>
          <form onSubmit={handleMockSeed}>
            <label>Number of Jira tickets</label>
            <input type="number" min="1" max="50" value={mockForm.num_jira_tickets} onChange={(e) => setMockForm({ ...mockForm, num_jira_tickets: +e.target.value })} />
            <label>Number of ServiceNow tickets</label>
            <input type="number" min="0" max="50" value={mockForm.num_servicenow_tickets} onChange={(e) => setMockForm({ ...mockForm, num_servicenow_tickets: +e.target.value })} />
            <button className="btn btn-secondary" disabled={seeding}>{seeding ? "Seeding..." : "Seed mock data"}</button>
          </form>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title">Skill confidence breakdown</div>
        {sortedSkills.length === 0 ? (
          <div className="empty-state">No skills detected yet. Sync GitHub or seed mock data above.</div>
        ) : (
          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            <ConfidenceRing skill={activeSkill} />
            <div style={{ flex: 1, minWidth: 260 }}>
              {sortedSkills.map((s) => (
                <div
                  key={s.skill}
                  className="skill-row"
                  style={{ cursor: "pointer", background: activeSkill?.skill === s.skill ? "var(--panel-raised)" : "transparent", borderRadius: 8, paddingLeft: 8 }}
                  onClick={() => setSelectedSkill(s.skill)}
                >
                  <span className="skill-name">{s.skill}</span>
                  <div className="bar-track"><div className="bar-fill" style={{ width: `${s.confidence_score}%` }} /></div>
                  <span className="score-num">{Math.round(s.confidence_score)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {activeSkill && (
        <div className="card">
          <div className="card-title">Evidence for "{activeSkill.skill}" ({activeSkill.evidence_count} contributions)</div>
          {activeSkill.evidence.map((ev, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <span className={`pill ${ev.peer_validated ? "verified" : ""}`}>{ev.source}</span>
              {ev.peer_validated && <span className="pill verified" style={{ marginLeft: 6 }}>peer validated</span>}
              <span style={{ marginLeft: 8, fontSize: 12, color: "var(--text-muted)" }}>
                {new Date(ev.date).toLocaleDateString()}
              </span>
              <div className="evidence-snippet">{ev.snippet}</div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
