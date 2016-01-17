"""
RiotAPIWrapper
~~~~~~~~~~~~~~

This library allows you to lookup stats through the Riot API
"""

import json
import threading
import time

# PIP imports
import requests
import requests_cache

# The time to pause between requests (in seconds)
WAIT_TIME = 1
# The maximum number of attempts to make for a request
MAX_RETRIES = 3

TIME_HOUR = 1000 * 60 * 60  # milliseconds in hour


class RiotAPIWrapper:
    """A class that wraps access to Riot's public API

    Initialize with the API Key. Returns None if an error occurs
    """

    request_lock = threading.Lock()

    def __init__(self, key):
        self._session = requests_cache.CachedSession(
            cache_name='RiotAPI_cache', backend='sqlite', expire_after=60)
        self._key = key

    def send_request(self, url, params=dict(), static=False):
        # Send http request to Riot API
        # If static is True, skip request throttling
        # Returns json object containing API result
        # or None if an error occured

        params['api_key'] = self._key
        success = False
        for _ in range(0, MAX_RETRIES):
            has_lock = False
            try:
                result = self._session.get(url, params=params)

                if not static and not result.from_cache:
                    # We hit the API. Pause so we don't go over the
                    # rate limit
                    print 'sent request to url: %s' % result.url
                    RiotAPIWrapper.request_lock.acquire()
                    has_lock = True
                    time.sleep(WAIT_TIME)
            finally:
                if has_lock:
                    RiotAPIWrapper.request_lock.release()

            if result.status_code == 200:
                success = True
                break

            # TODO: add support for more error codes and/or better
            # error handling
            if result.status_code == 404:
                return None

            if result.status_code == 429:
                # Rate limit hit, wait for the suggested time
                retry_after = int(result.headers['Retry-After'])
                time_to_sleep = min(10, retry_after) - WAIT_TIME
                print 'Rate limit hit. Pausing for %d seconds...' %\
                    (time_to_sleep + 1)
                time.sleep(time_to_sleep + 1)

        if success:
            return json.loads(result.text)

        return None

    def current_game_v1_0(self, platformID, summonerID):
        # Get information about a summoner's current game
        url = ('https://na.api.pvp.net/observer-mode/rest/consumer/'
               'getSpectatorGameInfo/%s/%s') % (platformID, str(summonerID))
        result = self.send_request(url)
        return result

    def game_v1_3(self, region, summonerID):
        # Get information about a summoner's recent games
        url = ('https://na.api.pvp.net/api/lol/%s/v1.3/game/by-summoner/%s/'
               'recent') % (region, str(summonerID))
        result = self.send_request(url)
        return result

    def stats_v1_3_ranked(self, summonerID, season=None):
        # Get a summoner's ranked stats
        # default behaviour is to retrieve stats for current season
        url = ('https://na.api.pvp.net/api/lol/na/v1.3/stats/by-summoner/%s/'
               'ranked') % (str(summonerID))
        if season:
            result = self.send_request(url, params={'season': season})
        else:
            result = self.send_request(url)

        return result

    def lol_static_data_v1_2_champion(self, locale=None, version=None,
                                      dataById=None, champData=None):
        # Retrieves list of champions
        url = 'https://global.api.pvp.net/api/lol/static-data/na/v1.2/champion'
        params = dict()
        for name, value in {'locale': locale,
                            'version': version,
                            'dataById': dataById,
                            'champData': champData}.items():
            if value is not None:
                params[name] = value

        result = self.send_request(url, params=params, static=True)
        return result

    def summoner_v1_4_by_name(self, region, summonerNames):
        # Lookup summoners by name
        url = 'https://na.api.pvp.net/api/lol/%s/v1.4/summoner/by-name/%s' %\
            (region, summonerNames)
        result = self.send_request(url)
        return result


# Load key and setup API wrapper
with open('key', 'rb') as f:
    key = f.read()

API = RiotAPIWrapper(key)
champion_names = None


def lookup_champion_names():
    # Helper function to get a dictionary mapping champion IDs to names
    result = API.lol_static_data_v1_2_champion()
    if result is None:
        return None

    to_ret = {}
    for champ in result[u'data'].values():
        to_ret[champ[u'id']] = champ[u'name']

    return to_ret


def get_champion_name(champID):
    """Looks up champion name from champion ID"""
    global champion_names

    if champion_names is None:
        # Lookup champion names from the Riot API
        champion_names = lookup_champion_names()
        if champion_names is None:
            return None

    try:
        to_ret = champion_names[champID]
    except KeyError:
        print 'Error looking up champion ID %d' % champID
        return None

    return to_ret


def get_teams(summonerID):
    """Returns the allies and enemies in the summoner's game

    Return value has the form (friendly_team, enemy_team),
    where each team is a dictionary mapping summoner IDs to champion IDs
    Returns none if an error occurs (i.e summoner is not in a game)
    """

    game = API.current_game_v1_0('NA1', summonerID)
    if game is None:
        return None

    participants = game[u'participants']
    friendly_team = dict()
    enemy_team = dict()

    # find friendly team ID
    for player in participants:
        if player[u'summonerId'] == int(summonerID):
            teamID = player[u'teamId']
            break
    else:
        return None

    for player in participants:
        player_summonerID = player[u'summonerId']
        player_champID = player[u'championId']
        if player[u'teamId'] == teamID:
            friendly_team[player_summonerID] = player_champID
        else:
            enemy_team[player_summonerID] = player_champID

    return (friendly_team, enemy_team)


def get_stats(summonerID, champID=0):
    """Returns the ranked stats for a player for a given champion

    If champID is 0, returns the stats for all champions
    Return value is a dictionary with the number of games played,
    number of wins, total kills, total assists, and total deaths for
    that champion
    """

    all_stats = API.stats_v1_3_ranked(summonerID)
    if all_stats is None:
        return None

    champions = all_stats[u'champions']
    for champ in champions:
        if champ[u'id'] == champID:
            stats = champ[u'stats']
            break
    else:
        # Player has no history with this champion
        return None

    if (champID != 0):
        champ_name = get_champion_name(champID)
    else:
        champ_name = 'All'
    num_games = stats[u'totalSessionsPlayed']
    num_wins = stats[u'totalSessionsWon']
    kills = stats[u'totalChampionKills']
    assists = stats[u'totalAssists']
    deaths = stats[u'totalDeathsPerSession']

    return {'num_games': num_games,
            'num_wins': num_wins,
            'kills': kills,
            'assists': assists,
            'deaths': deaths}


def get_recent_winrate(summonerID, recent_time=TIME_HOUR * 12):
    """Returns a string describing a summoner's recent win rate"""

    min_time = time.time() * 1000 - recent_time

    result = API.game_v1_3('na', summonerID)
    if result is None:
        return None

    games = result[u'games']
    recent_games = []
    for game in games:
        if game[u'createDate'] >= min_time:
            recent_games += [game]

    # Sort games by their times
    recent_games.sort(cmp=lambda g1, g2: cmp(g1[u'createDate'],
                                             g2[u'createDate']))

    record = ''
    for game in recent_games:
        if game[u'stats'][u'win']:
            record += '+'
        else:
            record += '-'

    return record


def get_summoner_id(name):
    """Lookup a summoner ID by name"""
    value = API.summoner_v1_4_by_name('na', name).values()[0]
    return value[u'id']
