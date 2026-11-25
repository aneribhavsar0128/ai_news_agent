import { useEffect, useMemo, useState } from "react";

import NewsCard from "../components/NewsCard";
import { getNews, refreshNews } from "../api/api";

const CATEGORY_FILTERS = [
  {
    key: "all",
    label: "All News",
  },
  {
    key: "india",
    label: "India",
  },
  {
    key: "world",
    label: "World",
  },
  {
    key: "technology",
    label: "AI & Technology",
  },
  {
    key: "business",
    label: "Business",
  },
  {
    key: "health",
    label: "Health & Science",
  },
];

function getArticleSection(article) {
  const text = [
    article.title,
    article.category,
    article.tags,
    article.source,
    article.summary,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (
    [
      "artificial intelligence",
      "openai",
      "machine learning",
      "technology",
      "software",
      "cybersecurity",
      "robotics",
      "nvidia",
      "semiconductor",
      "cloud",
      "digital",
      " ai ",
    ].some((keyword) => text.includes(keyword))
  ) {
    return "technology";
  }

  if (
    [
      "business",
      "economy",
      "economic",
      "finance",
      "financial",
      "market",
      "stock",
      "investment",
      "bank",
      "trade",
      "gdp",
    ].some((keyword) => text.includes(keyword))
  ) {
    return "business";
  }

  if (
    [
      "health",
      "medical",
      "science",
      "climate",
      "weather",
      "heatwave",
      "nasa",
      "medicine",
      "research",
    ].some((keyword) => text.includes(keyword))
  ) {
    return "health";
  }

  if (
    [
      "india",
      "indian",
      "delhi",
      "mumbai",
      "modi",
      "rbi",
      "isro",
    ].some((keyword) => text.includes(keyword))
  ) {
    return "india";
  }

  return "world";
}

function News() {
  const [articles, setArticles] = useState([]);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [sortOrder, setSortOrder] = useState("latest");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadNews = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await getNews();
      setArticles(response.data || []);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          requestError.message ||
          "Could not load the news articles."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNews();
  }, []);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError("");
      await refreshNews();
      const response = await getNews();
      setArticles(response.data || []);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          requestError.message ||
          "Could not refresh the news articles."
      );
    } finally {
      setRefreshing(false);
    }
  };

  const filteredArticles = useMemo(() => {
    const query = search.trim().toLowerCase();

    const filtered = articles.filter((article) => {
      const articleSection = getArticleSection(article);

      const matchesCategory =
        activeCategory === "all" ||
        articleSection === activeCategory;

      const searchableText = [
        article.title,
        article.summary,
        article.category,
        article.source,
        article.tags,
        article.why_it_matters,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !query || searchableText.includes(query);

      return matchesCategory && matchesSearch;
    });

    return [...filtered].sort((first, second) => {
      const timeFirst =
        new Date(first.published_at || first.created_at || 0).getTime() || 0;
      const timeSecond =
        new Date(second.published_at || second.created_at || 0).getTime() || 0;

      if (sortOrder === "latest") {
        return timeSecond - timeFirst;
      }

      if (sortOrder === "oldest") {
        return timeFirst - timeSecond;
      }

      const scoreDiff =
        (second.importance_score || 0) -
        (first.importance_score || 0);

      if (scoreDiff !== 0) {
        return scoreDiff;
      }

      return timeSecond - timeFirst;
    });
  }, [articles, search, activeCategory, sortOrder]);

  return (
    <section className="news-page">
      <div className="page-heading news-page-heading">
        <div>
          <p className="eyebrow">News Intelligence</p>
          <h1>Latest Collected News</h1>
          <p>
            Browse processed stories, AI insights, priorities,
            and source references.
          </p>
        </div>

        <div className="news-count-badge">
          <strong>{filteredArticles.length}</strong>
          <span>articles shown</span>
        </div>
      </div>

      <div className="news-toolbar">
        <div className="news-search-wrapper">
          <span className="news-search-icon">⌕</span>

          <input
            className="news-search-input"
            type="search"
            placeholder="Search by headline, source, category, or keyword..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />

          {search && (
            <button
              type="button"
              className="clear-search-button"
              onClick={() => setSearch("")}
              aria-label="Clear search"
            >
              ×
            </button>
          )}
        </div>

        <select
          className="news-sort-select"
          value={sortOrder}
          onChange={(event) =>
            setSortOrder(event.target.value)
          }
        >
          <option value="latest">Newest first</option>
          <option value="importance">
            Highest importance
          </option>
          <option value="oldest">Oldest first</option>
        </select>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing || loading}
          style={{
            padding: "9px 18px",
            borderRadius: "8px",
            fontWeight: 600,
            cursor: refreshing ? "wait" : "pointer",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            background: refreshing ? "#4b5563" : "#3b82f6",
            color: "#ffffff",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "14px",
            whiteSpace: "nowrap",
            transition: "background 0.2s ease"
          }}
        >
          {refreshing ? "Fetching Latest..." : "↻ Fetch Latest News"}
        </button>
      </div>

      <div className="news-filter-row">
        {CATEGORY_FILTERS.map((category) => (
          <button
            key={category.key}
            type="button"
            className={
              activeCategory === category.key
                ? "news-filter-button active"
                : "news-filter-button"
            }
            onClick={() =>
              setActiveCategory(category.key)
            }
          >
            {category.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="error-message">
          <strong>Unable to load news</strong>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="news-loading-grid">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              className="news-skeleton-card"
              key={index}
            >
              <div className="skeleton-line small" />
              <div className="skeleton-line title" />
              <div className="skeleton-line" />
              <div className="skeleton-line" />
              <div className="skeleton-line short" />
            </div>
          ))}
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="news-empty-state">
          <span>⌕</span>
          <h2>No matching stories</h2>
          <p>
            Try another search term or choose a different
            category.
          </p>

          <button
            type="button"
            onClick={() => {
              setSearch("");
              setActiveCategory("all");
            }}
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="news-card-grid-modern">
          {filteredArticles.slice(0, 100).map((article) => (
            <NewsCard
              key={article.id}
              article={article}
              section={getArticleSection(article)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default News;