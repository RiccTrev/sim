from distutils.log import error
import pandas as pd
import numpy as np
import datetime
import sys
import json
import requests
import os.path
from pathlib import Path


'''Parametri economici per simulazione SSP'''
# INPUTS
# Parametri economici SSP
PUN = 0.1
# Pun viene usato per determinare nella simulazione SSP i seguenti parametri come specificato:
# prezzo_energia = 0.9*PUN
# corr_forfettario = 0.6*PUN

'''Incentivi e costo energia'''
# COSTO MEDIO ENERGIA (€/kWh):
costo_medio_energia = 0.25
# INCENTIVO ARERA (energia condivsa) - restituzione costi di sistema (€/kWh)
incentivo_arera = 0.009
# INCENTIVO MISE (energia condivisa) - incentivazione energia condivisa (€/kWh)
incentivo_mise = 0.110
# RITIRO DEDICATO - valorizzazione energia immessa (€/kWh)
ritiro_dedicato = 0.090

'''Valorizzazione idroelettrico'''
###IDRO
# Valorizzazione energia prodotta idro (€/kWh)
val_prod_idro = 0.090
# Euro ricevuti dalla condivisione per l'energia (€/kWh)
inc_cond_idro = 0.070

'''Taglia impianto'''
# Modalità di calcolo dimensionamento impianto
taglia_specifica = -1

'''Algoritmo ripartizione'''
# Percentuali di ripartizione
p_attribuibile = 0.9
p_costi_gestione = 1 - p_attribuibile
##
p_fissa = 0.2
p_variabile = 1 - p_fissa
##
p_consumatori = 0.6
p_immissione = 1 - p_consumatori
##
p_produttore = 0.98
p_prosumer = 1 - p_produttore

'''Conto economico'''
Architettura_CER = 400  # €/partecipante una tantum
Tempo_Ammortamento_Architettura = 4  # Anni
####################################################################
Commissione = 48  # €/partecipante all'anno
####################################################################
Ammortamento_Impianto_Fotovoltaico = 0.00  # % del costo dell'impianto
Tempo_Ammortamento_Fotovoltaico = 10  # Anni


# @title Funzioni
# Sample di chiamata di funzioni per riga: df_finale['Esempio'] = df.apply(funzioni.NomeFunzione, axis = 1))
def CalcolaAutoconsumo(df):
    if df['Immissione'] > 0:
        Autoconsumo = 0
        return Autoconsumo
    else:
        if df['Fascia 1'] + 0.2 * df['Fascia 2'] > df['Produzione Aggiuntiva'] or df['Fascia 1'] > df[
            'Produzione Aggiuntiva']:
            Autoconsumo = df['Produzione Aggiuntiva']
            return Autoconsumo
        if df['Fascia 2'] >= 1 / 3 * df['Fascia 1']:
            Autoconsumo = df['Fascia 1'] + 0.2 * df['Fascia 2']
            return Autoconsumo
        else:
            Autoconsumo = df['Fascia 1']
            return Autoconsumo


def CalcolaImmissione(df):
    if df['Immissione'] > 0:
        Immissione = df['Immissione']
        return Immissione;
    else:
        if df['Fascia 2'] >= 1 / 3 * df['Fascia 1']:
            Immissione = df['Produzione Aggiuntiva'] - df['Autoconsumo']
            if Immissione < 0:
                raise TypeError('Attenzione! Immissione < 0 per l\'utente ' + str(
                    df['Identificativo'] + 'nel mese di ' + str(df['Periodo'])))
            return Immissione
        else:
            Immissione = df['Produzione Aggiuntiva'] - df['Autoconsumo']
            if Immissione < 0:
                raise TypeError('Attenzione! Immissione < 0 per l\'utente ' + str(
                    df['Identificativo'] + ' nel mese di ' + str(df['Periodo'])))
            return Immissione


def VerificaIdro(df):
    if 'IDRO' in df['Identificativo']:
        return 1
    else:
        return 0


def StimaProduzione(df):
  mesi = {
      0:'gen',
      1:'feb',
      2:'mar',
      3:'apr',
      4:'mag',
      5:'giu',
      6:'lug',
      7:'ago',
      8:'set',
      9:'ott',
      10:'nov',
      11:'dic'
  }
  output = pd.DataFrame(columns = ['Identificativo', 'Lat', 'Long', 'Periodo', 'Produzione'])
  old_id = str(0)
  for index, row in df.iterrows():
    if row['Potenza Da Installare'] == 0:
      continue
    if old_id == row['Identificativo']:
      continue
    else:
      old_id = row['Identificativo']
    response = requests.get("https://re.jrc.ec.europa.eu/api/v5_1/PVcalc?lat="+str(row['Lat'])+"&lon="+str(row['Long'])+"&raddatabase=PVGIS-SARAH&peakpower="+str(row['Potenza Da Installare'])+"&pvtechchoice=crystSi&loss="+str(16)+"&optimalinclination=1&vertical_optimum=1&outputformat=json")
    todos = json.loads(response.text)
    #for i in range (1,13)
    for i in range (0,12):
      new_row = {}
      new_row = {'Identificativo': row['Identificativo'], 'Lat':row['Lat'], 'Long':row['Long'],'Periodo':mesi[i], 'Produzione': todos['outputs']['monthly']['fixed'][i]['E_m']}
      output = output.append(new_row, ignore_index=True)
  return output

def CalcolaBenficiSSP(df, prezzo_energia, corr_forfettario):
    temporary_ssp = df.groupby(by=["Identificativo"], as_index=True).agg(
        {"Produzione": "sum", "Autoconsumo": "sum", "Esportata": "sum", "Importata": "sum"}).rename(
        columns={"Produzione": "Totale Produzione", "Autoconsumo": "Totale Autoconsumo",
                 "Esportata": "Totale Esportata", "Importata": "Totale Importata"}).reset_index()
    temporary_ssp['Beneficio SSP'] = temporary_ssp.apply(
        lambda x: min(PUN * x['Totale Importata'], prezzo_energia * x['Totale Esportata']) + corr_forfettario * min(
            x['Totale Importata'], x['Totale Esportata']), axis=1)
    return temporary_ssp


def CalcolaIncentivo(df, QuotaProCapite, Quota_Consumatori, Quota_Produttore, Quota_Prosumer, Quota_Idro):
    # copy = df.copy()
    if (df['Categoria'] == 'Consumer'):
        # print('Nome: '+str(copy['Identificativo']) + ' Categoria: ' +str(copy['Categoria']))
        # print('quota pro capite: '+ str(QuotaProCapite))
        # print('percentuale condivisa: '+ str(Quota_Produttore*copy['Percentuale Condivisa']))
        # print('Totale suo incentivo: '+str( QuotaProCapite + Quota_Consumatori*copy['Percentuale Condivisa']))
        # print('##########################################################################################')
        return QuotaProCapite + Quota_Consumatori * df['Percentuale Condivisa']


    elif (df['Categoria'] == 'Prosumer'):
        # print('Nome: '+str(copy['Identificativo']) + ' Categoria: ' +str(copy['Categoria']))
        # print('quota pro capite: '+ str(QuotaProCapite))
        # print('percentuale immessa: '+ str(Quota_Produttore*copy['Percentuale Immessa']))
        # print('percentuale immessa prosumer: '+str(Quota_Prosumer*copy['Percentuale Immessa Prosumer']))
        # print('Totale suo incentivo: '+str( QuotaProCapite + Quota_Produttore*copy['Percentuale Immessa'] + Quota_Prosumer*copy['Percentuale Immessa Prosumer']))
        # print('##########################################################################################')
        return QuotaProCapite + Quota_Consumatori * df['Percentuale Condivisa'] + Quota_Produttore * df[
            'Percentuale Immessa'] + Quota_Prosumer * df['Percentuale Immessa Prosumer']


    elif (df['Categoria'] == 'Produttore'):
        # print('Nome: '+str(copy['Identificativo']) + ' Categoria: ' +str(copy['Categoria']))
        # print('quota pro capite: '+ str(QuotaProCapite))
        # print('percentuale immessa: '+ str(Quota_Produttore*copy['Percentuale Immessa']))
        # print('Totale suo incentivo: '+str( QuotaProCapite + Quota_Produttore*copy['Percentuale Immessa']))
        # print('##########################################################################################')                ''' INSERIMENTO IDROELETTRICO'''
        if df['Identificativo'] == 'Idroelettrico':
            return Quota_Idro  ########################!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!########## Definire a cosa attinge il produttore idroelettrico.
        return QuotaProCapite + Quota_Produttore * df['Percentuale Immessa']
    else:
        print('non rientra in nessuna categoria ERRORE')


def simula(file, costo_medio_energia, incentivo_arera, incentivo_mise, ritiro_dedicato, val_prod_idro, inc_cond_idro,
                                              p_attribuibile, p_fissa, p_consumatori, p_produttore, Architettura_CER,
                                              Tempo_Ammortamento_Architettura, Commissione, Ammortamento_Fotovoltaico,
                                              Tempo_Ammortamento_Fotovoltaico, PUN, taglia_specifica):
    p_costi_gestione = 1 - p_attribuibile
    p_variabile = 1 - p_fissa
    p_immissione = 1 - p_consumatori
    p_prosumer = 1 - p_produttore

    # Percorso del file revised creato con il notebook 'Preparazione'
    try:
        # fn = 'c:Users/trevi/Desktop/Test/Sample_DER.xlsx'
        xl = pd.ExcelFile(file)
        xl.sheet_names
    except:
        return error

        # Creo un dizionario di DataFrame.
    dfs = {sh: xl.parse(sh, header=0) for sh in xl.sheet_names}
    # Stampo le chiavi del dizionario (nomi dei workspace di excel)
    dfs.keys()
    dft = dfs['CER']
    df = dfs['CER']

    # Stima della produzione
    df_produzione = StimaProduzione(df.fillna(0))
    df = pd.merge(df, df_produzione, on=('Identificativo', 'Periodo'), how='left')
    df = df.drop(columns=['Lat_y', 'Long_y', 'Lat_x', 'Long_x'])
    df = df.rename(columns={'Produzione': 'Produzione Aggiuntiva'})
    df = df.fillna(0)
    # Calcolo autoconsumo ed immissione per gli utenti CONSUMER. N.B. Non è possible calcolarlo per gli utenti prosumer poiché non abbiamo il consumo totale, ma solo il prelevamento dalla rete.
    df['Autoconsumo'] = df.apply(CalcolaAutoconsumo, axis=1)
    df['Immissione'] = df.apply(CalcolaImmissione, axis=1)

    # df = df.drop(columns=['Bolletta Annua'])

    '''STIMA FABBISOGNO, COSTI E DIMENSIONAMENTO PROD'''
    temporary = df.groupby(by=["Identificativo"], as_index=True).agg(
        {"Fascia 1": "sum", "Fascia 2": "sum", 'Immissione': 'sum', 'Autoconsumo': 'sum',
         'Produzione Aggiuntiva': 'sum'}).rename(
        columns={"Fascia 1": "Somma Fascia 1", "Fascia 2": "Somma Fascia 2", 'Immissione': 'Somma Immissione',
                 'Autoconsumo': 'Somma Autoconsumo',
                 'Produzione Aggiuntiva': 'Somma Produzione Aggiuntiva'}).reset_index()
    df = pd.merge(df, temporary, on=['Identificativo'], how="left")
    df = df.drop(columns=['Autoconsumo', 'Produzione Aggiuntiva'])
    df['Consumo Per Fotovoltaico'] = df.apply(
        lambda x: (x['Somma Fascia 1']) if (x['Somma Fascia 2'] < 0.5 * x['Somma Fascia 1']) else (
                    x['Somma Fascia 1'] * 12 / 10), axis=1)
    df['Consumo Per Fotovoltaico'] = df['Consumo Per Fotovoltaico'] - df['Somma Autoconsumo']
    # df['Produzione'] = df['Taglia Impianto'] * 1250
    df['Differenza'] = df.apply(lambda x: (1 / 3 * x['Somma Immissione'] - x['Consumo Per Fotovoltaico']) if (
                x['Identificativo'] == 'Idroelettrico') else (x['Somma Immissione'] - x['Consumo Per Fotovoltaico']),
                                axis=1)  # Questo è quanto prelevo/immetto al netto della produzione dell'impianto preesistente
    # df['Differenza'] = df.apply(lambda x: df['Somma Immissione'] - df['Consumo Per Fotovoltaico'] # Questo è quanto prelevo/immetto al netto della produzione dell'impianto preesistente

    df["Taglia Impianto Potenziale"] = df.apply(
        lambda x: (abs(x["Differenza"]) / 1250) if (x["Differenza"] < 0) else (-x['Differenza'] / 1250), axis=1)
    df['Costo Impianto Potenziale'] = df.apply(
        lambda x: (x['Taglia Impianto Potenziale'] * 1200) if (x["Differenza"] < 0) else (0), axis=1)
    df['Costo Potenza da Installare'] = df.apply(
        lambda x: (x['Potenza Da Installare'] * 1200) if (x["Potenza Da Installare"] > 0) else (0), axis=1)
    df['Consumo Totale Fasce'] = (df['Fascia 1'] + df['Fascia 2'] + df['Fascia 3'])

    ''''''

    '''CALCOLI STIMA SCAMBIO SUL POSTO'''
    # DataFrame per lo scambio sul posto
    df_ssp = dfs['SSP']

    prezzo_energia = 0.9 * PUN
    corr_forfettario = 0.6 * PUN
    # Input
    if df_ssp.empty:
        print('Non sono stati istanziati utenti con scambio sul posto')
    else:
        print('Sono stati istanziati utenti con scambio sul posto')
        df_ssp = CalcolaBenficiSSP(df_ssp, prezzo_energia, corr_forfettario)

    # Inserisco consumo totale
    temporary2 = df.groupby(by=["Identificativo"], as_index=True).agg({"Consumo Totale Fasce": "sum"}).rename(
        columns={"Consumo Totale Fasce": "Consumo Totale Annuo"}).reset_index()
    df = pd.merge(df, temporary2, on=['Identificativo'], how="left")
    # Inserisco costo bolletta totale
    temporary3 = df.groupby(by=["Identificativo"], as_index=True).agg({"Bolletta Mensile": "sum"}).rename(
        columns={"Bolletta Mensile": "Costo Bolletta"}).reset_index()
    df = pd.merge(df, temporary3, on=['Identificativo'], how="left")

    # Riduco a base annua
    df_finale = df.groupby('Identificativo').mean().drop(
        columns=['Fascia 1', 'Fascia 2', 'Fascia 3', 'Consumo Totale Fasce', 'Bolletta Mensile',
                 'Immissione']).reset_index()
    df_finale = df_finale.drop(columns=['Consumo Totale Annuo'])

    # Identifico conc he taglia di impianto lavorare (se specificata o meno)
    if taglia_specifica == 0:
        df_finale['Taglia Impianto Potenziale'] = 0
        df_finale['Costo Impianto Potenziale'] = 0
        produttore = {'Identificativo': 'Produttore', 'Taglia Impianto': taglia_specifica, 'Somma Fascia 1': 0,
                      'Consumo Per Fotovoltaico': 0, 'Somma Immissione': taglia_specifica * 1250, 'Costo Bolletta': 0,
                      'Differenza': taglia_specifica * 1250, 'Taglia Impianto Potenziale': taglia_specifica,
                      'Costo Impianto Potenziale': taglia_specifica * 1200, 'Percentuale Condivisa': 0}
        df_finale = df_finale.append(produttore, ignore_index=True)
    elif taglia_specifica == -1:
        produttore = {'Identificativo': 'Produttore', 'Taglia Impianto': df_finale['Taglia Impianto Potenziale'].sum(),
                      'Somma Fascia 1': 0, 'Consumo Per Fotovoltaico': 0,
                      'Somma Immissione': df_finale['Taglia Impianto Potenziale'].sum() * 1250, 'Costo Bolletta': 0,
                      'Differenza': df_finale['Taglia Impianto Potenziale'].sum() * 1250,
                      'Taglia Impianto Potenziale': df_finale['Taglia Impianto Potenziale'].sum(),
                      'Costo Impianto Potenziale': df_finale['Taglia Impianto Potenziale'].sum() * 1200,
                      'Percentuale Condivisa': 0}
        df_finale = df_finale.append(produttore, ignore_index=True)
    elif taglia_specifica == 0:
        df_finale['Taglia Impianto Potenziale'] = 0
        df_finale['Costo Impianto Potenziale'] = 0

    # Calcolo energia condivisa
    if taglia_specifica == 0:
        print('non ho specificato la taglia')
        negativi = abs(df_finale[df_finale['Differenza'] < 0]['Differenza'].sum())  # contributi in prelievo
        positivi = df_finale['Somma Immissione'].sum()
        condivisa = min(negativi, positivi)
        print('positivi vale:' + str(positivi))
        print('negativi vale: ' + str(negativi))

    else:
        print('ho specificato la taglia')
        negativi = abs(df_finale[df_finale['Differenza'] < 0]['Differenza'].sum())  # contributi in prelievo
        positivi = df_finale[(df_finale['Identificativo'] != 'Produttore') & (df_finale['Differenza'] > 0)][
                       'Differenza'].sum() + df_finale[df_finale['Identificativo'] == 'Produttore'][
                       'Differenza'].sum()  # contributi in immissione
        condivisa = min(negativi, positivi)
        print('positivi vale:' + str(positivi))
        print('negativi vale: ' + str(negativi))

    # Categorizzazione degli utenti
    df_finale['Categoria'] = df_finale.apply(lambda x: ('Consumer') if (x["Somma Immissione"] == 0) else (
        'Prosumer' if (x['Somma Immissione'] != 0 and x['Consumo Per Fotovoltaico'] != 0) else 'Produttore'), axis=1)
    numero_produttori = len(df_finale[df_finale['Categoria'] == 'Produttore'])
    numero_prosumer = len(df_finale[df_finale['Categoria'] == 'Prosumer'])
    numero_partecipanti = df_finale['Identificativo'].count() - len(df_finale[df_finale[
                                                                                  'Identificativo'] == 'Idroelettrico'])  # Partecipanti sono quelli che partecipano anche ai costi, l'idroelettrico non partecipa ai costi
    numero_membri = df_finale['Identificativo'].count()  # Membri sono tutti quelli che afferiscono alla CER
    numero_consumer = numero_partecipanti - numero_prosumer - numero_produttori

    # Calcolo parametri per la redistribuzione di costi ed incentivo
    tot_prelievo = abs(df_finale[df_finale['Differenza'] < 0]['Differenza'].sum())
    df_finale['Percentuale Condivisa'] = df_finale.apply(
        lambda x: (abs(x['Differenza']) / tot_prelievo) if (x["Differenza"] < 0) else (0), axis=1)

    tot_immessa = df_finale[(df_finale['Identificativo'] != 'Idroelettrico') & (df_finale['Somma Immissione'] > 0)][
        'Somma Immissione'].sum()  # + df_finale[(df_finale['Differenza']>0) & (df_finale['Categoria'] != 'Produttore')]['Differenza'].sum()  #Immetto ciò che imposto nell'excel + eventule surplus della produzione nel momento in cui ho differenza > 0
    df_finale['Percentuale Immessa'] = df_finale.apply(lambda x: (abs(x['Somma Immissione']) / tot_immessa) if (
                x["Somma Immissione"] > 0 and x['Identificativo'] != 'Idroelettrico') else (0), axis=1)

    # Partecipazione in immissione prosumer
    tot_immessa_prosumer = df_finale[df_finale['Categoria'] == 'Prosumer']['Somma Immissione'].sum()
    df_finale['Percentuale Immessa Prosumer'] = df_finale.apply(
        lambda x: (x['Somma Immissione'] / tot_immessa_prosumer) if (x["Categoria"] == 'Prosumer') else (0), axis=1)

    df_finale = df_finale.fillna(0)

    # Calcolo totale incentivo energia condivisa & incentivo attribuibile
    Incentivo_Totale_Condivisione = condivisa * (incentivo_arera + incentivo_mise)
    Incentivo_Attribuibile = Incentivo_Totale_Condivisione
    # Calcolo quota idroelettrico
    if len(df_finale[df_finale[
                         'Identificativo'] == 'Idroelettrico']) > 0:  # Se esiste un produttore idroelettrico aggiorna la quota attribuibile
        Quota_Idro = inc_cond_idro * df_finale[df_finale['Identificativo'] == 'Idroelettrico'][
            'Somma Immissione'].sum()  ##1/3 dell'energia che immette viene remunerata a 70€/MWh
        if (Quota_Idro > Incentivo_Totale_Condivisione):
            print('ATTENZIONE LA QUOTA PER L\'IDROELETTRICO SUPERA L\'INCENTIVO TOTALE ALLA CONDIVISIONE')
        Incentivo_Attribuibile = Incentivo_Attribuibile - Quota_Idro
    else:
        Quota_Idro = 0

    '''ALGORITMO DI RIPARTIZIONE'''
    ######## ATTENZIONE: AD OGNI STEP LA SOMMA DEI DUE NUMERI DEVE ESSERE 1
    Incentivo_Attribuibile = p_attribuibile * (Incentivo_Totale_Condivisione - Quota_Idro)
    Incentivo_Costi_Gestione = p_costi_gestione * Incentivo_Totale_Condivisione
    #########
    Quota_Fissa = (
                p_fissa * Incentivo_Attribuibile)  # ATTENZIONE: QUESTA QUOTA E' DA DIVIDERE IN PARTI UGUALI FRA I MEMBRI DELLA COMUNITA'.
    Quota_Variabile = p_variabile * Incentivo_Attribuibile
    #########
    Quota_Consumatori = p_consumatori * Quota_Variabile
    Quota_Immissione = p_immissione * Quota_Variabile
    #########
    Quota_Produttore = p_produttore * Quota_Immissione
    Quota_Prosumer = p_prosumer * Quota_Immissione
    ######### GESTISCO ECCEZIONE IN CUI NON CI SONO PROSUMER PER NON PERDERE QUOTE DI INCENTIVO
    if (numero_prosumer == 0):
        Quota_Produttore = 1 * Quota_Immissione
        Quota_Prosumer = 0 * Quota_Immissione

    # Verifica della congruenza
    if Incentivo_Totale_Condivisione == Incentivo_Attribuibile + Incentivo_Costi_Gestione + Quota_Idro:
        print('C\'è congruenza')

    QuotaProCapite = Quota_Fissa / numero_partecipanti

    # Consumatori: Quota fissa + % Quota Consumatori
    # Produttore: Quota fissa + % Fissa su Quota Variabile

    QuotaProCapite = Quota_Fissa / numero_partecipanti  # La quota pro capite viene attribuita nella funzione Calcola incentivo.
    df_finale['Incentivo Condivisione'] = df_finale.apply(CalcolaIncentivo, axis=1,
                                                          args=[QuotaProCapite, Quota_Consumatori, Quota_Produttore,
                                                                Quota_Prosumer, Quota_Idro])

    df_finale['Ritiro Dedicato'] = df_finale.apply(lambda x: (x['Somma Immissione'] * ritiro_dedicato) if (
                x["Somma Immissione"] > 0 and x['Identificativo'] != 'Idroelettrico') else 0,
                                                   axis=1)  # N.B viene escluso il produttore idroelettrico
    df_finale['Vendita Energia Idroelettrico'] = df_finale.apply(
        lambda x: (x['Somma Immissione'] * val_prod_idro) if (x['Identificativo'] == 'Idroelettrico') else 0,
        axis=1)  # Calcolo vedita alla rete energia idroelettrico secondo parametro settato "val_prod_idro"
    Ritiro_Dedicato_Totale = df_finale['Ritiro Dedicato'].sum()
    df_finale['Incentivo Totale'] = df_finale['Incentivo Condivisione'] + df_finale['Ritiro Dedicato'] + df_finale[
        'Vendita Energia Idroelettrico']  # Calcolo incentivo totale singolo utente. N.B. quota pro capite attribuita in funzione calcola incentivo

    '''CONTO ECONOMICO'''
    d = {'Architettura': [Architettura_CER], 'Tempo_Ammortamento_Architettura': [Tempo_Ammortamento_Architettura],
         'Tempo_Ammortamento_Architettura': [Tempo_Ammortamento_Architettura], 'Commissione': [Commissione],
         'Ammortamento_Impianto_Fotovoltaico': [Ammortamento_Impianto_Fotovoltaico],
         'Tempo_Ammortamento_Fotovoltaico': [Tempo_Ammortamento_Fotovoltaico]}
    Parametri_Ammortamento = pd.DataFrame(data=d)
    Flussi_Di_Cassa_CER = (Incentivo_Totale_Condivisione + Ritiro_Dedicato_Totale)
    Costo_Totale_Impianti = df_finale[df_finale['Categoria'] == 'Produttore']['Costo Impianto Potenziale'].sum()
    # Attribuzione costi di funzionameto
    # Costi di Funzionamento = commissione + costo architettura + rimborso quota impianti a produttori
    Costi_Di_Funzionamento = (Commissione * numero_partecipanti) + ((Architettura_CER * numero_partecipanti) / Tempo_Ammortamento_Architettura)  # Sarebbero da considerare separati
    Costi_Di_Impianto = (Costo_Totale_Impianti * Ammortamento_Impianto_Fotovoltaico / Tempo_Ammortamento_Fotovoltaico)
    Costi_Di_Funzionamento_Produttore = ((Costi_Di_Funzionamento) / numero_partecipanti) * numero_produttori
    Costi_Di_Funzionamento_Consumer = ((Costi_Di_Funzionamento - Costi_Di_Funzionamento_Produttore))

    Trattenute_Incentivi = Incentivo_Costi_Gestione
    Margine_CER = Incentivo_Attribuibile - Costi_Di_Funzionamento - Costi_Di_Impianto
    Bilancio_Economico_CER = Flussi_Di_Cassa_CER - Costi_Di_Funzionamento - Costi_Di_Impianto - Trattenute_Incentivi

    '''TEMPO DI RIENTRO'''
    # Entrata annuale per il produttore fotovoltaico derivante dall'ammortamento della percentuale dell'impianto sui componenti della CE
    df_finale['Rata CER Impianto'] = df_finale.apply(lambda x: (
    (x['Costo Impianto Potenziale'] * (Ammortamento_Impianto_Fotovoltaico) / Tempo_Ammortamento_Fotovoltaico)) if (
                (x["Categoria"] == 'Produttore') and x['Identificativo'] != 'Idroelettrico') else (0), axis=1)
    # Ripartisco i costi di funzionamento della CE: Produttore paga i costi di funzionamento produttore, I consumer pagano i costi di funzionamento consumer, Idroelettrico non paga nulla
    df_finale['Costi Funzionamento CER'] = df_finale.apply(
        lambda x: (0) if (x['Identificativo'] == 'Idroelettrico') else (
            (Costi_Di_Funzionamento_Produttore / numero_produttori) if (x['Categoria'] == 'Produttore') else (
                        Costi_Di_Funzionamento_Consumer * (
                            x['Incentivo Condivisione'] / df_finale[df_finale['Identificativo'] != 'Produttore'][
                        'Incentivo Condivisione'].sum()))), axis=1)
    # Ripartisco i costi di Impianto fra i membri della CE (0 per produttore perché non può pagarsi il suo impianto e proporzionale all'incentivo di condivisione per gli altri membri)
    df_finale['Contributo Alla Produzione'] = df_finale.apply(
        lambda x: ((0)) if ((x["Categoria"] == 'Produttore')) else (Costi_Di_Impianto * (x['Incentivo Condivisione'] / (
            df_finale[df_finale['Identificativo'] != 'Produttore']['Incentivo Condivisione'].sum()))), axis=1)
    #
    df_finale['Rientro Investimento Impianto'] = df_finale.apply(lambda x: ((x['Costo Impianto Potenziale']) / (
                x['Incentivo Condivisione'] + x['Ritiro Dedicato'] + x['Rata CER Impianto'] - x[
            'Costi Funzionamento CER'])) if (
                (x["Categoria"] == 'Produttore') & (x['Identificativo'] != 'Idroelettrico')) else (0), axis=1)
    df_finale['Beneficio Economico Totale'] = df_finale.apply(
        lambda x: (x['Incentivo Totale'] + x['Rata CER Impianto'] - x['Costi Funzionamento CER']) if (
                    x["Categoria"] == 'Produttore') else (
            x['Vendita Energia Idroelettrico'] + x['Incentivo Condivisione'] if x[
                                                                                    'Identificativo'] == 'Idroelettrico' else (
                        x['Incentivo Totale'] - x['Costi Funzionamento CER'] - x['Contributo Alla Produzione'])),
        axis=1)

    # Calcolo proporzione pagamento incentivo condivisione per calcolare quanto uno paga il gestore della cer (% sulle trattenute incentivo condivisione)
    inc_cond_no_prod = df_finale[df_finale['Categoria'] != 'Produttore'][
        'Incentivo Condivisione'].sum()  # totale incentivo condivisione, produttore escluso
    df_finale['Percentuale Trattenuta Incentivo Condivisione'] = df_finale.apply(
        lambda x: ((x['Incentivo Condivisione'] / inc_cond_no_prod) if (x['Categoria'] != 'Produttore') else (0)),
        axis=1)  # percentuale incentivo condivisione del singolo utente sul totale
    df_finale['Trattenuta Incentivo Condivisione'] = df_finale.apply(
        lambda x: ((Trattenute_Incentivi * (x['Percentuale Trattenuta Incentivo Condivisione']))),
        axis=1)  # Calcolo quanto un utente deve fornire al produttore per il contributo alla produzione proporzionalmente all'incentivo condivisione percepito

    '''Rimanipolazione finale per renderlo presentabile'''
    # Cambio di segno la colonna contributo alla produzione
    df_finale = df_finale.fillna(0)
    df_finale['Contributo Alla Produzione'] = -df_finale['Contributo Alla Produzione']
    # Inserisco il valore di rata cer impianto di produttore nella colonna contributo alla produzione
    df_finale.loc[df_finale['Categoria'] == 'Produttore', 'Contributo Alla Produzione'] = \
    df_finale[df_finale['Categoria'] == 'Produttore']['Rata CER Impianto']
    # Drop della colonne non volute
    if (numero_produttori > 0):
        df_finale.drop(
            ['Rata CER Impianto', 'Somma Fascia 1', 'Somma Fascia 2', 'Taglia Impianto', 'Consumo Per Fotovoltaico'],
            axis=1, inplace=True)
    else:
        df_finale.drop(['Rata CER Impianto', 'Somma Fascia 1', 'Somma Fascia 2', 'Consumo Per Fotovoltaico'], axis=1,
                       inplace=True)

    # Rinomino "Differenza" in "Bilancio Energetico", Incentivo Totale in Entrate Totali e Trattentuta Incentivo Condivisione in Costi Gestione CER
    df_finale = df_finale.rename(columns={'Differenza': 'Bilancio Energetico', 'Incentivo Totale': 'Entrate Totali',
                                          'Trattenuta Incentivo Condivizione': 'Costi Gestione CER'})
    # df_finale.style.format(thousands = '.', precision = 0)
    # df_finale.style.format(thousands = ',', precision = 2)
    #print(df_finale)

    dict_summary = {
        "condivisa": [condivisa],
        "numero_produttori": [numero_produttori],
        "numero_prosumer": [numero_prosumer],
        "numero_partecipanti": [numero_partecipanti],
        "numero_membri": [numero_membri],
        "numero_consumer": [numero_consumer],
        'Incentivo_Totale_Condivisione': [Incentivo_Totale_Condivisione],
        'Incentivo_Attribuibile': [Incentivo_Attribuibile],
        "Incentivo_Costi_Gestione": [Incentivo_Costi_Gestione],
        "Quota_Fissa": [Quota_Fissa],
        "Quota_Variabile": [Quota_Variabile],
        "Quota_Consumatori": [Quota_Consumatori],
        "Quota_Immissione": [Quota_Immissione],
        "Quota_Produttore": [Quota_Produttore],
        "Quota_Prosumer": [Quota_Prosumer],
        "QuotaProCapite": [QuotaProCapite],
        "Flussi_Di_Cassa_CER": [Flussi_Di_Cassa_CER],
        "Costo_Totale_Impianti": [Costo_Totale_Impianti],
        "Costi_Di_Funzionamento": [Costi_Di_Funzionamento],
        "Costi_Di_Impianto": [Costi_Di_Impianto],
        "Costi_Di_Funzionamento_Produttore": [Costi_Di_Funzionamento_Produttore],
        "Costi_Di_Funzionamento_Consumer": [Costi_Di_Funzionamento_Consumer],
        "Trattenute_Incentivi": [Trattenute_Incentivi],
        "Margine_CER": [Margine_CER],
        "Bilancio_Economico_CER": [Bilancio_Economico_CER],
        "Quota_Idro": [Quota_Idro]
    }
    #df_summary = pd.DataFrame(list(my_dict.items()), columns=['column1', 'column2'])
    #print(dict_summary)
    df_summary = pd.DataFrame.from_dict(dict_summary)

    print('DF_SUMMARY: ')
    print(df_summary)
    return df_finale, df_ssp, df_summary

