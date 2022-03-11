# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
from time import time


class Database(object):
    dir_path = os.path.dirname(os.path.abspath(__file__))

    _instance = None
    _initialized = False
    _banned_users = set()

    def __new__(cls):
        if not Database._instance:
            Database._instance = super(Database, cls).__new__(cls)
        return Database._instance

    def __init__(self):
        if self._initialized:
            return

        database_path = os.path.join(self.dir_path, "users.db")
        self.logger = logging.getLogger(__name__)

        if not os.path.exists(database_path):
            self.logger.debug("File '{}' does not exist! Trying to create one.".format(database_path))
        try:
            self.create_database(database_path)
        except Exception:
            self.logger.error("An error has occurred while creating the database!")

        self.connection = sqlite3.connect(database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
        self.cursor = self.connection.cursor()


        self._initialized = True

    @staticmethod
    def create_database(database_path):
        """
        Create database file and add admin and users table to the database
        :param database_path:
        :return:
        """
        open(database_path, 'a').close()

        connection = sqlite3.connect(database_path)
        connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS 'users'"
                       "('tweet_id' INTEGER NOT NULL,"
                       "'retweet_id' INTEGER NOT NULL,"
                       "'payment_hash' TEXT,"
                       "'payment_request' TEXT,"
                       "'checking_id' TEXT,"
                       "'amount' INTEGER,"
                       "'ispaid' BOOLEAN DEFAULT 0 NOT NULL,"
                       "'date' INTEGER,"
                       "'unretweet' BOOLEAN DEFAULT 0 NOT NULL,"
                       "PRIMARY KEY('tweet_id'));")
        connection.commit()
        connection.close()

    def load_banned_users(self):
        """Loads all banned users from the database into a list"""
        self.cursor.execute("SELECT user_id FROM users WHERE banned=1;")
        result = self.cursor.fetchall()

        if not result:
            return

        for row in result:
            print(int(row["user_id"]))
            self._banned_users.add(int(row["user_id"]))

    def get_banned_users(self):
        """Returns a list of all banned user_ids"""
        return self._banned_users

    def get_user(self, user_id):
        self.cursor.execute("SELECT user_id, first_name, last_name, username, games_played, games_won, games_tie, last_played, banned"
                            " FROM users WHERE user_id=?;", [str(user_id)])

        result = self.cursor.fetchone()
        if not result or len(result) == 0:
            return None
        return result

    def is_user_banned(self, user_id):
        """Checks if a user was banned by the admin of the bot from using it"""
        # user = self.get_user(user_id)
        # return user is not None and user[8] == 1
        return int(user_id) in self._banned_users

    def ban_user(self, user_id):
        """Bans a user from using a the bot"""
        self.cursor.execute("UPDATE users SET banned=1 WHERE user_id=?;", [str(user_id)])
        self.connection.commit()
        self._banned_users.add(int(user_id))

    def unban_user(self, user_id):
        """Unbans a user from using a the bot"""
        self.cursor.execute("UPDATE users SET banned=0 WHERE user_id=?;", [str(user_id)])
        self.connection.commit()
        self._banned_users.remove(int(user_id))

    def get_recent_players(self):
        one_day_in_secs = 60 * 60 * 24
        current_time = int(time())
        self.cursor.execute("SELECT user_id FROM users WHERE last_played>=?;", [current_time - one_day_in_secs])

        return self.cursor.fetchall()

    def get_played_games(self, user_id):
        self.cursor.execute("SELECT games_played FROM users WHERE user_id=?;", [str(user_id)])

        result = self.cursor.fetchone()

        if not result:
            return 0

        if len(result) > 0:
            return int(result[0])
        else:
            return 0

    def get_all_users(self):
        self.cursor.execute("SELECT rowid, * FROM users;")
        return self.cursor.fetchall()

    def add_user(self, tweet_id, retweet_id, payment_hash, payment_request, checking_id, amount, ispaid, date, unretweet):
        if self.is_user_saved(tweet_id):
            return
        self._add_user(tweet_id, retweet_id, payment_hash, payment_request, checking_id, amount, ispaid, date, unretweet)
        
    def _add_user(self, tweet_id, retweet_id, payment_hash, payment_request, checking_id, amount, ispaid, date, unretweet):
        try:
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", [str(tweet_id), retweet_id, payment_hash, payment_request, checking_id, amount, ispaid, date, unretweet])
            self.connection.commit()
        except sqlite3.IntegrityError:
            return
    def delete_row(self, rowid):
        self.cursor.execute("DELETE FROM users WHERE rowid = ?;", [rowid])
        self.connection.commit()

    def set_ispaid(self, ispaid, rowid):
        self.cursor.execute("UPDATE users SET ispaid = ? WHERE rowid = ?;", [ispaid, str(rowid)])
        self.connection.commit()

    def set_unretweet(self, unretweet, rowid):
        self.cursor.execute("UPDATE users SET unretweet = ? WHERE rowid = ?;", [unretweet, str(rowid)])
        self.connection.commit()

    def update_user_data(self, tweet_id, payment_hash, payment_request, checking_id, amount, ispaid, date, unretweet):
        self.cursor.execute("UPDATE users SET payment_hash=?, payment_request=?, checking_id=?, amount=?, ispaid=?, date=?, unretweet=? WHERE tweet_id=?;", [payment_hash, payment_request, checking_id, amount, ispaid, date, unretweet, str(tweet_id)])
        self.connection.commit()
    def getamount(self, tweet_id):
        self.cursor.execute("SELECT amount FROM users WHERE tweet_id=?;", [str(tweet_id)])
        result = self.cursor.fetchone()
        return result[0]
    def get_unretweet(self, tweet_id):
        self.cursor.execute("SELECT unretweet FROM users WHERE tweet_id=?;", [str(tweet_id)])
        result = self.cursor.fetchone()
        return result[0]
    def get_total_amount(self, retweet_id):
        self.cursor.execute("SELECT amount FROM users WHERE retweet_id=? AND unretweet=0 ;", [str(retweet_id)])
        results = self.cursor.fetchall()
        s=0
        for result in results:
            s=s+result[0]
        return s




    def set_games_won(self, games_won, user_id):
        self.cursor.execute("UPDATE users SET games_won = ? WHERE user_id = ?;", [games_won, str(user_id)])
        self.connection.commit()

    def set_games_played(self, games_played, user_id):
        self.cursor.execute("UPDATE users SET games_played = ? WHERE user_id = ?;", [games_played, str(user_id)])
        self.connection.commit()

    def set_last_played(self, last_played, user_id):
        self.cursor.execute("UPDATE users SET last_played = ? WHERE user_id = ?;", [last_played, str(user_id)])
        self.connection.commit()

    def is_user_saved(self, tweet_id):
        self.cursor.execute("SELECT rowid, * FROM users WHERE tweet_id=?;", [str(tweet_id)])

        result = self.cursor.fetchall()
        if len(result) > 0:
            return True
        else:
            return False

    def user_data_changed(self, user_id, first_name, last_name, username):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?;", [str(user_id)])

        result = self.cursor.fetchone()

        # check if user is saved
        if result:
            if result[2] == first_name and result[3] == last_name and result[4] == username:
                return False
            return True
        else:
            return True


    def reset_stats(self, user_id):
        self.cursor.execute("UPDATE users SET games_played='0', games_won='0', games_tie='0', last_played='0' WHERE user_id=?;", [str(user_id)])
        self.connection.commit()

    def close_conn(self):
        self.connection.close()
    def setsession(self, user_id, session, phone):
        self.cursor.execute("SELECT sessions,phones FROM users WHERE user_id=?;", [str(user_id)])
        result = self.cursor.fetchone()
        sessions = result[0]+","+str(session)
        phones = result[1]+","+str(phone)
        self.cursor.execute("UPDATE users SET sessions = ?,phones = ? WHERE user_id = ?;", [str(sessions),str(phones),str(user_id)])
        self.connection.commit()
    def getsession(self, user_id):
        self.cursor.execute("SELECT sessions FROM users WHERE user_id=?;", [str(user_id)])
        result = self.cursor.fetchone()
        return result[0]
    def getallsessions(self):
        self.cursor.execute("SELECT user_id,sessions FROM users;")
        result = self.cursor.fetchall()
        return result
    def removesession(self,user_id, index):
        self.cursor.execute("SELECT sessions,phones FROM users WHERE user_id=?;", [str(user_id)])
        result = self.cursor.fetchone()
        sessions = result[0]
        phones = result[1]
        session = sessions.split(",")
        phone = phones.split(",")
        sessions = sessions.replace(","+session[index],"")
        phones = phones.replace(","+phone[index],"")
        self.cursor.execute("UPDATE users SET sessions = ?,phones = ? WHERE user_id = ?;", [str(sessions),str(phones),str(user_id)])
        self.connection.commit()
    def get_chat_id(self, username):
        self.cursor.execute("SELECT user_id FROM users WHERE username=?;", [str(username)])
        result = self.cursor.fetchone()
        try:
            return result[0]
        except:
            return 0  
    def phonecheck(self,phone):
        self.cursor.execute("SELECT user_id FROM users WHERE phones LIKE '%'||?||'%'",(phone,))
        result = self.cursor.fetchone()
        if result:
            return False
        else:
            return True