from flask import Blueprint, render_template, request, flash, redirect, url_for
import pandas as pd
from .models import User
#Moduli per l'hash di password
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

#Definisco che questo file è un blueprint che contiene le url
auth = Blueprint('auth', __name__)

@auth.route('/login', methods =['GET', 'POST'])
def login(): 
    if request.method =='POST': 
        email = request.form.get('email')
        password = request.form.get('password')
        #Query sul database per vedere se esiste
        user = User.query.filter_by(email=email).first()
        if user: 
            if check_password_hash(user.password, password): #Confronta gli hash
                flash('Accesso effettuato!', category = 'success')
                login_user(user, remember = True)
                return redirect(url_for('views.elenco_sim'))
            else: 
                flash('Password incorretta!', category = 'error')
        else: 
            flash('Email non esistente!', category = 'error')

    return render_template("login.html", user = current_user)


@auth.route('/logout')
@login_required
def logout(): 
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods =['GET', 'POST'])
def sign_up(): 
    #Comportamento nel caso di POST request
    if request.method == 'POST': 
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        #Verifico se la mail è già registrata
        user = User.query.filter_by(email=email).first()
        if user: 
            flash('Email già registrata', category = 'error')
        #Controllo dei parametri in input
        elif len(email) < 4: 
            flash('Email deve essere contenere più di 3 caratteri', category='error')
        elif len(first_name) < 2: 
            flash('Nome deve essere contenere più di un carattere', category='error')
        elif password1 != password2: 
            flash('Password non corrispondenti', category='error')
        elif len(password1) < 7: 
            flash('Password deve contenere più di 7 caratteri', category='error')
        else: 
            #add user to db
            new_user = User(email=email, first_name=first_name, password = generate_password_hash(password1, method ="sha256"))
            db.session.add(new_user)
            db.session.commit()
            #Faccio il login dell'utente
            login_user(new_user, remember=True)
            flash('Account creato!', category='success')
            return redirect(url_for('views.elenco_sim'))

    return render_template("sign_up.html", user = current_user)