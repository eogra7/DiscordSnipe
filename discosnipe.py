import asyncio
import configparser
import math
import os
import re
import subprocess
import time

import discord
from termcolor import cprint

CONFIG_SECTION = 'DiscoSnipe'
CONFIG = None
DISCORD_CLIENT = None


def init():
    print('[INIT] DiscoSnipe v0.1-alpha started')
    print('[INIT] Loading config...')
    global CONFIG
    CONFIG = configparser.ConfigParser()
    if not CONFIG.read('discosnipe.cfg'):
        print('[INIT] discosnipe.cfg was not found. Initializing first time setup.')
        CONFIG = generate_config(CONFIG)
    return


class CatchLog(object):
    c_list = []

    def update(self):
        for catch in self.c_list:
            if time.time() - catch.time_caught > 120:
                self.c_list.remove(catch)

    def add(self, catch=None):
        self.update()
        self.c_list.append(catch)

    def exists(self, target=None):
        for catch in self.c_list:
            for poke in catch.pokemons:
                dist = distance_between(target, poke)
                if (dist < 50) & (target.name == poke.name):
                    return True
        return False


poke_to_relay = None
catch_log = CatchLog()


def main():
    init()

    discord_username = CONFIG.get(CONFIG_SECTION, 'username')
    discord_password = CONFIG.get(CONFIG_SECTION, 'password')
    discord_channels = CONFIG.get(CONFIG_SECTION, 'channels').split(',')

    print('[INIT] Configuration loaded! Logging in to Discord...')
    global DISCORD_CLIENT
    DISCORD_CLIENT = discord.Client()

    @DISCORD_CLIENT.event
    async def on_ready():
        print('[INIT] Logged in as ' + DISCORD_CLIENT.user.name)
        print('[INIT] Watching the following channels: ' + ', '.join(discord_channels))

    @DISCORD_CLIENT.event
    async def on_message(message):
        if message.channel.name in discord_channels:
            parse_message(message)

    async def relay_to_channel():
        global DISCORD_CLIENT
        await DISCORD_CLIENT.wait_until_ready()
        while not DISCORD_CLIENT.is_closed:
            for catch in catch_log.c_list:
                poke = catch.pokemons[0]
                if poke.iv is not None:
                    if not catch.relayed:
                        if float(poke.iv) == 100:
                            if poke.channel.name != 'donor_100iv':
                                msg = '**%sIV - %s at %s,%s [Moveset: %s]**' % (
                                    '100', poke.name.title(), poke.lat, poke.lon, poke.moveset)
                                channel = discord.Object(id='209174231269769216')  # donor_100iv 209174231269769216
                                await DISCORD_CLIENT.send_message(channel, msg)
                        # elif float(poke.iv) >= 90:
                        #     if poke.channel.name != '90plus_ivonly':
                        #         msg = '%s,%s - %s %sIV [Moveset: %s]' % (
                        #             poke.lat, poke.lon, poke.name.title(), str(round(float(poke.iv), 2)),
                        #               poke.moveset)
                        #         channel = discord.Object(id='209171120702619648')  # 90plus_ivonly 209171120702619648
                        #         await DISCORD_CLIENT.send_message(channel, msg)
                        catch.relayed = True

            await asyncio.sleep(1)

    # DISCORD_CLIENT.loop.create_task(relay_to_channel())
    DISCORD_CLIENT.run(discord_username, discord_password)


POKEMON = ["abra", "aerodactyl", "alakazam", "arbok", "arcanine", "articuno", "beedrill", "bellsprout", "blastoise",
           "bulbasaur", "butterfree", "caterpie", "chansey", "charizard", "charmander", "charmeleon", "clefable",
           "clefairy", "cloyster", "cubone", "dewgong", "diglett", "ditto", "dodrio", "doduo", "dragonair", "dragonite",
           "dratini", "drowzee", "dugtrio", "eevee", "ekans", "electabuzz", "electrode", "exeggcute", "exeggutor",
           "farfetch'd", "fearow", "flareon", "gastly", "gengar", "geodude", "gloom", "golbat", "goldeen", "golduck",
           "golem", "graveler", "grimer", "growlithe", "gyarados", "haunter", "hitmonchan", "hitmonlee", "horsea",
           "hypno", "ivysaur", "jigglypuff", "jolteon", "jynx", "kabuto", "kabutops", "kadabra", "kakuna", "kangaskhan",
           "kingler", "koffing", "krabby", "lapras", "lickitung", "machamp", "machoke", "machop", "magikarp", "magmar",
           "magnemite", "magneton", "mankey", "marowak", "meowth", "metapod", "mew", "mewtwo", "moltres", "mrmime",
           "muk",
           "nidoking", "nidoqueen", "nidoranf", "nidoranm", "nidorina", "nidorino", "ninetales", "oddish", "omanyte",
           "omastar", "onix", "paras", "parasect", "persian", "pidgeot", "pidgeotto", "pidgey", "pikachu", "pinsir",
           "poliwag", "poliwhirl", "poliwrath", "ponyta", "porygon", "primeape", "psyduck", "raichu", "rapidash",
           "raticate", "rattata", "rhydon", "rhyhorn", "sandshrew", "sandslash", "scyther", "seadra", "seaking", "seel",
           "shellder", "slowbro", "slowpoke", "snorlax", "spearow", "squirtle", "starmie", "staryu", "tangela",
           "tauros",
           "tentacool", "tentacruel", "vaporeon", "venomoth", "venonat", "venusaur", "victreebel", "vileplume",
           "voltorb",
           "vulpix", "wartortle", "weedle", "weepinbell", "weezing", "wigglytuff", "zapdos", "zubat"]


class Pokemon(object):
    class Moveset(object):
        def __init__(self, move1, move2):
            self.move2 = move2
            self.move1 = move1

        def __str__(self):
            return self.move1 + '/' + self.move2

    def __init__(self, name=None, lat=None, lon=None, channel=None, cp=None, iv=None, moveset=None):
        self.moveset = moveset
        self.iv = iv
        self.cp = cp
        self.channel = channel
        self.name = name
        self.lat = lat
        self.lon = lon


class CatchResult(object):
    CATCH_SUCCESS = 0
    CATCH_FAIL = 1
    CATCH_FAIL_RAN_AWAY = 2
    CATCH_FAIL_NOT_FOUND = 3
    CATCH_FAIL_NO_POKEBALLS = 4

    def __init__(self, result=None, pokemons=None):
        self.result = result
        self.time_caught = time.time()
        self.pokemons = pokemons
        self.relayed = False


def get_coords(message):
    if len(re.findall(r'(,)', message.content)) == 3:
        s = message.content.split(',')
        m = '%s.%s,%s.%s' % (s[0], s[1], s[2], s[3])
    else:
        m = message.content

    match = re.search("(-?\d{1,3}.\d*,\s?-?\d{1,3}.\d*)", m)
    if match:
        return match.group(0).replace(' ', '')
    return None


def get_poke_name(message):
    match = re.findall("([a-zA-Z]+)", message.content)
    if match:
        for word in match:
            word = word.lower()
            if word in POKEMON:
                return word
    return None


def distance_between(poke1, poke2):
    lat1 = float(poke1.lat)
    lon1 = float(poke1.lon)
    lat2 = float(poke2.lat)
    lon2 = float(poke2.lon)
    r = 6371 * 1000  # meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon1 - lon2)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    a = math.sin(dlat / 2.0) * math.sin(dlat / 2.0) + math.sin(dlon / 2.0) * math.sin(dlon / 2.0) * math.cos(
        lat1) * math.cos(lat2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    d = r * c
    return d


def get_snipe_result(stdout):
    pattern = re.compile(r'(\[.+(\bWe caught\b).+(.+\n){5})', re.MULTILINE)
    matches = re.findall(pattern, stdout)
    if len(matches) > 0:
        # catch success
        pokemons = []
        for match in matches:
            pattern = re.compile(r'[\S]+(?=\.?$)', re.MULTILINE)
            info = re.findall(pattern, match[0])
            poke = Pokemon(name=info[0][:-1],
                           cp=info[1],
                           iv=info[2],
                           moveset=Pokemon.Moveset(info[3], info[4]))
            pokemons.append(poke)
        return CatchResult(CatchResult.CATCH_SUCCESS, pokemons)
    elif 'There is no' in stdout:
        return CatchResult(CatchResult.CATCH_FAIL_NOT_FOUND)
    elif 'Got into the fight without any Pokeballs.' in stdout:
        return CatchResult(CatchResult.CATCH_FAIL_NO_POKEBALLS)
    else:
        # catch failure
        return CatchResult(CatchResult.CATCH_FAIL)


def snipe_pokemon(target):
    path = CONFIG.get(CONFIG_SECTION, 'pokesniper')
    directory = path[:path.rindex('\\') + 1]
    cprint('[SNIPE] Sniping %s at %s,%s from #%s' % (target.name.title(), target.lat, target.lon, target.channel.name),
           'yellow')
    child = subprocess.run(path + ' %s %s %s' % (target.name, target.lat, target.lon), stdout=subprocess.PIPE,
                           cwd=directory,
                           universal_newlines=True)
    with open('log.txt', 'a') as logfile:
        logfile.write(child.stdout)
        catch_result = get_snipe_result(child.stdout)
        if catch_result.result == CatchResult.CATCH_SUCCESS:
            for poke in catch_result.pokemons:
                cprint(
                    '[SNIPE] Caught %s (CP:%s IV:%s Moves:%s)' % (
                        poke.name.title(), poke.cp, str(round(float(poke.iv), 2)), poke.moveset),
                    'green')
                target.moveset = poke.moveset
                target.iv = poke.iv
            catch_result.pokemons = [target]
        else:
            catch_result.pokemons = [target]
            if catch_result.result == CatchResult.CATCH_FAIL:
                cprint(
                    '[SNIPE] Failed to catch the %s at %s,%s from #%s. See log.txt for details' % (
                        target.name.title(), target.lat, target.lon, target.channel.name),
                    'red')
            elif catch_result.result == CatchResult.CATCH_FAIL_NOT_FOUND:
                cprint(
                    "[SNIPE] Couldn't find the %s at %s,%s from #%s" % (
                        target.name.title(), target.lat, target.lon, target.channel.name),
                    'red')
            elif catch_result.result == CatchResult.CATCH_FAIL_NO_POKEBALLS:
                cprint(
                    '[SNIPE] Failed to catch the %s at %s,%s from #%s. Out of Pokeballs' % (
                        target.name.title(), target.lat, target.lon, target.channel.name),
                    'red')
        catch_log.add(catch_result)


def parse_message(msg):
    message = msg
    if 'Snipe Bot' in message.author.name:
        message.content = msg.content.split('\n')[len(msg.content.split('\n')) - 1]
    name = get_poke_name(message)
    coords = get_coords(message)
    # print('Name: ' + name)
    # print('Coords: ' + coords)
    if (name is not None) & (coords is not None):
        coords = coords.split(',')
        poke = Pokemon(name, coords[0], coords[1])
        poke.channel = message.channel
        if catch_log.exists(poke):
            cprint('Duplicate %s from #%s' % (poke.name.title(), poke.channel), 'grey')
        else:
            snipe_pokemon(poke)


def generate_config(config):
    pokesniper_path = None
    print('[SETUP] NOTE: Your credentials will be stored in plaintext in discosnipe.cfg!')
    config.add_section(CONFIG_SECTION)
    config.set(CONFIG_SECTION, 'username', input('Discord Username: '))
    config.set(CONFIG_SECTION, 'password', input('Discord Password: '))
    config.set(CONFIG_SECTION, 'channels', input('Channels'))
    if os.path.isfile('PokeSniper2.exe'):
        pokesniper_path = os.getcwd() + '\PokeSniper2.exe'
        print('[SETUP] PokeSniper executable found at ' + pokesniper_path)
        print('[SETUP] Leave PokeSniper Path blank to use this path.')
    path_input = input('PokeSniper Path: ')
    while not (is_path_valid(path_input) | (path_input == '')):
        print('[SETUP] Invalid path')
        path_input = input('PokeSniper Path: ')
    if path_input:
        pokesniper_path = path_input
    config.set(CONFIG_SECTION, 'pokesniper', pokesniper_path)
    print('[SETUP] Saving configuration...')
    with open('discosnipe.cfg', 'w') as configfile:
        config.write(configfile)
        print('[SETUP] Configuration saved. Setup complete.')
    return config


def is_path_valid(path):
    valid = os.path.isfile(path)
    return valid


main()
