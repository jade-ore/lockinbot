import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from os import system
import time
import datetime
import webserver
import re

# get the token
load_dotenv(dotenv_path='.env', verbose=True)
token = os.getenv('DISCORD_TOKEN')
ALLOWED_ID = 1067830715510706276

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
removed_time = {}
banned_people = []
job_filter_activated = False
# generate leaderboard
async def generate_leaderboard_embed():
    text = []
    sorted_times = dict(sorted(total_time.items(), key=lambda x: x[1], reverse=True))
    
    for i, (user, time) in enumerate(sorted_times.items(), 1):
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = time % 60
        text.append(f"#{i}: <@{user}>, time working: {hours}h {minutes}m {seconds}s\n")
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

@bot.event
async def on_message(message):
    ctx = bot.get_context(message)
    if message.author == bot.user:
        return
    has_job = re.search(r"j+?([^a-z1-9])*?[op0]+?([^a-z1-9])*?[bd]+?", message.content, re.IGNORECASE)
    if has_job and job_filter_activated:
        await message.delete()
        await message.channel.send(f"{message.author.mention} PLEASE CENSOR J*B")
        if message.author.id == ALLOWED_ID:
            await message.author.send("i know j*b is a very bad word but maybe you were typing a story heres your message just in case")
            await message.author.send(message.content)
    
    await bot.process_commands(message)

@bot.command()
async def helppls(ctx):
    embed = discord.Embed(color=int("FFFF00", 16), title="help", description="\n\n `!helppls` this command \n `!work help` gives you info about work\n`!rolehelp` gives you info about role \n`!selfremove <seconds>` removes time based on seconds\n`!selfremove undo` undo you selfremove if you remove too much\n`!calculateseconds <hours> <minutes> <seconds>` turns hours minutes seconds into seconds (example `!calculateseconds 1 0 0` would give 3600)")
    await ctx.send(embed=embed)
# work command
@bot.command()
async def work(ctx, *, mode):
    user_id = ctx.author.id
    if ctx.author.id in banned_people:
        embed = discord.Embed(color=int("FF0000", 16), title="you are BANNED!", description=f"\n<@{user_id}>you have gotten banned from using this bot, please go to jayden and explain why you should be unbanned alone with proof of you actually working")
        await ctx.send(embed=embed)
        return
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
async def checktime(ctx, member: discord.Member = None):
    user_id = ctx.author.id
    if ctx.author.id in banned_people:
        embed = discord.Embed(color=int("FF0000", 16), title="you are BANNED!", description=f"\n<@{user_id}>you have gotten banned from using this bot, please go to jayden and explain why you should be unbanned alone with proof of you actually working")
        await ctx.send(embed=embed)
        return
    if member:
        user_id = member.id
        member_check = ctx.guild.get_member(user_id)
        if member_check == None:
            await ctx.send("this person doesnt even exist")
            return
        if user_id not in working_start_time:
            embed = discord.Embed(color=int("FF0000", 16), title="lazy bum", description="bro they arent even working")
            await ctx.send(embed=embed)
            return
        session_time = int(time.time() - working_start_time[user_id])
        hours = session_time // 3600
        minutes = (session_time % 3600) // 60            
        seconds = session_time % 60
        embed = discord.Embed(color=int("d883f2", 16), title="how long they worked", description=f"hey <@{ctx.author.id}>! \n\n<@{user_id}> has worked for {hours} hours, {minutes} minutes and {seconds} seconds\n\nnow get back to work :3")
        await ctx.send(embed=embed)
    else:
        if user_id not in working_start_time:
            embed = discord.Embed(color=int("FF0000", 16), title="lazy bum", description="bro you arent even working")
            await ctx.send(embed=embed)
            return
        session_time = int(time.time() - working_start_time[user_id])
        hours = session_time // 3600
        minutes = (session_time % 3600) // 60
        seconds = session_time % 60
        embed = discord.Embed(color=int("d883f2", 16), title="how long you worked", description=f"hey <@{ctx.author.id}>! \n\nyou have worked for {hours} hours, {minutes} minutes and {seconds} seconds\n\nnow get back to work :3")
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

# role delete
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

#role help 
@bot.command()
async def rolehelp(ctx):
    color = int("00FF00", 16)
    embed = discord.Embed(colour=color, title="Role help", description="\n!rolecreate `<hex color>` `<role name>` this is to create a role, make sure you use hex numbers\n!roledelete `<name>` you can only delete roles that you created")
    await ctx.send(embed=embed)
# for jayden

@bot.command()
async def admin(ctx, command, id_input, time_input=None):
    id = int(id_input)
    int_time = int(time_input)
    if not int(ctx.author.id) == 1224926925185880218:
        await ctx.send("you arent jayden so you cant use this command")
        return
    if command == "forcestop":
        fake_time = int(time.time() - working_start_time.pop(id))
        hours = fake_time // 3600
        minutes = (fake_time % 3600) // 60
        seconds = fake_time % 60
        embed = discord.Embed(color=int("FF0000", 16), title="FORCEFULLY STOPPED!", description=f"<@{id}> was forcefully stopped\n\nthis person faked worked for {hours} hours, {minutes} minutes, and {seconds} seconds!!!\n\nno cheating >:(")
        await ctx.send(embed=embed)
    if command == "removetime":
        if time_input == None:
            await ctx.send("you need to add a time broski")
            return
        time_of_id = total_time[id]
        total_time[id] = time_of_id - int_time
        embed = discord.Embed(color=int("FF0000", 16), title="TIME REMOVED!", description=f"removed {int_time} seconds")
        await ctx.send(embed=embed)
    if command == "addtime":
        if time_input == None:
            await ctx.send("you need to add a time broski")
            return
        if id not in total_time:
            total_time[id] = 0
        total_time[id] = total_time[id] + int_time
        embed = discord.Embed(color=int("00FF00", 16), title="TIME ADDED!", description=f"added {int_time} seconds")
        await ctx.send(embed=embed)

@bot.command()
async def update(ctx, command, user=None, start=None):
    if command == "export":
        await ctx.send("people who have worked")
        for user, time in total_time.items():
            await ctx.send(f"user: {user}, time:{time}")
        await ctx.send("people who are currently working")
        for user, time in working_start_time.items():
            await ctx.send(f"user:{user}, UTC start time:{time}")
    if command == "import":
        working_start_time[int(user)] = float(start)
        await ctx.send(f"added {user} to dict")
        print(working_start_time)

@bot.command()
async def selfremove(ctx, time):
    if ctx.author.id in banned_people:
        embed = discord.Embed(color=int("FF0000", 16), title="you are BANNED!", description=f"\n{ctx.author.id}>you have gotten banned from using this bot, please go to jayden and explain why you should be unbanned alone with proof of you actually working")
        await ctx.send(embed=embed)
        return
    if time == 'undo':
        if ctx.author.id not in removed_time or removed_time[ctx.author.id] == 0:
            await ctx.send("you never removed any time")
            return
        total_time[ctx.author.id] += removed_time[ctx.author.id]
        removed_time[ctx.author.id] = 0
    try:
        if ctx.author.id not in total_time or total_time[ctx.author.id] < int(time):
            await ctx.send("you didnt even work that amount of time :pensive:")
            return
        total_time[ctx.author.id] -= int(time)
        await ctx.send(f"removed {time} seconds")
        removed_time[ctx.author.id] = int(time)
    except ValueError:
        if time == 'undo':
            return
        await ctx.send("time must be a number in seconds")

@bot.command()
async def calculateseconds(ctx, hrs_input, mins_input, sec_input):
    hrs = int(hrs_input)
    mins = int(mins_input)
    sec = int(sec_input)
    await ctx.send(f"{hrs} hours {mins} minutes {sec} seconds is {(hrs * 3600) + (mins * 60) + sec} seconds in total")

@bot.command()
async def jobfilter(ctx, on_off):
    global job_filter_activated
    if on_off == "on":
        job_filter_activated = True
        await ctx.send("j*b filter on")
    elif on_off == "off":
        job_filter_activated = False
        await ctx.send("job filter off")

@bot.command
async def loveyou(ctx):
    await ctx.send("ty love you too :heart:")
webserver.keep_alive()
bot.run(token=token)
# reset