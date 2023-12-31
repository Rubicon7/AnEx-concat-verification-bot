
# Secrets:
concat_api_secret = "<CONCAT API SECRET>"
discord_bot_token = "<DISCORD BOT TOKEN>"

# Access URLs
concat_api_base_url = "https://reg.anthroexpo.com"
concat_api_token_fetch_url = concat_api_base_url + "/api/oauth/token"
concat_api_user_fetch_url = concat_api_base_url + "/api/v0/users/search"
concat_api_reg_fetch_url = concat_api_base_url + "/api/v0/registration/search"

# Settings
database_path = "user_sessions.json"

playing_message = "Excel Any%"

discord_verified_role_server = 000000000000000000       # Server where the verified role will be given.
discord_verified_role_id = 000000000000000000          # The role that will be given to the user once verified.
discord_role_addition_log_entry = "Automatic verification"

automated_authentication_max_tries = 3                  # How many tries a user is allowed to attempt authentication with the bot in DMs.


# Channel settings:
DM_relay_channel = 000000000000000000                                    # Where ALL dms go, so you can monitor who says what to the bot.
DM_authentication_history_relay_channel = 000000000000000000               # Where authentication attempts go, and what their status is.

DM_self_initiate_reaction_message_channel_id =  000000000000000000           # The ID of the message below's channel.
DM_self_initiate_reaction_message_id = 000000000000000000                # The ID of the message users react on to have the bot reach out to them.
DM_self_initiate_reaction_message_emoji = '\U0001F4DD'  # What emoji to listen for on reactions. Currently :pencil2:



#Messages

DM_message_out_of_tries = "Apologies, for user security, there's no more automated attempts left. Please contact a staff member for assistance in getting the verified role."

DM_message_instruction = """Hello! Here's how you get verified:

Paste the email you used and the order number you received from registration into this DM **in one message together.**  

Example: `andrea@scissortailfandoms.org 601`

The email you used to register can be found at <https://reg.anthroexpo.com/account/login>
Order number can be found in your email inbox.

Here's where to find them:"""
DM_message_instruction_attachments = ["example1.png","example2.png"]

DM_message_authentication_success = "Got it! You're verified. No further action required."
DM_message_already_verified = "Already verified- no further action required."
DM_message_authentication_fail_canretry = "Could not verify that information. Make sure you've entered it correctly. Email is case sensitive!"
DM_message_authentication_ordernum_already_used = "This order number was already used by another user. One order number can only be used to verify one person."
DM_message_unable_to_parse = "Could not understand your message. Make sure it's entered correctly."
DM_message_authentication_system_error = "I'm having technical difficulties. Staff have been notified. Please try again, or contact staff if this error persists."


