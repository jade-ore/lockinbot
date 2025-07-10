import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import time
import datetime
import webserver

# get the token
load_dotenv(dotenv_path='.env', verbose=True)
token = os.getenv('DISCORD_TOKEN')

# see if .env exists and gets key
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('DISCORD_TOKEN='):
                token = line.split('=', 1)[1].strip()
                print(f"Manual token length: {len(token)}")
                break
except FileNotFoundError:
    print("Could not find .env file manually")

# essential bot stuff
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# bot initialization
bot = commands.Bot(command_prefix='!', intents=intents)

# variables used for work command
working_start_time = {}
total_time = {}
# generate leaderboard
async def generate_leaderboard_embed():
    text = []
    sorted_times = dict(sorted(total_time.items(), key=lambda x: x[1], reverse=True))
    
    for i, (user, time) in enumerate(sorted_times.items(), 1):
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        text.append(f"#{i}: <@{user}>, time working: {hours}h {minutes}m {seconds}s")
    
    return discord.Embed(title='Leaderboard', description="\n".join(text))

# reset leaderboard
@tasks.loop(time=datetime.time(hour=5, minute=0))
async def resetLeaderboard():
    global total_time
    embed = await generate_leaderboard_embed()
    channel = bot.get_channel(1380594904627019827)
    if channel:
        await channel.send("This is the leaderboard for today")
        await channel.send(embed=embed)
    total_time = {}

# prints when bot is ready
@bot.event
async def on_ready():
    print(f"ready to go in {bot.user.name}")
    resetLeaderboard.start()

# work command
@bot.command()
async def work(ctx, *, mode):
    user_id = ctx.author.id
    if mode == 'start':
        if user_id in working_start_time:
            await ctx.send("bro you are already working")
            return
        working_start_time[user_id] = time.time()
        print(working_start_time)
        await ctx.send(f"{ctx.author.mention} started a work session, yall should join in and also work - use `!work end` to end")
    elif mode == 'end':
        if not user_id in working_start_time:
            await ctx.send("bruh start working before you can end")
            return
        if user_id not in total_time:
            total_time[user_id] = 0
        session_time = int(time.time() - working_start_time.pop(user_id))
        total_time[user_id] += session_time
        hours = session_time // 3600
        minutes = (session_time % 3600) // 60
        seconds = session_time % 60
        total_hours = total_time[user_id] // 3600
        total_minutes = (total_time[user_id] % 3600) // 60
        total_seconds = total_time[user_id] % 60
        await ctx.send(f"{ctx.author.mention} worked for {hours} hours, {minutes} minutes and {seconds} seconds")
        await ctx.send(f"in total, {ctx.author.mention} worked {total_hours} hours, {total_minutes} minutes, and {total_seconds} seconds")
        print(total_time)
    elif mode == 'help':
        await ctx.send("to start your work session, use `!work start` and to end it use `!work end`")
    else:
        await ctx.send("not valid syntax bud, use `!work help` to use")
# parses if nothing is there
@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("you have to put a word after the command, use `!work help` for more info")
# checks amount of time worked
@bot.command()
async def checktime(ctx):
    user_id = ctx.author.id
    if user_id in working_start_time:
        session_time = int(time.time() - working_start_time[user_id])
        hours = session_time // 3600
        minutes = (session_time % 3600) // 60
        seconds = session_time % 60
        await ctx.send(f"you have worked for {hours} hours, {minutes} minutes and {seconds} seconds")
    else:
        await ctx.send("bro you arent even working")
# leaderboard
@bot.command()
async def leaderboard(ctx):
    embed = await generate_leaderboard_embed()
    await ctx.send(embed=embed, silent=True)

webserver.keep_alive()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)