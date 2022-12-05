import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def RipartizioneQuote(df_finale, df_summary):
    fig = make_subplots(
        rows=6, cols=3,
        specs=[[{"rowspan": 1, "colspan": 3}, None, None],
               [{"rowspan": 1, "colspan": 3}, None, None],
               [{"rowspan": 1, "colspan": 1}, {"rowspan": 1, "colspan": 2}, None],
               [{"rowspan": 1, "colspan": 1}, {"rowspan": 1, "colspan": 2}, None],
               [{"rowspan": 1, "colspan": 1}, {"rowspan": 1, "colspan": 2}, None],
               [{"rowspan": 1, "colspan": 1}, {"rowspan": 1, "colspan": 2}, None]],
        shared_yaxes=True)

    fig.add_trace(go.Bar(x=['Totale Ritiro Dedicato'], y=[df_finale['Ritiro Dedicato'].sum()],
                         marker_color=['blue'], text=[df_finale['Ritiro Dedicato'].sum().round(0)]),
                  1, 1)

    fig.add_trace(go.Bar(x=['Quota Idroelettrico'],
                         y=[df_finale[df_finale['Identificativo'] == 'Idroelettrico']['Entrate Totali'].sum()],
                         marker_color=['pink'], text=[
            df_finale[df_finale['Identificativo'] == 'Idroelettrico']['Entrate Totali'].sum().round(0)]),
                  2, 1)

    fig.add_trace(go.Bar(x=['Tot. Incentivo E. Condivisa'], y=[df_summary['Incentivo_Totale_Condivisione'][0]],
                         marker_color=['#00FF6F'], text=[df_summary['Incentivo_Totale_Condivisione'].round(0)]),
                  3, 1)
    fig.add_trace(
        go.Bar(x=['Costi di Gestione', 'Incentivo Attribuibile'],
               y=[df_summary['Incentivo_Costi_Gestione'][0], df_summary['Incentivo_Attribuibile'][0]],
               marker_color=['orange', 'red'],
               text=[df_summary['Incentivo_Costi_Gestione'][0].round(0),
                     df_summary['Incentivo_Attribuibile'][0].round(0)]),
        3, 2)

    fig.add_trace(go.Bar(x=['Incentivo Attribuibile'], y=[df_summary['Incentivo_Attribuibile'][0]],
                         marker_color=['red'], text=[df_summary['Incentivo_Attribuibile'][0].round(0)]),
                  4, 1)
    fig.add_trace(
        go.Bar(x=['Quota Fissa', 'Quota Variabile'], y=[df_summary['Quota_Fissa'][0], df_summary['Quota_Variabile'][0]],
               marker_color=['yellow', 'purple'],
               text=[df_summary['Quota_Fissa'][0].round(0), df_summary['Quota_Variabile'][0].round(0)]),
        4, 2)

    fig.add_trace(go.Bar(x=['Quota Variabile'], y=[df_summary['Quota_Variabile'][0]],
                         marker_color=['purple'], text=[df_summary['Quota_Variabile'][0].round(0)]),
                  5, 1)

    fig.add_trace(go.Bar(x=['Quota Consumatori', 'Quota Immissione'],
                         y=[df_summary['Quota_Consumatori'][0], df_summary['Quota_Immissione'][0]],
                         marker_color=['pink', '#4E8FFF'],
                         text=[df_summary['Quota_Consumatori'][0].round(0),
                               df_summary['Quota_Immissione'][0].round(0)]),
                  5, 2)

    fig.add_trace(go.Bar(x=['Quota Immissione'], y=[df_summary['Quota_Immissione'][0]],
                         marker_color=['#4E8FFF'], text=[df_summary['Quota_Immissione'][0].round(0)]),
                  6, 1)

    fig.add_trace(go.Bar(x=['Quota Produttore', 'Quota Prosumer'],
                         y=[df_summary['Quota_Produttore'][0], df_summary['Quota_Prosumer'][0]],
                         marker_color=['#FF5733', '#D58BB9'],
                         text=[df_summary['Quota_Produttore'][0].round(0), df_summary['Quota_Prosumer'][0].round(0)]),
                  6, 2)

    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'), showlegend=False)
    fig.update_layout(barmode='stack')
    fig.update_layout(height=900)
    fig.update_traces(texttemplate=format('%{value:,.0f}€'))
    fig.update_layout(
        title={
            'text': "Ripartizione Incentivo",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
        font=dict(
            # family="Courier New, monospace",
            size=18,
        ))

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


def BilancioEnergetico(df_finale):
    parziale = df_finale[df_finale['Identificativo'] != 'Produttore']
    fig = go.Figure()
    fig.update_layout(
        font=dict(
            # family="Courier New, monospace",
            size=18,
        ),
        title={
            'text': "Bilancio Energetico",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
        xaxis_tickfont_size=14,
        xaxis=dict(
            showgrid=True,
            zeroline=True,
            nticks=20,
            showline=True,
            title='',
            titlefont_size=16,
            tickfont_size=14,
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=True,
            nticks=20,
            showline=True,
            title='kWh',
            titlefont_size=16,
            tickfont_size=14,
        ),
        barmode='group',
        bargap=0.2,  # gap between bars of adjacent location coordinates.
        bargroupgap=0  # gap between bars of the same location coordinate.
    )
    fig.update_layout(height=900)

    fig.add_trace(go.Bar(x=parziale['Identificativo'], y=parziale['Bilancio Energetico'],
                         base=0,
                         marker_color='yellow',
                         name='Bilancio Energetico'
                         ))

    graphBilancioEnergetico = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphBilancioEnergetico


def ConfrontoCondivisioneRid(df_finale, df_summary):
    fig = go.Figure(data=[go.Pie(labels=['Incentivo<br>Condivisione', 'Ritiro Dedicato'],
                                 values=[df_summary['Incentivo_Totale_Condivisione'][0],
                                         df_finale['Ritiro Dedicato'].sum()])])

    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'), showlegend=True)
    fig.update_layout(height=650)
    fig.update_traces(texttemplate=format('%{value:,.0f}€'))
    fig.update_layout(
        title={
            'text': "% Inc. Cond. VS RID",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
        font=dict(
            size=18,
        ))

    graphConfrontoCondivisioneRid = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphConfrontoCondivisioneRid


def RipartizioneCondivisione(df_finale):
    parziale = df_finale[df_finale['Categoria'] != 'Produttore']
    fig = px.pie(parziale, values=parziale['Incentivo Condivisione'], names=parziale['Identificativo'],
                 color=parziale['Identificativo'])

    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'), showlegend=True)
    fig.update_layout(height=650)
    fig.update_traces(texttemplate=format('%{value:,.0f}€'))
    fig.update_layout(
        title={
            'text': "Ripartizione Incentivo Condivisione",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
        font=dict(
            size=18,
        ))
    graphRipartizioneCondivisione = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphRipartizioneCondivisione


def EntrateTotali(df_finale):
    parziale = df_finale[df_finale['Entrate Totali'] > 0]
    fig = px.pie(parziale, values=parziale['Entrate Totali'], names=parziale['Identificativo'],
                 color=parziale['Identificativo'])

    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'), showlegend=True)
    fig.update_layout(height=650)
    fig.update_traces(texttemplate=format('%{value:,.0f}€'))
    fig.update_layout(
        title={
            'text': "Entrate Totali",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
        font=dict(
            size=18,
        ))
    graphEntrateTotali = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphEntrateTotali


def ConfrontoBenefici(df_finale):
    fig = make_subplots(
        rows=5, cols=3,
        specs=[[{"rowspan": 1, "colspan": 3}, None, None],
               [{"rowspan": 1, "colspan": 3}, None, None],
               [{"rowspan": 1, "colspan": 3}, None, None],
               [{"rowspan": 1, "colspan": 3}, None, None],
               [{"rowspan": 1, "colspan": 3}, None, None]],
        subplot_titles=("Incentivo Condivisione €", 'Costi Annuali CER Partecipanti €', "Ritiro Dedicato €",
                        'Beneficio Economico Totale €', 'Incidenza Percentuale su Bolletta %'),
        shared_yaxes=True)

    parziale = df_finale[df_finale['Identificativo'] != 'Produttore']

    fig.add_trace(go.Bar(x=parziale['Identificativo'], y=parziale['Incentivo Condivisione'],
                         marker_color='blue', text=parziale['Incentivo Condivisione'].round(0)),
                  1, 1)

    fig.add_trace(go.Bar(x=df_finale['Identificativo'], y=df_finale['Costi Funzionamento CER'],
                         marker_color='purple', text=df_finale['Costi Funzionamento CER'].round(0)),
                  2, 1)

    fig.add_trace(go.Bar(x=df_finale['Identificativo'], y=df_finale['Ritiro Dedicato'],
                         marker_color='orange', text=df_finale['Ritiro Dedicato'].round(0)),
                  3, 1)
    fig.add_trace(go.Bar(x=parziale['Identificativo'], y=parziale['Beneficio Economico Totale'],
                         marker_color='cyan', text=parziale['Beneficio Economico Totale'].round(0)),
                  4, 1)

    fig.add_trace(go.Bar(x=df_finale[df_finale['Identificativo'] != 'Produttore']['Identificativo'],
                         y=((df_finale['Beneficio Economico Totale'] / df_finale['Costo Bolletta']) * 100),
                         marker_color='red',
                         text=((df_finale['Beneficio Economico Totale'] / df_finale['Costo Bolletta']) * 100).round(0)),
                  5, 1)

    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'), showlegend=False)
    fig.update_layout(barmode='stack')
    fig.update_layout(height=900)
    fig.update_traces(texttemplate=format('%{value:,.0f}'))

    graphConfrontoBenefici = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphConfrontoBenefici
