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
    
    # Calculate additional stats
    total_time = sum(r.get('time', 0) for r in results)
    successful = sum(1 for r in results if r.get('accuracy', 0) >= 80)
    success_rate = (successful / len(results) * 100) if results else 0
    
    # Main stats
    stats_text = (
        f"**Total Score:** {total_score:,} points\n"
        f"**Average Accuracy:** {average_accuracy:.1f}%\n"
        f"**Total Time:** {total_time:.1f}s\n"
        f"**Success Rate:** {success_rate:.1f}% ({successful}/{len(results)})"
    )
    
    embed.add_field(
        name="📊 Final Stats",
        value=stats_text,
        inline=False
    )
    
    if is_personal_best:
        embed.add_field(
            name="🎖️ Achievement",
            value="**New Personal Best!** 🎉",
            inline=True
        )
    
    if server_rank:
        embed.add_field(
            name="📈 Server Rank",
            value=f"**#{server_rank}**",
            inline=True
        )
    
    # Add detailed breakdown of all results
    # Split into multiple fields if needed (Discord field limit is 1024 chars)
    if results:
        # Group results into fields (each field can hold ~5-6 results depending on text length)
        results_per_field = 5
        num_fields = (len(results) + results_per_field - 1) // results_per_field
        
        for field_idx in range(num_fields):
            start_idx = field_idx * results_per_field
            end_idx = min(start_idx + results_per_field, len(results))
            field_results = results[start_idx:end_idx]
            
            breakdown_lines = []
            for i, r in enumerate(field_results):
                result_num = start_idx + i + 1
                text = r.get('text', 'N/A')
                score = r.get('score', 0)
                accuracy = r.get('accuracy', 0)
                time_sec = r.get('time', 0)
                difficulty = r.get('difficulty', 'unknown').capitalize()
                
                # Format: "1. [Text] | Score: X | Acc: Y% | Time: Zs | [Difficulty]"
                line = (
                    f"**{result_num}.** {text}\n"
                    f"   Score: {score:,} pts | Acc: {accuracy:.1f}% | "
                    f"Time: {time_sec:.1f}s | {difficulty}"
                )
                breakdown_lines.append(line)
            
            field_name = f"📝 Results {start_idx + 1}-{end_idx}" if num_fields > 1 else "📝 Results Breakdown"
            breakdown_text = "\n\n".join(breakdown_lines)
            
            # Ensure we don't exceed Discord's 1024 character limit per field
            if len(breakdown_text) > 1024:
                # Truncate if needed (shouldn't happen with 5 results, but safety check)
                breakdown_text = breakdown_text[:1020] + "..."
            
            embed.add_field(
                name=field_name,
                value=breakdown_text,
                inline=False
            )
    
    embed.set_footer(text="Great job! 🎉 Try again to beat your score!")
    
    return embed

