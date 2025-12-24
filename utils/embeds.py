"""Discord embed builders for bot responses."""

import discord
from typing import Optional, List
from data.tongue_twisters import get_twister_by_id


def create_session_started_embed(
    channel_name: str,
    player_name: str
) -> discord.Embed:
    """Create embed for session started message."""
    embed = discord.Embed(
        title="🎤 Tongue Twister Session Started!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Voice Channel",
        value=channel_name,
        inline=False
    )
    embed.add_field(
        name="Player",
        value=player_name,
        inline=False
    )
    embed.add_field(
        name="Available Commands",
        value=(
            "• `/twister start` - Random twister\n"
            "• `/twister practice <id>` - Practice specific twister\n"
            "• `/twister challenge` - Timed challenge (10 twisters)\n"
            "• `/twister list` - See all tongue twisters"
        ),
        inline=False
    )
    return embed


def create_twister_challenge_embed(
    twister_id: int,
    text: str,
    difficulty: str,
    is_practice: bool = False
) -> discord.Embed:
    """Create embed for twister challenge."""
    title = "🎯 Practice Mode" if is_practice else "🎤 Tongue Twister Challenge!"
    color = discord.Color.blue() if is_practice else discord.Color.orange()
    
    embed = discord.Embed(
        title=title,
        color=color
    )
    embed.add_field(
        name="Difficulty",
        value=difficulty.capitalize(),
        inline=True
    )
    embed.add_field(
        name="Twister ID",
        value=f"#{twister_id}",
        inline=True
    )
    embed.add_field(
        name="Ready? Say this as fast as you can:",
        value=f"**\"{text}\"**",
        inline=False
    )
    
    if not is_practice:
        embed.set_footer(text="I'm listening... (30 second timer)")
    else:
        embed.set_footer(text="No score tracking in practice mode. Take your time!")
    
    return embed


def create_results_embed(
    spoken_text: str,
    target_text: str,
    accuracy: float,
    time_seconds: float,
    score: int,
    difficulty: str,
    mistakes: Optional[List[str]] = None
) -> discord.Embed:
    """Create embed for attempt results."""
    embed = discord.Embed(
        title="✅ Nice Try!",
        color=discord.Color.green() if accuracy >= 80 else discord.Color.orange()
    )
    
    embed.add_field(
        name="You said:",
        value=f"*{spoken_text}*",
        inline=False
    )
    embed.add_field(
        name="Target:",
        value=f"**{target_text}**",
        inline=False
    )
    embed.add_field(
        name="Accuracy",
        value=f"{accuracy:.1f}%",
        inline=True
    )
    embed.add_field(
        name="Time",
        value=f"{time_seconds:.1f}s",
        inline=True
    )
    embed.add_field(
        name="Difficulty",
        value=difficulty.capitalize(),
        inline=True
    )
    embed.add_field(
        name="Score",
        value=f"**{score:,} points!** 🎉",
        inline=False
    )
    
    if mistakes:
        mistakes_text = "\n".join(f"• {m}" for m in mistakes[:5])  # Limit to 5
        if len(mistakes) > 5:
            mistakes_text += f"\n• ... and {len(mistakes) - 5} more"
        embed.add_field(
            name="Mistakes",
            value=mistakes_text,
            inline=False
        )
    
    embed.set_footer(text="Try again? Use /twister start for another challenge!")
    
    return embed


def create_twister_list_embed(
    twisters: List[dict],
    difficulty: Optional[str] = None
) -> discord.Embed:
    """Create embed for tongue twister list."""
    title = "📜 Tongue Twister Library"
    if difficulty:
        title += f" - {difficulty.capitalize()}"
    
    embed = discord.Embed(
        title=title,
        color=discord.Color.blue()
    )
    
    # Group by difficulty
    by_difficulty = {}
    for twister in twisters:
        diff = twister['difficulty']
        if diff not in by_difficulty:
            by_difficulty[diff] = []
        by_difficulty[diff].append(twister)
    
    # Add fields for each difficulty
    for diff in ['easy', 'medium', 'hard', 'insane']:
        if diff in by_difficulty:
            twister_list = by_difficulty[diff]
            value = "\n".join(
                f"{t['id']}. {t['text']}"
                for t in twister_list
            )
            embed.add_field(
                name=f"{diff.capitalize()} ({len(twister_list)})",
                value=value[:1024],  # Discord field limit
                inline=False
            )
    
    embed.set_footer(text="Use /twister practice <id> to practice a specific twister!")
    
    return embed


def create_session_ended_embed(
    attempts: int,
    successful: int,
    total_score: int,
    best_score: Optional[int] = None
) -> discord.Embed:
    """Create embed for session ended message."""
    embed = discord.Embed(
        title="👋 Session Ended",
        color=discord.Color.blue()
    )
    
    success_rate = (successful / attempts * 100) if attempts > 0 else 0
    
    embed.add_field(
        name="Session Stats",
        value=(
            f"**Attempts:** {attempts}\n"
            f"**Success Rate:** {success_rate:.1f}% ({successful}/{attempts})\n"
            f"**Total Score:** {total_score:,} points"
        ),
        inline=False
    )
    
    if best_score:
        embed.add_field(
            name="Best Score",
            value=f"{best_score:,} points",
            inline=True
        )
    
    embed.set_footer(text="Thanks for playing! See you next time! 🎉")
    
    return embed


def create_challenge_progress_embed(
    current: int,
    total: int,
    twister_text: str,
    difficulty: str,
    cumulative_score: int
) -> discord.Embed:
    """Create embed for challenge mode progress."""
    embed = discord.Embed(
        title=f"⚡ TIMED CHALLENGE MODE ⚡",
        description=f"**Twister {current}/{total}**",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="Difficulty",
        value=difficulty.capitalize(),
        inline=True
    )
    embed.add_field(
        name="Cumulative Score",
        value=f"{cumulative_score:,} points",
        inline=True
    )
    embed.add_field(
        name="Say this:",
        value=f"**\"{twister_text}\"**",
        inline=False
    )
    
    embed.set_footer(text="I'm listening... (30 second timer)")
    
    return embed


def create_challenge_complete_embed(
    total_score: int,
    average_accuracy: float,
    results: List[dict],
    is_personal_best: bool = False,
    server_rank: Optional[int] = None
) -> discord.Embed:
    """Create embed for challenge completion."""
    embed = discord.Embed(
        title="🏆 CHALLENGE COMPLETE! 🏆",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="Final Stats",
        value=(
            f"**Total Score:** {total_score:,} points\n"
            f"**Average Accuracy:** {average_accuracy:.1f}%"
        ),
        inline=False
    )
    
    if is_personal_best:
        embed.add_field(
            name="🎖️ Achievement",
            value="New Personal Best!",
            inline=True
        )
    
    if server_rank:
        embed.add_field(
            name="📊 Server Rank",
            value=f"#{server_rank}",
            inline=True
        )
    
    # Add breakdown of first few results
    if results:
        breakdown = "\n".join(
            f"{i+1}. {r.get('text', 'N/A')[:30]}... | {r.get('score', 0):,} pts | "
            f"{r.get('accuracy', 0):.1f}% | {r.get('time', 0):.1f}s"
            for i, r in enumerate(results[:5])
        )
        if len(results) > 5:
            breakdown += f"\n... and {len(results) - 5} more"
        embed.add_field(
            name="Breakdown",
            value=breakdown,
            inline=False
        )
    
    embed.set_footer(text="Great job! 🎉")
    
    return embed

