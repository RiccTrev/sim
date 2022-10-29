from sqlalchemy import ForeignKey

from functions import Tempo_Ammortamento_Fotovoltaico
from . import db #Import db dal file __init__
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(150))
    date = db.Column(db.DateTime(timezone=True), default = func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #Foreign Key N.B. IL NOME DELLA TABELLA è LOWER CASE. 

#Definisco la tabella degli user
class User(db.Model, UserMixin):
    #Definisco le colonne
    id = db.Column(db.Integer, primary_key=True) # id impostato come chiave primaria
    email = db.Column(db.String(150), unique = True) #Le email devono essere uniche
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note') #Informa della relazione con la tabella Note
    simulazioni = db.relationship('Simulazioni')

class Simulazioni(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    costo_medio_energia = db.Column(db.FLOAT)
    incentivo_arera = db.Column(db.FLOAT)
    incentivo_mise = db.Column(db.FLOAT)
    ritiro_dedicato = db.Column(db.FLOAT)
    val_prod_idro = db.Column(db.FLOAT)
    inc_cond_idro = db.Column(db.FLOAT)
    p_attribuibile = db.Column(db.FLOAT)
    p_fissa = db.Column(db.FLOAT)
    p_consumatori = db.Column(db.FLOAT)
    p_produttore = db.Column(db.FLOAT)
    Architettura_CER = db.Column(db.FLOAT)
    Tempo_Ammortamento_Architettura = db.Column(db.FLOAT)
    Commissione = db.Column(db.FLOAT)
    Ammortamento_Fotovoltaico = db.Column(db.FLOAT)
    Tempo_Ammortamento_Fotovoltaico = db.Column(db.FLOAT)
    PUN = db.Column(db.FLOAT)
    taglia_specifica = db.Column(db.FLOAT)
    df_ssp = db.Column(db.String(1000000000000000000))
    df_cer = db.Column(db.String(1000000000000000000))
    date = db.Column(db.DateTime(timezone=True), default = func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #Foreign Key N.B. IL NOME DELLA TABELLA è LOWER CASE. 