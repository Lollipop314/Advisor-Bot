from discord.ext import commands
from utils import FactionUpgrades
from bs4 import BeautifulSoup
from urlextract import URLExtract

import re
import datetime
import discord
import requests

badSubstrings = ["", "Cost", "Effect", "Formula", "Mercenary Template", "Requirement", "Gem Grinder and Dragon's "
                                                                                       "Breath Formula", 'Formula: ']

alias = {
    "upgrade": ["upg", "up", "u"],
    "challenge": ["ch", "c"],
    "research": ["r", "res"]
}

def format(lst: list, factionUpgrade=None):
    """Formats the list retrieved from BeautifulSoup"""

    # First line always return an url - we want to get the URL only for the thumbnail
    url = lst[0]
    extractor = URLExtract()
    newUrl = extractor.find_urls(url)
    lst.remove(url)
    lst.insert(0, newUrl[0])

    # We add the faction upgrade name to the list so embed can refer to this
    if factionUpgrade is not None:
        lst.insert(1, factionUpgrade)

    # For 10-12 upgrades, we want Cost to be first after Requirement, to look nice in Embed
    if lst[3].startswith('Requirement'):
        old = lst[3]
        new = lst[4]
        lst[3] = new
        lst[4] = old

    # Cleanup in case bad stuff goes through somehow
    for line in lst[3:]:
        if line in badSubstrings:
            lst.remove(line)

        # Notes are not really important for the embed
        if line.startswith("Note") or line.startswith("Tip"):
            lst.remove(line)

    # A little extra for Djinn 8 - show current UTC time and odd/even day
    if factionUpgrade == "Flashy Storm":
        utc_dt = datetime.datetime.utcnow()
        day = int(utc_dt.strftime("%d"))
        dj8 = ""
        if day % 2 == 0:
            dj8 = ", Odd-tier Day"
        elif day % 2 == 1:
            dj8 = ", Even-tier Day"

        lst.append(f'Current Time (UTC): {utc_dt.strftime("%H:%M")}' + dj8)

    # A little less for the Druid Challenges reward - remove picture from lst
    if factionUpgrade == "Primal Balance":
        lst.pop(5)

    print(lst)

    return lst


def factionUpgradeSearch(faction):
    # Getting the Upgrade from FactionUpgrades
    factionUpgrade = FactionUpgrades.getFactionUpgradeName(faction)

    # Retrieving data using Request and converting to BeautifulSoup object
    nawLink = "http://musicfamily.org/realm/FactionUpgrades/"
    content = requests.get(nawLink)
    soup = BeautifulSoup(content.content, 'html5lib')

    # Searching tags starting with <p>, which upgrades' lines on NaW begin with
    p = soup.find_all('p')

    # Our upgrade info will be added here
    screen = []

    # Iterating through p, finding until upgrade matches
    for tag in p:
        # space is necessary because there is always one after image
        if tag.get_text() == " " + factionUpgrade:
            # if True, adds full line so we can retrieve the image through our formatting function
            screen.append(str(tag))

            # Since we return true, we search using find_all_next function, and then break it there since we don't
            # need to iterate anymore at the end
            for line in tag.find_all_next(['p', 'br', 'hr', 'div']):
                # Not-a-Wiki stops lines after a break, a new line, or div, so we know the upgrade info stop there
                if str(line) == "<br/>" or str(line) == "<hr/>" or str(line).startswith("<div"):
                    break
                else:
                    # Otherwise, add the lines of upgrade to the list - line.text returns the text without HTML tags
                    screen.append(line.text)
            break

    # Then we run the list through a formatter, and that becomes our new list
    return format(screen, factionUpgrade)

def factionChallengeSearch(faction):
    # Retrieving data using Request and converting to BeautifulSoup object
    nawLink = "http://musicfamily.org/realm/Challenges/"
    content = requests.get(nawLink)
    soup = BeautifulSoup(content.content, 'html5lib')

    # Searching tags starting with <area>, which challenges' lines on NaW begin with
    p = soup.find_all('area')

    # Our upgrade info will be added here
    screen = []

    find = False
    # Iterating through p, finding until upgrade matches
    for tag in p:
        if faction in tag['href']:
            temp = tag['research'].split("</p>")
            # The following is to convert tag['research'] into a format that the format() function will work with
            temp = [re.sub("<p>|<b>|</b>|\n|\t", "", s) for s in temp]
            temp.insert(0, temp[1])
            temp.pop(2)
            screen = screen + temp
            find = True

    if not find:
        raise Exception("Invalid Input")

    # Then we run the list through a formatter, and that becomes our new list
    challengeName = screen[0].split("> ")[1]
    return format(screen, challengeName)

def researchSearch(res):
    nawLink = "http://musicfamily.org/realm/Researchtree/"
    content = requests.get(nawLink)
    soup = BeautifulSoup(content.content, 'html5lib')

    p = soup.find_all('area')

    for tag in p:
        if tag['research'].startswith(res + " "):
            print(tag)
            temp = re.split('\ \-\ |Research\ Name:|<p>|\ <p>|<p>\ |\ <p> ' , tag['research'])

    for line in temp:
        if line in badSubstrings:
            temp.remove(line)

    return temp

class Notawiki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=alias["upgrade"])
    async def upgrade(self, ctx, arg=None, number=None):
        """Retrieves information of a Faction Upgrade from Not-a-Wiki"""
        global color
        global faction

        # basic Help command
        if (arg is None and number is None) or (arg == "help" and number is None):
            emoji = discord.utils.get(ctx.guild.emojis, name="SuggestionMaster")
            description = "**.upgrade <faction>**\n**Aliases: **" + ', '.join(alias["upgrade"]) + \
                          "\n\nRetrieves a Faction upgrade information " \
                          "directly from Not-a-Wiki. <faction> inputs can be using two-letter Mercenary Template with " \
                          "upgrade number, or full Faction name with an upgrade number.\n\nExamples: Fairy 7, MK10 "
            embed = discord.Embed(title=f"{emoji}  Upgrade", description=description,
                                  colour=discord.Colour.dark_gold())
            return await ctx.send(embed=embed)

        # Checking if input returns an abbreviation faction i.e. FR7 or MK11, also accepts lowercase inputs
        if arg[2].isdigit() and number is None:
            faction = arg.upper()
            argColor = faction[0:2]
            color = FactionUpgrades.getFactionColour(argColor)

        # if number is added as an input, we automatically assume the full term, i.e. "Fairy 7"
        elif number is not None:
            # Some people just like to watch the world burn
            if int(number) < 0 or int(number) > 12:
                raise Exception('Invalid Input')

            arg2 = arg.lower()
            arg2 = arg2.capitalize()
            checks, fac, color = FactionUpgrades.getFactionAbbr(arg2)

            # checks is retrieved from FactionUpgrades, if the term is not in dictionary it returns False and we
            # raise Exception error
            if checks is False:
                raise Exception('Invalid Input')
            else:
                faction = fac + number

        # if inputs match neither above, raise Exception
        else:
            raise Exception('Invalid Input')

        async with ctx.channel.typing():
            # We get our list through Not-a-Wiki Beautiful Soup search
            data = factionUpgradeSearch(faction)

            # Embed things, using the list retrieved from factionUpgradeSearch
            thumbnail = data[0]
            title = f'**{data[1]}**'
            embed = discord.Embed(title=title, colour=discord.Colour(color), timestamp=datetime.datetime.utcnow())
            embed.set_footer(text="http://musicfamily.org/realm/FactionUpgrades/",
                             icon_url="http://musicfamily.org/realm/Factions/picks/RealmGrinderGameRL.png")
            embed.set_thumbnail(url=thumbnail)

            # Since the first two lines always are guaranteed to be an url and name of Faction upgrade, we ignore
            # them, and then start processing adding new fields for each line
            for line in data[2:]:
                newline = line.split(": ")
                first = f'**{newline[0]}**'
                embed.add_field(name=first, value=newline[1], inline=True)

        await ctx.send(embed=embed)

    @upgrade.error
    async def upgrade_error(self, ctx, error):
        if isinstance(error, Exception):
            title = " :exclamation:  Command Error!"
            description = "The parameters you used are not found in the list. Please try again."
            embed = discord.Embed(title=title, description=description, colour=discord.Colour.red())
            return await ctx.send(embed=embed)

    @commands.command(aliases=alias["challenge"])
    async def challenge(self, ctx, arg=None, number=None):
        """Retrieves information of a Faction Challenge from Not-a-Wiki"""
        global color
        global faction

        # Help panel in case of no input
        if (arg is None and number is None) or (arg == "help" and number is None):
            emoji = discord.utils.get(ctx.guild.emojis, name="SuggestionMaster")
            description = "**.challenge <faction>**\n**Aliases: **" + ', '.join(alias["challenge"]) + "\n\nRetrieves a " \
                        "Faction Challenge information directly from Not-a-Wiki. <faction> inputs can be using " \
                        "two-letter Faction abbreviation (like for Mercenary templates) with " \
                        "challenge number, or full Faction name with a challenge number.\n\nExamples: Fairy 3, DG6 "
            embed = discord.Embed(title=f"{emoji}  Challenge", description=description, colour=discord.Colour.dark_gold())
            return await ctx.send(embed=embed)

        # Checking if input returns an abbreviation faction i.e. FRC2 or MKC5, also accepts lowercase inputs
        if arg[2].isdigit() or arg[2] in ["R", "r"] and number is None:
            faction = arg.upper()
            argColor = faction[0:2]
            color = FactionUpgrades.getFactionColour(argColor)
            # No huge dictionary this time around
            faction2 = FactionUpgrades.getFactionNameFull(argColor)

            faction = faction2 + faction[0] + "C" + faction[2:]

        # if number is added as an input, we automatically assume the full term, i.e. "Fairy 7"
        elif number is not None:
            # Number checker has been moved to factionChallengeSearch()
            arg2 = arg.lower()
            arg2 = arg2.capitalize()
            checks, fac, color = FactionUpgrades.getFactionAbbr(arg2)

            # checks is retrieved from FactionUpgrades, if the term is not in dictionary it returns False and we
            # raise Exception error
            if checks is False:
                raise Exception('Invalid Input')
            else:
                faction = arg2 + arg2[0] + "C" + str(number).upper()

        # if inputs match neither above, raise Exception
        else:
            raise Exception('Invalid Input')

        async with ctx.channel.typing():
            # We get our list through Not-a-Wiki Beautiful Soup search
            # factionChallengeSearch takes parameters like "FairyFC1" or "FacelessFC1" (note the similar last 3 characters)
            data = factionChallengeSearch(faction)

            ignore = 4

            # Embed things, using the list retrieved from factionChallengeSearch
            thumbnail = data[0]
            # Spell rewards need special formatting
            if faction[-1:] == "R":
                title = f'**{data[1]}**'
                ignore = 3
            else:
                title = f'**{data[2]} : {data[1]}**'
            embed = discord.Embed(title=title, colour=discord.Colour(color), timestamp=datetime.datetime.utcnow())
            embed.set_footer(text="http://musicfamily.org/realm/Challenges/",
                             icon_url="http://musicfamily.org/realm/Factions/picks/RealmGrinderGameRL.png")
            embed.set_thumbnail(url=thumbnail)

            # Ignore the first 4 fields and create the rest
            for line in data[ignore:]:
                newline = line.split(": ")
                first = f'**{newline[0]}**'
                embed.add_field(name=first, value=newline[1], inline=True)

        await ctx.send(embed=embed)

    @challenge.error
    async def challenge_error(self, ctx, error):
        if isinstance(error, Exception):
            title = " :exclamation:  Command Error!"
            description = "The parameters you used are not found in the list. Please try again."
            embed = discord.Embed(title=title, description=description, colour=discord.Colour.red())
            return await ctx.send(embed=embed)

    @commands.command(aliases=alias["research"])
    async def research(self, ctx, researchName=None):
        """Retrieves Research upgrade from Not-a-Wiki"""

        if researchName is None or researchName == "help":
            description = "**.research <research>**\n**Aliases: **" + ', '.join(alias["research"]) + "\n\nRetrieves the " \
                    "Research info from Not-a-Wiki in an embed displaying name, cost, formula, and effect." \
                    "\n\nAcceptable inputs are only using research branch + number (i.e. S10, C340, E400)."
            emoji = discord.utils.get(ctx.guild.emojis, name="SuggestionMaster")
            embed = discord.Embed(title=f"{emoji}  Research", description=description, colour=discord.Colour.dark_green())
            return await ctx.send(embed=embed)

        researchName = researchName.upper()
        check = False
        dict = FactionUpgrades.getResearchBranch()
        if researchName[0].isalpha() and researchName[1:].isdigit():
            for key,value in dict.items():
                if key[0] == researchName[0]:
                    image = value
                    check = True

        if not check:
            raise Exception("Invalid Input")

        async with ctx.channel.typing():
            data = researchSearch(researchName)

            title = f'{data[0]} - {data[2]}'
            description = data[1]

            embed = discord.Embed(title=title, description=description, colour=discord.Colour.dark_green())
            embed.set_footer(text="http://musicfamily.org/realm/Researchtree/",
                             icon_url="http://musicfamily.org/realm/Factions/picks/RealmGrinderGameRL.png")
            embed.set_thumbnail(image)
            for line in data[3:]:
                line = line.strip()
                newLine = line.split(": ")
                first = f'**{newLine[0]}**'
                embed.add_field(name=first, value=newLine[1], inline=True)

            await ctx.send(embed=embed)

####
def setup(bot):
    bot.add_cog(Notawiki(bot))