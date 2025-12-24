"""Game commands for tongue twister bot."""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, date
from typing import Optional, Dict
import uuid
import aiosqlite
import os
from dotenv import load_dotenv

load_dotenv()

from game.session_manager import session_manager
from game.scoring import calculate_score, is_successful_attempt
from game.session import TwisterSession
from voice.handler import VoiceHandler
from voice.recorder import AudioRecorder
from voice.speech_to_text import get_whisper
from utils.text_similarity import calculate_accuracy, find_differences
from utils.embeds import (
    create_session_started_embed,
    create_twister_challenge_embed,
    create_results_embed,
    create_twister_list_embed,
    create_session_ended_embed,
    create_challenge_progress_embed,
    create_challenge_complete_embed
)
from data.tongue_twisters import (
    get_random_twister,
    get_twister_by_id,
    get_all_twisters,
    get_twisters_by_difficulty
)
from database.manager import db_manager
import config


class GameCommands(commands.Cog):
    """Game commands for tongue twister challenges."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_handler = VoiceHandler(bot)
        self.pending_duels: dict[str, dict] = {}  # duel_id -> duel info
    
    # Basic Commands
    @app_commands.command(name="twister_join", description="Join voice channel and start a session")
    async def join(self, interaction: discord.Interaction):
        """Join voice channel and start a session."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel to use this command!", ephemeral=True)
            return
        
        # Check if already in a session
        if session_manager.is_active(str(interaction.user.id), str(interaction.user.voice.channel.id)):
            await interaction.response.send_message("❌ You already have an active session in this channel!", ephemeral=True)
            return
        
        # Join voice channel
        voice_client = await self.voice_handler.join_voice_channel(interaction.user)
        if not voice_client:
            await interaction.response.send_message("❌ Failed to join voice channel. Check bot permissions!", ephemeral=True)
            return
        
        # Create session
        session = session_manager.create_session(
            channel_id=str(interaction.user.voice.channel.id),
            server_id=str(interaction.guild.id) if interaction.guild else "DM",
            player_id=str(interaction.user.id),
            player_name=interaction.user.display_name,
            mode='practice'
        )
        
        # Create database session
        await db_manager.create_session(
            session.session_id,
            str(interaction.user.id),
            str(interaction.guild.id) if interaction.guild else "DM",
            str(interaction.user.voice.channel.id),
            'solo'
        )
        
        embed = create_session_started_embed(
            interaction.user.voice.channel.name,
            interaction.user.display_name
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="twister_leave", description="End session and leave voice channel")
    async def leave(self, interaction: discord.Interaction):
        """End session and leave voice channel."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You're not in a voice channel!", ephemeral=True)
            return
        
        session = session_manager.get_session(
            str(interaction.user.id),
            str(interaction.user.voice.channel.id)
        )
        
        if not session:
            await interaction.response.send_message("❌ You don't have an active session!", ephemeral=True)
            return
        
        # End session
        session = session_manager.end_session(
            str(interaction.user.id),
            str(interaction.user.voice.channel.id)
        )
        
        # Update database
        if session:
            await db_manager.end_session(
                session.session_id,
                session.attempts,
                session.total_score
            )
        
        # Leave voice channel
        await self.voice_handler.leave_voice_channel(interaction.user.voice.channel.id)
        
        # Get best score from session
        best_score = session.total_score if session else 0
        
        embed = create_session_ended_embed(
            session.attempts if session else 0,
            session.successful_attempts if session else 0,
            session.total_score if session else 0,
            best_score
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="twister_start", description="Start a random tongue twister challenge")
    @app_commands.describe(difficulty="Difficulty level")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
        app_commands.Choice(name="Insane", value="insane"),
        app_commands.Choice(name="Random", value="random")
    ])
    async def start(
        self,
        interaction: discord.Interaction,
        difficulty: Optional[str] = "random"
    ):
        """Start a random tongue twister challenge."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        session = session_manager.get_session(
            str(interaction.user.id),
            str(interaction.user.voice.channel.id)
        )
        
        if not session:
            await interaction.response.send_message("❌ You must join a session first with `/twister join`!", ephemeral=True)
            return
        
        # Get random twister
        if difficulty and difficulty != "random":
            twister = get_random_twister(difficulty)
        else:
            twister = get_random_twister()
        
        # Update session
        session.current_twister_id = twister['id']
        session.waiting_for_attempt = True
        session.attempt_started_at = datetime.utcnow()
        
        # Send challenge embed
        embed = create_twister_challenge_embed(
            twister['id'],
            twister['text'],
            twister['difficulty'],
            is_practice=False
        )
        await interaction.response.send_message(embed=embed)
        
        # Get voice client
        voice_client = self.voice_handler.get_voice_client(interaction.user.voice.channel.id)
        if not voice_client:
            await interaction.followup.send("❌ Voice connection lost!", ephemeral=True)
            return
        
        # Record audio
        recorder = AudioRecorder(voice_client)
        audio_file = await recorder.record_user_audio(interaction.user.id, config.VOICE_RECORDING_TIMEOUT)
        
        if not audio_file:
            await interaction.followup.send("❌ Failed to record audio. Make sure your microphone is working!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        # Transcribe
        whisper = get_whisper()
        if not whisper:
            await interaction.followup.send("❌ Speech recognition not initialized!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        await interaction.followup.send("🎤 Processing your speech...", ephemeral=True)
        
        spoken_text = await whisper.transcribe(audio_file)
        
        if not spoken_text:
            await interaction.followup.send("❌ Could not understand your speech. Try speaking more clearly!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        # Calculate accuracy and score
        accuracy = calculate_accuracy(spoken_text, twister['text'])
        time_seconds = (datetime.utcnow() - session.attempt_started_at).total_seconds()
        score = calculate_score(accuracy, time_seconds, twister['difficulty'])
        is_successful = is_successful_attempt(accuracy)
        
        # Find mistakes
        mistakes = find_differences(spoken_text, twister['text'])
        
        # Update session
        session.attempts += 1
        if is_successful:
            session.successful_attempts += 1
        session.total_score += score
        session.waiting_for_attempt = False
        
        # Save to database
        await db_manager.get_or_create_player(str(interaction.user.id), interaction.user.display_name)
        attempt_id = await db_manager.save_attempt(
            str(interaction.user.id),
            twister['id'],
            spoken_text,
            accuracy,
            time_seconds,
            score,
            twister['difficulty'],
            session.mode,
            session.session_id
        )
        await db_manager.update_player_stats(
            str(interaction.user.id),
            accuracy,
            time_seconds,
            score,
            twister['id'],
            is_successful
        )
        
        # Send results
        embed = create_results_embed(
            spoken_text,
            twister['text'],
            accuracy,
            time_seconds,
            score,
            twister['difficulty'],
            mistakes
        )
        await interaction.followup.send(embed=embed)
        
        # Cleanup audio file
        try:
            os.remove(audio_file)
        except:
            pass
    
    @app_commands.command(name="twister_practice", description="Practice a specific tongue twister")
    @app_commands.describe(twister_id="Tongue twister ID (1-20)")
    async def practice(
        self,
        interaction: discord.Interaction,
        twister_id: int
    ):
        """Practice a specific tongue twister."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        session = session_manager.get_session(
            str(interaction.user.id),
            str(interaction.user.voice.channel.id)
        )
        
        if not session:
            await interaction.response.send_message("❌ You must join a session first with `/twister join`!", ephemeral=True)
            return
        
        # Get twister
        twister = get_twister_by_id(twister_id)
        if not twister:
            await interaction.response.send_message(f"❌ Tongue twister #{twister_id} not found!", ephemeral=True)
            return
        
        # Update session
        session.current_twister_id = twister['id']
        session.waiting_for_attempt = True
        session.attempt_started_at = datetime.utcnow()
        session.mode = 'practice'
        
        # Send challenge embed
        embed = create_twister_challenge_embed(
            twister['id'],
            twister['text'],
            twister['difficulty'],
            is_practice=True
        )
        await interaction.response.send_message(embed=embed)
        
        # Get voice client
        voice_client = self.voice_handler.get_voice_client(interaction.user.voice.channel.id)
        if not voice_client:
            await interaction.followup.send("❌ Voice connection lost!", ephemeral=True)
            return
        
        # Record audio
        recorder = AudioRecorder(voice_client)
        audio_file = await recorder.record_user_audio(interaction.user.id, config.VOICE_RECORDING_TIMEOUT)
        
        if not audio_file:
            await interaction.followup.send("❌ Failed to record audio. Make sure your microphone is working!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        # Transcribe
        whisper = get_whisper()
        if not whisper:
            await interaction.followup.send("❌ Speech recognition not initialized!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        await interaction.followup.send("🎤 Processing your speech...", ephemeral=True)
        
        spoken_text = await whisper.transcribe(audio_file)
        
        if not spoken_text:
            await interaction.followup.send("❌ Could not understand your speech. Try speaking more clearly!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        # Calculate accuracy (no scoring in practice mode)
        accuracy = calculate_accuracy(spoken_text, twister['text'])
        time_seconds = (datetime.utcnow() - session.attempt_started_at).total_seconds()
        mistakes = find_differences(spoken_text, twister['text'])
        
        # Update session
        session.attempts += 1
        session.waiting_for_attempt = False
        
        # Send results (no score in practice)
        embed = create_results_embed(
            spoken_text,
            twister['text'],
            accuracy,
            time_seconds,
            0,  # No score in practice
            twister['difficulty'],
            mistakes
        )
        embed.title = "🎯 Practice Results"
        embed.set_field_at(
            len(embed.fields) - 2,  # Score field
            name="Score",
            value="Practice mode (no scoring)",
            inline=False
        )
        await interaction.followup.send(embed=embed)
        
        # Cleanup audio file
        try:
            os.remove(audio_file)
        except:
            pass
    
    @app_commands.command(name="twister_list", description="View all tongue twisters")
    @app_commands.describe(difficulty="Filter by difficulty")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
        app_commands.Choice(name="Insane", value="insane")
    ])
    async def list_twisters(
        self,
        interaction: discord.Interaction,
        difficulty: Optional[str] = None
    ):
        """View all tongue twisters."""
        if difficulty:
            twisters = get_twisters_by_difficulty(difficulty)
        else:
            twisters = get_all_twisters()
        
        embed = create_twister_list_embed(twisters, difficulty)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="twister_challenge", description="Start a timed challenge (10 twisters)")
    async def challenge(self, interaction: discord.Interaction):
        """Start a timed challenge mode."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        session = session_manager.get_session(
            str(interaction.user.id),
            str(interaction.user.voice.channel.id)
        )
        
        if not session:
            await interaction.response.send_message("❌ You must join a session first with `/twister join`!", ephemeral=True)
            return
        
        # Update session for challenge mode
        session.mode = 'timed_challenge'
        session.twisters_completed = 0
        session.twisters_total = config.CHALLENGE_TWISTER_COUNT
        session.challenge_results = []
        
        await interaction.response.send_message(
            "⚡ **TIMED CHALLENGE MODE** ⚡\n\n"
            "Complete 10 tongue twisters as fast and accurately as possible!\n\n"
            "Rules:\n"
            "• 30 seconds per twister\n"
            "• Mixed difficulties\n"
            "• Cumulative score\n"
            "• Results added to leaderboard\n\n"
            "Starting in 3... 2... 1... GO!",
            ephemeral=False
        )
        
        await asyncio.sleep(3)
        
        # Run challenge
        cumulative_score = 0
        results = []
        
        for i in range(config.CHALLENGE_TWISTER_COUNT):
            # Get random twister (mix of difficulties)
            if i < 3:
                difficulty = 'easy'
            elif i < 7:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
            
            twister = get_random_twister(difficulty)
            
            # Update session
            session.current_twister_id = twister['id']
            session.waiting_for_attempt = True
            session.attempt_started_at = datetime.utcnow()
            
            # Send progress
            embed = create_challenge_progress_embed(
                i + 1,
                config.CHALLENGE_TWISTER_COUNT,
                twister['text'],
                twister['difficulty'],
                cumulative_score
            )
            await interaction.followup.send(embed=embed)
            
            # Get voice client
            voice_client = self.voice_handler.get_voice_client(interaction.user.voice.channel.id)
            if not voice_client:
                await interaction.followup.send("❌ Voice connection lost!", ephemeral=True)
                break
            
            # Record audio
            recorder = AudioRecorder(voice_client)
            audio_file = await recorder.record_user_audio(
                interaction.user.id,
                config.CHALLENGE_TIME_PER_TWISTER
            )
            
            if not audio_file:
                await interaction.followup.send("❌ Failed to record audio. Skipping...", ephemeral=True)
                continue
            
            # Transcribe
            whisper = get_whisper()
            if not whisper:
                await interaction.followup.send("❌ Speech recognition not initialized!", ephemeral=True)
                break
            
            spoken_text = await whisper.transcribe(audio_file)
            
            if not spoken_text:
                await interaction.followup.send("❌ Could not understand speech. Skipping...", ephemeral=True)
                continue
            
            # Calculate score
            accuracy = calculate_accuracy(spoken_text, twister['text'])
            time_seconds = (datetime.utcnow() - session.attempt_started_at).total_seconds()
            score = calculate_score(accuracy, time_seconds, twister['difficulty'])
            is_successful = is_successful_attempt(accuracy)
            
            cumulative_score += score
            session.total_score += score
            session.attempts += 1
            if is_successful:
                session.successful_attempts += 1
            
            # Save result
            results.append({
                'text': twister['text'],
                'accuracy': accuracy,
                'time': time_seconds,
                'score': score,
                'difficulty': twister['difficulty']
            })
            
            # Save to database
            await db_manager.get_or_create_player(str(interaction.user.id), interaction.user.display_name)
            await db_manager.save_attempt(
                str(interaction.user.id),
                twister['id'],
                spoken_text,
                accuracy,
                time_seconds,
                score,
                twister['difficulty'],
                'challenge',
                session.session_id
            )
            await db_manager.update_player_stats(
                str(interaction.user.id),
                accuracy,
                time_seconds,
                score,
                twister['id'],
                is_successful
            )
            
            # Cleanup
            try:
                os.remove(audio_file)
            except:
                pass
            
            session.twisters_completed += 1
        
        # Challenge complete
        avg_accuracy = sum(r['accuracy'] for r in results) / len(results) if results else 0
        
        # Check if personal best
        player_stats = await db_manager.get_player_stats(str(interaction.user.id))
        is_pb = player_stats and cumulative_score > (player_stats.get('best_score', 0) or 0)
        
        # Get server rank
        rank = await db_manager.get_player_rank(
            str(interaction.user.id),
            'server',
            str(interaction.guild.id) if interaction.guild else None
        )
        
        embed = create_challenge_complete_embed(
            cumulative_score,
            avg_accuracy,
            results,
            is_pb,
            rank
        )
        await interaction.followup.send(embed=embed)
    
    # Stats Commands
    @app_commands.command(name="twister_stats", description="View player statistics")
    @app_commands.describe(user="User to view stats for (default: yourself)")
    async def stats(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None
    ):
        """View player statistics."""
        target_user = user or interaction.user
        
        stats = await db_manager.get_player_stats(str(target_user.id))
        
        if not stats:
            await interaction.response.send_message(f"❌ No statistics found for {target_user.mention}!", ephemeral=True)
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
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="twister_leaderboard", description="View leaderboards")
    @app_commands.describe(scope="Leaderboard scope", difficulty="Filter by difficulty")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Server", value="server"),
        app_commands.Choice(name="Global", value="global")
    ])
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
        app_commands.Choice(name="Insane", value="insane")
    ])
    async def leaderboard(
        self,
        interaction: discord.Interaction,
        scope: Optional[str] = "server",
        difficulty: Optional[str] = None
    ):
        """View leaderboards."""
        server_id = str(interaction.guild.id) if interaction.guild and scope == "server" else None
        
        leaderboard = await db_manager.get_leaderboard(
            scope=scope or "server",
            server_id=server_id,
            difficulty=difficulty,
            limit=15
        )
        
        if not leaderboard:
            await interaction.response.send_message("❌ No leaderboard data available yet!", ephemeral=True)
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
            str(interaction.user.id),
            scope or "server",
            server_id
        )
        
        if user_rank:
            embed.set_footer(text=f"Your rank: #{user_rank}")
        else:
            embed.set_footer(text="Play to get on the leaderboard!")
        
        await interaction.response.send_message(embed=embed)
    
    # Competitive Commands
    @app_commands.command(name="twister_duel", description="Challenge another player to a duel")
    @app_commands.describe(player="Player to challenge")
    async def duel(
        self,
        interaction: discord.Interaction,
        player: discord.Member
    ):
        """Challenge another player to a duel."""
        if interaction.user.id == player.id:
            await interaction.response.send_message("❌ You can't duel yourself!", ephemeral=True)
            return
        
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        if not player.voice or player.voice.channel != interaction.user.voice.channel:
            await interaction.response.send_message("❌ Your opponent must be in the same voice channel!", ephemeral=True)
            return
        
        # Create pending duel
        duel_id = str(uuid.uuid4())
        self.pending_duels[duel_id] = {
            'challenger_id': str(interaction.user.id),
            'opponent_id': str(player.id),
            'channel_id': str(interaction.user.voice.channel.id),
            'server_id': str(interaction.guild.id) if interaction.guild else "DM",
            'created_at': datetime.utcnow()
        }
        
        embed = discord.Embed(
            title="⚔️ DUEL CHALLENGE! ⚔️",
            description=(
                f"{interaction.user.mention} has challenged {player.mention}!\n\n"
                f"Format: Best of {config.DUEL_BEST_OF} rounds\n"
                f"- Same tongue twister for both players\n"
                f"- Highest score wins each round\n"
                f"- First to {config.DUEL_BEST_OF // 2 + 1} round wins overall"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text=f"{player.mention}, use /twister accept to accept! Challenge expires in 2 minutes.")
        
        await interaction.response.send_message(embed=embed)
        
        # Cleanup after timeout
        await asyncio.sleep(config.DUEL_TIMEOUT)
        if duel_id in self.pending_duels:
            del self.pending_duels[duel_id]
    
    @app_commands.command(name="twister_accept", description="Accept a pending duel challenge")
    async def accept(self, interaction: discord.Interaction):
        """Accept a pending duel challenge."""
        # Find pending duel for this user
        duel_id = None
        for did, duel in self.pending_duels.items():
            if duel['opponent_id'] == str(interaction.user.id):
                duel_id = did
                break
        
        if not duel_id:
            await interaction.response.send_message("❌ You don't have any pending duel challenges!", ephemeral=True)
            return
        
        duel = self.pending_duels[duel_id]
        del self.pending_duels[duel_id]
        
        challenger_id = int(duel['challenger_id'])
        opponent_id = int(duel['opponent_id'])
        channel_id = int(duel['channel_id'])
        
        challenger = interaction.guild.get_member(challenger_id) if interaction.guild else None
        if not challenger:
            await interaction.response.send_message("❌ Challenger not found!", ephemeral=True)
            return
        
        # Join voice channel
        voice_client = await self.voice_handler.join_voice_channel(interaction.user)
        if not voice_client:
            await interaction.response.send_message("❌ Failed to join voice channel!", ephemeral=True)
            return
        
        await interaction.response.send_message("⚔️ Duel accepted! Starting match...")
        
        # Run duel
        challenger_wins = 0
        opponent_wins = 0
        rounds_to_win = config.DUEL_BEST_OF // 2 + 1
        
        for round_num in range(1, config.DUEL_BEST_OF + 1):
            if challenger_wins >= rounds_to_win or opponent_wins >= rounds_to_win:
                break
            
            # Get random twister (increasing difficulty)
            if round_num <= 2:
                difficulty = 'easy'
            elif round_num <= 4:
                difficulty = 'medium'
            else:
                difficulty = 'hard'
            
            twister = get_random_twister(difficulty)
            
            await interaction.followup.send(
                f"⚔️ **ROUND {round_num}/{config.DUEL_BEST_OF}** ⚔️\n\n"
                f"Both players will say:\n"
                f"**\"{twister['text']}\"**\n\n"
                f"{challenger.mention}, you're up first!\n"
                f"I'm listening...",
                ephemeral=False
            )
            
            # Challenger's turn
            challenger_score = await self._process_player_attempt(
                interaction, voice_client, challenger, twister, round_num
            )
            
            if challenger_score is None:
                await interaction.followup.send("❌ Challenger's attempt failed. Skipping round...")
                continue
            
            await interaction.followup.send(
                f"{challenger.mention}: **{challenger_score['score']:,} points** "
                f"({challenger_score['accuracy']:.1f}% accuracy, {challenger_score['time']:.1f}s)"
            )
            
            await interaction.followup.send(f"Now {interaction.user.mention}'s turn!\nI'm listening...")
            
            # Opponent's turn
            opponent_score = await self._process_player_attempt(
                interaction, voice_client, interaction.user, twister, round_num
            )
            
            if opponent_score is None:
                await interaction.followup.send("❌ Opponent's attempt failed. Skipping round...")
                continue
            
            await interaction.followup.send(
                f"{interaction.user.mention}: **{opponent_score['score']:,} points** "
                f"({opponent_score['accuracy']:.1f}% accuracy, {opponent_score['time']:.1f}s)"
            )
            
            # Determine round winner
            if challenger_score['score'] > opponent_score['score']:
                challenger_wins += 1
                winner = challenger.mention
            elif opponent_score['score'] > challenger_score['score']:
                opponent_wins += 1
                winner = interaction.user.mention
            else:
                winner = "Tie"
            
            await interaction.followup.send(
                f"🎉 {winner} wins Round {round_num}!\n\n"
                f"Score: {challenger.mention}: {challenger_wins} | {interaction.user.mention}: {opponent_wins}"
            )
            
            await asyncio.sleep(2)
        
        # Determine match winner
        if challenger_wins > opponent_wins:
            winner = challenger
            winner_wins = challenger_wins
            loser_wins = opponent_wins
        elif opponent_wins > challenger_wins:
            winner = interaction.user
            winner_wins = opponent_wins
            loser_wins = challenger_wins
        else:
            winner = None
        
        if winner:
            embed = discord.Embed(
                title="🏆 DUEL COMPLETE! 🏆",
                description=f"{winner.mention} wins the duel!\n\nFinal Score: {challenger.mention}: {challenger_wins} | {interaction.user.mention}: {opponent_wins}",
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="🤝 DUEL COMPLETE! 🤝",
                description=f"It's a tie!\n\nFinal Score: {challenger.mention}: {challenger_wins} | {interaction.user.mention}: {opponent_wins}",
                color=discord.Color.blue()
            )
        
        await interaction.followup.send(embed=embed)
    
    async def _process_player_attempt(
        self,
        interaction: discord.Interaction,
        voice_client: discord.VoiceClient,
        player: discord.Member,
        twister: dict,
        round_num: int
    ) -> Optional[Dict]:
        """Process a player's attempt in a duel."""
        # Record audio
        recorder = AudioRecorder(voice_client)
        audio_file = await recorder.record_user_audio(player.id, config.VOICE_RECORDING_TIMEOUT)
        
        if not audio_file:
            return None
        
        # Transcribe
        whisper = get_whisper()
        if not whisper:
            return None
        
        start_time = datetime.utcnow()
        spoken_text = await whisper.transcribe(audio_file)
        
        if not spoken_text:
            return None
        
        # Calculate score
        accuracy = calculate_accuracy(spoken_text, twister['text'])
        time_seconds = (datetime.utcnow() - start_time).total_seconds()
        score = calculate_score(accuracy, time_seconds, twister['difficulty'])
        
        # Save to database
        await db_manager.get_or_create_player(str(player.id), player.display_name)
        await db_manager.save_attempt(
            str(player.id),
            twister['id'],
            spoken_text,
            accuracy,
            time_seconds,
            score,
            twister['difficulty'],
            'duel',
            None
        )
        await db_manager.update_player_stats(
            str(player.id),
            accuracy,
            time_seconds,
            score,
            twister['id'],
            is_successful_attempt(accuracy)
        )
        
        # Cleanup
        try:
            os.remove(audio_file)
        except:
            pass
        
        return {
            'score': score,
            'accuracy': accuracy,
            'time': time_seconds,
            'spoken': spoken_text
        }
    
    # Custom Twister Commands
    @app_commands.command(name="twister_custom_add", description="Add a custom tongue twister")
    @app_commands.describe(text="The tongue twister text", difficulty="Difficulty level")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard"),
        app_commands.Choice(name="Insane", value="insane")
    ])
    async def custom_add(
        self,
        interaction: discord.Interaction,
        text: str,
        difficulty: Optional[str] = None
    ):
        """Add a custom tongue twister."""
        # Validate text
        if len(text) < 10:
            await interaction.response.send_message("❌ Tongue twister must be at least 10 characters long!", ephemeral=True)
            return
        
        if len(text) > 500:
            await interaction.response.send_message("❌ Tongue twister must be less than 500 characters!", ephemeral=True)
            return
        
        # Auto-detect difficulty if not provided
        if not difficulty:
            word_count = len(text.split())
            if word_count <= 5:
                difficulty = 'easy'
            elif word_count <= 10:
                difficulty = 'medium'
            elif word_count <= 15:
                difficulty = 'hard'
            else:
                difficulty = 'insane'
        
        # Get next custom twister ID (start from 1000)
        db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
        
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT MAX(twister_id) FROM tongue_twisters WHERE twister_id >= 1000"
            ) as cursor:
                row = await cursor.fetchone()
                next_id = (row[0] or 999) + 1
            
            # Insert custom twister
            await db.execute(
                """
                INSERT INTO tongue_twisters 
                (twister_id, text, difficulty, word_count, focus_sounds, created_by, is_official)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_id,
                    text,
                    difficulty,
                    len(text.split()),
                    "Custom",
                    str(interaction.user.id),
                    False
                )
            )
            await db.commit()
        
        embed = discord.Embed(
            title="✅ Custom Tongue Twister Added!",
            description=f"Your custom twister has been added with ID #{next_id}",
            color=discord.Color.green()
        )
        embed.add_field(name="Text", value=text, inline=False)
        embed.add_field(name="Difficulty", value=difficulty.capitalize(), inline=True)
        embed.add_field(name="ID", value=f"#{next_id}", inline=True)
        embed.set_footer(text="Use /twister practice to try it out!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="twister_custom_list", description="View custom tongue twisters")
    async def custom_list(self, interaction: discord.Interaction):
        """View custom tongue twisters."""
        db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
        
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                """
                SELECT twister_id, text, difficulty, created_by
                FROM tongue_twisters
                WHERE is_official = FALSE
                ORDER BY twister_id DESC
                LIMIT 20
                """
            ) as cursor:
                twisters = []
                async for row in cursor:
                    twisters.append({
                        'id': row[0],
                        'text': row[1],
                        'difficulty': row[2],
                        'created_by': row[3]
                    })
        
        if not twisters:
            await interaction.response.send_message("❌ No custom tongue twisters found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📜 Custom Tongue Twisters",
            color=discord.Color.blue()
        )
        
        twister_list = "\n".join(
            f"**#{t['id']}** - {t['text'][:50]}{'...' if len(t['text']) > 50 else ''} "
            f"({t['difficulty']})"
            for t in twisters[:15]
        )
        
        embed.description = twister_list[:4096]
        embed.set_footer(text=f"Showing {len(twisters)} custom twisters. Use /twister practice <id> to try them!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="twister_daily", description="Start the daily challenge")
    async def daily(self, interaction: discord.Interaction):
        """Start the daily challenge."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        session = session_manager.get_session(
            str(interaction.user.id),
            str(interaction.user.voice.channel.id)
        )
        
        if not session:
            await interaction.response.send_message("❌ You must join a session first with `/twister join`!", ephemeral=True)
            return
        
        # Get or create today's daily challenge
        db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
        today = date.today()
        
        async with aiosqlite.connect(db_path) as db:
            # Check if daily challenge exists
            async with db.execute(
                "SELECT twister_id FROM daily_challenges WHERE challenge_date = ?",
                (today,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    twister_id = row[0]
                else:
                    # Create new daily challenge with random twister
                    twister = get_random_twister()
                    twister_id = twister['id']
                    await db.execute(
                        "INSERT INTO daily_challenges (challenge_date, twister_id) VALUES (?, ?)",
                        (today, twister_id)
                    )
                    await db.commit()
            
            # Get twister
            async with db.execute(
                "SELECT text, difficulty FROM tongue_twisters WHERE twister_id = ?",
                (twister_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    await interaction.response.send_message("❌ Daily challenge twister not found!", ephemeral=True)
                    return
                
                twister_text = row[0]
                twister_difficulty = row[1]
        
        # Update session
        session.current_twister_id = twister_id
        session.waiting_for_attempt = True
        session.attempt_started_at = datetime.utcnow()
        session.mode = 'daily'
        
        embed = discord.Embed(
            title="📅 Daily Challenge",
            description=f"Today's tongue twister for everyone!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Difficulty",
            value=twister_difficulty.capitalize(),
            inline=True
        )
        embed.add_field(
            name="Twister ID",
            value=f"#{twister_id}",
            inline=True
        )
        embed.add_field(
            name="Say this:",
            value=f"**\"{twister_text}\"**",
            inline=False
        )
        embed.set_footer(text="I'm listening... (30 second timer)")
        
        await interaction.response.send_message(embed=embed)
        
        # Get voice client
        voice_client = self.voice_handler.get_voice_client(interaction.user.voice.channel.id)
        if not voice_client:
            await interaction.followup.send("❌ Voice connection lost!", ephemeral=True)
            return
        
        # Record audio
        recorder = AudioRecorder(voice_client)
        audio_file = await recorder.record_user_audio(interaction.user.id, config.VOICE_RECORDING_TIMEOUT)
        
        if not audio_file:
            await interaction.followup.send("❌ Failed to record audio. Make sure your microphone is working!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        # Transcribe
        whisper = get_whisper()
        if not whisper:
            await interaction.followup.send("❌ Speech recognition not initialized!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        await interaction.followup.send("🎤 Processing your speech...", ephemeral=True)
        
        spoken_text = await whisper.transcribe(audio_file)
        
        if not spoken_text:
            await interaction.followup.send("❌ Could not understand your speech. Try speaking more clearly!", ephemeral=True)
            session.waiting_for_attempt = False
            return
        
        # Calculate accuracy and score
        accuracy = calculate_accuracy(spoken_text, twister_text)
        time_seconds = (datetime.utcnow() - session.attempt_started_at).total_seconds()
        score = calculate_score(accuracy, time_seconds, twister_difficulty)
        is_successful = is_successful_attempt(accuracy)
        
        # Find mistakes
        mistakes = find_differences(spoken_text, twister_text)
        
        # Update session
        session.attempts += 1
        if is_successful:
            session.successful_attempts += 1
        session.total_score += score
        session.waiting_for_attempt = False
        
        # Save to database
        await db_manager.get_or_create_player(str(interaction.user.id), interaction.user.display_name)
        attempt_id = await db_manager.save_attempt(
            str(interaction.user.id),
            twister_id,
            spoken_text,
            accuracy,
            time_seconds,
            score,
            twister_difficulty,
            'daily',
            session.session_id
        )
        await db_manager.update_player_stats(
            str(interaction.user.id),
            accuracy,
            time_seconds,
            score,
            twister_id,
            is_successful
        )
        
        # Save daily challenge attempt
        db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
        
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                """
                INSERT INTO daily_challenge_attempts 
                (attempt_id, challenge_date, user_id, score, accuracy, time_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (attempt_id, today, str(interaction.user.id), score, accuracy, time_seconds)
            )
            await db.commit()
        
        # Get daily leaderboard rank
        db_path = os.getenv("DATABASE_PATH", "./data/twister.db")
        
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                """
                SELECT COUNT(*) + 1
                FROM daily_challenge_attempts
                WHERE challenge_date = ? AND score > ?
                """,
                (today, score)
            ) as cursor:
                row = await cursor.fetchone()
                daily_rank = row[0] if row else 1
        
        # Send results
        embed = create_results_embed(
            spoken_text,
            twister_text,
            accuracy,
            time_seconds,
            score,
            twister_difficulty,
            mistakes
        )
        embed.set_footer(text=f"Daily Challenge Rank: #{daily_rank} | Try again tomorrow for a new challenge!")
        await interaction.followup.send(embed=embed)
        
        # Cleanup audio file
        try:
            os.remove(audio_file)
        except:
            pass


async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(GameCommands(bot))
