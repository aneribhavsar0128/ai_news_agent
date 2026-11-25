import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";

import { askNewsAgent } from "../api/api";

const SUGGESTED_QUESTIONS = [
  "What are the biggest AI developments today?",
  "Summarize the most important India news.",
  "What is happening in global politics?",
  "What are the major business stories today?",
  "What trends are emerging in technology?",
];

function AskAI() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [retrievedCount, setRetrievedCount] = useState(0);

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");

  const [error, setError] = useState("");
  const [recentQueries, setRecentQueries] = useState([]);

  const hasResult = Boolean(answer);

  const uniqueSources = useMemo(() => {
    return Array.from(
      new Map(
        sources.map((source) => [
          source.url || source.title,
          source,
        ])
      ).values()
    );
  }, [sources]);

  const startLoadingSequence = () => {
    setLoadingStep("Searching ChromaDB memory...");

    const stepTwo = window.setTimeout(() => {
      setLoadingStep(
        "Retrieving the most relevant news articles..."
      );
    }, 700);

    const stepThree = window.setTimeout(() => {
      setLoadingStep("Generating a grounded answer...");
    }, 1500);

    return () => {
      window.clearTimeout(stepTwo);
      window.clearTimeout(stepThree);
    };
  };

  const handleAsk = async (
    event = null,
    forcedQuery = null
  ) => {
    event?.preventDefault();

    const cleanedQuery = (
      forcedQuery ?? query
    ).trim();

    if (!cleanedQuery) {
      setError("Please enter a question.");
      return;
    }

    const clearLoadingTimers =
      startLoadingSequence();

    try {
      setLoading(true);
      setError("");
      setAnswer("");
      setSources([]);
      setRetrievedCount(0);

      const response =
        await askNewsAgent(cleanedQuery);

      const returnedAnswer =
        response.data.answer ||
        "I could not find enough relevant information in the current news database.";

      const returnedSources =
        response.data.sources || [];

      setAnswer(returnedAnswer);
      setSources(returnedSources);

      setRetrievedCount(
        response.data.retrieved_articles ??
          returnedSources.length
      );

      setRecentQueries((currentQueries) => {
        const updatedQueries = [
          cleanedQuery,
          ...currentQueries.filter(
            (item) => item !== cleanedQuery
          ),
        ];

        return updatedQueries.slice(0, 5);
      });
    } catch (requestError) {
      const message =
        requestError.response?.data?.detail ||
        requestError.response?.data?.message ||
        requestError.message ||
        "The news agent could not answer this question.";

      setError(message);
      setAnswer("");
      setSources([]);
      setRetrievedCount(0);
    } finally {
      clearLoadingTimers();
      setLoading(false);
      setLoadingStep("");
    }
  };

  const askSuggestedQuestion = async (
    question
  ) => {
    setQuery(question);
    await handleAsk(null, question);
  };

  const useRecentQuery = async (
    recentQuery
  ) => {
    setQuery(recentQuery);
    await handleAsk(null, recentQuery);
  };

  return (
    <section className="ask-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            RAG Assistant
          </p>

          <h1>Ask the News Agent</h1>

          <p>
            Ask questions grounded in your
            stored and processed news memory.
          </p>
        </div>

        <div className="agent-pill">
          <span className="agent-dot" />
          Agent online
        </div>
      </div>

      <div className="ask-hero">
        <div className="ask-hero-copy">
          <span className="ask-icon">
            ✦
          </span>

          <div>
            <h2>
              What would you like to know?
            </h2>

            <p>
              Search across the latest
              collected news, trends,
              companies, politics, business
              and technology.
            </p>
          </div>
        </div>

        <form
          className="ask-form ask-form-modern"
          onSubmit={handleAsk}
        >
          <textarea
            rows="5"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);

              if (error) {
                setError("");
              }
            }}
            placeholder="Example: What are the most important AI developments today?"
            disabled={loading}
          />

          <div className="ask-form-footer">
            <span>
              Answers are grounded in
              articles stored in ChromaDB.
            </span>

            <button
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Thinking..."
                : "Ask AI"}
            </button>
          </div>
        </form>

        {!hasResult &&
          !loading && (
            <div className="suggestion-block">
              <p className="suggestion-label">
                Try asking
              </p>

              <div className="suggestion-grid">
                {SUGGESTED_QUESTIONS.map(
                  (question) => (
                    <button
                      key={question}
                      type="button"
                      className="suggestion-card"
                      onClick={() =>
                        askSuggestedQuestion(
                          question
                        )
                      }
                    >
                      <span>↗</span>
                      {question}
                    </button>
                  )
                )}
              </div>
            </div>
          )}
      </div>

      {recentQueries.length > 0 && (
        <div className="recent-query-row">
          <span>Recent:</span>

          {recentQueries.map(
            (recentQuery) => (
              <button
                key={recentQuery}
                type="button"
                disabled={loading}
                onClick={() =>
                  useRecentQuery(
                    recentQuery
                  )
                }
              >
                {recentQuery}
              </button>
            )
          )}
        </div>
      )}

      {loading && (
        <div className="thinking-panel">
          <div className="thinking-orb">
            <span />
            <span />
            <span />
          </div>

          <div>
            <h3>
              News Agent is working
            </h3>

            <p>
              {loadingStep ||
                "Processing your question..."}
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>
            Request failed
          </strong>

          <span>{error}</span>
        </div>
      )}

      {answer && (
        <div className="answer-panel answer-panel-modern">
          <div className="answer-header">
            <div>
              <p className="eyebrow">
                Grounded response
              </p>

              <h2>Answer</h2>
            </div>

            <div className="retrieval-badge">
              {retrievedCount} supporting{" "}
              {retrievedCount === 1
                ? "article"
                : "articles"}
            </div>
          </div>

          <div className="answer-body">
            <ReactMarkdown>
              {answer}
            </ReactMarkdown>
          </div>

          {uniqueSources.length > 0 && (
            <div className="sources-section">
              <div className="sources-heading">
                <h3>Sources used</h3>

                <span>
                  {uniqueSources.length}{" "}
                  {uniqueSources.length ===
                  1
                    ? "reference"
                    : "references"}
                </span>
              </div>

              <div className="source-card-grid">
                {uniqueSources.map(
                  (source, index) => {
                    const similarity =
                      typeof source.distance ===
                      "number"
                        ? Math.max(
                            0,
                            Math.min(
                              100,
                              Math.round(
                                (2 -
                                  source.distance) *
                                  50
                              )
                            )
                          )
                        : null;

                    return (
                      <a
                        key={
                          source.url ||
                          `${source.title}-${index}`
                        }
                        href={
                          source.url || "#"
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="source-card"
                      >
                        <div className="source-card-top">
                          <span className="source-index">
                            {String(
                              index + 1
                            ).padStart(
                              2,
                              "0"
                            )}
                          </span>

                          <span className="source-open">
                            ↗
                          </span>
                        </div>

                        <h4>
                          {source.title ||
                            "Untitled article"}
                        </h4>

                        <div className="source-card-meta">
                          <span>
                            {source.source ||
                              "Unknown source"}
                          </span>

                          {similarity !==
                            null && (
                            <span>
                              Match{" "}
                              {similarity}%
                            </span>
                          )}
                        </div>
                      </a>
                    );
                  }
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default AskAI;       