import discord
import asyncio
import re
import subprocess
import io
import configparser

print('DiscoSnipe v0.1-alpha started')
print('Loading config...')

config = configparser.RawConfigParser()
config.read('config.cfg')
# ================================
# CONFIGURATION
# ================================
# Discord Username/Password
DISCORD_USERNAME = config.get('DiscoSnipe', 'username')
DISCORD_PASSWORD = config.get('DiscoSnipe', 'password')
# Channels to get pokemon from
CHANNELS = config.get('DiscoSnipe', 'channels').split(',')
# Put the path to the directory where PokeSniper is here
POKESNIPER_PATH = config.get('DiscoSnipe', 'pokesniper-path') + '\\'

# ===========================================
# End of configuration
# You do not need to edit anything below here
# ===========================================

POKEMON = {"abra", "aerodactyl", "alakazam", "arbok", "arcanine", "articuno", "beedrill", "bellsprout", "blastoise",
         "bulbasaur", "butterfree", "caterpie", "chansey", "charizard", "charmander", "charmeleon", "clefable",
         "clefairy", "cloyster", "cubone", "dewgong", "diglett", "ditto", "dodrio", "doduo", "dragonair", "dragonite",
         "dratini", "drowzee", "dugtrio", "eevee", "ekans", "electabuzz", "electrode", "exeggcute", "exeggutor",
         "farfetch'd", "fearow", "flareon", "gastly", "gengar", "geodude", "gloom", "golbat", "goldeen", "golduck",
           "golem", "graveler", "grimer", "growlithe", "gyarados", "haunter", "hitmonchan", "hitmonlee", "horsea",
           "hypno", "ivysaur", "jigglypuff", "jolteon", "jynx", "kabuto", "kabutops", "kadabra", "kakuna", "kangaskhan",
           "kingler", "koffing", "krabby", "lapras", "lickitung", "machamp", "machoke", "machop", "magikarp", "magmar",
           "magnemite", "magneton", "mankey", "marowak", "meowth", "metapod", "mew", "mewtwo", "moltres", "mrmime", "muk",
           "nidoking", "nidoqueen", "nidoranf", "nidoranm", "nidorina", "nidorino", "ninetales", "oddish", "omanyte",
           "omastar", "onix", "paras", "parasect", "persian", "pidgeot", "pidgeotto", "pidgey", "pikachu", "pinsir",
           "poliwag", "poliwhirl", "poliwrath", "ponyta", "porygon", "primeape", "psyduck", "raichu", "rapidash",
           "raticate", "rattata", "rhydon", "rhyhorn", "sandshrew", "sandslash", "scyther", "seadra", "seaking", "seel",
           "shellder", "slowbro", "slowpoke", "snorlax", "spearow", "squirtle", "starmie", "staryu", "tangela", "tauros",
           "tentacool", "tentacruel", "vaporeon", "venomoth", "venonat", "venusaur", "victreebel", "vileplume", "voltorb",
           "vulpix", "wartortle", "weedle", "weepinbell", "weezing", "wigglytuff", "zapdos", "zubat"}

class Pokemon(object):
    def __init__(self, name, loc):
        self.name = name
        self.loc = loc

last_pokemon = Pokemon('','')

def get_pokemon(message):
    match = re.search('(-?\d{1,3}.\d*,\s?-?\d{1,3}.\d*)', message.content)
    if match:
        loc = match.group(0).replace(' ','')
        words_match = re.findall('([a-zA-Z]+)', message.content)
        if words_match:
            name = '*';
            for word in words_match:
                if word.lower() in POKEMON:
                    name = word.lower()
            pokemon = Pokemon(name, loc)
            if (pokemon.name==last_pokemon.name) & (pokemon.loc==last_pokemon.loc):
                print('[%s] Duplicate %s' % (message.channel.name, pokemon.name))
            else:
                print('[%s] %s at %s' % (message.channel.name, pokemon.name, pokemon.loc))
                last_pokemon.name = pokemon.name
                last_pokemon.loc = pokemon.loc
                subprocess.Popen(POKESNIPER_PATH + 'PokeSniper2.exe ' + pokemon.name + ' ' + pokemon.loc.replace(',', ' '), cwd=POKESNIPER_PATH)

        return True
    else:
        return False

client = discord.Client()



@client.event
async def on_ready():
    print('Logged in as ' + client.user.name)
    print('Waiting for pokemon...')

@client.event
async def on_message(message):
    if message.channel.name in CHANNELS:
        get_pokemon(message)


client.run(DISCORD_USERNAME, DISCORD_PASSWORD)
