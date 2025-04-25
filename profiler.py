from scraper import SteamAPI
from database import Database
from collections import Counter, defaultdict

import time
import random

class Profiler:
    def __init__(self):
        self.current_time = int(time.time())


    def build_profile(self, *steamids: int):
        '''

        '''
        if not steamids:
            return {}

        steam_api = SteamAPI()
        users = {}
        for steamid in steamids:
            games = steam_api.get_user_library(steamid)
            users[steamid] = {
                'total_playtime': 0,
                'last2weeks_playtime': 0,
                'games': games
            }


        current_unix_time = self.current_time
        max_days = 365

        for steamid, user_data in users.items():
            # Calculate User's account total_playtime and Last 2 weeks playtime (in minutes)
            total_playtime = 0
            last2weeks_playtime = 0
            for game in user_data.get('games'):
                total_playtime += game.get('playtime_forever', 0)
                last2weeks_playtime += game.get('playtime_2weeks', 0)
            user_data['total_playtime'] = total_playtime
            user_data['last2weeks_playtime'] = last2weeks_playtime

            # Calculate playtime_ratio --> playtime_share = app's playtime_forever / user's total_playtime 
            for game in user_data.get('games'):
                game_playtime = game.get('playtime_forever', 0)
                try:
                    playtime_ratio = game_playtime / total_playtime # Playtime score (normalized)
                except ZeroDivisionError:
                    playtime_ratio = 0
                game['playtime_ratio'] = round(playtime_ratio, 6)

            # Calculate last2weeks_playtime_ratio --> 2 WEEKS playtime_share = app's playtime_2weeks / user's last2weeks_playtime 
            for game in user_data.get('games'):
                game_playtime = game.get('playtime_2weeks', 0)
                try:
                    last2weeks_playtime_ratio = game_playtime / last2weeks_playtime # 2 wEEKS Playtime score (normalized)
                except ZeroDivisionError:
                    last2weeks_playtime_ratio = 0 
                game['last2weeks_playtime_ratio'] = round(last2weeks_playtime_ratio, 6)

            # 0.1 to 1 MULTIPLIER --> days since the game was last played devided by a year (365 days)
            for game in user_data.get('games'):
                rtime_last_played = game.get('rtime_last_played', 0)
                if rtime_last_played == 0:
                    score = 0.1
                else:
                    days_since_played = (current_unix_time - rtime_last_played) / (24 * 60 * 60)
                    score = max(0.1, 1 - (days_since_played / max_days))
                game['recently_played_score'] = round(score, 3)

            # Calculate SCORE
            for game in user_data.get('games', []):
                playtime_ratio = game.get('playtime_ratio', 0)
                last2weeks_playtime_ratio = game.get('last2weeks_playtime_ratio', 0)/10 # add VALUE to the games that were played within 2 weeks
                last_played = game.get('recently_played_score', 0)
                # Final score
                game['like_score'] = round(playtime_ratio * last_played + last2weeks_playtime_ratio, 5)


            all_games = sorted(user_data.get('games'), key=lambda app: app['like_score'], reverse=True)    # sort by like_score descneding
            top_games = []

            # Append only top 15 somewhat recent games played be the user to base recommendations of off
            if len(all_games) > 15:
                m = 15
            else:
                m = len(all_games)

            for game in all_games[:m]: 
                g = {
                    'appid': game.get('appid'),
                    'name': game.get('name'),
                    'like_score': game.get('like_score')
                }     
                top_games.append(g)
            user_data['recent_interests'] = top_games or []

            played = []
            for game in all_games:
                played.append(game.get('appid'))
            user_data['played_appids'] = played or []

        return users
    

    def recommend(self, *users):
        users = Profiler().build_profile(*users)

        appids = []
        for steamid, user_data in users.items():
            for game in user_data.get('games'):
                appids.append(game.get('appid'))

        Database().check_and_insert_missing(appids)

        # Count shared interests across users
        interest_counter = Counter()

        # Per-user genre like score averages
        all_user_genre_averages = {}

        for steamid, user_data in users.items():
            interests = user_data.get('recent_interests', [])

            # Extract appids from user's recent interests
            appids = [interest['appid'] for interest in interests if 'appid' in interest]
            interest_counter.update(appids)

            # Fetch detailed items for this user's interests
            items = Database().get_items(appids)

            for item in items:
                genres = item.genres
                tags = item.tags
                combined = genres + tags


                # item.combined = list(set(combined))
                item.combined = list(set(genres)) # TEST Only Genres, NO USER TAGS



                # Match like_score from user data
                for id_ in interests:
                    if item.appid == id_.get('appid'):
                        item.like_score = id_.get('like_score')
                        break  # assume one match per appid

                # Build genre_scores
                item.genre_scores = {
                    genre: item.like_score for genre in item.combined
                }

            # Calculate average genre scores for this user
            genre_totals = defaultdict(float)
            genre_counts = defaultdict(int)

            for item in items:
                for genre, score in item.genre_scores.items():
                    if score is not None:
                        genre_totals[genre] += score
                        genre_counts[genre] += 1

            genre_averages = {
                genre: round(genre_totals[genre] / genre_counts[genre], 6)
                for genre in genre_totals
            }

            # Sort the genre averages for this user
            sorted_averages = dict(
                sorted(genre_averages.items(), key=lambda x: x[1], reverse=True)
            )

            all_user_genre_averages[steamid] = sorted_averages

        
        # Print per-user genre preferences
        for steamid, genre_scores in all_user_genre_averages.items():
            

            # Get user's top N genres (e.g., top 5)
            top_genres = list(genre_scores.keys())[:5]

            # Get user's already played/interested appids
            for id_, user_data in users.items():
                if steamid == id_:
                    played_appids = user_data.get('played_appids')

            # Fetch all available items from the database
            all_items = Database().get_items()  # you'll need this method or similar

            # Filter and score potential recommendations
            recommendations = []
            for item in all_items:
                if item.appid in played_appids:
                    continue  # skip already played
                
                
                if not (1 <= item.is_trending <= 150):  # less than 1 and greater than 100
                    continue    # skip not trending games

                release_unix = item.release if item.release else 0  # Set release_unix to 0 if item.release is None
                if not (0 < release_unix <= self.current_time): # not (Check if release time is valid (between 1970 and the current time))
                    continue # Skip invalid items

                combined = set(item.genres + item.tags)
                match_score = len(set(top_genres) & combined)

                if match_score > 0:
                    recommendations.append((item, match_score))

            # Sort recommendations by match score (descending)
            recommendations.sort(key=lambda x: x[1], reverse=True)

            # random.shuffle(recommendations)
            # Show top recommendations
            message = f"""
🎯 Recommendations for User: {steamid}

"""
            print(f"\n🎯 Recommendations for User: {steamid}")
            for item, score in recommendations[:10]:  # top 10 matches
                line = f"  🔹 {item.name}\n"
                message += line
                print(f"  🔹 {item.name}")

        return message
    

if __name__ == "__main__":
    user1 = '76561198155754193'     # Me
    user2 = '76561198010509711'     # Vinit
    user3 = '76561198814557594'     # Maratoshi
    user4 = '76561198024243803'     # Kenny
    user5 = '76561198019513664'     # Veq
    user6 = '76561198051960038'     # Silewa
    user7 = '76561198057915422'     # REOR
    user8 = '76561199103805880'     # LEFTY

    Profiler().recommend(user6)
