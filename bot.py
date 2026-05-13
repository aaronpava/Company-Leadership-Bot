"""
Company Leadership Bot — Strategic Decision Analysis

Facilitates high-stakes strategic decision analysis between twelve distinct
leadership perspectives at Company, a mission-driven federal contracting agency
specializing in web development, Drupal expertise, open data, and open-source
solutions for large federal agencies.

Usage:
    python bot.py
    python bot.py --topic "Should we pursue a new IDIQ vehicle for cloud services?"
    python bot.py --topic "..." --rounds 2 --output report.md

Environment variables:
    OPENAI_API_KEY  — Required for AI-generated perspectives. If not set, the
                      bot runs in demo mode with structured placeholder responses.
    OPENAI_MODEL    — Model to use (default: gpt-4o).
"""

import argparse
import os
import sys
import textwrap

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from personas import PERSONAS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPANY_CONTEXT = """
Company is a mission-driven federal contracting agency with the following profile:

- Core competencies: web development, Drupal CMS, open data portals, open-source solutions
- Clients: large federal agencies (CMS, HHS, USDA, EPA, DOE, DOT, and others)
- Contract vehicles: GSA MAS, CIO-SP3, OASIS
- Values: open source, transparency, mission impact, technical excellence
- Size: ~150 FTEs; mix of federal employees and subcontractors
- Regulatory context: FISMA, Section 508, FedRAMP, DCAA, CPARS
"""

SYSTEM_PROMPT_TEMPLATE = """
You are {title} at Company, a federal IT contracting firm.

{background}

Your priorities are:
{priorities}

Your communication style:
{style}

Company context:
{company_context}

You are participating in a structured leadership discussion about a strategic decision.
Respond as this specific leader — stay in character, be specific and substantive, and
draw on your area of expertise. Keep your response to 3–5 focused paragraphs.
Do NOT use bullet points; write in flowing prose.
"""

SYNTHESIS_PROMPT = """
You are a neutral strategic facilitator summarizing a leadership discussion at Company,
a federal IT contracting firm specializing in Drupal, open data, and open-source solutions.

Below are perspectives from twelve Company leaders on the following decision:

{topic}

{perspectives}

Write a concise synthesis (4–6 paragraphs) that:
1. Identifies the key areas of agreement across the leadership team
2. Highlights the primary tensions or disagreements
3. Outlines 3–5 concrete recommended next steps that the team should prioritize
4. Notes any critical risks or dependencies that leaders flagged

Write in clear, executive-level prose suitable for sharing with the leadership team.
"""

DEMO_PERSPECTIVE_TEMPLATE = (
    "[DEMO MODE — set OPENAI_API_KEY for AI-generated perspectives]\n\n"
    "As {title}, my perspective on '{topic}' centers on {first_priority}. "
    "I would evaluate this decision through the lens of {second_priority} and "
    "ensure we account for {third_priority}. "
    "My communication approach is: {style_snippet}"
)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

console = Console() if RICH_AVAILABLE else None


def print_header(text: str) -> None:
    if RICH_AVAILABLE:
        console.print(Rule(f"[bold cyan]{text}[/bold cyan]"))
    else:
        width = 72
        print("\n" + "=" * width)
        print(f"  {text}")
        print("=" * width + "\n")


def print_persona_response(persona: dict, response: str, round_label: str = "") -> None:
    title = persona["title"]
    label = f"{round_label} — " if round_label else ""

    if RICH_AVAILABLE:
        header = f"[bold yellow]{label}{title}[/bold yellow]"
        console.print(Panel(response, title=header, border_style="blue", padding=(1, 2)))
    else:
        width = 72
        divider = "-" * width
        print(divider)
        print(f"  {label}{title}")
        print(divider)
        for line in textwrap.wrap(response, width=width - 4):
            print(f"  {line}")
        print()


def print_synthesis(synthesis: str) -> None:
    if RICH_AVAILABLE:
        console.print(
            Panel(
                Markdown(synthesis),
                title="[bold green]Strategic Synthesis[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        print_header("Strategic Synthesis")
        for line in synthesis.split("\n"):
            print(textwrap.fill(line, width=72) if line.strip() else "")
        print()


def print_summary_table(personas: list[dict], round_count: int) -> None:
    if not RICH_AVAILABLE:
        return
    table = Table(title="Leadership Perspectives Summary", show_lines=True)
    table.add_column("Leader", style="bold cyan", no_wrap=True)
    table.add_column("Role Focus", style="white")
    table.add_column("Top Priority", style="yellow")
    for p in personas:
        table.add_row(p["title"], p["style"][:80] + "…", p["priorities"][0])
    console.print(table)


# ---------------------------------------------------------------------------
# AI interaction
# ---------------------------------------------------------------------------


def build_system_prompt(persona: dict) -> str:
    priorities_str = "\n".join(f"- {p}" for p in persona["priorities"])
    return SYSTEM_PROMPT_TEMPLATE.format(
        title=persona["title"],
        background=persona["background"],
        priorities=priorities_str,
        style=persona["style"],
        company_context=COMPANY_CONTEXT,
    )


def get_ai_perspective(
    client: "openai.OpenAI",
    model: str,
    persona: dict,
    topic: str,
    prior_perspectives: list[tuple[str, str]] | None = None,
) -> str:
    """Call the OpenAI API to get a persona's perspective on the topic."""
    messages = [{"role": "system", "content": build_system_prompt(persona)}]

    if prior_perspectives:
        prior_text = "\n\n".join(
            f"{title}:\n{text}" for title, text in prior_perspectives
        )
        user_content = (
            f"The strategic decision under discussion:\n{topic}\n\n"
            f"Here are perspectives already shared by your colleagues:\n\n{prior_text}\n\n"
            f"Now share your response. You may agree, disagree, build on, or challenge "
            f"what your colleagues said — stay grounded in your role and priorities."
        )
    else:
        user_content = (
            f"The strategic decision under discussion:\n{topic}\n\n"
            f"Share your perspective on this decision from your role as {persona['title']}."
        )

    messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


def get_ai_synthesis(
    client: "openai.OpenAI",
    model: str,
    topic: str,
    all_perspectives: list[tuple[str, str]],
) -> str:
    """Generate a strategic synthesis of all perspectives."""
    perspectives_text = "\n\n".join(
        f"**{title}**:\n{text}" for title, text in all_perspectives
    )
    prompt = SYNTHESIS_PROMPT.format(topic=topic, perspectives=perspectives_text)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Demo mode (no API key)
# ---------------------------------------------------------------------------


def get_demo_perspective(persona: dict, topic: str) -> str:
    """Return a structured demo response when no API key is available."""
    style_words = persona["style"].split()[:12]
    style_snippet = " ".join(style_words) + "…"
    return DEMO_PERSPECTIVE_TEMPLATE.format(
        title=persona["title"],
        topic=topic,
        first_priority=persona["priorities"][0],
        second_priority=persona["priorities"][1] if len(persona["priorities"]) > 1 else "strategic alignment",
        third_priority=persona["priorities"][2] if len(persona["priorities"]) > 2 else "organizational impact",
        style_snippet=style_snippet,
    )


def get_demo_synthesis(topic: str, personas: list[dict]) -> str:
    """Return a structured demo synthesis."""
    titles = ", ".join(p["title"] for p in personas[:4]) + ", and eight others"
    return (
        f"[DEMO MODE — set OPENAI_API_KEY for AI-generated synthesis]\n\n"
        f"**Strategic Synthesis: {topic}**\n\n"
        f"Across the twelve leadership perspectives — including {titles} — "
        f"several themes emerged. Leaders broadly agreed on the importance of "
        f"mission alignment, financial sustainability, and technical excellence. "
        f"Key tensions centered on speed vs. quality, short-term revenue vs. "
        f"long-term investment, and centralized vs. distributed decision-making.\n\n"
        f"**Recommended next steps:**\n"
        f"1. Convene a working group to define success metrics\n"
        f"2. Conduct a financial risk assessment\n"
        f"3. Engage key federal clients for early feedback\n"
        f"4. Identify quick wins to build momentum\n"
        f"5. Set a 30-day checkpoint to review progress"
    )


# ---------------------------------------------------------------------------
# Core facilitation logic
# ---------------------------------------------------------------------------


def facilitate_discussion(
    topic: str,
    rounds: int = 1,
    output_file: str | None = None,
    skip_synthesis: bool = False,
) -> None:
    """Run the full leadership discussion facilitation."""
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    use_ai = api_key and OPENAI_AVAILABLE
    client = None

    if use_ai:
        client = openai.OpenAI(api_key=api_key)
    else:
        if not OPENAI_AVAILABLE:
            print(
                "Note: openai package not installed. Running in demo mode.\n"
                "Install with: pip install openai\n"
            )
        else:
            print(
                "Note: OPENAI_API_KEY not set. Running in demo mode.\n"
                "Set the environment variable to enable AI-generated perspectives.\n"
            )

    output_lines: list[str] = []

    def record(text: str) -> None:
        output_lines.append(text)

    # Header
    print_header("Company Leadership Bot — Strategic Decision Analysis")
    record("# Company Leadership Bot — Strategic Decision Analysis\n")

    if RICH_AVAILABLE:
        console.print(
            Panel(
                f"[bold white]{topic}[/bold white]",
                title="[bold magenta]Strategic Decision Under Analysis[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            )
        )
    else:
        print(f"Strategic Decision: {topic}\n")
    record(f"**Strategic Decision:** {topic}\n")
    record(f"**Rounds of discussion:** {rounds}\n")
    record(f"**Participants:** {len(PERSONAS)} leaders\n\n---\n")

    all_perspectives: list[tuple[str, str]] = []

    for round_num in range(1, rounds + 1):
        round_label = f"Round {round_num}" if rounds > 1 else ""
        print_header(f"Round {round_num} — Leadership Perspectives" if rounds > 1 else "Leadership Perspectives")
        record(f"\n## {'Round ' + str(round_num) + ' — ' if rounds > 1 else ''}Leadership Perspectives\n")

        round_perspectives: list[tuple[str, str]] = []
        prior = all_perspectives if round_num > 1 else None

        for persona in PERSONAS:
            if RICH_AVAILABLE:
                with console.status(f"[cyan]Gathering perspective from {persona['title']}…[/cyan]"):
                    if use_ai:
                        response = get_ai_perspective(client, model, persona, topic, prior)
                    else:
                        response = get_demo_perspective(persona, topic)
            else:
                print(f"Gathering perspective from {persona['title']}…")
                if use_ai:
                    response = get_ai_perspective(client, model, persona, topic, prior)
                else:
                    response = get_demo_perspective(persona, topic)

            print_persona_response(persona, response, round_label)
            record(f"\n### {persona['title']}\n\n{response}\n")
            round_perspectives.append((persona["title"], response))

        all_perspectives.extend(round_perspectives)

    # Synthesis
    if not skip_synthesis:
        print_header("Strategic Synthesis")
        record("\n---\n\n## Strategic Synthesis\n")

        if RICH_AVAILABLE:
            with console.status("[green]Generating strategic synthesis…[/green]"):
                if use_ai:
                    synthesis = get_ai_synthesis(client, model, topic, all_perspectives)
                else:
                    synthesis = get_demo_synthesis(topic, PERSONAS)
        else:
            print("Generating strategic synthesis…")
            if use_ai:
                synthesis = get_ai_synthesis(client, model, topic, all_perspectives)
            else:
                synthesis = get_demo_synthesis(topic, PERSONAS)

        print_synthesis(synthesis)
        record(synthesis)

    # Optional file output
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        if RICH_AVAILABLE:
            console.print(f"\n[green]Report saved to:[/green] {output_file}")
        else:
            print(f"\nReport saved to: {output_file}")

    if RICH_AVAILABLE:
        console.print(
            Rule("[bold cyan]Discussion Complete[/bold cyan]")
        )
    else:
        print("\n" + "=" * 72)
        print("  Discussion Complete")
        print("=" * 72)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Company Leadership Bot — facilitate strategic decision analysis "
            "between twelve leadership perspectives."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python bot.py
              python bot.py --topic "Should we bid on a new CMS consolidation IDIQ?"
              python bot.py --topic "Expand open-source practice?" --rounds 2
              python bot.py --topic "..." --output analysis.md --no-synthesis

            Environment variables:
              OPENAI_API_KEY   API key for AI-generated perspectives (required for AI mode)
              OPENAI_MODEL     Model name (default: gpt-4o)
            """
        ),
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="The strategic decision or question to analyze. If not provided, you will be prompted.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="Number of discussion rounds (default: 1). Use 2 for a response round.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help="Optional path to write a Markdown report of the discussion.",
    )
    parser.add_argument(
        "--no-synthesis",
        action="store_true",
        help="Skip the final strategic synthesis.",
    )
    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="Print all twelve leadership personas and exit.",
    )
    return parser.parse_args()


def list_personas() -> None:
    """Print all personas in a readable format."""
    if RICH_AVAILABLE:
        table = Table(title="Company Leadership Team — Twelve Perspectives", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="bold cyan", no_wrap=True)
        table.add_column("Top Priority", style="yellow")
        table.add_column("Communication Style (excerpt)", style="white")
        for i, p in enumerate(PERSONAS, 1):
            style_excerpt = p["style"][:70] + ("…" if len(p["style"]) > 70 else "")
            table.add_row(str(i), p["title"], p["priorities"][0], style_excerpt)
        console.print(table)
    else:
        print(f"\nCompany Leadership Team — {len(PERSONAS)} Perspectives\n")
        print("=" * 72)
        for i, p in enumerate(PERSONAS, 1):
            print(f"{i:2}. {p['title']}")
            print(f"    Top priority: {p['priorities'][0]}")
            print()


def main() -> None:
    args = parse_args()

    if args.list_personas:
        list_personas()
        sys.exit(0)

    topic = args.topic
    if not topic:
        if RICH_AVAILABLE:
            console.print(
                "\n[bold cyan]Company Leadership Bot[/bold cyan] — Strategic Decision Analysis\n"
            )
        else:
            print("\nCompany Leadership Bot — Strategic Decision Analysis\n")
        topic = input("Enter the strategic decision or question to analyze:\n> ").strip()
        if not topic:
            print("No topic provided. Exiting.")
            sys.exit(1)

    if args.rounds < 1:
        print("--rounds must be at least 1.")
        sys.exit(1)

    facilitate_discussion(
        topic=topic,
        rounds=args.rounds,
        output_file=args.output,
        skip_synthesis=args.no_synthesis,
    )


if __name__ == "__main__":
    main()
