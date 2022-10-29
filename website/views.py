import string
from flask import Blueprint, render_template, request, flash, jsonify, url_for, redirect
from flask_login import login_required, current_user, logout_user
from . import db
from .models import Note, Simulazioni
from .models import User
import json
import functions
import pandas as pd
import pathlib

#Definisco che questo file è un blueprint che contiene le url
views = Blueprint('views', __name__)

@views.route('/', methods = ["GET", "POST"]) #Definisco il nome della url. In questo caso viene mostrata la pagina alla url corrispondente a /
@login_required
def elenco_sim(): 
    if request.method =='POST': 
        note = request.form.get('note')
        if len(note) < 1:
            flash('Note is too short!', category='error')
        else: 
            new_note= Note(data = note, user_id = current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Simulazione eseguita con successo!', category='success')
    return render_template("elenco_sim.html", user = current_user)

@views.route('/delete-note', methods=["POST"])
def delete_note(): 
    note= json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note: 
        if note.user_id == current_user.id: 
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


@views.route('/delete-sim', methods=["POST"])
def delete_sim(): 
    sim= json.loads(request.data)
    simId = sim['simId']
    sim = Simulazioni.query.get(simId)
    if sim: 
        if sim.user_id == current_user.id: 
            db.session.delete(sim)
            db.session.commit()

    return jsonify({})


@views.route('/set_up', methods = ["GET", "POST"])
@login_required
def set_up():
    if request.method == 'POST':
        nome = request.form.get('nome')
        file = request.files.get('file')
        costo_medio_energia = float(request.form.get('costo_medio_energia'))
        incentivo_arera = float(request.form.get('incentivo_arera'))
        incentivo_mise = float(request.form.get('incentivo_mise'))
        ritiro_dedicato = float(request.form.get('ritiro_dedicato'))
        val_prod_idro = float(request.form.get('val_prod_idro'))
        inc_cond_idro = float(request.form.get('inc_cond_idro'))
        p_attribuibile = float(request.form.get('p_attribuibile'))
        p_fissa = float(request.form.get('p_fissa'))
        p_consumatori = float(request.form.get('p_consumatori'))
        p_produttore = float(request.form.get('p_produttore'))
        Architettura_CER = float(request.form.get('Architettura_CER'))
        Tempo_Ammortamento_Architettura = float(request.form.get('Tempo_Ammortamento_Architettura'))
        Commissione = float(request.form.get('Commissione'))
        Ammortamento_Fotovoltaico = float(request.form.get('Ammortamento_Fotovoltaico'))
        Tempo_Ammortamento_Fotovoltaico = float(request.form.get('Tempo_Ammortamento_Fotovoltaico'))
        PUN = float(request.form.get('PUN'))
        taglia_specifica = float(request.form.get('taglia_specifica'))
        #Verifica del file in input con corretta esec
        try: 
            df_cer, df_ssp  = functions.simula(file, costo_medio_energia, incentivo_arera, 
            incentivo_mise, ritiro_dedicato, val_prod_idro, inc_cond_idro, 
            p_attribuibile, p_fissa, p_consumatori, p_produttore, Architettura_CER, 
            Tempo_Ammortamento_Architettura, Commissione, Ammortamento_Fotovoltaico, 
            Tempo_Ammortamento_Fotovoltaico, PUN, taglia_specifica)
            #converto i df in json
            json_df_cer = df_cer.to_json(orient = 'columns')
            json_df_ssp = df_ssp.to_json(orient = "columns")

            #Salvo la simulazione nel database
            try: 
                new_sim= Simulazioni(nome = nome, 
                costo_medio_energia = float(costo_medio_energia), 
                incentivo_arera = float(incentivo_arera),
                incentivo_mise = float(incentivo_mise),
                ritiro_dedicato = float(ritiro_dedicato),
                val_prod_idro = float(val_prod_idro), 
                inc_cond_idro = float(inc_cond_idro),
                p_attribuibile = float(p_attribuibile),
                p_fissa = float(p_fissa),
                p_consumatori = float(p_consumatori),
                p_produttore = float(p_produttore),
                Architettura_CER = float(Architettura_CER),
                Tempo_Ammortamento_Architettura = float(Tempo_Ammortamento_Architettura),
                Commissione =float(Commissione),
                Ammortamento_Fotovoltaico = float(Ammortamento_Fotovoltaico),
                Tempo_Ammortamento_Fotovoltaico =float(Tempo_Ammortamento_Fotovoltaico),
                PUN = float(PUN),
                taglia_specifica = float(taglia_specifica),
                df_cer = json_df_cer, 
                df_ssp = json_df_ssp, 

                user_id = current_user.id)
                #new_sim= Simulazioni(nome = nome, df_cer = json_df_cer, df_ssp = json_df_ssp, user_id = current_user.id)

                db.session.add(new_sim)
                db.session.commit()
                return render_template('result.html',  user = current_user, df_cer = df_cer, df_ssp = df_ssp, sim = new_sim)

            except: 
                flash('Impossibile salvare la simulazione. Controllare parametri in input', category='error')
        except: 
            flash('Problema con il file in input', category='error')

        
    return render_template("set_up.html", user = current_user)


@views.route('/dettagli_sim/<id_sim>', methods = ["GET", "POST"])
@login_required
def dettagli_sim(id_sim):
    #Query sul database per vedere se esiste
    sim = Simulazioni.query.filter_by(id=id_sim).first()
    df_cer = pd.read_json(sim.df_cer)
    df_ssp = pd.read_json(sim.df_ssp)
    return render_template("dettagli_sim.html", user = current_user, df_cer = df_cer, df_ssp = df_ssp, sim = sim)