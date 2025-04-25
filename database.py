import os
import time
import datetime
import sqlite3
from datetime import timedelta
from scraper import SteamDB, SteamAPI


class Database:
    def __init__(self, genres=None, tags=None, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.genres = genres or []
        self.tags = tags or []


    @staticmethod
    def db_connect():
        """
        Establish a connection to the local 'db.db' SQLite database.

        Sets the row factory to sqlite3.Row to enable dictionary-style access to query results,
        allowing you to access columns by name (e.g., row['column_name']).

        :return: SQLite3 connection object
        """
        conn = sqlite3.connect('localdb.db')
        conn.row_factory = sqlite3.Row  # Allows rows to behave like dictionaries
        return conn


    @staticmethod
    def create_database():
        '''
        Create localdb.db
        '''

        if os.path.exists('localdb.db'):
            return
        
        conn = sqlite3.connect('localdb.db')
        conn.execute("PRAGMA foreign_keys = ON;") # foreign key support
        cursor = conn.cursor()


        # Main Table for Items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                appid INTEGER UNIQUE,
                name TEXT,
                discount INTEGER,
                price INTEGER,    
                rating INTEGER,
                release INTEGER,
                follows INTEGER,
                is_trending INTEGER,
                is_topselling INTEGER,
                is_toprated INTEGER,
                is_mostwishlisted INTEGER,
                has_tags INTEGER,
                has_genres INTEGER,
                requested_details INTEGER,
                last_updated TEXT DEFAULT (datetime('now'))
            )
        ''')

        # Table for SteamDB Tags and their SteamDB specific IDs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS steamdb_tags (
                id INTEGER PRIMARY KEY,
                tag_id INTEGER UNIQUE,
                tag TEXT,
                label_count INTEGER
            )
        ''')

        # Join Table for Genres
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS join_genres (
                items_appid INTEGER,
                genre_id INTEGER,
                PRIMARY KEY (items_appid, genre_id),
                FOREIGN KEY (items_appid) REFERENCES items(appid) ON DELETE CASCADE,
                FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
            )
        ''')

        # Table for Genres
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY,
                genre TEXT UNIQUE
            )
        ''')

        # Join Table for User Categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS join_tags (
                items_appid INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (items_appid, tag_id),
                FOREIGN KEY (items_appid) REFERENCES items(appid) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')

        # Table for User Tags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                tag TEXT UNIQUE
            )
        ''')

        # Trigger for setting current date on update in last_updated column
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_items_last_updated
            AFTER UPDATE ON items
            FOR EACH ROW
            BEGIN
                UPDATE items SET last_updated = datetime('now') WHERE id = OLD.id;
            END;
        ''')

        # Trigger for setting current date on insert in last_updated column
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS insert_items_last_updated
            AFTER INSERT ON items
            FOR EACH ROW
            BEGIN
                UPDATE items SET last_updated = datetime('now') WHERE id = NEW.id;
            END;
        ''')


    def insert_all(self, items):
        '''
        Inserts or updates items in the database.

        Loops through each item in the provided dictionary. For each item:
        - If the item is not in the database, it inserts it as a new record.
        - If the item already exists (matched by appid), it updates the existing record.

        Parameters:
            items (list): A list of dictionaries where each dictionary contains item details (e.g. appid, name, price, tags, etc.).
        Returns:
            None
        '''

        conn = self.db_connect()
        cursor = conn.cursor()

        cursor.execute("BEGIN TRANSACTION")
        existing_appids = {row[0] for row in cursor.execute("SELECT appid FROM items").fetchall()}
        
        for item in items:
            appid = item.get('appid')

            requested_details = cursor.execute('''SELECT requested_details FROM items WHERE appid = ?''', (appid,)).fetchone() # Value to check if the details were already requested thru SteamSpy API
            # Determine the new value for requested_details based on the current value
            new_requested_details = item.get('requested_details', 0)

            # Only update requested_details if the current value is not 1 and the new value is 0
            if requested_details and requested_details[0] == 1 and new_requested_details == 0:
                new_requested_details = requested_details[0]  # Keep the value as 1

            if appid in existing_appids:
                # Update
                cursor.execute('''
                    UPDATE items SET
                        name=?,
                        discount=?,
                        price=?,
                        rating=?,
                        release=?,
                        follows=?,
                        is_trending=?,
                        is_topselling=?,
                        is_toprated=?,
                        is_mostwishlisted=?,
                        requested_details=?       
                    WHERE appid=?
                ''', (
                    item.get('name'),
                    item.get('discount'),
                    item.get('price'),
                    item.get('rating'),
                    item.get('release'),
                    item.get('follows'),
                    item.get('is_trending', 0),
                    item.get('is_topselling', 0),
                    item.get('is_toprated', 0),
                    item.get('is_mostwishlisted', 0),
                    new_requested_details,
                    item.get('appid')
                ))
            else:
                # Insert
                cursor.execute('''
                    INSERT INTO items (
                        appid,
                        name,
                        discount,
                        price,
                        rating,
                        release,
                        follows,
                        is_trending,
                        is_topselling,
                        is_toprated,
                        is_mostwishlisted,
                        requested_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('appid'),
                    item.get('name'),
                    item.get('discount'),
                    item.get('price'),
                    item.get('rating'),
                    item.get('release'),
                    item.get('follows'),
                    item.get('is_trending', 0),
                    item.get('is_topselling', 0),
                    item.get('is_toprated', 0),
                    item.get('is_mostwishlisted', 0),
                    new_requested_details
                ))
                existing_appids.add(appid) # Add tag immediately so future iterations catch it
            

            if not item.get('genres') and not item.get('tags'):
                continue


            has_genres = False
            for genre in item.get('genres') or []:
                cursor.execute('''INSERT OR IGNORE INTO genres (genre) VALUES (?)''', (genre,))

                result = cursor.execute('''SELECT id FROM genres WHERE genre = ?''', (genre,)).fetchone()
                if result:
                    has_genres = True
                    cursor.execute('''INSERT OR IGNORE INTO join_genres (items_appid, genre_id) VALUES (?, ?)''', (appid, result[0]))
            if has_genres:
                cursor.execute('''UPDATE items SET has_genres = ? WHERE appid = ?''', (1, appid))

            has_tags = False
            for tag in item.get('tags') or []:
                cursor.execute('''INSERT OR IGNORE INTO tags (tag) VALUES (?)''', (tag,))

                result = cursor.execute('''SELECT id FROM tags WHERE tag = ?''', (tag,)).fetchone()
                if result:
                    cursor.execute('''INSERT OR IGNORE INTO join_tags (items_appid, tag_id) VALUES (?, ?)''', (appid, result[0]))
                    has_tags = True
            if has_tags:
                cursor.execute('''UPDATE items SET has_tags = ? WHERE appid = ?''', (1, appid))

        conn.commit()
        conn.close()


    def insert_steamdbtags(self, tags):
        '''
        Inserts or updates a tag in the database.
        If a tag with the same tag_id exists, updates the label_count and tag name.
        '''

        conn = self.db_connect()
        cursor = conn.cursor()

        cursor.execute("BEGIN TRANSACTION")
        existing_tagids = {row[0] for row in cursor.execute("SELECT tag_id FROM steamdb_tags").fetchall()}

        for tag in tags:
            tagid = tag.get('id')
            if tagid in existing_tagids:
                cursor.execute('''
                    UPDATE steamdb_tags SET
                        tag=?,
                        label_count=?
                    WHERE tag_id=?
                ''', (
                    tag.get('tag'),
                    tag.get('label_count'),
                    tag.get('id')
                ))
            else:
                cursor.execute('''
                    INSERT INTO steamdb_tags (
                        tag_id,
                        tag,
                        label_count
                    )
                    VALUES (?, ?, ?)
                ''', (
                    tag.get('id'),
                    tag.get('tag'),
                    tag.get('label_count')
                ))
                existing_tagids.add(tagid) # Add tag immediately so future iterations catch it
        conn.commit()
        conn.close()


    @staticmethod
    def get_categories(cursor, row_appid: int):
        '''
        Retrieve the genres and tags associated with a specific item ID from the database.

        Parameters:
            cursor (sqlite3.Cursor): Active database cursor for executing queries.
            row_appid (int): ID of the item to retrieve genres and categories for.

        Returns:
            tuple: A tuple containing two lists:
                - genres (list of str): List of genre names linked to the item.
                - tags (list of str): List of tag names linked to the item.
        '''

        genre_rows = cursor.execute('''
            SELECT g.genre 
            FROM join_genres mg
            JOIN genres g ON mg.genre_id = g.id
            WHERE mg.items_appid = ?
        ''', (row_appid,)).fetchall()

        genres = [genre_row['genre'] for genre_row in genre_rows]


        tags_rows = cursor.execute('''
            SELECT g.tag 
            FROM join_tags mg
            JOIN tags g ON mg.tag_id = g.id
            WHERE mg.items_appid = ?
        ''', (row_appid,)).fetchall()

        tags = [tag_row['tag'] for tag_row in tags_rows]   

        return genres, tags


    @classmethod
    def get_items(cls, ids: list = None):
        '''
        Retrieve items from the database.

        Parameters:
            ids (list): Optional list of app IDs to filter results. If None, fetches all.
        Returns:
            List of item records as dictionaries.
        '''

        conn = cls.db_connect()
        cursor = conn.cursor()

        items = []
        if not ids:
            rows = cursor.execute("SELECT * FROM items").fetchall()
            for row in rows:
                row_appid = row['appid']
                if row is None:
                    continue

                genres, tags = cls.get_categories(cursor, row_appid)
                row = dict(row)
                row.update({
                    'genres': genres,
                    'tags': tags
                })

                item = cls(**row)
                items.append(item)

        else:
            for id_ in ids:
                row = cursor.execute("SELECT * FROM items WHERE appid = ?", (id_,)).fetchone()
                if row is None:
                    continue

                row_appid = row['appid']

                genres, tags = cls.get_categories(cursor, row_appid)
                row = dict(row)
                row.update({
                    'genres': genres,
                    'tags': tags
                })
                
                item = cls(**row)
                items.append(item)
                
        conn.close()  
        return items


    def get_appids(self):
        '''
        Retrieve app IDs and their corresponding 'has_tags' values from the 'items' table.

        Returns:
            A list of dictionaries, each with:
                - 'appid' (int)
                - 'has_tags' (int)
        '''
        try:
            with self.db_connect() as conn:
                cursor = conn.cursor()
                rows = cursor.execute("SELECT appid, has_tags, has_genres, requested_details, last_updated FROM items").fetchall()
                return [{'appid': row[0], 'has_tags': row[1], 'has_genres': row[2], 'requested_details': row[3], 'last_updated': row[4]} for row in rows]
        except Exception as e:
            print(f"Error fetching appids: {e}")
            return []



    def check_and_insert_missing(self, ids: list) -> None:
        '''
        Check if app ids are already in Database, if not, request (via SteamSpy API) and insert to db id's categories and genres.

        Parameters:
            ids (list): List of IDs
        '''

        apps = self.get_appids()
        db_ids = []
        for id in apps:
            db_ids.append(id.get('appid'))

        not_found_ids = []
        for id_ in ids:
            if id_ not in db_ids:
                not_found_ids.append(id_)
        
        new_items = []
        if not_found_ids:
            print(f'Not found in localdb: {len(not_found_ids)} App IDs')
            # print(", ".join(str(x) for x in not_found_ids))
            for i, id_ in enumerate(not_found_ids):
                print(f'({i+1}/{len(not_found_ids)})', end=' ')
                data = SteamAPI().get_app_details(id_)
                new_items.append(data)
            
        self.insert_all(new_items)



    def update(self):
        '''
        Fetches the latest app data from SteamDB for Trending, Top Selling and Top Rated games.

        Steps:
            1. Retrieves a list of apps from SteamDB trending, topselling and toprated pages. (default top 250 apps).
            2. Identifies and Fetches tags and genres for each new app IDs not yet stored locally. (via SteamSpy API). (1s polling limit)
            3. Inserts or Updates App IDs into the database with SteamDB's price, rating, followers and trending position.

        This method is intended to keep the local database in sync with the latest app listings from SteamDB.
        '''

        steamdb = SteamDB()

        print(f'{datetime.datetime.now().replace(second=0, microsecond=0)} Initializing Update.')
        print('-'*40)
        # Get ~1000 apps from each SteamDB page (toprated, topselling, trending)
        try:
            print('Downloading top rated...', end=' ')
            toprated_data = steamdb.get_toprated(0, 'Game', None, 250)
            print('done.')
        except Exception as e:
            print(e)

        try:
            print('Downloading top selling...', end=' ')
            time.sleep(2)
            topselling_data = steamdb.get_topselling(0, 'Game', None, 250)
            print('done.')
        except Exception as e:
            print(e)

        try:
            print('Downloading trending...', end=' ')
            time.sleep(2.6)
            trending_data = steamdb.get_trending(0, 'Game', None, 250)
            print('done.') 
        except Exception as e:
            print(e)

        try:
            print('Downloading user tags...', end=' ')
            time.sleep(1.2)
            steamdb_tags = steamdb.get_tags()
            print('done.')
        except Exception as e:
            print(e)


        # Filter out SteamDB duplicates based on 'appid'
        combined_data = (toprated_data or []) + (topselling_data or []) + (trending_data or [])
        unique_data = {}
        for app in combined_data:
            appid = app['appid']
            if appid not in unique_data:
                unique_data[appid] = app
            else:
                # Merge: update only missing keys
                for key, value in app.items():
                    if key not in unique_data[appid] or not unique_data[appid][key]:
                        unique_data[appid][key] = value

        # Convert back to a list containing unique appids
        data = list(unique_data.values())

        # Compare which appids are New
        steamdb_ids = []
        for item in data:
            steamdb_ids.append(item.get('appid'))

        localdb = self.get_appids()
        local_ids = []

        # UPDATE LOGIC
        for i in localdb:
            i_has_tags = i.get('has_tags', 0)
            i_has_genres = i.get('has_genres', 0)
            already_requested = i.get('requested_details', 0)

            last_updated = i.get('last_updated', datetime.datetime.now())
            last_updated_date = datetime.datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S')
            current_date = datetime.datetime.now()
            # Calculate the date one month ago (approximately 30 days)
            one_month_ago = current_date - timedelta(days=30)

            # ADD TO THE "EXCLUDE" LIST, 1) IF item HAS tags AND genres AND was requested or 2) IF item HAS AT LEAST tags OR genres BUT was requested AND within a month
            if ((i_has_tags and i_has_genres) and already_requested) or ((i_has_tags or i_has_genres) and already_requested and last_updated_date > one_month_ago): 
                local_ids.append(i.get('appid'))
        # UPDATE LOGIC
        #   
        new_ids = set(steamdb_ids) - set(local_ids)

        # Check if there are New IDs
        steamapi = SteamAPI()
        if new_ids:
            items_to_insert = []
            for i, id_ in enumerate(new_ids):
                print(f'({i+1}/{len(new_ids)})', end=' ')
                data_details = steamapi.get_app_details(id_)

                for item in data:
                    if item.get('appid') == id_:
                        item.update(data_details)
                    items_to_insert.append(item)
        else:
            items_to_insert = data

        # Insert to DB
        print('\nUpdating database...')
        self.is_trending_reset() # reset trending, topselling and toprated position values before updating with new current ones from SteamDB
        self.insert_all(items_to_insert)
        # Inserts or Updates SteamDB Tags (label counts)
        self.insert_steamdbtags(steamdb_tags) 
        
        print(f'{datetime.datetime.now().replace(second=0, microsecond=0)} Update Complete.')
        print('-'*40)
        print('Info:')
        print('  New IDs:', len(new_ids))
        print('  Updated IDs:', len(steamdb_ids)-len(new_ids))
        print('  Updated Game-Tags:', len(steamdb_tags), end='\n\n\n')

    def is_trending_reset(self):
        '''
        Resets the 'is_trending', 'is_topselling', 'is_toprated' status for all items in the database.

        Returns:
            None
        '''

        conn = self.db_connect()
        cursor = conn.cursor()

        cursor.execute('''
                UPDATE items
                SET is_trending = 0,
                    is_topselling = 0,
                    is_toprated = 0''')
        conn.commit()
        conn.close()


    def __str__(self):
        lines = [f"Info:"]
        for key, value in self.__dict__.items():
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)



if __name__ == "__main__":
    pass