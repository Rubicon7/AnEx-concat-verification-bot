"""Personal mode for personal things."""

import shutil
import traceback
from typing import List
import discord
from discord.ext import commands
from urllib.request import urlopen
import os.path
from datetime import timedelta
import asyncio

from discord.ext.commands import has_permissions, MissingPermissions

import json

import requests

import bot_settings
import data_model



### Model

class Session:

    def __init__(self, userid: int,triesleft:int, verified:bool, consumed_order_number:int):
        self.userid = userid
        self.triesleft = triesleft
        self.verified = verified
        self.consumed_order_number = consumed_order_number




### Communication API

class RegValidationAPI:
    def __init__(self, filename: str):
        self.filename = filename
        self.lock = asyncio.Lock()
        self.api_token = "invalid"

    """ Read a session file from disk. """
    async def read_sessions(self) -> List[Session]:
        async with self.lock:
            try:
                with open(self.filename, 'r') as file:
                    data = json.load(file)
                    return [Session(**session_data) for session_data in data['sessions']]
            except (FileNotFoundError, json.JSONDecodeError):
                return []
            except(KeyError):
                await self.write_sessions([]) #Initialize database

    """ Write a session file to disk. """
    async def write_sessions(self, sessions: List[Session]):
        async with self.lock:
            # Create a backup before writing changes
            backup_filename = f"{self.filename}.bak"
            try:
                shutil.copy2(self.filename, backup_filename)
            except Exception as e:
                print(f"[write_sessions]: Could not create backup: {e}")
                pass

            # Write the updated data to the file
            with open(self.filename, 'w') as file:
                data = {'sessions': [vars(session) for session in sessions]}
                json.dump(data, file, indent=2)
    

    """ Returns true if a session entry exists yet. False if not."""
    async def has_session(self, user_id:int) -> bool:
        sessions = await self.read_sessions()

        for session in sessions: #Iterate through and find a session with our userid.
            if(session.userid == user_id):
                return True
        return False

    """ Updates the concat access token. Throws an exception if there's an issue."""
    def update_token(self):
        url = bot_settings.concat_api_token_fetch_url
        headers = {"Content-Type" : "application/x-www-form-urlencoded"}

        #Generate access token

        data = {
            "client_id": "1",
            "client_secret": bot_settings.concat_api_secret,
            "grant_type": "client_credentials",
            "scope": ["user:read","registration:read"],
        }

        try:
            response = requests.post(url, headers=headers, data=data)


            if response.status_code == 200:
                # Successful request
                self.api_token = response.json().get("access_token")
                print("Updated concat token")
            else:
                # Handle errors
                print("Error:", response.text)
        except Exception as e:
            print("update_token - Cannot obtain token:")
            traceback.print_exc()
            raise Exception(data_model.enums.api_cannot_get_token)
            

    
    """ Get a resulting concat user's order number from a given email. Throws exceptions on errors."""
    def get_order_number_from_email(self, email:str):
        #Can throw various exceptions depending on the result

        
        
        headers = {"Content-Type" : "application/json",
           "Authorization":f"Bearer {self.api_token}",}
        
        data = {
            "limit":1,
            "filter":{
                "email":email,
            },
        }

        #Attempt 1 - attempt to gather information.
        # If there's a 'no user with this email' error, return no_email_match
        # If there's an invalid token error, refresh token.
        # Attempt 2. If there's an invalid token error, throw no_token.

        response = requests.post(bot_settings.concat_api_user_fetch_url, headers=headers, data=json.dumps(data))

        if('"Invalid token."' in response.text or '"Token expired."' in response.text): #Attempt 2.
            self.update_token()
            headers = {"Content-Type" : "application/json",
           "Authorization":f"Bearer {self.api_token}",}
            response = requests.post(bot_settings.concat_api_user_fetch_url, headers=headers, data=json.dumps(data))
        
        

        print(f"get_user_from_email response: {response.text}")

        jsondata = None
        payload = None
        try:
            jsondata = json.loads(response.text)
            #userid = jsondata.get('data')[0].get('id')
            #print(f"User ID: {userid}") #If there's a key error, the exception will catch this.
        except Exception as e:
            print(f"[get_user_from_email] Json parse user data exception: {e}")
            raise Exception(data_model.enums.api_system_error)

        if 'data' in jsondata and len(jsondata['data']) != 0: #Has a data payload
            # Fetch user id for this email then look up registrations with it.
            
            userid = jsondata.get('data')[0].get('id')
            data = {
                "limit":1,
                "filter":{
                    "userIds":[userid], 
                },
            }

            response = requests.post(bot_settings.concat_api_reg_fetch_url, headers=headers, data=json.dumps(data))

            if('"Invalid token."' in response.text or '"Token expired."' in response.text): #Attempt 2. In case the token was invalidated between now and last request
                self.update_token()
                headers = {"Content-Type" : "application/json",
            "Authorization":f"Bearer {self.api_token}",}
                response = requests.post(bot_settings.concat_api_reg_fetch_url, headers=headers, data=json.dumps(data))

            try:
                jsondata = json.loads(response.text)
                print(f"Order number: {jsondata.get('data')[0].get('order').get('orderId')}") #If there's a key error, the exception will catch this.
            except Exception as e:
                print(f"[get_user_from_email] Json prase order exception: {e}")
                raise Exception(data_model.enums.failure_emailok_noorder) #No data, no order


            return jsondata.get('data')[0].get('order').get('orderId')

        else: #No data, invalid email
            raise Exception(data_model.enums.failure_bademail)


        #if response.status_code == 200:
        #    # Successful request
        #    print("Response:", response.text)
        #else:
        #    # Handle errors
        #    print("Error:", response.text)


        pass
    




    """ Return a session object associated with a user id. If they don't have one, one is created and returned."""
    async def get_session(self, user_id:int) -> Session:
        sessions = await self.read_sessions()

        for session in sessions: #Iterate through and find a session with our userid.
            if(session.userid == user_id):
                return session

        #Here, no session exists for this user, so create one.
        print(f"Creating session for user {user_id}")

        newsession = Session(user_id,bot_settings.automated_authentication_max_tries,False,-1)
        sessions.append(newsession)
        await self.write_sessions(sessions)

        return newsession

    """ Set the session object of the new session's user ID to the new session object. Automatically saves to disk."""
    async def set_session(self, newSession:Session):
        sessions = await self.read_sessions()

        #Find the session of this userid. Remove it if it exists.
        for session in sessions: #Iterate through and find a session with our userid.
            if(session.userid == newSession.userid):
                sessions.remove(session)
                break
        
        sessions.append(newSession)
        await self.write_sessions(sessions)



### Discord 

class RegValidationInterface(commands.Cog):
    '''Reg validation Interface cog'''



    def __init__(self, bot:commands.Bot):
        self.bot : commands.Bot = bot
        self.api : RegValidationAPI = RegValidationAPI(bot_settings.database_path)
        #self.sessions = await self.api.read_sessions()
        bot.loop.create_task(dropReactOnMyMessageService(bot))
        
        
    
    
    
    
    ### Listeners
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):
        """Runs when a reaction is tacked onto a message"""
        if(payload.user_id == self.bot.user.id): return #Ignore myself

        if(payload.message_id == bot_settings.DM_self_initiate_reaction_message_id):
            if(str(payload.emoji) == bot_settings.DM_self_initiate_reaction_message_emoji):
                print("goodness")
                await self.userPressedSelfInitiateEmoji(payload.user_id, payload.member)

    

    """Run when a user added a reaction to a self-initiation message."""
    async def userPressedSelfInitiateEmoji(self, user_id:int, member:discord.Member):
        # User has entry in sessions: 
        #   User is verified already:
        #       Send verified message
        #   User has attempts left:
        #       Send intro message
        #   Else:
        #       Send apology message.
        user = self.bot.get_user(user_id)

        session = await self.api.get_session(user_id)

        if(session.verified):
            return await user.send(bot_settings.DM_message_already_verified)
        if(session.triesleft <= 0):
            return await user.send(bot_settings.DM_message_out_of_tries)
        else:
            attachments = [discord.File(f) for f in bot_settings.DM_message_instruction_attachments]
            return await user.send(bot_settings.DM_message_instruction,files=attachments)
            


    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        print("message: "+message.content)
        guild = self.bot.get_guild(bot_settings.discord_verified_role_server)
        
        #is not me
        if(message.author.id == self.bot.user.id): return
        
        #if in dms
        #if user also in auth server
        #if no session yet say intro and don't parse input
        #else normal flow
        if isinstance(message.channel, discord.abc.PrivateChannel): #Is a DM
            member = guild.get_member(message.author.id)
            if(member is not None): #Is in the relevant server
                if(await self.api.has_session(message.author.id) == False): #Post intro message if no existing session
                    await self.api.get_session(message.author.id) #Create initial session
                    attachments = [discord.File(f) for f in bot_settings.DM_message_instruction_attachments]
                    await message.channel.send(bot_settings.DM_message_instruction,files=attachments)
                    return
                else: #Existing session, parse message flow:
                    await self.handleValidationMessage(message)


    async def handleValidationMessage(self, message:discord.Message):
        log_channel = self.bot.get_channel(bot_settings.DM_authentication_history_relay_channel) 
        result = "NONE"
        session = await self.api.get_session(message.author.id)

        if(session.verified):
            return await message.channel.send(bot_settings.DM_message_already_verified)

        if(session.triesleft <= 0):
            return await message.channel.send(bot_settings.DM_message_out_of_tries)
        
        # Parse input
        parseOrderNum = -1
        parseEmail = ""
        try:
            parseEmail, parseOrderNum = self.tryParseValidationMessage(message.content)
            print("parsed: ",parseEmail, parseOrderNum)
        except Exception as e:
            print("[handleValidationMessage] Exception parsing: "+str(e))
            result = data_model.enums.failure_cannot_prase
            await message.channel.send(bot_settings.DM_message_unable_to_parse)
        

        if(parseOrderNum != -1 and parseEmail != ""):
            

            if(await self.checkIfOrderNumAlreadyUsed(parseOrderNum)): #This runs if this order number was used before.
                await message.channel.send(bot_settings.DM_message_authentication_ordernum_already_used)
                session.triesleft -= 1
                await self.api.set_session(session)
            else: #Not already used ordernum

                order_number_from_email = -1
            
                try:
                    order_number_from_email = self.api.get_order_number_from_email(parseEmail)
                    #if this matches the parsed order number, verify the user.

                    if(int(order_number_from_email) == int(parseOrderNum)):
                        await self.verify_user(session, parseOrderNum)
                        await message.channel.send(bot_settings.DM_message_authentication_success)
                        result = data_model.enums.success
                    else:
                        raise Exception(data_model.enums.failure_emailok_badordernum)

                except Exception as e:
                    print("Verification exception: "+str(e))
                    traceback.print_exc()
                    result = e.args[0] #Some error occurred.
                    if(result == data_model.enums.api_cannot_get_token):
                        await message.channel.send(bot_settings.DM_message_authentication_system_error)
                    elif(result == data_model.enums.api_system_error):
                        await message.channel.send(bot_settings.DM_message_authentication_system_error)
                    elif(   result == data_model.enums.failure_bademail
                    or result == data_model.enums.failure_emailok_badordernum
                    or result == data_model.enums.failure_emailok_noorder):
                        await message.channel.send(bot_settings.DM_message_authentication_fail_canretry)
                        session.triesleft -= 1
                        await self.api.set_session(session)
                        if(session.triesleft <= 0):
                            await message.channel.send(bot_settings.DM_message_out_of_tries)

                    else:
                        #catchall, some other error maybe.
                        await message.channel.send(bot_settings.DM_message_authentication_system_error)
                
                









        debugstr = f"{message.author.name}/({message.author.id}) -> {result} - [{session.triesleft} tries left], Verified: {session.verified}, "
        if(session.verified): debugstr += f"Order num: {session.consumed_order_number}"

        await log_channel.send(debugstr)

    """Gives the user a verified role, marks their session as verified, and consumes the order number."""
    async def verify_user(self, session:Session, ordernum:int):
        gld = self.bot.get_guild(bot_settings.discord_verified_role_server) 
        m = gld.get_member(session.userid) #Get the user from server's perspective (Member)
        role = gld.get_role(bot_settings.discord_verified_role_id)
        
        await m.add_roles(role, 
                          reason=bot_settings.discord_role_addition_log_entry + f" (Order {ordernum})")
        session.consumed_order_number = ordernum
        session.verified = True
        await self.api.set_session(session)
        


    def tryParseValidationMessage(self, text:str) -> (str, int):
        num = None
        email = None
        
        if(text == None or text == ""): raise Exception(data_model.enums.failure_cannot_prase)
        for word in text.split():
            if(word.isdigit()):
                num = int(word)
                continue
            if('@' in word and '.' in word):
                email = word
                continue
        if(num is not None and email is not None):
            return email, num
        raise Exception(data_model.enums.failure_cannot_prase)
    
    """ Return true if this order number was already used for verification in the past."""
    async def checkIfOrderNumAlreadyUsed(self, ordernum:int):
        sessions = await self.api.read_sessions()
        for sesh in sessions:
            if(int(sesh.consumed_order_number) == int(ordernum)):
                return True
        return False




""" Drops the initial react on the message pointed to in bot_settings.py """
async def dropReactOnMyMessageService(bot):
    mchan = bot.get_channel(bot_settings.DM_self_initiate_reaction_message_channel_id)
    mesg = await mchan.fetch_message(bot_settings.DM_self_initiate_reaction_message_id)

    await mesg.add_reaction(bot_settings.DM_self_initiate_reaction_message_emoji)
    

async def setup(bot):
    await bot.add_cog(RegValidationInterface(bot))

