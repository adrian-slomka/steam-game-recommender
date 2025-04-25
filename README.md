# Steam Game Recommender + Discord Bot (optional)


A script with a optional Discord bot that recommends games based on Steam library using Slash Commands.


## How It Works

1) When a user enters their SteamID, the bot fetches their game library. (Steam Web API Key)

2) The script analyzes game genres, tags, and playtime.

3) A list of suggested games is returned directly in the Discord chat.

The bot also performs regular background updates of game data every 24 hours to keep recommendations accurate and relevant.


## Features

-  **Game Recommendations**
Get personalized game suggestions by entering your SteamID.

 
-  **Compare Libraries (WIP)**
Find co-op games both you and a friend own.


-  **Automatic + Manual Updates**
The bot updates its database every 24 hours — or manually via `/sara update`.


-  **Slash Command Interface**
Easy-to-use `/sara` commands directly from Discord.



## 💬 Available Commands


`/sara trending` - Recommend games based on your Steam library

`/sara compare` - Find common co-op games between two Steam accounts (WIP)

`/sara update` - Manually trigger a database update


## 🛠️ Setup


### 1. Clone the Repo

 
```bash
git  clone  https://github.com/your-username/steam-recommender-bot.git
cd  steam-recommender-bot
```

  

### 2. Install Requirements

  

```bash
pip  install  -r  requirements.txt
```

  

### 3. Environment Variables

  

Create a .env file in the project root and add the following:
```bash
API_KEY='YOUR_STEAM_API_KEY'
DISCORD_AUTH='YOUR_DISCORD_APP_AUTH_TOKEN'
```

1) Steam API KEY from: https://steamcommunity.com/dev/apikey
2) Discord bot authenticaion token from: https://discord.com/developers/applications

  
### 4. Geckodriver for Selenium

https://github.com/mozilla/geckodriver/releases
* read more about this down below in Limitations

### 5. Run the Bot

```bash
python  main.py
```

  
  

# Limitations

  

There are a FEW technical limitations:

  

### 1. SteamDB Scraping & WebDriver Dependency

  

To gather real-time data from **SteamDB trending, top sellers, and other dynamic pages**, the bot uses **Selenium** for browser automation. This is necessary to bypass bot detection mechanisms present on SteamDB.

  

- A compatible **WebDriver** (e.g., [GeckoDriver](https://github.com/mozilla/geckodriver/releases) for Firefox) and a **locally installed web browser** are required.

- You may need to **manually update the path** to your browser executable in the `scraper.py` file to match your system configuration.

  

### 2. Steam API Rate Limits & Missing Genre Data

  

Due to Steam API’s rate limits (approximately **1 request per second**), real-time fetching of missing genre or tag data can slow down responses, especially if the game is not already cached in the local database.

  

- In such cases, the bot may timeout or return an error message in Discord.

- To mitigate this, a **prebuilt game metadata database** is available for download, significantly speeding up the setup and response times.

- If you prefer to set up your own database, instructions are included in `main.py`.
