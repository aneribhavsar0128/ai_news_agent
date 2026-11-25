function StatCard({ title, value, subtitle, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-icon">{icon}</span>
        <span>{title}</span>
      </div>

      <h3>{value}</h3>
      <p>{subtitle}</p>
    </div>
  );
}

export default StatCard;