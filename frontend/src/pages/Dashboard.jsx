import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import client from "../api/client";

export default function Dashboard() {
  const [employees, setEmployees] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([client.get("/employees"), client.get("/projects")])
      .then(([e, p]) => {
        setEmployees(e.data);
        setProjects(p.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const totalSkills = employees.reduce((sum, e) => sum + (e.skills?.length || 0), 0);
  const verifiedSkills = employees.reduce(
    (sum, e) => sum + (e.skills?.filter((s) => s.confidence_score >= 50).length || 0),
    0
  );

  return (
    <Layout>
      <div className="page-header">
        <div>
          <div className="eyebrow">Overview</div>
          <h1>Workforce intelligence</h1>
          <p className="subtitle">
            Real work contributions, turned into verified skill profiles across your organization.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Link to="/employees" className="btn btn-secondary">+ Add employee</Link>
          <Link to="/projects" className="btn btn-primary">+ New project</Link>
        </div>
      </div>

      {loading ? (
        <p style={{ color: "var(--text-muted)" }}><span className="loading-dot" /> Loading...</p>
      ) : (
        <>
          <div className="grid-3">
            <div className="card">
              <div className="card-title">Employees tracked</div>
              <h2 style={{ fontSize: 32 }}>{employees.length}</h2>
            </div>
            <div className="card">
              <div className="card-title">Verified skill entries</div>
              <h2 style={{ fontSize: 32, color: "var(--verified)" }}>{verifiedSkills}</h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>of {totalSkills} total detected</p>
            </div>
            <div className="card">
              <div className="card-title">Active projects</div>
              <h2 style={{ fontSize: 32 }}>{projects.length}</h2>
            </div>
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <div className="card-title">Employees</div>
            {employees.length === 0 ? (
              <div className="empty-state">
                No employees yet. <Link to="/employees">Add your first employee</Link> and sync their GitHub activity.
              </div>
            ) : (
              <table>
                <thead>
                  <tr><th>Name</th><th>Top skills</th><th>Skills tracked</th><th></th></tr>
                </thead>
                <tbody>
                  {employees.map((e) => (
                    <tr key={e.id}>
                      <td>{e.name}</td>
                      <td>
                        {(e.skills || [])
                          .slice()
                          .sort((a, b) => b.confidence_score - a.confidence_score)
                          .slice(0, 3)
                          .map((s) => (
                            <span key={s.skill} className="pill verified" style={{ marginRight: 6 }}>
                              {s.skill} · {Math.round(s.confidence_score)}
                            </span>
                          ))}
                        {(!e.skills || e.skills.length === 0) && <span style={{ color: "var(--text-muted)" }}>No data synced yet</span>}
                      </td>
                      <td>{e.skills?.length || 0}</td>
                      <td><Link to={`/employees/${e.id}`}>View graph &rarr;</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </Layout>
  );
}
