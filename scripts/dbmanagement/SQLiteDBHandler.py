# Run the following commands to install the packages before importing:
# pip install pandas
# praw, discord, dotenv, sqlite3

import discord
import dotenv
import os
import pandas as pd
import sqlite3
from itertools import chain

def connectDB():
    # connect to database
    connection = sqlite3.connect(r"scripts\dbmanagement\UserInfo.db")
    print("Database opened successfully")
    # create db cursor
    cur = connection.cursor()
    print("Connection made")
    return connection, cur

# for creating tables and inserting data
def execute_query(query):
    connection, cur = connectDB()
    try:
        cur.execute(query)
        connection.commit()
        print("Query successful")
        connection.close()          # saves the commit
    except Exception as err:
        print(f"Error: '{err}'")


# for viewing tables and data
def read_query(query):
    connection, cur = connectDB()
    result = None
    try:
        cur.execute(query)
        result = cur.fetchall()
        return result
    except Exception as err:
        print(f"Error: '{err}'")


def user_exists(userID):
    """Checks if the user exists in the DB. If they don't, it puts them in """
    findUsers = """
    SELECT ID FROM UserStats;
    """
    knownUsers = read_query(findUsers)      # returns as nested list
    knownUsers = chain.from_iterable(knownUsers)
    if userID in knownUsers:
        return True
    else:
        updateQuery = f"""
        INSERT INTO UserStats VALUES
        ({userID}, 0, 0, 1, 0);
        """
        execute_query(updateQuery)
        return False


def update_points(userID, points_to_add):
    """Updates the user's points in the DB. To get userID, try using ctx.message.author.id"""
    points_to_add = int(points_to_add)
    if user_exists(userID):
        findPoints = f"""
        SELECT Points FROM UserStats
        WHERE ID = {userID}
        """
        currentPoints = read_query(findPoints)
        # grab value from nested list
        currentPoints = currentPoints[0][0]

        newPoints = currentPoints + points_to_add
        updateQuery = f"""
        UPDATE UserStats
        SET Points = {newPoints}
        WHERE ID = {userID};
        """
    else:
        updateQuery = f"""
        INSERT INTO UserStats VALUES
        ({userID}, {points_to_add}, 0, 1, 0);
        """
    execute_query(updateQuery)


def update_gold(userID, gold_to_add):
    """Updates the user's gold in the DB. To get userID, try using ctx.message.author.id"""
    gold_to_add = int(gold_to_add)
    if user_exists(userID):
        findGold = f"""
        SELECT Gold FROM UserStats
        WHERE ID = {userID};
        """
        currentGold = read_query(findGold)
        # grab value from nested list
        currentGold = currentGold[0][0]

        newGold = currentGold + gold_to_add
        updateQuery = f"""
        UPDATE UserStats
        SET Gold = {newGold}
        WHERE ID = {userID};
        """
    else:
        updateQuery = f"""
        INSERT INTO UserStats VALUES
        ({userID}, 0, {gold_to_add}, 1, 0);
        """
    execute_query(updateQuery)

"""
MAKE SURE THE TABLE ONLY HAS LEGITIMATE USERS IN IT (don't manually add fake user IDs to the table)
"""
async def print_full_tuples(ctx, results: str):
    for result in results:
        ID, points, gold, level, exp = result
        member = await ctx.bot.fetch_user(ID)
        red = 0xFF1010
        embed=discord.Embed(title=f"{member.name}",
                        url="https://realdrewdata.medium.com/",
                        color=red)

        embed.add_field(name = "Stats", value=f"Points: {points}\nGold: {gold}\nLevel: {level}\nEXP: {exp}", inline=False)
        await ctx.send(embed=embed)

async def print_ranked_tuples(ctx, results: str):
    rankNum = 0
    colors = {
        'red': 0xFF1010,
        'green': 0x03D000,
        'blue': 0x106EFF,
        'yellow': 0xFFFB10, 
        'purple': 0x8B10FF}
    rankColor = colors["red"]
    for result in results:
        ID, points, gold, level, exp = result
        member = await ctx.bot.fetch_user(ID)
        rankNum+=1

        if rankNum == 2:
            rankColor = colors["green"]
        elif rankNum == 3:
            rankColor = colors["blue"]
        elif rankNum == 4:
            rankColor = colors["yellow"]
        elif rankNum >= 5:
            rankColor = colors["purple"]
        
        embed=discord.Embed(title=f"Rank {rankNum}",
                        url="https://realdrewdata.medium.com/",
                        color=rankColor)

        embed.add_field(name=f"{member.name}", value=f"Points: {points}\nGold: {gold}\nLevel: {level}\nEXP: {exp}", inline=False)
        await ctx.send(embed=embed)
        if rankNum >= 5:
            break

# all info on each player in the server
async def view_stats(ctx):
    select_query = """
    SELECT * FROM UserStats;
    """
    results = read_query(select_query)
    await print_full_tuples(ctx, results)

# all info on the players with the top 5 points
async def view_top5(ctx):
    select_query = """
    SELECT * FROM UserStats
    ORDER BY Points DESC;
    """
    results = read_query(select_query)
    await print_ranked_tuples(ctx, results)

# all info on specific player
async def get_stats(ctx, user: discord.Member):
    userID = user.id
    user_exists(userID)

    select_query = f"""
    SELECT * FROM UserStats
    WHERE ID = {userID};
    """
    result = read_query(select_query)
    await print_full_tuples(ctx, result)
    return result


def get_character_from_db(discordid : int, charname = None) -> list:
    if (discordid is None):
        print("bad discordID")
        return
    findChar = f"""
    SELECT * FROM Characters
    WHERE discordID = {discordid};
    """
    if charname is not None:
        findChar = f"""
        SELECT * FROM Characters
        WHERE discordID = {discordid}
        AND name = '{charname}';
        """
    result = read_query(findChar)
    return result


def save_character_into_db(discordid : int, stat_dict : dict) -> list:
    if (discordid is None or stat_dict is None):
        return

    name = f"{stat_dict['name']}"
    query = f"""
    SELECT * FROM Characters
    WHERE discordID = {discordid}
    AND name = '{name}';
    """
    if len(read_query(query)) > 0:
        skill_1 = f"'{stat_dict['skills'][0]}'" if stat_dict['skills'][0] is not None else 'NULL'
        skill_2 = f"'{stat_dict['skills'][1]}'" if stat_dict['skills'][1] is not None else 'NULL'
        skill_3 = f"'{stat_dict['skills'][2]}'" if stat_dict['skills'][2] is not None else 'NULL'
        skill_4 = f"'{stat_dict['skills'][3]}'" if stat_dict['skills'][3] is not None else 'NULL'
        skill_5 = f"'{stat_dict['skills'][4]}'" if stat_dict['skills'][4] is not None else 'NULL'
        query = f"""
        UPDATE Characters
        SET level = {stat_dict['level']},
            exp = {stat_dict['exp']},
            hp = {stat_dict['hp']},
            mp = {stat_dict['mp']},
            strength = {stat_dict['strength']},
            dexterity = {stat_dict['dexterity']},
            vitality = {stat_dict['vitality']},
            magic = {stat_dict['magic']},
            spirit = {stat_dict['spirit']},
            skill_1 = {skill_1},
            skill_2 = {skill_2},
            skill_3 = {skill_3},
            skill_4 = {skill_4},
            skill_5 = {skill_5}
        WHERE discordID = {discordid}
        AND name = '{stat_dict['name']}';
        """
        message = "Character Saved!"
    else:
        print("Character doesn't exist, moving to create.")
        skill_1 = f"'{stat_dict['skills'][0]}'" if stat_dict['skills'][0] is not None else 'NULL'
        skill_2 = f"'{stat_dict['skills'][1]}'" if stat_dict['skills'][1] is not None else 'NULL'
        skill_3 = f"'{stat_dict['skills'][2]}'" if stat_dict['skills'][2] is not None else 'NULL'
        skill_4 = f"'{stat_dict['skills'][3]}'" if stat_dict['skills'][3] is not None else 'NULL'
        skill_5 = f"'{stat_dict['skills'][4]}'" if stat_dict['skills'][4] is not None else 'NULL'
        #print(skill_1, skill_2, skill_3, skill_4, skill_5)
        query = f"""
        INSERT INTO Characters (
            ID,
            discordID,
            name,
            level,
            exp,
            hp,
            mp,
            strength,
            dexterity,
            vitality,
            magic,
            spirit,
            luck,
            weapon,
            skill_type,
            skill_1,
            skill_2,
            skill_3,
            skill_4,
            skill_5
        ) 
        VALUES (
            NULL,
            {discordid},
            '{stat_dict['name']}',
            {stat_dict['level']},
            {stat_dict['exp']},
            {stat_dict['hp']},
            {stat_dict['mp']},
            {stat_dict['strength']},
            {stat_dict['dexterity']},
            {stat_dict['vitality']},
            {stat_dict['magic']},
            {stat_dict['spirit']},
            {stat_dict['luck']},
            '{stat_dict['weapon']}',
            '{stat_dict['skill_type']}',
            {skill_1},
            {skill_2},
            {skill_3},
            {skill_4},
            {skill_5}
        );
        """
        message = "Adventurer Successfully Created!"
    execute_query(query)
    return message


def update_user_info(player_dict : dict):
    """Updates an entire user's row in the UserInfo table"""
    if player_dict is None:
        return
    user_exists(player_dict['id'])
    query = f"""
    UPDATE UserStats
    SET Points = {player_dict['points']},
    Gold = {player_dict['gold']},
    Level = {player_dict['level']},
    EXP = {player_dict['exp']}
    WHERE ID = {player_dict['id']}
    """
    execute_query(query)


def delete_char_from_table(ctx, name : str):
    if (ctx is None or name is None):
        return
    query = f"""
    DELETE FROM Characters
    WHERE discordid = {ctx.message.author.id}
    AND name = '{name}';
    """
    execute_query(query)



async def get_my_stats(ctx):
    user_exists(ctx.message.author.id)
    select_query = f"""
    SELECT * FROM UserStats
    WHERE ID = {ctx.message.author.id};
    """
    result = read_query(select_query)
    return result


async def test_points(ctx):
    userID = ctx.message.author.id
    update_points(userID, int(1))


async def test_gold(ctx):
    userID = ctx.message.author.id
    update_gold(userID, int(1))