from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

#Istanzio db
db=SQLAlchemy()
DB_NAME = "database.db"

#Inizializzazione della app
def create_app(): 
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '123qweasdzxc' #Secret key della app
    #Configuro db
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    #Importo le view
    from .views import views
    from .auth import auth

    #registro le blueprint
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    #Controllo se esiste il db ed importo le tabelle
    from .models import User, Note, Simulazioni

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id): 
        return User.query.get(int(id))

    return app 

def create_database(app): 
    if not path.exists('website/' + DB_NAME): #N.B. Impostare il nome della cartella!
        with app.app_context():
            db.create_all()
        print('Created Database!')