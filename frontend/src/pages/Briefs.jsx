import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";

import {
  generateDailyBrief,
  getDailyBriefs,
} from "../api/api";


const EMPTY_BRIEF = {
  title: "Daily Brief",
  summary: "No summary available.",
  top_stories: [],
  india: [],
  world: [],
  technology_ai: [],
  business: [],
  health_science: [],
  key_trends: [],
  what_to_watch_next: [],
};


function parseBriefJson(value) {
  if (!value) {
    return {
      ...EMPTY_BRIEF,
    };
  }

  if (typeof value === "object") {
    return {
      ...EMPTY_BRIEF,
      ...value,
    };
  }

  try {
    const parsed = JSON.parse(value);

    return {
      ...EMPTY_BRIEF,
      ...parsed,
    };
  } catch (error) {
    console.error(
      "Stored brief JSON could not be parsed:",
      error
    );

    return {
      ...EMPTY_BRIEF,
      summary:
        "Stored brief data could not be parsed.",
    };
  }
}


function formatBriefDate(value) {
  if (!value) {
    return "Unknown date";
  }

  const parsedDate = new Date(
    `${value}T00:00:00`
  );

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(parsedDate);
}


function normalizeStories(stories) {
  return Array.isArray(stories)
    ? stories
    : [];
}


function StoryCard({ story }) {
  const title =
    story?.headline ||
    story?.title ||
    "Untitled story";

  return (
    <article className="brief-story-card">
      <div className="brief-story-top">
        <span>
          {story?.category || "General"}
        </span>

        {story?.importance_score !== undefined &&
          story?.importance_score !== null && (
            <strong>
              {story.importance_score}/10
            </strong>
          )}
      </div>

      <h4>{title}</h4>

      <p>
        {story?.summary ||
          "No summary available."}
      </p>

      {story?.why_it_matters && (
        <div className="brief-story-insight">
          <strong>Why it matters</strong>

          <span>
            {story.why_it_matters}
          </span>
        </div>
      )}

      <div className="brief-story-footer">
        <span>
          {story?.source ||
            "Unknown source"}
        </span>

        {story?.url && (
          <a
            href={story.url}
            target="_blank"
            rel="noreferrer"
          >
            Read source ↗
          </a>
        )}
      </div>
    </article>
  );
}


function BriefSection({
  title,
  icon,
  stories = [],
}) {
  const safeStories =
    normalizeStories(stories);

  if (safeStories.length === 0) {
    return null;
  }

  return (
    <section className="brief-content-section">
      <div className="brief-section-heading">
        <div>
          <span>{icon}</span>
          <h3>{title}</h3>
        </div>

        <span className="brief-section-count">
          {safeStories.length} stories
        </span>
      </div>

      <div className="brief-story-grid">
        {safeStories.map(
          (story, index) => (
            <StoryCard
              key={
                story.id ||
                story.url ||
                `${story.headline || story.title}-${index}`
              }
              story={story}
            />
          )
        )}
      </div>
    </section>
  );
}


function BriefListCard({
  title,
  icon,
  items = [],
  accent = false,
}) {
  const safeItems = Array.isArray(items)
    ? items
    : [];

  if (safeItems.length === 0) {
    return null;
  }

  return (
    <section
      className={
        accent
          ? "brief-list-card accent"
          : "brief-list-card"
      }
    >
      <div className="brief-list-card-heading">
        <span>{icon}</span>
        <h3>{title}</h3>
      </div>

      <ul>
        {safeItems.map((item, index) => {
          const text =
            typeof item === "string"
              ? item
              : item?.title ||
                item?.summary ||
                JSON.stringify(item);

          return (
            <li key={`${text}-${index}`}>
              {text}
            </li>
          );
        })}
      </ul>
    </section>
  );
}


function Briefs() {
  const [briefs, setBriefs] =
    useState([]);

  const [
    selectedBriefId,
    setSelectedBriefId,
  ] = useState(null);

  const [loading, setLoading] =
    useState(true);

  const [
    generating,
    setGenerating,
  ] = useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  const loadBriefs = useCallback(
    async ({
      selectNewest = false,
    } = {}) => {
      try {
        setLoading(true);
        setError("");

        const response =
          await getDailyBriefs();

        const responseItems =
          Array.isArray(response.data)
            ? response.data
            : response.data?.briefs || [];

        const sortedItems = [
          ...responseItems,
        ].sort((first, second) => {
          const firstDate =
            new Date(
              `${first.date}T00:00:00`
            ).getTime();

          const secondDate =
            new Date(
              `${second.date}T00:00:00`
            ).getTime();

          if (secondDate !== firstDate) {
            return secondDate - firstDate;
          }

          return (
            Number(second.id || 0) -
            Number(first.id || 0)
          );
        });

        setBriefs(sortedItems);

        if (sortedItems.length === 0) {
          setSelectedBriefId(null);
          return;
        }

        if (selectNewest) {
          setSelectedBriefId(
            sortedItems[0].id
          );
          return;
        }

        setSelectedBriefId(
          (currentSelectedId) => {
            const stillExists =
              sortedItems.some(
                (brief) =>
                  brief.id ===
                  currentSelectedId
              );

            return stillExists
              ? currentSelectedId
              : sortedItems[0].id;
          }
        );
      } catch (requestError) {
        setError(
          requestError.response?.data
            ?.detail ||
            requestError.message ||
            "Could not load daily brief history."
        );
      } finally {
        setLoading(false);
      }
    },
    []
  );


  useEffect(() => {
    loadBriefs({
      selectNewest: true,
    });
  }, [loadBriefs]);


  const handleGenerateBrief =
    async () => {
      try {
        setGenerating(true);
        setError("");
        setSuccess("");

        const response =
          await generateDailyBrief();

        const generatedBrief =
          response.data;

        if (!generatedBrief?.brief) {
          setError(
            generatedBrief?.message ||
              "No processed articles were available for a new brief."
          );
          return;
        }

        setSuccess(
          `New brief generated using ${
            generatedBrief.articles_used ||
            0
          } articles.`
        );

        await loadBriefs({
          selectNewest: true,
        });
      } catch (requestError) {
        setError(
          requestError.response?.data
            ?.detail ||
            requestError.response?.data
              ?.message ||
            requestError.message ||
            "Could not generate a new brief."
        );
      } finally {
        setGenerating(false);
      }
    };


  const selectedBrief =
    useMemo(() => {
      const record = briefs.find(
        (brief) =>
          brief.id === selectedBriefId
      );

      if (!record) {
        return null;
      }

      return {
        ...record,
        parsed: parseBriefJson(
          record.json
        ),
      };
    }, [
      briefs,
      selectedBriefId,
    ]);


  const totalArticles =
    briefs.reduce(
      (sum, brief) =>
        sum +
        Number(
          brief.articles_used || 0
        ),
      0
    );


  const selectedData =
    selectedBrief?.parsed ||
    EMPTY_BRIEF;


  const openEmailPreview = () => {
    if (!selectedBrief?.html) {
      return;
    }

    const previewWindow =
      window.open(
        "",
        "_blank",
        "noopener,noreferrer"
      );

    if (!previewWindow) {
      setError(
        "The browser blocked the email preview window."
      );
      return;
    }

    previewWindow.document.open();
    previewWindow.document.write(
      selectedBrief.html
    );
    previewWindow.document.close();
  };


  return (
    <section className="briefs-page">
      <div className="page-heading briefs-page-heading">
        <div>
          <p className="eyebrow">
            Brief Archive
          </p>

          <h1>
            Daily Intelligence Briefs
          </h1>

          <p>
            Review saved briefings,
            key trends, top stories,
            and category insights
            generated by the News Agent.
          </p>
        </div>

        <div className="briefs-heading-actions">
          <div className="briefs-header-stats">
            <div>
              <strong>
                {briefs.length}
              </strong>

              <span>
                Saved briefs
              </span>
            </div>

            <div>
              <strong>
                {totalArticles}
              </strong>

              <span>
                Articles analyzed
              </span>
            </div>
          </div>

          <button
            type="button"
            className="generate-brief-button"
            onClick={
              handleGenerateBrief
            }
            disabled={
              generating ||
              loading
            }
          >
            {generating
              ? "Generating..."
              : "Generate New Brief"}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <strong>
            Request failed
          </strong>

          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="success-message">
          <strong>
            Brief generated
          </strong>

          <span>{success}</span>
        </div>
      )}

      {loading ? (
        <div className="brief-loading-layout">
          <div className="brief-sidebar-skeleton" />
          <div className="brief-main-skeleton" />
        </div>
      ) : briefs.length === 0 ? (
        <div className="brief-empty-state">
          <span>▤</span>

          <h2>
            No saved briefs yet
          </h2>

          <p>
            Generate a daily brief from
            the latest processed news.
          </p>

          <button
            type="button"
            className="generate-brief-button"
            onClick={
              handleGenerateBrief
            }
            disabled={generating}
          >
            {generating
              ? "Generating..."
              : "Generate First Brief"}
          </button>
        </div>
      ) : (
        <div className="briefs-layout-modern">
          <aside className="brief-history-panel">
            <div className="brief-history-heading">
              <div>
                <p className="eyebrow">
                  Archive
                </p>

                <h2>
                  Brief History
                </h2>
              </div>

              <span>
                {briefs.length}
              </span>
            </div>

            <div className="brief-history-list">
              {briefs.map((brief) => {
                const active =
                  brief.id ===
                  selectedBriefId;

                return (
                  <button
                    key={brief.id}
                    type="button"
                    className={
                      active
                        ? "brief-history-item active"
                        : "brief-history-item"
                    }
                    onClick={() => {
                      setSelectedBriefId(
                        brief.id
                      );
                      setError("");
                      setSuccess("");
                    }}
                  >
                    <div className="brief-history-date">
                      <span className="brief-calendar-icon">
                        ▣
                      </span>

                      <div>
                        <strong>
                          {formatBriefDate(
                            brief.date
                          )}
                        </strong>

                        <span>
                          {brief.articles_used ||
                            0}{" "}
                          articles
                        </span>

                        <small>
                          Brief #{brief.id}
                        </small>
                      </div>
                    </div>

                    <span className="brief-history-arrow">
                      →
                    </span>
                  </button>
                );
              })}
            </div>
          </aside>

          <main className="brief-detail-modern">
            {!selectedBrief ? (
              <div className="brief-select-state">
                <span>▤</span>

                <h2>
                  Select a briefing
                </h2>

                <p>
                  Choose a saved date
                  from the archive.
                </p>
              </div>
            ) : (
              <>
                <div className="brief-detail-hero">
                  <div>
                    <p className="eyebrow">
                      Daily Intelligence Report
                    </p>

                    <h2>
                      {selectedData.title ||
                        "AI Daily News Brief"}
                    </h2>

                    <div className="brief-detail-meta">
                      <span>
                        {formatBriefDate(
                          selectedBrief.date
                        )}
                      </span>

                      <span>•</span>

                      <span>
                        {selectedBrief.articles_used ||
                          0}{" "}
                        articles analyzed
                      </span>

                      <span>•</span>

                      <span>
                        Brief #
                        {selectedBrief.id}
                      </span>
                    </div>
                  </div>

                  <div className="brief-report-badge">
                    Generated
                  </div>
                </div>

                <section className="brief-summary-card">
                  <div className="brief-summary-icon">
                    ✦
                  </div>

                  <div>
                    <p className="eyebrow">
                      Executive Summary
                    </p>

                    <div className="brief-summary-content">
                      <ReactMarkdown>
                        {selectedData.summary ||
                          "No executive summary available."}
                      </ReactMarkdown>
                    </div>
                  </div>
                </section>

                <BriefSection
                  title="Top Stories"
                  icon="🔥"
                  stories={
                    selectedData.top_stories
                  }
                />

                <BriefSection
                  title="India"
                  icon="🇮🇳"
                  stories={
                    selectedData.india
                  }
                />

                <BriefSection
                  title="World"
                  icon="🌍"
                  stories={
                    selectedData.world
                  }
                />

                <BriefSection
                  title="AI & Technology"
                  icon="🤖"
                  stories={
                    selectedData.technology_ai
                  }
                />

                <BriefSection
                  title="Business"
                  icon="📈"
                  stories={
                    selectedData.business
                  }
                />

                <BriefSection
                  title="Health & Science"
                  icon="🔬"
                  stories={
                    selectedData.health_science
                  }
                />

                <div className="brief-insight-grid">
                  <BriefListCard
                    title="Key Trends"
                    icon="📌"
                    items={
                      selectedData.key_trends
                    }
                  />

                  <BriefListCard
                    title="What to Watch Next"
                    icon="👀"
                    items={
                      selectedData.what_to_watch_next
                    }
                    accent
                  />
                </div>

                <div className="brief-detail-footer">
                  <span>
                    Stored automatically by
                    your AI News Agent
                  </span>

                  {selectedBrief.html && (
                    <button
                      type="button"
                      onClick={
                        openEmailPreview
                      }
                    >
                      Open email preview
                    </button>
                  )}
                </div>
              </>
            )}
          </main>
        </div>
      )}
    </section>
  );
}

export default Briefs;