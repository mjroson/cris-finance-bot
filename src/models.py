from peewee import *
import datetime


db = SqliteDatabase('expense.db')


#(Pdb) message.from_user.values
#{'id': 157425944, 'is_bot': False, 'first_name': 'Matias', 'username': 'mroson', 'language_code': 'en'}

class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    external_id = CharField(unique=True)
    name = CharField()
    username = CharField()
    lang = CharField()
    extra = TextField()


class Chat(BaseModel):
    chat_id = CharField(unique=True)
    extra_info = TextField()


class Expense(BaseModel):
    user = ForeignKeyField(User, backref='tweets')
    description = TextField()
    created_date = DateTimeField(default=datetime.datetime.now)
    price = FloatField()
    categories = TextField()


db.connect()
db.create_tables([User, Expense, Chat])
