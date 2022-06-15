import ZODB
import persistent

db = ZODB.DB('database.fs')


class Meta(persistent.Persistent):
    version=1


class User(persistent.Persistent):

    def __init__(self, discord_account_id: int):
        self.id = discord_account_id


class Guild(persistent.Persistent):
    pass


class Token(persistent.Persistent):
    pass


class Member(persistent.Persistent):
    pass
