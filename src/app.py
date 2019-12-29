import datetime
from flask import Flask
from flask_peewee.db import Database
from flask_peewee.rest import RestAPI
from flask_peewee.admin import Admin
from flask_peewee.auth import Auth
from models import User, Expense, Chat, db
from flask_cors import CORS

# configure our database
DATABASE = {
    'name': 'expense.db',
    'engine': 'peewee.SqliteDatabase',
}
DEBUG = True
SECRET_KEY = 'ssshhhh'

app = Flask(__name__)
app.config.from_object(__name__)


# create an Auth object for use with our flask app and database wrapper
# auth = Auth(app, db)


admin = Admin(app, None)
admin.register(User)
admin.register(Expense)
admin.register(Chat)
admin.setup()

# create a RestAPI container
api = RestAPI(app)

# register the Note model
api.register(User)
api.register(Expense)
api.register(Chat)

api.setup()

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

if __name__ == '__main__':
    # User.create_table(fail_silently=True)
    # Chat.create_table(fail_silently=True)
    # Expense.create_table(fail_silently=True)
    
    #Expense.create_table(fail_silently=True)
    #User.create_table(fail_silently=True)
    app.run(host='0.0.0.0')
