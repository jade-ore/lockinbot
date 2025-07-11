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
created_roles = {}
# generate leaderboard
async def generate_leaderboard_embed():
    text = []
    sorted_times = dict(sorted(total_time.items(), key=lambda x: x[1], reverse=True))
    
    for i, (user, time) in enumerate(sorted_times.items(), 1):
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        text.append(f"#{i}: <@{user}>, time working: {hours}h {minutes}m {seconds}s")
    color = int("FFFF00", 16)
    return discord.Embed(color=color, title='Leaderboard', description="\n".join(text))

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
            embed = discord.Embed(color=int("FF0000", 16), title="locked in already", description="you're already working :3")
            await ctx.send(embed=embed)
            return
        working_start_time[user_id] = time.time()
        color = int("d883f2", 16)
        embed = discord.Embed(color=color, title="started working", description=f"{ctx.author.mention} started a work session! you guys should join too :3 \nuse `!work end` to end the session\nuse `!checktime` to see how much you've been working")
        await ctx.send(embed=embed)
    elif mode == 'end':
        if not user_id in working_start_time:
            embed= discord.Embed(color=int("FF0000", 16), title="lazy bum", description="bruh start working before you can end")
            await ctx.send(embed=embed)
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
        color = int("80f2ff", 16)
        embed = discord.Embed(color=color, title="work session end", description=f"nice work {ctx.author.mention}! you worked:\n\n{hours} hours, {minutes} minutes and {seconds} seconds\n\nin total today, you have worked:\n\n{total_hours} hours, {total_minutes} minutes, and {total_seconds} seconds")
        await ctx.send(embed=embed)
        print(total_time)
    elif mode == 'help':
        color = int("00FF00", 16)
        embed = discord.Embed(title="work command guide", description="\n\nto start your work session, use `!work start`\n to end a work session use `!work end` \nuse `!leaderboard` to see the leaderboard", color=color)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(color=int("FF0000", 16), title="i dont understand", description="not valid syntax bud\n use `!work help` to use")
        await ctx.send(embed=embed)
# parses if nothing is there
@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(color=int("FF0000", 16), title="i dont understand", description="\nyou have to put a word after the command, use `!work help` for more info")
        await ctx.send(embed=embed)
# checks amount of time worked
@bot.command()
async def checktime(ctx):
    user_id = ctx.author.id
    if user_id in working_start_time:
        session_time = int(time.time() - working_start_time[user_id])
        hours = session_time // 3600
        minutes = (session_time % 3600) // 60
        seconds = session_time % 60
        embed = discord.Embed(color=int("d883f2", 16), title="how long you worked", description=f"hey <@{ctx.author.id}>! \n\nyou have worked for {hours} hours, {minutes} minutes and {seconds} seconds\n\nnow get back to work :3")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(color=int("FF0000", 16), title="lazy bum", description="bro you arent even working")
        await ctx.send(embed=embed)
# leaderboard
@bot.command()
async def leaderboard(ctx):
    embed = await generate_leaderboard_embed()
    await ctx.send(embed=embed)
# role maker
@bot.command()
async def rolecreate(ctx, color, *, roleName):
    guild = ctx.guild
    if ctx.author.id not in created_roles:
        created_roles[ctx.author.id] = []
    if color.startswith('#'):
        color = color[1:]
    try:
        color_int = int(color, 16)
        role = await guild.create_role(name=roleName, colour=discord.Colour(color_int))
        created_roles[ctx.author.id].append(role.id)
        await ctx.author.add_roles(role)
        embed = discord.Embed(color=int("00FF00", 16),title="role created! :3", description=f"created role '{roleName}' with color #{color}")
        await ctx.send(embed=embed)
    except ValueError:
        embed = discord.Embed(color=int("FF0000",16),title="invalid color", description="use hex color format (#FF0000 or FF0000)")
        await ctx.send(embed=embed)
        
@bot.command()
async def roledelete(ctx, inputrole):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=inputrole)
    if not role:
        embed = discord.Embed(color=int("FF0000",16),title="nonexistent?!", description="this role doesnt exist`")
        await ctx.send(embed=embed)
        return
    if role.id not in created_roles[ctx.author.id]:
        embed = discord.Embed(color=int("FF0000",16),title="no grief :3", description="you can only delete roles you made\nto make a role use `!rolecreate`")
        await ctx.send(embed=embed)
        return
    await role.delete()
    embed = discord.Embed(color=int("fc9e3f", 16), title="executed! >:3", description=f"deleted role {role}")
    await ctx.send(embed=embed)

@bot.command()
async def rolehelp(ctx):
    color = int("00FF00", 16)
    embed = discord.Embed(colour=color, title="Role help", description="\n!rolecreate `<hex color>` `<role name>` this is to create a role, make sure you use hex numbers\n!roledelete `<name>` you can only delete roles that you created")
    await ctx.send(embed=embed)

webserver.keep_alive()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)