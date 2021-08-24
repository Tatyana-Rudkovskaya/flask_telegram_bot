# curl https://api.telegram.org/bot1886989245:'+os.environ.get("TELEGRAM_API_KEY")+'/getUpdates
# curl https://api.telegram.org/bot1886989245:'+os.environ.get("TELEGRAM_API_KEY")+'/deleteMessage -d chat_id=746265890 -d message_id=7
# curl -s -X POST https://api.telegram.org/bot1886989245:'+os.environ.get("TELEGRAM_API_KEY")+'/sendMessage -d text="Tatyana is the coolest" -d chat_id=746265890
# https://api.telegram.org/bot1886989245:'+os.environ.get("TELEGRAM_API_KEY")+'/getUpdates
#.open C:/Users/tarud/dev/flask_telegram_api/database.db


import os
import flask
import flask_sqlalchemy # helps us to easily interact with the database per Models
import flask_praetorian
import flask_cors
import threading
import requests

db = flask_sqlalchemy.SQLAlchemy()
guard = flask_praetorian.Praetorian()
cors = flask_cors.CORS()
#print("hello")

# A generic user model that might be used by an app powered by flask-praetorian
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    realname = db.Column(db.Text)
    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    status = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.Integer)

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id



# Initialize flask app for the example
app = flask.Flask(__name__, static_folder='../build', static_url_path=None)
app.debug = True
app.config['SECRET_KEY'] = 'top secret'
app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}

# Initialize the flask-praetorian instance for the app
guard.init_app(app, User)

# Initialize a local database for the example
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'database.db')}"
db.init_app(app)

# Initializes CORS so that the api_tool can talk to the example app
cors.init_app(app)

# Add users for the example - Seeding of database
with app.app_context():
    db.create_all()
    if db.session.query(User).filter_by(username='yasoob').count() < 1:
        db.session.add(User(
          username='yasoob',
          realname='Yosob Habun'
		))
    db.session.commit()
    if db.session.query(User).filter_by(username='alex').count() < 1:
        db.session.add(User(
          username='alex',
          realname='Alex Brandt'
		))
    db.session.commit()
    # if db.session.query(Message).filter_by(id=1).count() < 1:
    #     db.session.add(Message(
    #         text="Hey",
    #         status=0,
    #         user_id=2,             
    #         chat_id = 5624584
	# 	))
    # db.session.commit()
    # if db.session.query(Message).filter_by(id=2).count() < 1:
    #     db.session.add(Message(
    #         text="Bye",
    #         status=0,
    #         user_id=1,             
    #         chat_id = 5624584
	# 	))
    # db.session.commit()



# TODO DONE interval that checks the getUpdates endpoint of the telegram api  
def interval():
    threading.Timer(5.0, interval).start()
    r =requests.get('https://api.telegram.org/bot1886989245:'+os.environ.get("TELEGRAM_API_KEY")+'/getUpdates')
    jsonRespone = r.json()
    with app.app_context():
        # TODO check if we already processed the last message and save all the messsages in the database
        query = db.session.query(Message)   
        result = db.session.execute(query) 
        print(query.count(), len(jsonRespone['result']))
        if query.count() < len(jsonRespone['result']):
            # send ONE new message
            print('New messsage') 
            myobj = {'chat_id': '746265890', 'text': ''}
            message = jsonRespone['result'][-1]['message']['text']
            if message == "yes":
                myobj['text'] = 'Yeeeeahhhh'
            else:
                myobj['text'] = 'NOOOOOOO'
            # TODO write your buisness logic
            # TODO respond with a curl request to the telegram api which sends a message to the chat
            response = requests.post(
                'https://api.telegram.org/bot1886989245:'+os.environ.get("TELEGRAM_API_KEY")+'/sendMessage', data=myobj)      

        for eventuallyNewMessage in jsonRespone['result']:  
            result = db.session.execute(query)
            foundMessages = [x for x in result if x[0] == eventuallyNewMessage['message']['message_id']]
            if len(foundMessages) == 0:
                db.session.add(Message(
                    id=eventuallyNewMessage['message']['message_id'],
                    text=eventuallyNewMessage['message']['text'],
                    status=0,
                    user_id=eventuallyNewMessage['message']['from']['id'],             
                    chat_id = eventuallyNewMessage['message']['chat']['id']
                ))                
        db.session.commit()

interval()
# Run the example
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)