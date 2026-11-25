import html
import re
from typing import Any


def clean_text(value: Any) -> str:
    """
    Remove HTML tags and normalize whitespace from RSS/LLM text.
    """
    if value is None:
        return ""

    text = str(value)

    # Remove HTML tags from RSS content
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode entities such as &amp;
    text = html.unescape(text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def safe_text(value: Any) -> str:
    """
    Escape text before inserting it into HTML.
    """
    return html.escape(clean_text(value))


def truncate_text(value: Any, limit: int = 320) -> str:
    text = clean_text(value)

    if len(text) <= limit:
        return html.escape(text)

    shortened = text[:limit].rsplit(" ", 1)[0]
    return html.escape(shortened + "…")


def format_summary(value: Any) -> str:
    """
    Format a summary with basic support for markdown-style headings,
    bold text and line breaks.
    """
    text = clean_text(value)

    if not text:
        return "Today's briefing includes important developments across India, world affairs, technology, business and science."

    escaped = html.escape(text)

    # Convert **bold** into HTML
    escaped = re.sub(
        r"\*\*(.*?)\*\*",
        r"<strong>\1</strong>",
        escaped,
    )

    # Improve common generated headings
    escaped = escaped.replace(
        "Executive Summary:",
        "<strong>Executive Summary:</strong>",
    )
    escaped = escaped.replace(
        "Three Key Trends:",
        "<br><br><strong>Key Trends:</strong>",
    )
    escaped = escaped.replace(
        "Two Things to Watch Next:",
        "<br><br><strong>What to Watch:</strong>",
    )

    return escaped


def get_story_title(story: dict) -> str:
    return safe_text(
        story.get("headline")
        or story.get("title")
        or "Untitled story"
    )


def render_story_card(
    story: dict,
    featured: bool = False,
) -> str:
    title = get_story_title(story)

    summary = truncate_text(
        story.get("summary")
        or story.get("description"),
        360 if featured else 260,
    )

    why_it_matters = truncate_text(
        story.get("why_it_matters")
        or story.get("why"),
        220,
    )

    source = safe_text(
        story.get("source")
        or "Unknown source"
    )

    category = safe_text(
        story.get("category")
        or "General"
    )

    url = story.get("url") or ""

    importance = story.get("importance_score")

    importance_html = ""

    if importance is not None:
        importance_html = f"""
        <span style="
            display:inline-block;
            padding:4px 9px;
            margin-left:6px;
            border-radius:999px;
            background:#fff1f7;
            color:#be185d;
            font-size:11px;
            font-weight:700;
        ">
            Priority {html.escape(str(importance))}/10
        </span>
        """

    source_link = source

    if url:
        safe_url = html.escape(str(url), quote=True)

        source_link = f"""
        <a
            href="{safe_url}"
            target="_blank"
            style="
                color:#2563eb;
                text-decoration:none;
                font-weight:600;
            "
        >
            {source} ↗
        </a>
        """

    border_color = "#ec4899" if featured else "#dbe3ef"
    background = "#fffafb" if featured else "#ffffff"

    why_html = ""

    if why_it_matters:
        why_html = f"""
        <div style="
            margin-top:14px;
            padding:12px 14px;
            border-left:3px solid #ec4899;
            border-radius:0 8px 8px 0;
            background:#f8fafc;
        ">
            <div style="
                margin-bottom:4px;
                color:#111827;
                font-size:12px;
                font-weight:700;
            ">
                Why it matters
            </div>

            <div style="
                color:#526077;
                font-size:13px;
                line-height:1.55;
            ">
                {why_it_matters}
            </div>
        </div>
        """

    return f"""
    <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="
            margin-bottom:16px;
            border:1px solid {border_color};
            border-radius:14px;
            background:{background};
        "
    >
        <tr>
            <td style="padding:20px;">
                <div style="margin-bottom:10px;">
                    <span style="
                        display:inline-block;
                        padding:4px 9px;
                        border-radius:999px;
                        background:#eef2ff;
                        color:#4338ca;
                        font-size:10px;
                        font-weight:700;
                        letter-spacing:0.04em;
                        text-transform:uppercase;
                    ">
                        {category}
                    </span>

                    {importance_html}
                </div>

                <div style="
                    margin-bottom:10px;
                    color:#111827;
                    font-size:{'20px' if featured else '17px'};
                    font-weight:700;
                    line-height:1.4;
                ">
                    {title}
                </div>

                <div style="
                    color:#526077;
                    font-size:14px;
                    line-height:1.65;
                ">
                    {summary or "No summary available."}
                </div>

                {why_html}

                <div style="
                    margin-top:14px;
                    padding-top:12px;
                    border-top:1px solid #e5e7eb;
                    color:#7b8799;
                    font-size:12px;
                ">
                    Source: {source_link}
                </div>
            </td>
        </tr>
    </table>
    """


def render_section(
    title: str,
    icon: str,
    stories: list,
    featured: bool = False,
) -> str:
    if not stories:
        return ""

    cards = "".join(
        render_story_card(
            story,
            featured=featured,
        )
        for story in stories
    )

    return f"""
    <tr>
        <td style="padding:8px 28px 18px;">
            <div style="
                margin:8px 0 16px;
                color:#111827;
                font-size:20px;
                font-weight:800;
                line-height:1.3;
            ">
                <span style="margin-right:7px;">{icon}</span>
                {html.escape(title)}
            </div>

            {cards}
        </td>
    </tr>
    """


def render_bullet_section(
    title: str,
    icon: str,
    items: list,
    accent: str = "#2563eb",
) -> str:
    if not items:
        return ""

    rendered_items = ""

    for item in items:
        if isinstance(item, dict):
            value = (
                item.get("title")
                or item.get("headline")
                or item.get("text")
                or str(item)
            )
        else:
            value = item

        rendered_items += f"""
        <tr>
            <td
                width="22"
                valign="top"
                style="
                    padding:0 0 12px;
                    color:{accent};
                    font-size:14px;
                    font-weight:700;
                "
            >
                •
            </td>

            <td
                valign="top"
                style="
                    padding:0 0 12px;
                    color:#526077;
                    font-size:14px;
                    line-height:1.6;
                "
            >
                {safe_text(value)}
            </td>
        </tr>
        """

    return f"""
    <table
        role="presentation"
        width="100%"
        cellspacing="0"
        cellpadding="0"
        border="0"
        style="
            margin-bottom:18px;
            border:1px solid #e5e7eb;
            border-radius:14px;
            background:#f8fafc;
        "
    >
        <tr>
            <td style="padding:18px 20px;">
                <div style="
                    margin-bottom:14px;
                    color:#111827;
                    font-size:17px;
                    font-weight:800;
                ">
                    {icon} {html.escape(title)}
                </div>

                <table
                    role="presentation"
                    width="100%"
                    cellspacing="0"
                    cellpadding="0"
                    border="0"
                >
                    {rendered_items}
                </table>
            </td>
        </tr>
    </table>
    """


def generate_email_html(brief: dict) -> str:
    title = safe_text(
        brief.get("title")
        or "Daily News Intelligence Brief"
    )

    date_value = safe_text(
        brief.get("date")
        or ""
    )

    summary = format_summary(
        brief.get("summary")
        or ""
    )

    top_stories = render_section(
        "Top Stories",
        "🔥",
        brief.get("top_stories", []),
        featured=True,
    )

    india = render_section(
        "India",
        "🇮🇳",
        brief.get("india", []),
    )

    world = render_section(
        "World",
        "🌍",
        brief.get("world", []),
    )

    technology = render_section(
        "AI & Technology",
        "🤖",
        brief.get("technology_ai", []),
    )

    business = render_section(
        "Business & Markets",
        "📈",
        brief.get("business", []),
    )

    health = render_section(
        "Health & Science",
        "🔬",
        brief.get("health_science", []),
    )

    key_trends = render_bullet_section(
        "Key Trends",
        "📌",
        brief.get("key_trends", []),
        accent="#2563eb",
    )

    watch_next = render_bullet_section(
        "What to Watch Next",
        "👀",
        brief.get("what_to_watch_next", []),
        accent="#ea580c",
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>{title}</title>
    </head>

    <body style="
        margin:0;
        padding:0;
        background:#eef2f7;
        font-family:Arial,Helvetica,sans-serif;
    ">
        <div style="
            display:none;
            max-height:0;
            overflow:hidden;
            opacity:0;
            color:transparent;
        ">
            Your daily briefing covering the most important developments across India, world affairs, technology, business and science.
        </div>

        <table
            role="presentation"
            width="100%"
            cellspacing="0"
            cellpadding="0"
            border="0"
            style="background:#eef2f7;"
        >
            <tr>
                <td
                    align="center"
                    style="padding:24px 10px;"
                >
                    <table
                        role="presentation"
                        width="100%"
                        cellspacing="0"
                        cellpadding="0"
                        border="0"
                        style="
                            width:100%;
                            max-width:700px;
                            overflow:hidden;
                            border:1px solid #dde5ef;
                            border-radius:20px;
                            background:#ffffff;
                            box-shadow:0 14px 40px rgba(15,23,42,0.08);
                        "
                    >
                        <!-- Header -->
                        <tr>
                            <td style="
                                padding:34px 28px 30px;
                                text-align:center;
                                background:
                                    linear-gradient(
                                        135deg,
                                        #111827,
                                        #1e293b
                                    );
                            ">
                                <div style="
                                    margin-bottom:8px;
                                    color:#f472b6;
                                    font-size:11px;
                                    font-weight:700;
                                    letter-spacing:0.16em;
                                    text-transform:uppercase;
                                ">
                                    AI News Agent
                                </div>

                                <div style="
                                    margin:0;
                                    color:#ffffff;
                                    font-size:29px;
                                    font-weight:800;
                                    line-height:1.25;
                                ">
                                    {title}
                                </div>

                                <div style="
                                    margin-top:10px;
                                    color:#cbd5e1;
                                    font-size:13px;
                                ">
                                    {date_value}
                                </div>
                            </td>
                        </tr>

                        <!-- Executive summary -->
                        <tr>
                            <td style="padding:26px 28px 18px;">
                                <table
                                    role="presentation"
                                    width="100%"
                                    cellspacing="0"
                                    cellpadding="0"
                                    border="0"
                                    style="
                                        border:1px solid #dbeafe;
                                        border-radius:14px;
                                        background:#eff6ff;
                                    "
                                >
                                    <tr>
                                        <td style="padding:20px;">
                                            <div style="
                                                margin-bottom:10px;
                                                color:#1e3a8a;
                                                font-size:17px;
                                                font-weight:800;
                                            ">
                                                ⚡ Morning Overview
                                            </div>

                                            <div style="
                                                color:#334155;
                                                font-size:14px;
                                                line-height:1.75;
                                            ">
                                                {summary}
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        {top_stories}
                        {india}
                        {world}
                        {technology}
                        {business}
                        {health}

                        <!-- Trends and watch list -->
                        <tr>
                            <td style="padding:4px 28px 24px;">
                                {key_trends}
                                {watch_next}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="
                                padding:22px 28px;
                                text-align:center;
                                border-top:1px solid #e5e7eb;
                                background:#f8fafc;
                            ">
                                <div style="
                                    color:#64748b;
                                    font-size:12px;
                                    line-height:1.6;
                                ">
                                    Generated automatically by your AI News Agent.
                                </div>

                                <div style="
                                    margin-top:5px;
                                    color:#94a3b8;
                                    font-size:11px;
                                ">
                                    Stories are selected and summarized from your configured news sources.
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """