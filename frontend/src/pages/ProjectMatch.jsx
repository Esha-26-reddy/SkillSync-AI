import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import Layout from "../components/Layout";
import client from "../api/client";

export default function ProjectMatch() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [matching, setMatching] = useState(false);

  useEffect(() => {
    client.get("/projects").then((res) => {
      const p = res.data.find((x) => x.id === id);
      setProject(p);
      if (p?.last_match_result) setResult(p.last_match_result);
    });
  }, [id]);

  async function runMatch() {
    setError("");
    setMatching(true);
    try {
      const res = await client.post(`/projects/${id}/match`);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Matching failed.");
    } finally {
      setMatching(false);
    }
  }

  if (!project) {
    return (
      <Layout>
        <p style={{ color: "var(--text-muted)" }}><span className="loading-dot" /> Loading...</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="page-header">
        <div>
          <div className="eyebrow">Project Match</div>
          <h1>{project.name}</h1>
          <p className="subtitle">{project.description}</p>
          <div style={{ marginTop: 8 }}>
            {project.required_skills.map((s) => <span key={s} className="pill" style={{ marginRight: 6 }}>{s}</span>)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Link to="/projects" className="btn btn-secondary">&larr; Back</Link>
          <button className="btn btn-primary" onClick={runMatch} disabled={matching}>
            {matching ? "Matching..." : result ? "Re-run match" : "Form Shadow Squad"}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!result && !error && (
        <div className="empty-state card">Click "Form Shadow Squad" to match verified skills against this project's requirements.</div>
      )}

      {result && (
        <>
          <div className="card">
            <div className="card-title">Shadow Squad ({result.shadow_squad.length} people)</div>
            {result.shadow_squad.length === 0 ? (
              <div className="empty-state">No employees matched any required skill.</div>
            ) : (
              result.shadow_squad.map((m) => (
                <div key={m.employee_id} style={{ borderBottom: "1px solid var(--border)", padding: "14px 0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Link to={`/employees/${m.employee_id}`} style={{ fontWeight: 600, fontSize: 15 }}>{m.name}</Link>
                    <span className="pill verified">match score {m.match_score}</span>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    {m.matched_skills.map((s) => (
                      <span key={s} className="pill verified" style={{ marginRight: 6 }}>{s} · verified</span>
                    ))}
                    {m.adjacent_skills.map((s) => (
                      <span key={s} className="pill signal" style={{ marginRight: 6 }}>{s} · transferable</span>
                    ))}
                  </div>
                  {m.evidence_highlights.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      {m.evidence_highlights.map((h, i) => (
                        <div key={i} className="evidence-snippet">{h}</div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {result.bridge_learning_plan.length > 0 && (
            <div className="card">
              <div className="card-title">Bridge Learning Plan (skill gaps)</div>
              {result.bridge_learning_plan.map((plan) => (
                <div key={plan.skill} style={{ borderBottom: "1px solid var(--border)", padding: "12px 0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span className="pill signal">{plan.skill}</span>
                    {plan.suggested_mentor && (
                      <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Suggested mentor: <b style={{ color: "var(--text)" }}>{plan.suggested_mentor}</b></span>
                    )}
                  </div>
                  <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 13 }}>
                    {plan.resources.map((r, i) => (
                      <li key={i}><a href={r.url} target="_blank" rel="noreferrer">{r.title}</a></li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          {result.other_candidates.length > 0 && (
            <div className="card">
              <div className="card-title">Other candidates considered</div>
              <table>
                <thead><tr><th>Name</th><th>Matched skills</th><th>Score</th></tr></thead>
                <tbody>
                  {result.other_candidates.map((c) => (
                    <tr key={c.employee_id}>
                      <td><Link to={`/employees/${c.employee_id}`}>{c.name}</Link></td>
                      <td>{c.matched_skills.join(", ") || "—"}</td>
                      <td>{c.match_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
