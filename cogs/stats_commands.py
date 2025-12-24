"""Stats and leaderboard commands."""

import discord
from discord.ext import commands
from typing import Optional

from database.manager import db_manager
from utils.embeds import create_twister_list_embed


class StatsCommands(commands.Cog):
    """Stats and leaderboard commands."""
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    @discord.slash_command(name="twister", description="Tongue twister game commands")
    async def twister(self, ctx: discord.ApplicationContext):
        """Main twister command group."""
        pass
    
    @twister.subcommand(name="stats", description="View player statistics")
    async def stats(
        self,
        ctx: discord.ApplicationContext,
        user: Optional[discord.Member] = discord.SlashCommandOption(
            name="user",
            description="User to view stats for (default: yourself)",
            required=False
        )
    ):
        """View player statistics."""
        target_user = user or ctx.author
        
        stats = await db_manager.get_player_stats(str(target_user.id))
        
        if not stats:
            await ctx.respond(f"❌ No statistics found for {target_user.mention}!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Statistics",
            color=discord.Color.blue()
        )
        
        # Overall performance
        success_rate = (stats['successful_attempts'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0
        avg_score = stats['total_score'] / stats['total_attempts'] if stats['total_attempts'] > 0 else 0
        
        embed.add_field(
            name="Overall Performance",
            value=(
                f"**Total Attempts:** {stats['total_attempts']}\n"
                f"**Success Rate:** {success_rate:.1f}% ({stats['successful_attempts']}/{stats['total_attempts']})\n"
                f"**Total Score:** {stats['total_score']:,} points\n"
                f"**Average Score:** {avg_score:.0f} points per attempt"
            ),
            inline=False
        )
        
        # Personal bests
        fastest = f"{stats['fastest_time']:.1f}s" if stats['fastest_time'] else "N/A"
        embed.add_field(
            name="Personal Bests",
            value=(
                f"**Highest Score:** {stats['best_score']:,} points\n"
                f"**Fastest Time:** {fastest}\n"
                f"**Best Twister ID:** #{stats['best_score_twister_id'] or 'N/A'}"
            ),
            inline=False
        )
        
        # By difficulty
        difficulty_stats = stats.get('difficulty_stats', {})
        if difficulty_stats:
            diff_text = ""
            for diff in ['easy', 'medium', 'hard', 'insane']:
                if diff in difficulty_stats:
                    ds = difficulty_stats[diff]
                    diff_text += (
                        f"**{diff.capitalize()}:** "
                        f"{ds['avg_accuracy']:.1f}% accuracy "
                        f"({ds['attempts']} attempts)\n"
                    )
            
            if diff_text:
                embed.add_field(
                    name="By Difficulty",
                    value=diff_text,
                    inline=False
                )
        
        embed.set_footer(text=f"Last played: {stats.get('last_played', 'Never')}")
        
        await ctx.respond(embed=embed)
    
    @twister.subcommand(name="leaderboard", description="View leaderboards")
    async def leaderboard(
        self,
        ctx: discord.ApplicationContext,
        scope: Optional[str] = discord.SlashCommandOption(
            name="scope",
            description="Leaderboard scope",
            choices=["server", "global"],
            required=False,
            default="server"
        ),
        difficulty: Optional[str] = discord.SlashCommandOption(
            name="difficulty",
            description="Filter by difficulty",
            choices=["easy", "medium", "hard", "insane"],
            required=False
        )
    ):
        """View leaderboards."""
        server_id = str(ctx.guild.id) if ctx.guild and scope == "server" else None
        
        leaderboard = await db_manager.get_leaderboard(
            scope=scope or "server",
            server_id=server_id,
            difficulty=difficulty,
            limit=15
        )
        
        if not leaderboard:
            await ctx.respond("❌ No leaderboard data available yet!", ephemeral=True)
            return
        
        title = "🏆 Leaderboard"
        if difficulty:
            title += f" - {difficulty.capitalize()}"
        if scope == "server":
            title += " (Server)"
        else:
            title += " (Global)"
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.gold()
        )
        
        # Format leaderboard
        medals = ["👑", "🥈", "🥉"]
        leaderboard_text = ""
        
        for i, entry in enumerate(leaderboard, 1):
            medal = medals[i - 1] if i <= 3 else f"{i}."
            username = entry['username']
            score = entry['total_score']
            
            if difficulty:
                attempts = entry.get('attempts', 0)
                accuracy = entry.get('avg_accuracy', 0)
                best = entry.get('best_score', 0)
                leaderboard_text += (
                    f"{medal} **{username}** - {score:,} pts\n"
                    f"   Best: {best:,} | Attempts: {attempts} | Avg: {accuracy:.1f}%\n"
                )
            else:
                attempts = entry.get('attempts', 0)
                success_rate = entry.get('success_rate', 0)
                best = entry.get('best_score', 0)
                leaderboard_text += (
                    f"{medal} **{username}** - {score:,} pts\n"
                    f"   Best: {best:,} | Attempts: {attempts} | Success: {success_rate:.1f}%\n"
                )
        
        embed.description = leaderboard_text[:4096]  # Discord limit
        
        # Find user's rank
        user_rank = await db_manager.get_player_rank(
            str(ctx.author.id),
            scope or "server",
            server_id
        )
        
        if user_rank:
            embed.set_footer(text=f"Your rank: #{user_rank}")
        else:
            embed.set_footer(text="Play to get on the leaderboard!")
        
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    """Load the cog."""
    bot.add_cog(StatsCommands(bot))

