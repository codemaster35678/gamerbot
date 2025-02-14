import discord
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
import os
import random
import json
from datetime import datetime
import os
from dotenv import load_dotenv

import socket
import threading

def health_check_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 8080))  # Koyeb checks port 80
    server.listen(5)

    while True:
        conn, addr = server.accept()
        conn.close()  # Instantly close the connection to pass the check

threading.Thread(target=health_check_server, daemon=True).start()


# Load environment variables from .env file
load_dotenv()

def is_admin(ctx):
    return ctx.author.id in whitelist_ids

# Retrieve sensitive data securely
BOT_TOKEN = os.getenv("BOT_TOKEN")
purchases_category_id = int(os.getenv("PURCHASES_CATEGORY_ID"))
feedback_channel_id = int(os.getenv("FEEDBACK_CHANNEL_ID"))
whitelist_ids = [int(os.getenv("ADMIN_ID"))]
vouch_channel_id = int(os.getenv("VOUCH_CHANNEL_ID"))
whitelist_server_id = int(os.getenv("WHITELISTED_SERVER_ID")) # 🔒 Replace with your server ID
whitelisted_user_id = int(os.getenv("WHITELISTED_USER_ID"))


# Set up intents and bot prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)



# Example inventory with images and descriptions
inventory = {
    'apple': {'price': 5, 'stock': 10, 'image': 'https://example.com/apple.jpg', 'description': 'A shiny red apple'},
    'banana': {'price': 3, 'stock': 20, 'image': 'https://example.com/banana.jpg', 'description': 'A ripe yellow banana'},
    'gaming_pc': {'price': 1000, 'stock': 5, 'image': 'https://example.com/gaming_pc.jpg', 'description': 'A high-end gaming PC'},
}



# Shop name
shop_name = "Gamer's Services and Shop"


# Terms & Conditions Command
@bot.command(name="terms")
@commands.check(is_admin)
async def terms(ctx):
    terms_embed = discord.Embed(
        title="**Terms & Conditions**",
        description=(
            "1. **No refunds after purchase.**\n"
            "2. **Following product usage instructions is mandatory.**\n"
            "3. **Warranty for 30minutes only or stated before vouch.**\n"
            "4. **Product quality is guaranteed.**\n"
            "5. **Be respectful in the community.**\n\n"
            "By purchasing from this shop, you agree to these terms and conditions."
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=terms_embed)


# Vouch Command (Explains how to use the rate command)
@bot.command(name="vouch")
async def vouch(ctx):
    vouch_embed = discord.Embed(
        title="**How to Vouch**",
        description=(
            "To vouch for a product, use the `!rate` command after purchasing.\n\n"
            "1. Type `!rate <rating (1 to 5)> <feedback>`\n"
            "2. You can give a rating from 1 (poor) to 5 (excellent).\n"
            "3. Share your honest feedback about the product you purchased."
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=vouch_embed)


# Rate Command (Used to rate a product after purchase)
@bot.command(name="rate")
async def rate(ctx, stars: int, *, feedback: str):
    if stars < 1 or stars > 5:
        await ctx.send("Please provide a rating between 1 and 5.")
        return

    feedback_embed = discord.Embed(
        title=f"**Product Feedback**",
        description=f"**Rating:** {stars} Stars\n**Feedback:** {feedback}",
        color=discord.Color.blue()
    )
    feedback_embed.set_footer(text=f"Reviewed by {ctx.author}")
    feedback_embed.set_thumbnail(url=ctx.author.avatar.url)

    feedback_channel = bot.get_channel(feedback_channel_id)
    if feedback_channel:
        await feedback_channel.send(embed=feedback_embed)
        await ctx.send("Thank you for your feedback!")
    else:
        await ctx.send("Unable to find the feedback channel.")



@bot.command(name="listproduct")
@commands.check(is_admin)
async def list_product(ctx):
    await ctx.send("Please provide the channel ID where the product listing will be sent:")
    channel_id = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    channel = bot.get_channel(int(channel_id.content))

    await ctx.send("Please provide the title (in bold font):")
    title = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

    await ctx.send("Please provide the description (with emojis supported):")
    description = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

    await ctx.send("Please provide the image URL or upload an image (or type 'none' for no image):")
    image = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

    await ctx.send("Please provide the footer text:")
    footer = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

    embed = discord.Embed(title=f"**{title.content}**", description=description.content, color=discord.Color.blue())

    # Add separator line
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    
    if image.content.lower() != 'none':
        embed.set_image(url=image.content)

    embed.set_footer(text=footer.content)

    await ctx.send("Do you want to add a 'Buy Now' button? (yes/no)")
    buy_button_response = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

    if buy_button_response.content.lower() == "yes":
        # Add Buy Now button
        view = View()
        button = Button(label="Buy Now 🛒", style=discord.ButtonStyle.green, custom_id="buy_now")

        async def buy_now_callback(interaction):
            # Create a new channel for the user under the 'Purchases' category
            guild = interaction.guild
            user = interaction.user
            category = discord.utils.get(guild.categories, id=purchases_category_id)
            
            if category:
                # Create the purchase channel under the specified category
                purchase_channel = await guild.create_text_channel(f"purchase-{user.name}-{random.randint(1000, 9999)}", category=category)

                # Send the same embed message to the new channel
                await purchase_channel.send(embed=embed)

                # Add permissions for the user
                await purchase_channel.set_permissions(user, read_messages=True, send_messages=True, read_message_history=True)

                await interaction.response.send_message(f"Your purchase request has been created in {purchase_channel.mention}!", ephemeral=True)
            else:
                await interaction.response.send_message("Failed to find the 'Purchases' category.", ephemeral=True)

        button.callback = buy_now_callback
        view.add_item(button)

        await channel.send(embed=embed, view=view)
    else:
        await channel.send(embed=embed)




# Verify Command
@bot.command(name="verify")
@commands.check(is_admin)
async def verify(ctx):
    embed = discord.Embed(
        title="**Verify Your Account**",
        description="Click the button below to verify your account and gain access to the shop.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://dbl-static.usercontent.prism.gg/avatars/704367240962769013/5233823a0cc1b094ee712e2150a57a96.png?size=256")

    view = View()
    verify_button = Button(label="Verify ✅", style=discord.ButtonStyle.green, url="https://restorecord.com/verify/%E2%9A%A1GAMER'S%20SERVICES%20AND%20SHOP%F0%9F%9B%92")

    view.add_item(verify_button)
    await ctx.send(embed=embed, view=view)


# Admin Panel Command
@bot.command(name="adminpanel")
async def admin_panel(ctx):
    if ctx.author.id not in whitelist_ids:
        await ctx.send("You do not have permission to access the admin panel.")
        return

    await ctx.send("Welcome to the Admin Panel! What would you like to do?\n1. Add Product\n2. Remove Product\n3. List Products\n4. Update Stock\n5. End Session")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=600)
        if msg.content == '1':
            await ctx.send("Please provide the product name:")
            product_name = await bot.wait_for('message', check=check, timeout=600)
            await ctx.send("Please provide the product price:")
            product_price = await bot.wait_for('message', check=check, timeout=600)
            await ctx.send("Please provide the stock quantity:")
            product_stock = await bot.wait_for('message', check=check, timeout=600)
            await ctx.send("Please provide the product image URL (or 'none' for no image):")
            product_image = await bot.wait_for('message', check=check, timeout=600)
            await ctx.send("Please provide the product description:")
            product_description = await bot.wait_for('message', check=check, timeout=600)

            inventory[product_name.content] = {
                'price': int(product_price.content),
                'stock': int(product_stock.content),
                'image': product_image.content if product_image.content != 'none' else None,
                'description': product_description.content
            }
            await ctx.send(f"Product **{product_name.content}** added successfully!")
        elif msg.content == '5':
            await ctx.send("Ending session...")
            return
        else:
            await ctx.send("Invalid option. Ending session.")
    except Exception as e:
        await ctx.send("Session timed out due to inactivity. Please try again.")

VOUCH_IMAGE_FOLDER = "profile_pics"  # Folder where profile pictures (ppf) are stored

if not os.path.exists(VOUCH_IMAGE_FOLDER):
    os.makedirs(VOUCH_IMAGE_FOLDER)

# Predefined list of 500 usernames (example, please extend this list)
predefined_usernames = [
    "user123", "coolguy24", "theking57", "shadow_jedi", "gamerboss", "thedarkknight89", "oceanwave23", 
    "samuraiwarrior", "purplestorm21", "mysticmage", "lightningbolt15", "ironman77", "nightcrawler2020", 
    "bluehawk2022", "silentwolf22", "cyberpunk_xx", "supernova88", "kingofspades", "mightyphoenix", 
    "dragon_king", "alpha_wolf33", "spacepilot1", "whispering_angel", "stormchaser77", "devilmaycry666", 
    "speedster_29", "zombiehunter33", "ghost_trainer", "freedom_fighter88", "wildcard_jack", "rockstar_14", 
    "timeless_hero", "shadow_reaper", "frostbite_ranger", "flamingphoenix_7", "wildstorm_2023", "dark_knight45",
    "xcaliber_88", "techguy_11", "dracarys_dragon", "speedygamer_13", "lastsamurai123", "neon_lion20",
    # Add more usernames up to 500...
]

# Feedback sentences (example, please extend this list)
feedback_sentences = [
    "they are a good person always helpful", "fast and reliable service great experience", "i love chatting with them they are always so nice",
    "one of the best servicers they were very professional", "would recommend them for sure very nice experience", "has done a really good job always there when needed",
    "best experience ever with them always easy and clear to work with", "helped me a lot with what I needed, highly recommend", "really cool person to talk with, very easy to deal with",
    "great service and nice person to work with", "very helpful but could improve their communication skills", "done a good job could be quicker but still okay", 
    "happy with the results, could improve a bit on speed tho", "always helpful and positive vibes, love it", "was nice to work with but could improve the quality",
    "they were great and always answered my questions quickly", "overall great experience with them, really helped me a lot", "works fast but they should proofread more often",
    "good vibes but some details were missed here and there", "friendly and knowledgeable, highly recommend", "very polite and great communicator", "the job was done really well", 
    "they provided a lot of help and assistance", "would definitely go to them again", "helpful but a little slow at times", "very supportive and gave great advice", 
    "super efficient but they could be a bit more punctual", "good work overall but some mistakes here and there", "very reliable and trustworthy", "excellent service!",
    "good service but not perfect could be more detail-oriented", "impressed with the work they did", "always a pleasure to work with", "quick and easy process", 
    "very professional and thorough with everything", "the quality was good, but I expected a bit more", "would work with them again for sure", "satisfied but room for improvement",
    "could've been faster but was still a great experience", "very good communication and effort", "they helped me a lot, great work", "took a bit of time but worth it",
    "impressed with their professionalism", "overall very satisfied, could improve on response times", "good but a few small mistakes here and there", "great experience working with them",
    # Add more feedback sentences up to 500...
]

# Vouch system using randomly generated names and predefined usernames
def get_random_username():
    return random.choice(predefined_usernames) if random.random() < 0.5 else f"user{random.randint(1000, 9999)}"

def get_random_feedback():
    return random.choice(feedback_sentences)

def get_random_profile_picture():
    files = os.listdir(VOUCH_IMAGE_FOLDER)
    return f"{VOUCH_IMAGE_FOLDER}/{random.choice(files)}" if files else None

def get_random_rating():
    return random.choice([4, 5])  # Randomly choose between 4 or 5 stars

# Send vouch message every 2 minutes
async def send_vouches():
    
    channel = await bot.fetch_channel(vouch_channel_id)


    while True:
        username = get_random_username()
        feedback = get_random_feedback()
        profile_picture = get_random_profile_picture()
        rating = get_random_rating()

        # Create the embed message
        feedback_embed = discord.Embed(
            title="**Product Feedback**",
            description=f"**Rating:** {rating} Stars\n**Feedback:** {feedback}",
            color=discord.Color.blue()
        )
        feedback_embed.set_footer(text=f"Reviewed by {username}")  # Reviewer username

        # If a profile picture exists, use it in the embed
        if profile_picture:
                file = discord.File(profile_picture, filename="profile_pic.png")
                feedback_embed.set_thumbnail(url="attachment://profile_pic.png")
                await channel.send(embed=feedback_embed, file=file)
        else:
                await channel.send(embed=feedback_embed)

        await asyncio.sleep(2000)  # Wait for 2 minutes before sending the next vouch

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    bot.loop.create_task(send_vouches())  # Start the vouch messages task



# DM All Members Command
@bot.command()
@commands.check(is_admin)
async def dmall(ctx, *, message: str):
    """DM all members in the server. 📩"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to use this command. ❌")
        return

    success_count = 0
    failed_count = 0

    await ctx.send("📨 Sending messages... This may take a while.")

    for member in ctx.guild.members:
        if member.bot or member == ctx.author:  # Skip bots and the command author
            continue
        try:
            await member.send(message)
            success_count += 1
        except discord.Forbidden:
            failed_count += 1  # DM is disabled for this user
        except discord.HTTPException as e:
            failed_count += 1  # Other errors like rate limits
            print(f"Could not DM {member.name}: {e}")

    await ctx.send(f"✅ Message sent to {success_count} members. ❌ Failed to DM {failed_count} members.")


BACKUP_FOLDER = r"C:\Users\shali\OneDrive\Desktop\RAM\EXPERIMENTS\BACKUP\BACKUP BOT\backups"

# Ensure backup folder exists
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)


# Check if user is admin
def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# Backup Command
@bot.command()
@is_admin()
async def backup(ctx):
    guild = ctx.guild
    backup_data = {
        "server_name": guild.name,
        "server_id": guild.id,
        "roles": [],
        "categories": [],
        "channels": [],
        "messages": {}
    }

    # Backup Roles
    for role in guild.roles:
        backup_data["roles"].append({
            "name": role.name,
            "permissions": role.permissions.value,
            "color": role.color.value,
            "position": role.position
        })

    # Backup Categories
    category_map = {}
    for category in guild.categories:
        backup_data["categories"].append({"id": category.id, "name": category.name})
        category_map[category.id] = category.name

    # Backup Channels
    for channel in guild.channels:
        channel_data = {
            "name": channel.name,
            "type": str(channel.type),
            "category_id": channel.category_id
        }
        backup_data["channels"].append(channel_data)

        # Backup Messages (only for text channels)
        if isinstance(channel, discord.TextChannel):
            backup_data["messages"][channel.name] = []
            async for message in channel.history(limit=100):
                msg_data = {
                    "author": message.author.name,
                    "content": message.content if message.content else None,
                    "embeds": [embed.to_dict() for embed in message.embeds] if message.embeds else []
                }
                backup_data["messages"][channel.name].append(msg_data)

    # Save Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup{timestamp}_{guild.id}.json"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=4)

    await ctx.send(f"✅ Backup created: `{backup_filename}`")

# Restore Command
@bot.command()
@is_admin()
async def restore(ctx, filename: str):
    backup_path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.exists(backup_path):
        return await ctx.send("❌ Backup file not found.")

    with open(backup_path, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    guild = ctx.guild

    # Restore Roles
    for role_data in reversed(backup_data["roles"]):
        if not discord.utils.get(guild.roles, name=role_data["name"]):
            await guild.create_role(
                name=role_data["name"],
                permissions=discord.Permissions(role_data["permissions"]),
                color=discord.Color(role_data["color"])
            )

    # Restore Categories
    category_map = {}
    for category_data in backup_data["categories"]:
        category = discord.utils.get(guild.categories, name=category_data["name"])
        if not category:
            category = await guild.create_category(category_data["name"])
        category_map[category_data["id"]] = category

    # Restore Channels under correct categories
    channel_map = {}
    for channel_data in backup_data["channels"]:
        if not discord.utils.get(guild.channels, name=channel_data["name"]):
            category = category_map.get(channel_data["category_id"])
            if channel_data["type"] == "text":
                new_channel = await guild.create_text_channel(channel_data["name"], category=category)
            elif channel_data["type"] == "voice":
                new_channel = await guild.create_voice_channel(channel_data["name"], category=category)
            channel_map[channel_data["name"]] = new_channel

    # Restore Messages & Embeds (Ensuring Correct Order)
    for channel_name, messages in backup_data["messages"].items():
        if channel_name in channel_map:
            channel = channel_map[channel_name]
            messages.reverse()
            for msg in messages:
                content = msg["content"]
                embeds = [discord.Embed.from_dict(embed) for embed in msg["embeds"]]

                # Only send if content or embeds exist
                if content or embeds:
                    await channel.send(content=content, embeds=embeds)

    await ctx.send(f"✅ Server restored from `{filename}`!")

# Delete All Channels (Fix: Confirm Before Deleting)
@bot.command()
@is_admin()
async def deleteall(ctx):
    await ctx.send("⚠️ **Are you sure you want to delete all channels?** Type `CONFIRM` to proceed.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == "CONFIRM"

    try:
        await bot.wait_for("message", check=check, timeout=15)
    except:
        return await ctx.send("❌ Action canceled.")

    channels_to_delete = [channel for channel in ctx.guild.channels if channel != ctx.channel]

    for channel in channels_to_delete:
        try:
            await channel.delete()
        except:
            pass  # Ignore if deletion fails

    await ctx.send("✅ **All channels deleted successfully!**")





def whitelist_only():
    """Check if the user is whitelisted and in the correct server."""
    async def predicate(ctx):
        if ctx.guild is None:
            return False  # Prevents DM usage
        if ctx.guild.id != whitelist_server_id:
            await ctx.send("❌ **This bot is restricted to a specific server!**")
            return False
        if ctx.author.id != whitelisted_user_id:
            await ctx.send("🚫 **You are not whitelisted to use this command!**")
            return False
        return True
    return commands.check(predicate)


# 🎉 Command: gstart (Whitelist Only)
@bot.command()
@whitelist_only()
async def gstart(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        await ctx.send("📢 Enter the **Channel ID** where the giveaway will be sent:")
        channel_id = int((await bot.wait_for("message", check=check)).content)
        channel = bot.get_channel(channel_id)

        await ctx.send("🏆 Enter the **Giveaway Title**:")
        title = (await bot.wait_for("message", check=check)).content

        await ctx.send("✍️ Enter the **Description** (supports Nitro emojis) or type 'none':")
        description = (await bot.wait_for("message", check=check)).content
        if description.lower() == "none":
            description = ""

        await ctx.send("🎊 Enter the **Number of Winners**:")
        num_winners = int((await bot.wait_for("message", check=check)).content)

        await ctx.send("🎁 Enter the **Prize**:")
        prize = (await bot.wait_for("message", check=check)).content

        await ctx.send("😍 Enter the **Reaction Emoji** for entering:")
        reaction_emoji = (await bot.wait_for("message", check=check)).content

        await ctx.send("📸 Enter the **Thumbnail Link** or type 'none':")
        thumbnail_link = (await bot.wait_for("message", check=check)).content
        if thumbnail_link.lower() == "none":
            thumbnail_link = None

        await ctx.send("🏅 Enter **Winner Selection** (User ID for fixed winner or 'none' for random):")
        winner_selection = (await bot.wait_for("message", check=check)).content

        await ctx.send("⏳ Enter the **Time Duration** (in seconds):")
        duration = int((await bot.wait_for("message", check=check)).content)

        await ctx.send("⏳ Enter the **DM/TicketCreate Timer** (in seconds, type 'none' if not applicable):")
        dm_ticket_timer = (await bot.wait_for("message", check=check)).content
        dm_ticket_timer = int(dm_ticket_timer) if dm_ticket_timer.lower() != "none" else None

        await ctx.send("👥 Enter **Role Required to Win** (or type 'none'):")
        role_required = (await bot.wait_for("message", check=check)).content
        if role_required.lower() == "none":
            role_required = None

        await ctx.send("👑 Enter the **Host Mention** (or type 'none'):")
        host_mention = (await bot.wait_for("message", check=check)).content
        if host_mention.lower() == "none":
            host_mention = ""

        await ctx.send("🎭 Choose the **Type of Giveaway** (dm / norequest / ticketcreate):")
        giveaway_type = (await bot.wait_for("message", check=check)).content.lower()

        await ctx.send("📩 Enter the **Custom Winning Message** (or type 'none'):")
        custom_winning_message = (await bot.wait_for("message", check=check)).content
        if custom_winning_message.lower() == "none":
            custom_winning_message = None

        embed = discord.Embed(title=f"🎉 {title} 🎉", description=description, color=discord.Color.gold())
        embed.add_field(name="🏆 Prize:", value=prize, inline=False)
        embed.add_field(name="👥 Winners:", value=f"{num_winners}", inline=False)
        embed.add_field(name="⏳ Time Left:", value=f"{duration} seconds", inline=False)
        embed.set_footer(text="React to enter!")
        if thumbnail_link:
            embed.set_thumbnail(url=thumbnail_link)

        giveaway_message = await channel.send(embed=embed)
        await giveaway_message.add_reaction(reaction_emoji)

        # 🔄 Real-time countdown
        for i in range(duration, 0, -1):
            embed.set_field_at(2, name="⏳ Time Left:", value=f"{i} seconds", inline=False)
            await giveaway_message.edit(embed=embed)
            await asyncio.sleep(1)

        message = await channel.fetch_message(giveaway_message.id)
        users = [user async for user in message.reactions[0].users() if not user.bot]

        if not users:
            await channel.send("❌ No one entered the giveaway.")
            return

        if winner_selection.lower() == "none":
            winners = random.sample(users, min(len(users), num_winners))
        else:
            winners = [ctx.guild.get_member(int(winner_selection))]

        winner_mentions = ", ".join(winner.mention for winner in winners)
        winner_embed = discord.Embed(title="🎉 Giveaway Ended!", description=f"The winner is {winner_mentions}!", color=discord.Color.green())

        await channel.send(embed=winner_embed)
        if custom_winning_message:
            await channel.send(f"🎊 {winner_mentions}, {custom_winning_message}")

        if giveaway_type == "dm":
            await channel.send(f"📢 {winner_mentions}, you have won **{prize}**! 🎁")
            if dm_ticket_timer:
                await asyncio.sleep(dm_ticket_timer)
                await channel.send("⏳ **Timer Over!**")

        elif giveaway_type == "ticketcreate":
            await channel.send(f"🎟️ {winner_mentions}, please create a ticket for your prize! 🎟️")
            if dm_ticket_timer:
                await asyncio.sleep(dm_ticket_timer)
                await channel.send("⏳ **Timer Over!**")

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")


# 🔁 Command: greroll <message_id> → Finds a new winner & restarts DM/Ticket timer
@bot.command()
@whitelist_only()
async def greroll(ctx, message_id: int):
    channel = ctx.channel
    try:
        message = await channel.fetch_message(message_id)
        users = [user async for user in message.reactions[0].users() if not user.bot]

        if not users:
            await ctx.send("❌ No one entered the giveaway.")
            return

        new_winner = random.choice(users)
        await channel.send(f"🎉 New Winner: {new_winner.mention}! 🎊")
        # Restart DM/Ticket timer if applicable
        await asyncio.sleep(5)  # Example timer restart

    except:
        await ctx.send("❌ Invalid Message ID!")



# Run the bot
bot.run(BOT_TOKEN)

