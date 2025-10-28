import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Słownik do przechowywania mapowań: kod_zaproszenia -> id_roli
invite_roles = {}
# Słownik do śledzenia poprzednich użyć zaproszeń
previous_uses = {}

@bot.event
async def on_ready():
    print(f'✅ Zalogowano jako {bot.user}')
    # Inicjalizacja śledzenia zaprosień przy starcie
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            for invite in invites:
                previous_uses[invite.code] = invite.uses
        except:
            pass

@bot.command()
@commands.has_permissions(manage_roles=True)
async def map_invite(ctx, invite_code: str, *, role: discord.Role):
    """Mapuje kod zaproszenia do roli"""
    invite_roles[invite_code] = role.id
    await ctx.send(f"✅ Zmapowano link `{invite_code}` -> rola **{role.name}**")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def show_mappings(ctx):
    """Pokazuje aktualne mapowania zaproszeń do ról"""
    if not invite_roles:
        await ctx.send("❌ Brak zmapowanych zaproszeń.")
        return
    
    embed = discord.Embed(title="Mapowania Zaproszeń", color=0x00ff00)
    for invite_code, role_id in invite_roles.items():
        role = ctx.guild.get_role(role_id)
        if role:
            embed.add_field(
                name=f"Link: {invite_code}", 
                value=f"Rola: {role.mention}", 
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=2))
    
    try:
        # Pobierz aktualne zaproszenia
        current_invites = await member.guild.invites()
        
        # Znajdź które zaproszenie zostało użyte
        used_invite = None
        for invite in current_invites:
            previous_use = previous_uses.get(invite.code, 0)
            if invite.uses > previous_use:
                used_invite = invite
                break
        
        if used_invite and used_invite.code in invite_roles:
            role_id = invite_roles[used_invite.code]
            role = member.guild.get_role(role_id)
            
            if role:
                await member.add_roles(role)
                print(f"🎯 Nadano rolę {role.name} użytkownikowi {member.name} przez link: {used_invite.code}")
                
        # Zaktualizuj śledzenie użyć
        for invite in current_invites:
            previous_uses[invite.code] = invite.uses
            
    except Exception as e:
        print(f"❌ Błąd przy nadawaniu roli: {e}")

@bot.event
async def on_invite_create(invite):
    # Aktualizuj gdy tworzone jest nowe zaproszenie
    previous_uses[invite.code] = invite.uses

@bot.event
async def on_invite_delete(invite):
    # Usuń gdy zaproszenie jest usuwane
    if invite.code in previous_uses:
        del previous_uses[invite.code]
    if invite.code in invite_roles:
        del invite_roles[invite.code]

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
