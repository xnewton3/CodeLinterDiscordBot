import discord
import subprocess
import tempfile
import os
import json
import logging
import asyncio
import warnings
import datetime
import time
import json
import re
import sys
import os
import requests
import subprocess
import discord
import nltk
import pytz
import aiohttp
import traceback
import functools
import logging
import cachetools

from os import readv
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from discord import Embed, Intents
from discord.ext import tasks, commands
from discord.ext.commands import cooldowns, Bot, when_mentioned_or
from difflib import SequenceMatcher
from pytz import timezone
from functools import wraps
from cachetools import TTLCache

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
bot_owner_id = 557917550923612170 # This is MY userid, make sure you replace it with your own!

# Load linters from linters.json
logging.info("Loading linters configuration from linters.json")
with open('linters.json') as f:
    linters = json.load(f)

# Define intents
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Custom directory for temporary files
custom_temp_dir = 'tempfiles'  # Change this to your desired path


# Custom Permission Checks
def is_bot_owner():
    def predicate(ctx):
        return ctx.author.id == bot_owner_id

    return commands.check(predicate)


@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')


@client.event
@is_bot_owner()
async def on_message(message):
    logging.debug(f"Environment Variables: {os.environ}")
    # Ignore messages from non-owner users and bots

    language = None

    if '```' in message.content:
        logging.info("Detected code block in message.")
        code_block = message.content.split('```')
        if len(code_block) >= 2:
            code = code_block[1].strip()
            logging.debug("Extracted code from message.")
        else:
            await message.channel.send("Error: Code block structure is incorrect.")
            logging.warning("Code block structure in message is incorrect.")
            return

        if message.content.startswith('```\n<?php'):
            language = 'php'
            logging.info("Detected PHP code block.")

        linter_info = linters.get(language)
        if not linter_info or not linter_info.get("linter"):
            await message.channel.send(f"There is no linter registered for '{language}'.")
            logging.warning(f"No linter registered for '{language}'.")
            return

        linter = linter_info["linter"]
        formatter = linter_info.get("formatter")
        logging.debug(f"Linter: {linter}, Formatter: {formatter}")

        # Create a temporary file in the custom directory
        with tempfile.NamedTemporaryFile(suffix='.php', dir=custom_temp_dir, delete=False) as tmp_file:
            tmp_file.write(code.encode('utf-8'))
            tmp_file_path = tmp_file.name
            logging.info(f"Temporary file created at {tmp_file_path}")

        try:
            # Run the linter
            logging.info("Running linter process.")
            lint_process = subprocess.run(['php', linter, tmp_file_path, '--standard=PHPruleset.xml'],
                                          capture_output=True, text=True)
            logging.debug(f"Linter output: {lint_process.stdout}")
            if lint_process.returncode != 0:
                await message.channel.send(f"Linter found issues:\n```\n{lint_process.stdout}\n```")
                logging.info("Linter found issues.")

                # Now run the formatter with phpcbf
                if formatter:
                    logging.info("Running formatter process.")

                    # Check if the file exists and print its contents
                    if os.path.exists(tmp_file_path):
                        with open(tmp_file_path, 'r') as formatted_file:
                            temp_file_contents = formatted_file.read()
                            logging.debug(f"Temporary file contents:\n{temp_file_contents}")
                    else:
                        logging.error(f"Temporary file does not exist at {tmp_file_path}")

                    fix_process = subprocess.run(
                        ['php', 'linters/phpcbf.phar', '--standard=PHPruleset.xml', tmp_file_path],
                        capture_output=True, text=True)
                    logging.debug(f"Formatter output: {fix_process.stdout}")
                    logging.debug(f"Formatter error output: {fix_process.stderr}")

                    if fix_process.returncode == 1:
                        logging.info("Formatter successfully applied fixes.")
                        with open(tmp_file_path, 'r') as formatted_file:
                            formatted_code = formatted_file.read()
                        await message.channel.send(f"Formatted Code:\n```{language}\n{formatted_code}\n```")
                    else:
                        await message.channel.send(f"Formatter failed:\n```\n{fix_process.stderr}\n```")
                        logging.error("Formatter failed to apply fixes.")
            else:
                await message.channel.send("No linting issues found.")
                logging.info("No linting issues found.")

        finally:
            # os.remove(tmp_file_path)
            logging.info(f"Temporary file {tmp_file_path} not deleted.")


client.run(TOKEN)
