from scraper import SteamDB, SteamAPI
from database import Database
from discord_bot import discord_run

def init_app():
    '''
    Only use for the first app launch if there is no localdb.

    It might take from 1,5hr to 2hrs to create new database with appids and their genres
    '''

    Database().create_database()
    data = SteamAPI().get_pages_steamspy(0, 5)
    apps = set()
    for id in data:
        apps.add(id.get('appid'))
    Database().check_and_insert_missing(apps)



if __name__ == "__main__":
    discord_run()

    # FIRST APP INIT, CREATES DB WITH 5K MOST OWNED APPIDS
    #
    # init_app()
    #
    # Only use this function if there is no localdb.db
    # This function will create new .db and download 5000 most owned game appids from SteamSpy and for each
    # for each appid it will make an additioanl reqeust (1s polling limit per appid) to fetch appids details such as genres and tags


    # data = SteamAPI().get_user_library(76561198155754193)
    # print(data)