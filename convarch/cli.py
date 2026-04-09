"""CLI interface for conversation-archive."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .database import Database
from .models import Conversation, Message

console = Console()


def _get_db(db_path: Optional[str] = None) -> Database:
    return Database(Path(db_path) if db_path else None)


@click.group()
@click.option("--db", default=None, help="Path to database file")
@click.pass_context
def cli(ctx, db):
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db


@cli.command()
@click.option("--source", required=True, type=click.Choice(["chatgpt", "claude"]))
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def import_(ctx, source, file_path):
    """Import conversations from an AI platform export."""
    from .search import embed_conversation

    db = _get_db(ctx.obj["db_path"])
    file_path = Path(file_path)

    if source == "chatgpt":
        from .parsers.chatgpt import parse_chatgpt_export
        conversations = parse_chatgpt_export(file_path)
    elif source == "claude":
        from .parsers.claude import parse_claude_export
        conversations = parse_claude_export(file_path)
    else:
        console.print(f"[red]Unknown source: {source}[/red]")
        return

    console.print(f"Parsed {len(conversations)} conversations from {source}")

    with console.status("Generating embeddings..."):
        for conv in conversations:
            embedding = embed_conversation(conv)
            db.save_conversation(conv, embedding)

    console.print(f"[green]✓ Imported {len(conversations)} conversations[/green]")
    db.close()


# Register import_ as "import" command name
cli.add_command(import_, "import")


@cli.command()
@click.argument("query")
@click.option("--top", default=10, help="Number of results")
@click.pass_context
def search(ctx, query, top):
    """Semantic search across conversations."""
    from .search import search as do_search

    db = _get_db(ctx.obj["db_path"])

    with console.status("Searching..."):
        results = do_search(db, query, top_k=top)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title=f"Search: '{query}'")
    table.add_column("Score", width=6)
    table.add_column("Platform", width=10)
    table.add_column("Title", width=40)
    table.add_column("Date", width=12)
    table.add_column("Messages", width=8)

    for conv, score in results:
        date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "—"
        table.add_row(
            f"{score:.3f}", conv.platform, conv.title[:40],
            date_str, str(len(conv.messages)),
        )

    console.print(table)
    db.close()


@cli.command()
@click.option("--platform", default=None, help="Filter by platform")
@click.option("--after", default=None, help="Filter by date (YYYY-MM-DD)")
@click.option("--limit", default=20, help="Max results")
@click.pass_context
def browse(ctx, platform, after, limit):
    """Browse conversations with optional filters."""
    db = _get_db(ctx.obj["db_path"])
    conversations = db.list_conversations(platform=platform, after=after, limit=limit)

    if not conversations:
        console.print("[yellow]No conversations found.[/yellow]")
        return

    table = Table(title="Conversations")
    table.add_column("ID", width=8)
    table.add_column("Platform", width=10)
    table.add_column("Title", width=45)
    table.add_column("Date", width=12)
    table.add_column("Msgs", width=5)

    for conv in conversations:
        date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "—"
        table.add_row(
            conv.id[:8], conv.platform, conv.title[:45],
            date_str, str(len(conv.messages)),
        )

    console.print(table)
    db.close()


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown")
@click.option("--output", required=True, type=click.Path())
@click.option("--platform", default=None)
@click.pass_context
def export(ctx, fmt, output, platform):
    """Export conversations to Markdown or JSON."""
    from .export import export_json, export_markdown

    db = _get_db(ctx.obj["db_path"])
    conversations = db.list_conversations(platform=platform, limit=10000)

    if not conversations:
        console.print("[yellow]No conversations to export.[/yellow]")
        return

    output_path = Path(output)
    if fmt == "markdown":
        export_markdown(conversations, output_path)
    else:
        export_json(conversations, output_path)

    console.print(f"[green]✓ Exported {len(conversations)} conversations to {output}[/green]")
    db.close()


@cli.command()
@click.option("--title", required=True)
@click.option("--platform", default="manual")
@click.pass_context
def add(ctx, title, platform):
    """Add a conversation manually (reads from stdin)."""
    import sys

    db = _get_db(ctx.obj["db_path"])
    console.print("Enter messages (format: 'user: message' or 'assistant: message'). Empty line to finish.")

    messages = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            break
        if ": " in line:
            role, content = line.split(": ", 1)
            if role.lower() in ("user", "assistant", "system"):
                messages.append(Message(role=role.lower(), content=content))

    if not messages:
        console.print("[yellow]No messages entered.[/yellow]")
        return

    from datetime import datetime
    from .search import embed_conversation

    conv = Conversation(title=title, platform=platform, messages=messages,
                        created_at=datetime.now(), updated_at=datetime.now())
    embedding = embed_conversation(conv)
    db.save_conversation(conv, embedding)
    console.print(f"[green]✓ Added conversation: {title}[/green]")
    db.close()


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    db = _get_db(ctx.obj["db_path"])
    total = db.count()
    console.print(f"Total conversations: {total}")

    if total > 0:
        convs = db.list_conversations(limit=10000)
        platforms = {}
        for c in convs:
            platforms[c.platform] = platforms.get(c.platform, 0) + 1
        for p, count in sorted(platforms.items()):
            console.print(f"  {p}: {count}")

    db.close()


if __name__ == "__main__":
    cli()
