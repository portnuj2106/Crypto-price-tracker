import os
from datetime import datetime

import sqlalchemy as db
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class UserDatabase:
    def __init__(self, url):
        self.engine = db.create_engine(url)
        self.connection = self.engine.connect()
        self.metadata = db.MetaData()
        self.users = db.Table("users", self.metadata,
                       db.Column('user_id', db.Integer, primary_key=True),
                             db.Column('user_name', db.TEXT),
                             db.Column('user_curs', db.TEXT),
                             )
        self.user_alerts = db.Table("user_alerts", self.metadata,
                                    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id'), primary_key=True),
                                    db.Column('currencies', db.TEXT),
                                    db.Column('threshold', db.Float),
                                    db.Column('alert_preference', db.TEXT),
                                    )
        self.alert_history = db.Table("alert_history", self.metadata,
                                      db.Column('user_id', db.Integer, db.ForeignKey('users.user_id')),
                                      db.Column('alert_text', db.TEXT),
                                      db.Column('alert_datetime', db.DateTime),
                                      )
        self.metadata.create_all(self.engine)

    # Related to alert history
    async def add_alert_history(self, user_id, alert_text):
        insert_statement = self.alert_history.insert().values(
            user_id=user_id,
            alert_text=alert_text,
            alert_datetime=datetime.now()
        )
        self.connection.execute(insert_statement)
        self.connection.commit()
        return True

    async def get_alert_history(self, user_id):
        select_statement = self.alert_history.select().where(self.alert_history.columns.user_id == user_id)
        result = self.connection.execute(select_statement)
        alert_history = []
        for row in result:
            alert_info = {
                'alert_text': row[1],
                'alert_datetime': row[2].strftime("%Y-%m-%d %H:%M:%S")
            }
            alert_history.append(alert_info)
        return alert_history

    # Related to adding user to database
    async def add_user(self, user_id, user_name):
        insert_statement = self.users.insert().values(user_id=user_id, user_name=user_name)
        self.connection.execute(insert_statement)
        self.connection.commit()

    async def user_exists(self, user_id):
        select_statement = self.users.select().where(self.users.columns.user_id == user_id)
        result = self.connection.execute(select_statement)
        return result.fetchone() is not None

    # Related to setting alerts
    async def add_or_update_user_alerts(self, user_id, currencies, threshold, alert_preference):
        # Check if the user exists
        if not await self.user_exists(user_id):
            return False  # User doesn't exist, return False or raise an exception

        # Check if alerts already exist for the user
        if self.user_alerts_exist(user_id):
            # If alerts exist, update them
            update_statement = self.user_alerts.update().where(self.user_alerts.columns.user_id == user_id).values(
                currencies=currencies,
                threshold=threshold,
                alert_preference=alert_preference
            )
            self.connection.execute(update_statement)
            self.connection.commit()
            return True  # Alert updated successfully
        else:
            # If alerts don't exist, add them
            insert_statement = self.user_alerts.insert().values(
                user_id=user_id,
                currencies=currencies,
                threshold=threshold,
                alert_preference=alert_preference
            )
            self.connection.execute(insert_statement)
            self.connection.commit()
            return True

    def user_alerts_exist(self, user_id):
        select_statement = self.user_alerts.select().where(self.user_alerts.columns.user_id == user_id)
        result = self.connection.execute(select_statement)
        return result.fetchone() is not None

    async def get_user_alerts(self, user_id):
        select_statement = self.user_alerts.select().where(self.user_alerts.columns.user_id == user_id)
        result = self.connection.execute(select_statement)
        user_alerts = {}
        for row in result:
            user_alerts['currencies'] = row[1]  # Access currencies using integer index (1)
            user_alerts['threshold'] = row[2]  # Access threshold using integer index (2)
            user_alerts['alert_preference'] = row[3]  # Access alert_preference using integer index (3)
        return user_alerts


database = UserDatabase(os.getenv('DB_URL'))