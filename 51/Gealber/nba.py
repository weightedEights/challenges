from collections import namedtuple
import csv
import os
import sqlite3

import requests

DATA_URL = 'https://query.data.world/s/ezwk64ej624qyverrw6x7od7co7ftm'
DATA_CACHED = 'nba.data'
NBA_DB = 'nba.db'

# start clean
if os.path.isfile(NBA_DB):
    os.remove(NBA_DB)

Player = namedtuple('Player', ('name year first_year team college active '
                               'games avg_min avg_points'))

conn = sqlite3.connect(NBA_DB)
cur = conn.cursor()


def _get_csv_data():
    """GIVEN:
       Load in CSV data in from remote URL or local cache file"""
    if os.path.isfile(DATA_CACHED):
        with open(DATA_CACHED) as f:
            return f.read()
    else:
        with requests.Session() as session:
            return session.get(DATA_URL).content.decode('utf-8')


def load_data():
    """GIVEN:
       Converts NBA CSV data into a list of Player namedtuples"""
    content = _get_csv_data()
    reader = csv.DictReader(content.splitlines(), delimiter=',')
    for row in reader:
        player = Player(name=row['Player'],
                        year=row['Draft_Yr'],
                        first_year=row['first_year'],
                        team=row['Team'],
                        college=row['College'],
                        active=row['Yrs'],
                        games=row['Games'],
                        avg_min=row['Minutes.per.Game'],
                        avg_points=row['Points.per.Game'])
        yield player


# CODE HERE (tests under __main__):

def import_to_db(players=None):
    """Create database table in sqlite3 and import the players data

       required table SQL:
       CREATE TABLE players (name, year, first_year, team, college,
                             active, games, avg_min, avg_points)
    """
    if players is None:
        players = list(load_data())

    cur.execute('''CREATE TABLE players (name VARCHAR, year INTEGER, first_year INTEGER, team VARCHAR , college VARCHAR,
                             active INTEGER, games INTEGER, avg_min FLOAT, avg_points FLOAT)''')
    cur.executemany('''INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?)''', players)


def player_with_max_points_per_game():
    """The player with highest average points per game (don't forget to CAST to
       numeric in your SQL query)"""
    c = cur.execute('''SELECT name, MAX(avg_points) FROM players''')
    return c.fetchone()[0]


def number_of_players_from_duke():
    """Return the number of players with college == Duke University"""
    c = cur.execute('''SELECT COUNT(*) FROM players WHERE college=?''', ("Duke University",))
    return c.fetchone()[0]


def percentage_of_players_first_year():
    """Return 2 digit percentage of players whose first year it is
       (first_year column)"""
    number_of_players = cur.execute('''SELECT COUNT(*) FROM players''').fetchone()[0]
    number_rookie = cur.execute('''SELECT COUNT(*) FROM players WHERE first_year=?''', (1,)).fetchone()[0]
    return number_rookie / number_of_players * 100


def avg_years_active_players_stanford():
    """Return the average years that players from "Stanford University
       are active ("active" column)"""
    c = cur.execute('''SELECT AVG(active) FROM players WHERE college=?''', ("Stanford University",))
    return c.fetchone()[0]


def year_with_most_drafts():
    """Return the year with the most drafts, in SQL you can use GROUP BY"""
    c = cur.execute('''SELECT year, MAX(count) FROM (SELECT year COUNT(year) as count FROM players GROUP BY year)''')
    return c.fetchone()[0]


def most_games_per_year_for_veterans():
    """Top 6 players that are > 10 years active, that have the
       highest # games / year"""
    c = cur.execute('''SELECT name FROM players WHERE active > 10 ORDER BY games/active DESC LIMIT 6''')
    return [data[0] for data in c.fetchall()]


if __name__ == '__main__':
    import_to_db()


    # A. check if the import went well
    def _verify_total_row_count_after_import():
        sql = '''SELECT COUNT(*) FROM players'''
        cur.execute(sql)
        ret = cur.fetchall()
        return ret[0][0]


    assert _verify_total_row_count_after_import() == 3961

    # B. some simple asserts of the data analysis functions
    assert player_with_max_points_per_game() == 'Michael Jordan'

    assert number_of_players_from_duke() == 58

    assert round(avg_years_active_players_stanford(), 2) == 4.58

    assert round(percentage_of_players_first_year(), 2) == 1.51

    assert int(year_with_most_drafts()) == 1984

    expected = ['A.C. Green', 'Alex English', 'Jack Sikma',
                'John Stockton', 'Mark Eaton', 'Terry Tyler']
    assert sorted(most_games_per_year_for_veterans()) == expected
