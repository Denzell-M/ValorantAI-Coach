"""
I, Denzell Willis-Mackay, 000371340, state that this is my original work and any source that has not been deemed appropriate
will be cited and given appropriate reference. All work has been done by myself and not obtained from another classmate inside
or outside of Mohawk College.

Please see the Documentation.txt file for more information.

Denzell Mackay, September 2024
Student ID:000371340
"""

import discord
from openai import OpenAI
from discord.ext import commands
import logging
#import asyncio

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load OpenAI API key
with open("api/gpt.txt", "r") as f:
    gptApi_key = f.read()

# Initialize OpenAI client
client = OpenAI(api_key=gptApi_key)

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Called when the bot is fully logged in."""
    logger.info(f'Logged on as {bot.user}')
    logger.info('------------------')
    print("Hello! I'm your friendly bot.")

    # Sync commands globally
    try:
        
        print("Attempting to sync commands...")
        synced = await bot.tree.sync()
        print(f"Commands synced: {[command.name for command in synced]}")
        logger.info(f"Synced {len(synced)} commands globally.")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

# Add the /info command
@bot.tree.command(name="info", description="Provides information about this bot.")
async def faq(interaction: discord.Interaction):
    """Responds with information to help users identify this bot."""
    faq_content = (
        "**FAQ Bot**\n"
        "Hello! I'm a helpful assistant bot developed by LostZenith.\n"
        "I can coach you on becoming a better Valorant player. If you have any questions about the game or my abilities, feel free to ask!\n\n"
        "**How to use:**\n"
        "- Please use slash commands in order to function this coaching bot!"
        "- What is a slash command? Type \"/\" followed by the word \"coach\" and you will be able to write a question."
        "- Please note that is how you were able to open this dialog! Pretty cool?"
        "- More features released in the future!"
        "**Features:**\n"
        "- Provide tips on improving skills.\n"
        "- Provide information about the game and its mechanics.\n"
        "- Assist users in learning about Valorant.\n"
        "- Offer suggestions for improving skills.\n"
        "- Help users find resources and information.\n"
        "- Provide tips on macro strategies.\n"
        "\n"
        "**Developer Contact:**\n"
        "If you have any questions or need support, please contact LostZenith."
    )
    await interaction.response.send_message(faq_content, ephemeral=True)


# Track the last 5 interactions only
conversation_history = []

# Add the /coach command to interact with OpenAI
@bot.tree.command(name="coach", description="Ask coach a question.")
async def gpt(interaction: discord.Interaction, *, question: str):
    """Handles the /coach command to interact with OpenAI."""
    await interaction.response.defer()  # Helps with timeout issues

    # Log the user details and their prompt
    user_id = interaction.user.id
    username = interaction.user.name

    try:
        # Use the current question to classify
        classification_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Classify the following question as tactical advice, mechanics advice, or off-topic."},
                {"role": "user", "content": question}
            ],
            temperature=0,
            max_tokens=32,
        )
        classification = classification_response.choices[0].message.content.strip().lower()

        valorant_maps = ["Ascent", "Bind", "Haven", "Split", "Icebox", "Breeze", "Fracture", "Pearl", "Lotus"]
        valorant_roles = ["Controller", "Duelist", "Sentinel", "Initiator"]
        valorant_agents = ["Jett", "Phoenix", "Sage", "Brimstone", "Omen", "Cypher", "Clove", "Sova", "Killjoy", "Raze", "Reyna", "Skye", "Yoru", "Astra", "KAY/O", "Chamber", "Neon", "Fade", "Harbor", "Gekko"]

        # Initialize base system prompt
        dialog = [
            {"role": "system",
             "content": ("You are the world's best Valorant coach. Always provide tactical and mechanics advice with enthusiasm, "
                         "and answer only questions related to Valorant gameplay and strategy. Do not solve math problems or provide information "
                         f"unrelated to Valorant tactics, maps, agents, or roles. The maps in the game are: {valorant_maps}, the roles in the game are: {valorant_roles}, and the agents in the game are: {valorant_agents}."
                         "If a question appears to be a math problem or unrelated query, respond by reminding the user that you can only help with Valorant gameplay and strategy.")}
        ]

        # Check for maps and agents mentioned
        mentioned_maps = [map_name for map_name in valorant_maps if map_name.lower() in question.lower()]
        mentioned_roles = [role for role in valorant_roles if role.lower() in question.lower()]
        mentioned_agents = [agent_name for agent_name in valorant_agents if agent_name.lower() in question.lower()]

        if mentioned_maps:
            map_names = ", ".join(mentioned_maps)
            dialog[0]["content"] += f" The user is asking about the map(s): {map_names}."
        if mentioned_roles:
            role_names = ", ".join(mentioned_roles)
            dialog[0]["content"] += f" The user is interested in the agent role(s): {role_names}. Focus on strategies specific to these role(s)."
        if mentioned_agents:
            agent_names = ", ".join(mentioned_agents)
            dialog[0]["content"] += f" The user is interested in the agent(s): {agent_names}."

        # Append recent conversation history to dialog
        for entry in conversation_history:
            dialog.append(entry)
        
        # Add the current user question to dialog
        dialog.append({"role": "user", "content": question})

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=dialog,
            temperature=0.7,
            max_tokens=256,
        )
        reply = response.choices[0].message.content + "\n\n"

        # Limit conversation history to the last 5 turns (user-bot pairs)
        if len(conversation_history) >= 10:  # 5 turns (user + bot response)
            conversation_history.pop(0)  # Remove oldest message
            conversation_history.pop(0)  # Remove oldest response

        # Add the current user question and bot reply to history
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": reply})

        # Send the reply
        await interaction.followup.send(reply)

        # Log additional details for debugging
        logger.info(f"Detected maps: {mentioned_maps}, Detected agents: {mentioned_agents}, Detected roles: {mentioned_roles}")
        logger.info(f"User: {username} (ID: {user_id}) asked: {question}\n")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await interaction.followup.send(
            "I'm sorry, an error occurred while processing your request. Please try again later."
        )


def main():
    """Set up and log in the bot."""
    discord_token = "api/key.txt"

    try:
        with open(discord_token, "r", encoding='utf-8') as file:
            token = file.read().strip()
        bot.run(token)
    except FileNotFoundError:
        logger.error(
            f"Error: Could not find the token file at {discord_token}. Please check that the working directory is correct."
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
