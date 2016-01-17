#!/usr/bin/python

import time
import logging
from jabberbot import JabberBot, botcmd

from pprint import pprint

import RiotAPI

TIME_HOUR = 1000 * 60 * 60

# Output any errors from the jabberbot to stdout
logging.basicConfig()


class LeagueBot(JabberBot):
    def __init__(self, username, password, port, server, debug=False):
        JabberBot.__init__(self, username, password, port=port, server=server,
                           debug=debug)

    def get_player_id(self, mess):
        sender = str(mess.getFrom())
        username = sender.split('@')[0]
        return int(username[3:])  # remove 'sum' from the start of the username

    @botcmd(thread=True)
    def stats(self, mess, args):
        """The ranked win rate and KDA"""

        summ_id = self.get_player_id(mess)
        teams = RiotAPI.get_teams(summ_id)
        if teams is None:
            return "You must be in a game to check stats"
        friendly, enemies = teams

        self.send_simple_reply(mess, "Looking up stats...")

        lines = ["Your team:"]
        for summonerID, champID in friendly.iteritems():
            champ_stats = RiotAPI.get_stats(summonerID, champID)
            to_send = ">>" + RiotAPI.get_champion_name(champID) + ": "
            to_send += self.format_stats(champ_stats)
            lines += [to_send]

        lines += ["Enemy team:"]
        for summonerID, champID  in enemies.iteritems():
            champ_stats = RiotAPI.get_stats(summonerID, champID)
            to_send = ">>" + RiotAPI.get_champion_name(champID) + ": "
            to_send += self.format_stats(champ_stats)
            lines += [to_send]

        pprint(lines)
        # Send response to user
        for line in lines[:-1]:
            self.send_simple_reply(mess, line)
            time.sleep(0.25)
        self.send_simple_reply(mess, lines[-1])

    @botcmd(thread=True)
    def tilt(self, mess, args):
        """The win/loss history each player's recent games"""

        summ_id = self.get_player_id(mess)
        num_hours = 12
        if len(args.split()) > 0:
            try:
                num_hours = int(args.split()[0])
            except ValueError:
                pass

        teams = RiotAPI.get_teams(summ_id)
        if teams is None:
            return "You must be in a game to check match history"
        friendly, enemies = teams

        self.send_simple_reply(mess, "Looking up match history...")

        lines = ["Match history for the last %d hours:" % num_hours]
        lines += ["Your team:"]
        for summonerID, champID in friendly.iteritems():
            to_send = ">>" + RiotAPI.get_champion_name(champID) + ": "
            to_send += RiotAPI.get_recent_winrate(summonerID,
                                                  num_hours * TIME_HOUR)
            lines += [to_send]

        lines += ["Enemy team:"]
        for summonerID, champID in enemies.iteritems():
            to_send = ">>" + RiotAPI.get_champion_name(champID) + ": "
            to_send += RiotAPI.get_recent_winrate(summonerID,
                                                  num_hours * TIME_HOUR)
            lines += [to_send]

        pprint(lines)
        # Send response to user
        for line in lines[:-1]:
            self.send_simple_reply(mess, line)
            time.sleep(0.25)
        self.send_simple_reply(mess, lines[-1])

    def format_stats(self, champ_stats):
        # Helper function that takes the champion stats and returns a
        # formatted string
        if not champ_stats or champ_stats["num_games"] == 0:
            return "No stats"

        num_wins = float(champ_stats["num_wins"])
        num_games = float(champ_stats["num_games"])
        kills = float(champ_stats["kills"])
        assists = float(champ_stats["assists"])
        deaths = float(champ_stats["deaths"])

        win_rate = num_wins / num_games
        avg_kills = kills / num_games
        avg_assists = assists / num_games
        avg_deaths = deaths / num_games

        return '{:.0%} of {:d}, {:.1f}/{:.1f}/{:.1f}'.format(
            win_rate, int(num_games), avg_kills, avg_deaths, avg_assists)


def start_bot(username, password):
    full_username = username + '@pvp.net/xiff'
    full_password = 'AIR_' + password
    port = 5223
    server = '192.64.174.69'

    bot = LeagueBot(full_username, full_password, port=port, server=server)
    bot.serve_forever()


if __name__ == '__main__':
    with open('login', 'rb') as f:
        username, password = f.read().splitlines()[0:2]
    start_bot(username, password)
