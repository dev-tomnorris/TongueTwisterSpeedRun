"""Competitive play commands (duels and tournaments)."""

import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import uuid

from game.session_manager import session_manager
from game.scoring import calculate_score, is_successful_attempt
from voice.handler import VoiceHandler
from voice.recorder import AudioRecorder
from voice.speech_to_text import get_whisper
from utils.text_similarity import calculate_accuracy, find_differences
from utils.embeds import create_twister_challenge_embed, create_results_embed
from data.tongue_twisters import get_random_twister
from database.manager import db_manager
import config


class CompetitiveCommands(commands.Cog):
    """Competitive play commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_handler = VoiceHandler(bot)
        self.pending_duels: Dict[str, Dict] = {}  # duel_id -> duel info
    
    @discord.slash_command(name="twister", description="Tongue twister game commands")
    async def twister(self, ctx: discord.ApplicationContext):
        """Main twister command group."""
        pass
    
    @twister.subcommand(name="duel", description="Challenge another player to a duel")
    async def duel(
        self,
        ctx: discord.ApplicationContext,
        opponent: discord.Member = discord.SlashCommandOption(
            name="player",
            description="Player to challenge",
            required=True
        )
    ):
        """Challenge another player to a duel."""
        if ctx.author.id == opponent.id:
            await ctx.respond("❌ You can't duel yourself!", ephemeral=True)
            return
        
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.respond("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        if not opponent.voice or opponent.voice.channel != ctx.author.voice.channel:
            await ctx.respond("❌ Your opponent must be in the same voice channel!", ephemeral=True)
            return
        
        # Create pending duel
        duel_id = str(uuid.uuid4())
        self.pending_duels[duel_id] = {
            'challenger_id': str(ctx.author.id),
            'opponent_id': str(opponent.id),
            'channel_id': str(ctx.author.voice.channel.id),
            'server_id': str(ctx.guild.id) if ctx.guild else "DM",
            'created_at': datetime.utcnow()
        }
        
        embed = discord.Embed(
            title="⚔️ DUEL CHALLENGE! ⚔️",
            description=(
                f"{ctx.author.mention} has challenged {opponent.mention}!\n\n"
                f"Format: Best of {config.DUEL_BEST_OF} rounds\n"
                f"- Same tongue twister for both players\n"
                f"- Highest score wins each round\n"
                f"- First to {config.DUEL_BEST_OF // 2 + 1} round wins overall"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text=f"{opponent.mention}, use /twister accept to accept! Challenge expires in 2 minutes.")
        
        await ctx.respond(embed=embed)
        
        # Cleanup after timeout
        await asyncio.sleep(config.DUEL_TIMEOUT)
        if duel_id in self.pending_duels:
            del self.pending_duels[duel_id]
    
    @twister.subcommand(name="accept", description="Accept a pending duel challenge")
    async def accept(self, ctx: discord.ApplicationContext):
        """Accept a pending duel challenge."""
        # Find pending duel for this user
        duel_id = None
        for did, duel in self.pending_duels.items():
            if duel['opponent_id'] == str(ctx.author.id):
                duel_id = did
                break
        
        if not duel_id:
            await ctx.respond("❌ You don't have any pending duel challenges!", ephemeral=True)
            return
        
        duel = self.pending_duels[duel_id]
        del self.pending_duels[duel_id]
        
        challenger_id = int(duel['challenger_id'])
        opponent_id = int(duel['opponent_id'])
        channel_id = int(duel['channel_id'])
        
        challenger = ctx.guild.get_member(challenger_id) if ctx.guild else None
        if not challenger:
            await ctx.respond("❌ Challenger not found!", ephemeral=True)
            return
        
        # Join voice channel
        voice_client = await self.voice_handler.join_voice_channel(ctx.author)
        if not voice_client:
            await ctx.respond("❌ Failed to join voice channel!", ephemeral=True)
            return
        
        await ctx.respond("⚔️ Duel accepted! Starting match...")
        
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
            
            await ctx.followup.send(
                f"⚔️ **ROUND {round_num}/{config.DUEL_BEST_OF}** ⚔️\n\n"
                f"Both players will say:\n"
                f"**\"{twister['text']}\"**\n\n"
                f"{challenger.mention}, you're up first!\n"
                f"I'm listening...",
                ephemeral=False
            )
            
            # Challenger's turn
            challenger_score = await self._process_player_attempt(
                ctx, voice_client, challenger, twister, round_num
            )
            
            if challenger_score is None:
                await ctx.followup.send("❌ Challenger's attempt failed. Skipping round...")
                continue
            
            await ctx.followup.send(
                f"{challenger.mention}: **{challenger_score['score']:,} points** "
                f"({challenger_score['accuracy']:.1f}% accuracy, {challenger_score['time']:.1f}s)"
            )
            
            await ctx.followup.send(f"Now {ctx.author.mention}'s turn!\nI'm listening...")
            
            # Opponent's turn
            opponent_score = await self._process_player_attempt(
                ctx, voice_client, ctx.author, twister, round_num
            )
            
            if opponent_score is None:
                await ctx.followup.send("❌ Opponent's attempt failed. Skipping round...")
                continue
            
            await ctx.followup.send(
                f"{ctx.author.mention}: **{opponent_score['score']:,} points** "
                f"({opponent_score['accuracy']:.1f}% accuracy, {opponent_score['time']:.1f}s)"
            )
            
            # Determine round winner
            if challenger_score['score'] > opponent_score['score']:
                challenger_wins += 1
                winner = challenger.mention
            elif opponent_score['score'] > challenger_score['score']:
                opponent_wins += 1
                winner = ctx.author.mention
            else:
                winner = "Tie"
            
            await ctx.followup.send(
                f"🎉 {winner} wins Round {round_num}!\n\n"
                f"Score: {challenger.mention}: {challenger_wins} | {ctx.author.mention}: {opponent_wins}"
            )
            
            await asyncio.sleep(2)
        
        # Determine match winner
        if challenger_wins > opponent_wins:
            winner = challenger
            winner_wins = challenger_wins
            loser_wins = opponent_wins
        elif opponent_wins > challenger_wins:
            winner = ctx.author
            winner_wins = opponent_wins
            loser_wins = challenger_wins
        else:
            winner = None
        
        if winner:
            embed = discord.Embed(
                title="🏆 DUEL COMPLETE! 🏆",
                description=f"{winner.mention} wins the duel!\n\nFinal Score: {challenger.mention}: {challenger_wins} | {ctx.author.mention}: {opponent_wins}",
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="🤝 DUEL COMPLETE! 🤝",
                description=f"It's a tie!\n\nFinal Score: {challenger.mention}: {challenger_wins} | {ctx.author.mention}: {opponent_wins}",
                color=discord.Color.blue()
            )
        
        await ctx.followup.send(embed=embed)
    
    async def _process_player_attempt(
        self,
        ctx: discord.ApplicationContext,
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
        # Pass the target text as initial prompt to help Whisper transcribe correctly
        spoken_text = await whisper.transcribe(audio_file, initial_prompt=twister['text'])
        
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
            import os
            os.remove(audio_file)
        except:
            pass
        
        return {
            'score': score,
            'accuracy': accuracy,
            'time': time_seconds,
            'spoken': spoken_text
        }
    
    @twister.subcommand(name="tournament", description="Start a tournament (Phase 3)")
    async def tournament(
        self,
        ctx: discord.ApplicationContext,
        players: Optional[str] = discord.SlashCommandOption(
            name="players",
            description="Comma-separated list of player mentions",
            required=False
        )
    ):
        """Start a tournament (placeholder for Phase 3)."""
        await ctx.respond(
            "🏆 Tournament mode is coming soon!\n"
            "This feature will support bracket-style tournaments with multiple players.",
            ephemeral=True
        )


def setup(bot: commands.Bot):
    """Load the cog."""
    bot.add_cog(CompetitiveCommands(bot))

