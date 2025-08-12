import discord
from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Attachment, Embed, ButtonStyle
from discord.ui import View, Button
import os
import json
from flask import Flask
from threading import Thread

# ------------ CONFIGURATION BOT ------------
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
CONFIG_FILE = "config.json"

# Création du fichier config si inexistant
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# ------------ KEEP ALIVE POUR RENDER ------------
app = Flask('')

@app.route('/')
def home():
    return "Bot en ligne !"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------ COMMANDES ------------

@bot.tree.command(name="setup", description="Configurer le salon pour les réponses à l'animation")
@app_commands.describe(channel="Salon où les réponses seront envoyés")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: Interaction, channel: TextChannel):
    await interaction.response.defer(ephemeral=True)
    config = load_config()
    config[str(interaction.guild_id)] = channel.id
    save_config(config)
    await interaction.followup.send(f"✅ Salon d'animation configuré sur {channel.mention}", ephemeral=True)

@setup.error
async def setup_error(interaction: Interaction, error: app_commands.AppCommandError):
    await interaction.response.defer(ephemeral=True)
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.followup.send("❌ Tu dois être **administrateur** pour utiliser cette commande.", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ Une erreur est survenue : {str(error)}", ephemeral=True)

@bot.tree.command(name="anim", description="Envoyer une réponse à l'animation")
@app_commands.describe(message="La réponse à envoyer")
async def anim(interaction: Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    config = load_config()
    guild_id = str(interaction.guild_id)
    if guild_id not in config:
        await interaction.followup.send("❌ Aucun salon configuré. Utilise `/setup`.", ephemeral=True)
        return
    channel = bot.get_channel(config[guild_id])
    if not channel:
        await interaction.followup.send("❌ Salon introuvable. Refaire `/setup`.", ephemeral=True)
        return
    await channel.send(f"**Réponse de {interaction.user.mention} :**\n{message}")
    await interaction.followup.send("✅ Réponse envoyée !", ephemeral=True)

@bot.tree.command(name="ping", description="Tester si le bot est en ligne")
async def ping(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send("🏓 Pong ! Je suis bien en ligne.", ephemeral=True)

@bot.tree.command(name="animcreate", description="Créer une animation avec question et image (admin seulement)")
@app_commands.describe(
    question="La question à poser",
    salon="Le salon où envoyer l'embed",
    ping="Mention à envoyer avec la question",
    image="Image ou illustration de la question"
)
@app_commands.checks.has_permissions(administrator=True)
async def animcreate(interaction: Interaction, question: str, salon: TextChannel, ping: str, image: Attachment):
    await interaction.response.defer(ephemeral=True)
    embed = Embed(title=question, description="/anim pour répondre", color=discord.Color.blue())
    embed.set_image(url=image.url)
    embed.set_footer(text=f"Envoyé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    try:
        await salon.send(content=ping, embed=embed)
        await interaction.followup.send("✅ Animation envoyée avec succès !", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : {str(e)}", ephemeral=True)

@animcreate.error
async def animcreate_error(interaction: Interaction, error: app_commands.AppCommandError):
    await interaction.response.defer(ephemeral=True)
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.followup.send("❌ Tu dois être **administrateur** pour utiliser cette commande.", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ Une erreur est survenue : {str(error)}", ephemeral=True)

@bot.tree.command(name="animexsetup", description="Définir le salon et le ping pour animations spéciales Animex")
@app_commands.describe(channel="Salon où les animations spéciales seront envoyées", ping="Mention à utiliser")
@app_commands.checks.has_permissions(administrator=True)
async def animexsetup(interaction: Interaction, channel: TextChannel, ping: str):
    await interaction.response.defer(ephemeral=True)
    config = load_config()
    config[f"animex_{interaction.guild_id}"] = {"channel_id": channel.id, "ping": ping}
    save_config(config)
    await interaction.followup.send(f"✅ Salon configuré : {channel.mention}\n📣 Ping : `{ping}`", ephemeral=True)

@bot.tree.command(name="animexanimcreate", description="Créer animation spéciale Animex dans tous les serveurs")
@app_commands.describe(question="La question à poser", image="Image ou illustration")
async def animexanimcreate(interaction: Interaction, question: str, image: Attachment):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.id != 1109887334884847747:
        await interaction.followup.send("❌ Tu n'es pas autorisé à utiliser cette commande.", ephemeral=True)
        return
    config = load_config()
    embed = Embed(title="🌟 Animation spéciale Animex !", description=question, color=discord.Color.purple())
    embed.set_image(url=image.url)
    embed.set_footer(text="/animexanswer pour répondre", icon_url=interaction.user.display_avatar.url)
    success = failed = 0
    for key, value in config.items():
        if key.startswith("animex_"):
            channel = bot.get_channel(value.get("channel_id"))
            ping = value.get("ping", "")
            if channel:
                try:
                    await channel.send(content=ping, embed=embed)
                    success += 1
                except:
                    failed += 1
            else:
                failed += 1
    await interaction.followup.send(f"✅ Animation envoyée dans {success} serveurs.\n❌ Échecs : {failed}", ephemeral=True)

@bot.tree.command(name="animexanswer", description="Répondre à l'animation spéciale Animex")
@app_commands.describe(message="Ta réponse")
async def animexanswer(interaction: Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(1403054503783039016)
    if not channel:
        await interaction.followup.send("❌ Salon de réponse introuvable.", ephemeral=True)
        return
    try:
        await channel.send(f"**Réponse de {interaction.user.mention} :**\n{message}")
        await interaction.followup.send("✅ Ta réponse a été envoyée !", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur : {str(e)}", ephemeral=True)

@bot.tree.command(name="help", description="Affiche toutes les commandes du bot")
async def help_command(interaction: Interaction):
    await interaction.response.defer()
    embed = Embed(title="📖 Aide - Commandes disponibles", description="Voici la liste des commandes :", color=discord.Color.blurple())
    embed.add_field(name="`/setup`", value="Configurer le salon où les réponses seront envoyées *(admin)*", inline=False)
    embed.add_field(name="`/anim`", value="Envoyer une réponse *(tous)*", inline=False)
    embed.add_field(name="`/animcreate`", value="Créer une animation *(admin)*", inline=False)
    embed.add_field(name="`/animexsetup`", value="Configurer le salon des animations spéciales *(admin)*", inline=False)
    embed.add_field(name="`/animexanswer`", value="Répondre à une animation spéciale *(tous)*", inline=False)
    embed.add_field(name="`/help`", value="Afficher ce message", inline=False)
    support_button = Button(label="🎟️ Support Discord", url="https://discord.gg/VaRCptDGQM", style=ButtonStyle.link)
    view = View()
    view.add_item(support_button)
    await interaction.followup.send(embed=embed, view=view)

# ------------ EVENT READY ------------
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes slash synchronisées.")
    except Exception as e:
        print(f"❌ Erreur sync commandes : {e}")
    print(f"🤖 Connecté en tant que {bot.user}")

# ------------ LANCEMENT ------------
keep_alive()
import time
time.sleep(5)  # Pause de 5 secondes avant connexion
bot.run(os.getenv("DISCORD_TOKEN"))
