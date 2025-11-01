import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

print(f"Token length: {len(token)}")
print(f"Token preview: {token[:15]}...{token[-10:]}")

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f'SUCCESS! Logged in as {client.user}')
    await client.close()

print("Attempting to connect...")
try:
    client.run(token)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
