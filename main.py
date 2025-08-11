import os
import json
import time
import discord
from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Attachment, Embed, ButtonStyle
from discord.ui import View, Button
from flask import Flask
from threading import Thread

# ---------- KEEP ALIVE POUR RENDER ----------
app = Flask('')

@app.route('/')
def home():
    return "Bot en ligne !"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ---------- BOT DISCORD ----------
intents = discord.Intents.default()
intents.message_content = True  # Pour éviter le warning
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

# Commande setup
@bot.tree.command(name="setup", description="Configurer le salon pour les réponses à l'animation")
@app_commands.describe(channel="Salon où les réponses seront envoyés")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    config[str(interaction.guild_id)] = channel.id
    save_config(config)
    await interaction.response.send_message(f"✅ Salon d'animation configuré sur {channel.mention}", ephemeral=True)

@setup.error
async def setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ Tu dois être **administrateur** pour utiliser cette commande.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ Une erreur est survenue : {str(error)}", ephemeral=True
        )

# Commande anim
@bot.tree.command(name="anim", description="Envoyer une réponse à l'animation")
@app_commands.describe(message="La réponse à envoyer")
async def anim(interaction: discord.Interaction, message: str):
    config = load_config()
    guild_id = str(interaction.guild_id)

    if guild_id not in config:
        await interaction.response.send_message("❌ Aucun salon configuré. Utilise `/setup`.", ephemeral=True)
        return

    channel_id = config[guild_id]
    channel = bot.get_channel(channel_id)

    if not channel:
        await interaction.response.send_message("❌ Salon introuvable. Refaire `/setup`.", ephemeral=True)
        return

    await channel.send(f"**Réponse de {interaction.user.mention} :**\n{message}")
    await interaction.response.send_message("✅ Réponse envoyé !", ephemeral=True)

# commande ping
@bot.tree.command(name="ping", description="Tester si le bot est en ligne")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong ! Je suis bien en ligne.", ephemeral=True)

# Commande animcreate
@bot.tree.command(name="animcreate", description="Créer une animation avec une question et une image (admin seulement)")
@app_commands.describe(
    question="La question à poser",
    salon="Le salon où envoyer l'embed",
    ping="Mention à envoyer avec la question",
    image="Image ou illustration de la question"
)
@app_commands.checks.has_permissions(administrator=True)
async def animcreate(
    interaction: Interaction,
    question: str,
    salon: TextChannel,
    ping: str,
    image: Attachment
):
    # Créer l'embed
    embed = discord.Embed(
        title=question,
        description="/anim pour répondre",
        color=discord.Color.blue()
    )
    embed.set_image(url=image.url)
    embed.set_footer(
        text=f"Envoyé par {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    try:
        await salon.send(content=ping, embed=embed)
        await interaction.response.send_message("✅ Animation envoyée avec succès !", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)

# Gestion d'erreurs si non-admin
@animcreate.error
async def animcreate_error(interaction: Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ Tu dois être **administrateur** pour utiliser cette commande.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ Une erreur est survenue : {str(error)}", ephemeral=True
        )

# Animex animation spéciale

# Commande animexsetup
@bot.tree.command(name="animexsetup", description="Définir le salon et le ping pour les animations spéciales Animex")
@app_commands.describe(
    channel="Salon où les animations spéciales seront envoyées",
    ping="Mention à utiliser lors de l’envoi"
)
@app_commands.checks.has_permissions(administrator=True)
async def animexsetup(interaction: Interaction, channel: TextChannel, ping: str):
    config = load_config()
    config_key = f"animex_{interaction.guild_id}"
    config[config_key] = {
        "channel_id": channel.id,
        "ping": ping
    }
    save_config(config)
    await interaction.response.send_message(
        f"✅ Salon configuré : {channel.mention}\n📣 Ping configuré : `{ping}`",
        ephemeral=True
    )

# Commande animexanimcreate
@bot.tree.command(name="animexanimcreate", description="Créer une animation spéciale Animex dans tous les serveurs")
@app_commands.describe(
    question="La question à poser",
    image="Image ou illustration de la question"
)
async def animexanimcreate(
    interaction: Interaction,
    question: str,
    image: Attachment
):
    # Vérifier que seul l'ID autorisé peut utiliser la commande
    if interaction.user.id != 1109887334884847747:
        await interaction.response.send_message("❌ Tu n'es pas autorisé à utiliser cette commande.", ephemeral=True)
        return

    config = load_config()

    embed = discord.Embed(
        title="🌟 Animation spéciale Animex !",
        description=question,
        color=discord.Color.purple()
    )
    embed.set_image(url=image.url)
    embed.set_footer(
        text="/animexanswer pour répondre",
        icon_url=interaction.user.display_avatar.url
    )

    success = 0
    failed = 0

    for key, value in config.items():
        if key.startswith("animex_"):
            guild_id = int(key.split("_")[1])
            channel_id = value.get("channel_id")
            ping = value.get("ping", "")

            channel = bot.get_channel(channel_id)

            if channel:
                try:
                    await channel.send(content=ping, embed=embed)
                    success += 1
                except Exception:
                    failed += 1
            else:
                failed += 1

    await interaction.response.send_message(
        f"✅ Animation envoyée dans {success} serveurs.\n❌ Échecs : {failed}", ephemeral=True
    )

# Commande animexanswer
@bot.tree.command(name="animexanswer", description="Envoyer ta réponse à l'animation spéciale d'Animex")
@app_commands.describe(message="Ta réponse à l'animation spéciale")
async def animexanswer(interaction: Interaction, message: str):
    channel = bot.get_channel(1403054503783039016)  # salon fixe

    if not channel:
        await interaction.response.send_message("❌ Salon de réponse introuvable.", ephemeral=True)
        return

    try:
        await channel.send(f"**Réponse de {interaction.user.mention} :**\n{message}")
        await interaction.response.send_message("✅ Ta réponse a été envoyée !", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur : {str(e)}", ephemeral=True)

# Commande help
@bot.tree.command(name="help", description="Affiche toutes les commandes du bot")
async def help_command(interaction: Interaction):
    embed = Embed(
        title="📖 Aide - Commandes disponibles",
        description="Voici la liste des commandes que tu peux utiliser avec ce bot :",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="COMMANDES DE BASE",
        value="Commandes des animations gérées par le staff du serveur",
        inline=False
    )
    embed.add_field(
        name="`/setup`",
        value="Configurer le salon où les réponses seront envoyées *(admin seulement)*",
        inline=False
    )
    embed.add_field(
        name="`/anim`",
        value="Envoyer une réponse à l'animation *(disponible pour tous)*",
        inline=False
    )
    embed.add_field(
        name="`/animcreate`",
        value="Créer une question d'animation avec image et ping *(admin seulement)*",
        inline=False
    )
    embed.add_field(
        name="`LES ANIMATIONS SPÉCIALES D'ANIMEX`",
        value="Commandes des animations gérées directement par Animex *(Les animations seront envoyées avant 22h)*",
        inline=False
    )
    embed.add_field(
        name="`/animexsetup`",
        value="Configurer le salon où les animations spéciales d'Animex seront envoyées *(admin seulement)*",
        inline=False
    )
    embed.add_field(
        name="`/animexanswer`",
        value="Envoyer une réponse à l'animation spéciale d'Animex *(disponible pour tous)*",
        inline=False
    )
    embed.add_field(
        name="`/help`",
        value="Afficher ce message d’aide",
        inline=False
    )
    embed.set_footer(text="Besoin d’aide supplémentaire ? Clique sur le bouton ci-dessous 👇")

    # Bouton vers le serveur de support
    support_button = Button(
        label="🎟️ Support Discord",
        url="https://discord.gg/VaRCptDGQM",
        style=ButtonStyle.link
    )

    view = View()
    view.add_item(support_button)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# ---------- EVENT READY ----------
@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes slash synchronisées.")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation : {e}")
    print(f"🤖 Bot connecté en tant que {bot.user}")

# ---------- LANCEMENT ----------
if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Erreur : DISCORD_TOKEN introuvable dans les variables d'environnement.")
    else:
        try:
            bot.run(token)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print("⚠️ Rate limit détecté. Attente 60 secondes avant redémarrage...")
                time.sleep(60)
                os._exit(1)  # Laisse Render redémarrer après délai
            else:
                raise e
