const SECTION_LABELS = {
  india: "India",
  world: "World",
  technology: "AI & Technology",
  business: "Business",
  health: "Health & Science",
};

function formatDate(value) {
  if (!value) {
    return "Date unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function NewsCard({ article, section = "world" }) {
  const importance = article.importance_score || 0;

  const tags = (article.tags || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 3);

  return (
    <article className="news-card-modern">
      <div className="news-card-top">
        <span
          className={`news-section-badge section-${section}`}
        >
          {SECTION_LABELS[section] || "World"}
        </span>

        <div className="importance-badge">
          <span>Priority</span>
          <strong>{importance}/10</strong>
        </div>
      </div>

      <h2 className="news-card-title">
        {article.title || "Untitled news article"}
      </h2>

      <div className="news-card-source-row">
        <span>{article.source || "Unknown source"}</span>
        <span>•</span>
        <span>
          {formatDate(
            article.published_at || article.created_at
          )}
        </span>
      </div>

      <p className="news-card-summary">
        {article.summary || "No summary available."}
      </p>

      {article.why_it_matters && (
        <div className="news-insight-box">
          <span className="insight-symbol">✦</span>

          <p>
            <strong>Why it matters</strong>
            {article.why_it_matters}
          </p>
        </div>
      )}

      {tags.length > 0 && (
        <div className="news-tag-row">
          {tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
      )}

      <div className="news-card-footer">
        <span>
          {article.estimated_read_time || "1 min read"}
        </span>

        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noreferrer"
          >
            Read full story
            <span>↗</span>
          </a>
        )}
      </div>
    </article>
  );
}

export default NewsCard;