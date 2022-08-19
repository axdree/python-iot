<<<<<<< HEAD
import dash
from dash import dcc

from dash import html

from flask_login.utils import login_required
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output

import requests
import dash_bootstrap_components as dbc
from pandasql import sqldf


def return_dash_app(flaskapp):

    app1 = dash.Dash(
        __name__,
        server=flaskapp,
        url_base_pathname="/",
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )
    
    card_content1 = [
    dbc.CardHeader("Cylinder 1 Stocks"),
    dbc.CardBody(
        [
            html.H5("", className="card-title" , id = 'cyl1')
        ]
    ),
    ]
    
    card_content2 = [
    dbc.CardHeader("Cylinder 2 Stocks"),
    dbc.CardBody(
        [
            html.H5("", className="card-title" , id = 'cyl2')
        ]
    ),
    ]
    
    
    card_content3 = [
    dbc.CardHeader("Cylinder 3 Stocks"),
    dbc.CardBody(
        [
            html.H5("", className="card-title" , id = 'cyl3')
        ]
    ),
    ]
    
    card_content4 = [
    dbc.CardHeader("Cylinder 4 Stocks"),
    dbc.CardBody(
        [
            html.H5("", className="card-title" , id = 'cyl4')
        ]
    ),
    ]
    
    
    
    
    
    
    
    
    cards = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(dbc.Card(card_content1, color="primary", inverse=True)),
                dbc.Col(
                    dbc.Card(card_content2, color="primary", inverse=True)
                ),
                dbc.Col(dbc.Card(card_content3, color="primary", inverse=True)),
                dbc.Col(dbc.Card(card_content4, color="primary", inverse=True)),

            ],
            className="mb-4",
        )
    ]
    )

    app1.layout = html.Div(
        [
            dbc.NavbarSimple(
                children=[
                    dbc.NavItem(dbc.NavLink("Dashboard", href="http://localhost:1234")),
                    dbc.NavItem(
                        dbc.NavLink(
                            "Settings",
                            href="http://localhost:1234/settings",
                        )
                    ),
                    dbc.NavItem(
                        dbc.NavLink(
                            "Add Medication", href="http://localhost:1234/config"
                        )
                    )
                ],
                brand="Pill Dispenser",
                brand_href="#",
                color="light",
                dark=False
                #  style  = dict(color = 'black')
            ),
            cards , 
            # html.H2(
            #     children="Percentage of Doses Taken",
            #     style={
            #         "text-align": "center",
            #         "font-size": 30,
            #         "color": "black",
            #         "font-family": "'Arial",
            #     },
            # ),
            #  html.Div([], id = 'radio'),
            html.Div([dcc.Graph(id="pie")]),
            #  html.Div([dcc.Graph(id = 'highestbar', style = {'width' : '50%'})  , dcc.Graph(id = 'lowestbar' , style = {'width' : '50%'})]  , style = {'display' : 'flex'}),
            html.H2(
                id="h2text",
                children=f"",
                style={
                    "text-align": "center",
                    "font-size": 30,
                    "color": "black",
                    "font-family": "'Arial",
                },
            ),
            
            html.Div([dcc.Graph(id="line")] , style = {'margin-top' : 100}),
        ],
        style={"background": "white"},
    )

    @app1.callback(
        Output("pie", "figure"),
        Output("h2text", "children"),
        Output("line", "figure"),
        Output('cyl1' , 'children'),
        Output('cyl2' , 'children'),
        Output('cyl3'  ,'children'),
        Output('cyl4' , 'children'),
        Input("pie", "figure"),
    )
    def update_line_chart(va):
        #  print('inorout' , inorout)
        data = requests.get(
            f"https://api.thingspeak.com/channels/1830827/feeds.json?api_key=93KE283ET68L90M1&results=300"
        )

        frame = pd.DataFrame(data.json()["feeds"]).rename(
            columns=dict(field1="date", field2="time of day", field3="taken")
        )
        frame['takenstring'] = frame.taken.map({'0' : 'not taken' , '1' : 'taken'})
        print(frame)
        frame["total"] = 1
        fig = px.pie(
            frame,
            names="takenstring",
            values="total",
            facet_col="time of day",
        ).update_layout(title_text='Percentage of Doses Missed/Taken', title_x=0.5  , title = dict(font = dict(size = 35)))




        linefig = px.line(
            sqldf(
                " select [date] , cast( sum(taken) as float) / cast (sum(total) as float ) [proportion of doses taken] from frame group by  [date]"
            ).set_index('date').rolling(7).mean().reset_index() ,
            x="date",
            y="proportion of doses taken",
        ).update_layout(title_text='7 day average of Percentage of doses taken', title_x=0.5  , title = dict(font = dict(size = 35)))
    
        stocks = requests.get('http://localhost:1234/getstock' , auth = ('pythoniot' , 'P@$$w0rd'))
        stocks = stocks.json()
        
        
    
        
        return (
            fig,
            f"The Patient is most likely to miss doses for {frame.groupby('time of day')['taken'].sum().sort_values( ascending = False).index[0] }:00",
            linefig,
            str(stocks['cyl1']) + ' pill(s)', 
            str(stocks['cyl2'])+ ' pill(s)', 
            str(stocks['cyl3'])+ ' pill(s)', 
            str(stocks['cyl4'])+ ' pill(s)' 
        )
    
    for view_function in app1.server.view_functions:
        if view_function.startswith(app1.config.url_base_pathname):
            app1.server.view_functions[view_function] = login_required(
                app1.server.view_functions[view_function]
            )

    return app1

