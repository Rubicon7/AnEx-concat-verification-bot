import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import discord.abc
import sys, traceback
import bot_settings
import os

os.environ['DISPLAY'] = ':0' #linux req'd

intents = discord.Intents.default()
intents.members = True
#intents.presences = True
intents.reactions=True 

def get_prefix(bot, msg):
    return '' #Disable prefix
    

desc = '''Registration validation bot'''

startup_extensions = ['regvalidation']
bot = commands.Bot(command_prefix=get_prefix,description=desc,intents=intents)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name=bot_settings.playing_message))
    bot.remove_command('help')
    if __name__ == '__main__':
        for extension in startup_extensions:
            try:
                await bot.load_extension(extension)
            except Exception as e:
                print('Failed to load extension ' + extension, file=sys.stderr)
                traceback.print_exc()
    
    print('Successfully logged in and booted!')


@bot.event
async def on_message(message):
    # Handles logging DM history.
    log_channel = bot.get_channel(bot_settings.DM_relay_channel) 
    
    
    
    if isinstance(message.channel, discord.DMChannel):
        #Makes sure it's not her talking, may be a good idea to delete just to make sure DMs are actually sending...
        if message.author.id != bot.user.id: 
            #Sends message to the logs channel with the Name, ID, and message from the DM
            await log_channel.send(message.author.name + "/()" + str(message.author.id) + ") : " + message.content)
            if(message.attachments and message.author.id != bot.user.id):
                a = ""
                for i in message.attachments: a += a + i.url
                
                await log_channel.send("Attachments: "+ a)
            
            


bot.run(bot_settings.discord_bot_token, reconnect=True)
