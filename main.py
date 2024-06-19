from dash import Dash, html, dcc, Input, Output
import dash_cytoscape as cyto
import pandas as pd
import json


df = pd.read_csv("railway.csv")

json_file = "station_coords.json"
with open(json_file, 'r') as file:
    station_coords = json.load(file)

station_labels = {
    'London Paddington': {'label': 'London', 'text-valign': 'top', 'text-halign': 'right'},
    'Cardiff Central': {'label': 'Cardiff'},
    'Liverpool Lime Street': {'label': 'Liverpool', 'text-halign': 'left'},
    'York': {'label': 'York'},
    'Manchester Piccadilly': {'label': 'Manchester'},
    'Oxford': {'label': 'Oxford'},
    'Birmingham New Street': {'label': 'Birmingham', 'text-valign': 'bottom', 'text-halign': 'left'},
    'Reading': {'label': 'Reading', 'text-valign': 'bottom'},
    'Durham': {'label': 'Durham'},
    'Edinburgh Waverley': {'label': 'Edinburgh'}
}


app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H3('Most popular routes'),
    dcc.Dropdown(
        id='route-selection',
        options=[
            {'label': 'Top 10', 'value': 10},
            {'label': 'Top 30', 'value': 30},
            {'label': 'All', 'value': 'all'}
        ],
        value=10,
        clearable=False,
        style={'width': '50%'}
    ),
    html.Br(),
    html.Div(id='hoverNode'),
    html.Div(id='hoverEdge'),
    cyto.Cytoscape(
        id='cytoscape-simple-graph',
        style={'width': '100%', 'height': '70vh'},
        layout={'name': 'preset'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'width': 'data(width)',
                    'height': 'data(height)',
                    'background-color': '#0074D9',
                    'color': '#000',
                    'font-size': '16px',
                    'text-opacity': 0,
                    'shape': 'ellipse'
                }
            },
            {
                'selector': '.station',
                'style': {
                    'font-size': '16px',
                    'text-opacity': 1,
                }
            },
            *[
                {
                    'selector': f'.{station.lower().replace(" ", "_")}',
                    'style': {
                        'label': details['label'],
                        'text-halign': details.get('text-halign', 'center'),
                        'text-valign': details.get('text-valign', 'top'),
                    }
                } for station, details in station_labels.items()
            ],
            {
                'selector': '.top-route',
                'style': {
                    'line-color': '#FF4136',
                    'width': 'data(width)',
                    'target-arrow-color': '#FF4136',
                    'target-arrow-shape': 'triangle',
                    'arrow-scale': 1,
                    'curve-style': 'bezier'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'line-color': '#888',
                    'width': 'data(width)',
                    'curve-style': 'bezier'
                }
            }
        ],
        userZoomingEnabled=False,
        userPanningEnabled=True
    )
])

@app.callback(
    Output('cytoscape-simple-graph', 'elements'),
    Input('route-selection', 'value')
)
def update_elements(selected_value):
    if selected_value == 'all':
        top_routes = df.groupby(['Departure Station', 'Arrival Destination'])['Transaction ID'].count().reset_index(name='Tickets Sold').sort_values(by='Tickets Sold', ascending=False)
    else:
        top_routes = df.groupby(['Departure Station', 'Arrival Destination'])['Transaction ID'].count().reset_index(name='Tickets Sold').sort_values(by='Tickets Sold', ascending=False).head(selected_value)

    nodes = []
    scale = 150
    for station, coords in station_coords.items():
        node_class = 'station'
        if station in station_labels:
            node_class += ' ' + station.lower().replace(' ', '_')
        nodes.append({
            'data': {'id': station, 'label': station, 'width': 20, 'height': 20},
            'position': {'x': coords[1] * scale, 'y': -coords[0] * scale},
            'classes': node_class
        })

    edges = []
    for _, row in top_routes.iterrows():
        route = (row['Departure Station'], row['Arrival Destination'])
        edges.append({
            'data': {'source': route[0], 'target': route[1], 'label': f"{route[0]} --> {route[1]}", 'Tickets Sold': row['Tickets Sold'], 'width': 2},
            'classes': 'top-route'
        })

    return nodes + edges

@app.callback(
    Output('hoverNode', 'children'),
    Input('cytoscape-simple-graph', 'mouseoverNodeData')
)
def display_hover_node_data(data):
    if data:
        return "Station: %s" % data['label']

@app.callback(
    Output('hoverEdge', 'children'),
    Input('cytoscape-simple-graph', 'mouseoverEdgeData')
)
def display_hover_edge_data(data):
    if data:
        label = data['label']
        tickets_sold = data['Tickets Sold'] if 'Tickets Sold' in data else None
        if tickets_sold:
            return "Route: %s, Tickets Sold: %s" % (label, tickets_sold)
        else:
            return "Route: %s" % label

if __name__ == '__main__':
    app.run_server(debug=True)
