import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "news_articles")

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


def build_article_document(article):
    return f"""
Title: {article.title}
Source: {article.source}
Category: {article.category}
Summary: {article.summary}
Why it matters: {article.why_it_matters}
Who is affected: {article.who_is_affected}
Future impact: {article.future_impact}
Tags: {article.tags}
Published at: {article.published_at}
"""


def store_article_embedding(article):
    embedding_id = f"article_{article.id}"

    document = build_article_document(article)

    metadata = {
        "article_id": article.id,
        "title": article.title or "",
        "source": article.source or "",
        "category": article.category or "",
        "url": article.url or "",
        "importance_score": article.importance_score or 0,
        "tags": article.tags or "",
        "published_at": article.published_at or "",
    }

    collection.upsert(
        ids=[embedding_id],
        documents=[document],
        metadatas=[metadata]
    )

    return embedding_id


def search_similar_articles(query_text, n_results=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )

    return results


def get_collection_count():
    return collection.count()