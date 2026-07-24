// Signature visual: renders the Skill Confidence Score as a ring made of
// four arcs (Frequency 30%, Complexity 30%, Recency 20%, Peer Validation 20%),
// each arc's length scaled by that sub-score. This mirrors the exact formula
// from the pitch deck and makes the "explainability" tangible at a glance.
const SIZE = 132;
const STROKE = 10;
const RADIUS = (SIZE - STROKE) / 2;
const CIRC = 2 * Math.PI * RADIUS;

const SEGMENTS = [
  { key: "frequency_score", weight: 0.3, color: "#2dd4bf", label: "Frequency" },
  { key: "complexity_score", weight: 0.3, color: "#0891b2", label: "Complexity" },
  { key: "recency_score", weight: 0.2, color: "#f5a524", label: "Recency" },
  { key: "peer_validation_score", weight: 0.2, color: "#a78bfa", label: "Peer Validation" },
];

export default function ConfidenceRing({ skill }) {
  let offset = 0;
  const arcs = SEGMENTS.map((seg) => {
    const value = skill[seg.key] || 0; // 0-100
    const arcLength = (CIRC * seg.weight) * (value / 100);
    const arc = { ...seg, value, dasharray: `${arcLength} ${CIRC - arcLength}`, dashoffset: -offset };
    offset += CIRC * seg.weight;
    return arc;
  });

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        <circle cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} fill="none" stroke="#232e4a" strokeWidth={STROKE} />
        {arcs.map((a) => (
          <circle
            key={a.key}
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={a.color}
            strokeWidth={STROKE}
            strokeDasharray={a.dasharray}
            strokeDashoffset={a.dashoffset}
            strokeLinecap="butt"
            transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
          />
        ))}
        <text x="50%" y="46%" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="26" fill="#eef1f7" fontWeight="500">
          {Math.round(skill.confidence_score)}
        </text>
        <text x="50%" y="62%" textAnchor="middle" fontFamily="Inter" fontSize="10" fill="#8b93a7">
          confidence
        </text>
      </svg>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {SEGMENTS.map((seg) => (
          <div key={seg.key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: seg.color, display: "inline-block" }} />
            <span style={{ color: "#8b93a7", flex: 1 }}>{seg.label}</span>
            <span style={{ fontFamily: "JetBrains Mono", color: "#eef1f7" }}>{Math.round(skill[seg.key] || 0)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
