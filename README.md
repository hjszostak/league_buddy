# League Buddy
A chat bot that allows you to look up League of Legends stats in game. Currently only the North American region is supported.

This uses the [Riot Games API](https://developer.riotgames.com/) to lookup statistics and interacts with the user via the League of Legends chat system. XMPP message handling is done with the [jabberbot](https://pypi.python.org/pypi/jabberbot) library.
## Getting Started
Obtain an [API developer key](https://developer.riotgames.com/) from Riot, and save this key to a file called 'key' in the same directory as the [RiotAPI.py](RiotAPI.py) file. Also, create a [League of Legends account](https://signup.leagueoflegends.com/) for the chat bot. Save the login credentials to a file called 'login' in the same directory as [buddy.py](buddy.py) with the following form:

    username
    password
    
## Usage
Start the bot by running [buddy.py](buddy.py).To interact with the bot, send it chat messages through the League of Legends client.

Available commands:
* help: Displays a list of all available commands
* stats: Displays the win rate and average K/D/A for each summoner in the player's current game. Stats displayed are from ranked games in the current season (in game only)
* tilt `<hours=12>`: Displays the match history for each summoner in the player's current game over the past specified amount of time (in game only)

## Example
    Me: stats
    League Buddy: Looking up stats...
        Your team:
        >>Poppy: 100% of 1, 11.0/5.0/17.0
        >>Ekko: 33% of 6, 4.5/6/8.5
        >>Zed: 58% of 69, 8.1/5.4/6.8
        >>Fiora: No stats
        >>Lucian: 62% of 16, 5.6/3.5/6.2
        Enemy team:
        >>Nami: 60% of 247, 1.5/4.2/17.2
        >>Ezreal: 54% of 61, 6.1/4.9/8.7
        >>Ashe: 0% of 1, 0.0/6.0/17.0
        >>Master Yi: 59% of 124, 9.6/5.4/5.5
        >>Lee Sin: 100% of 2, 7.5/7.5/12.5
    Me: tilt 10
    League Buddy: Looking up match history...
        Match history for the last 10 hours:
        Your team:
        >>Poppy: -+--+
        >>Ekko: +
        >>Zed: 
        >>Fiora: --
        >>Lucian: +
        Enemy team:
        >>Nami: 
        >>Ezreal: +-++-
        >>Ashe: ++-
        >>Master Yi: +
        >>Lee Sin: -+++
