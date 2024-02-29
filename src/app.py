#Final APP for deployment
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objs as go
import dash_mantine_components as dmc

# Load the dataset
df = pd.read_csv('https://github.com/rmejia41/open_datasets/raw/main/chronicdiseases_ind.csv', low_memory=False)

# Selecting specific columns
selected_columns = ['YearEnd', 'LocationAbbr', 'LocationDesc', 'DataSource', 'Question', 'DataValueType', 'DataValue', 'Stratification1', 'StratificationCategoryID1']
dff = df[selected_columns]

# Transpose the dataset
dff_transposed = dff.pivot_table(
    index=['YearEnd', 'LocationAbbr', 'LocationDesc', 'DataSource', 'DataValueType', 'Stratification1', 'StratificationCategoryID1'],
    columns='Question',
    values='DataValue',
    aggfunc='first'
).reset_index()

# Sort the transposed dataset
dff_transposed_sorted = dff_transposed.sort_values(by=['YearEnd', 'LocationAbbr', 'LocationDesc'])

# Rename 'Stratification1' column to 'Demographic'
dff_transposed_sorted.rename(columns={'Stratification1': 'Demographic'}, inplace=True)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
server = app.server

# Prepare dropdown options
year_options = [{'label': 'No Selection', 'value': 'No Selection'}] + \
               [{'label': year, 'value': year} for year in dff_transposed_sorted['YearEnd'].unique()]
health_indicator_options = [{'label': 'No Selection', 'value': 'No Selection'}] + \
                           [{'label': indicator, 'value': indicator} for indicator in dff_transposed_sorted.columns[7:]]

# App layout
app.layout = dbc.Container([
    html.H1("U.S. Chronic Disease Indicators (CDI) Dashboard", className="text-center mb-3"),
    dbc.Row([
        dbc.Col([
            html.Label("Select Year:"),
            dcc.Dropdown(
                id='year_dropdown',
                options=year_options,
                value='No Selection',
                style={'width': '100%'}  # Ensures dropdown stretches to column width
            ),
        ], width=6, md=3),  # Adjust column width for different screen sizes
        dbc.Col([
            html.Label("Select Health Indicator:"),
            dcc.Dropdown(
                id='health_indicator_dropdown',
                options=health_indicator_options,
                value='No Selection',
                style={'width': '100%', 'minWidth': '900px'}  # Makes dropdown wider while ensuring it matches year dropdown alignment
            ),
        ], width=6, md=4),  # Increase md value to make the column wider on medium screens
    ]),
    dbc.Row([
        dbc.Col([
            dmc.Anchor(
                "CDC Source Link",
                href="https://data.cdc.gov/Chronic-Disease-Indicators/U-S-Chronic-Disease-Indicators-CDI-/g4ie-h725/about_data",
                className="mt-1",
                style={"display": "block"}
            )
        ], width=12),
    ], justify="start"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='us_map'), width=12)
    ], className="mt-1"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='indicator_chart'), width=12)
    ], className="mt-3"),
], fluid=True)

@app.callback(
    [Output('us_map', 'figure'),
     Output('indicator_chart', 'figure')],
    [Input('year_dropdown', 'value'),
     Input('health_indicator_dropdown', 'value')]
)
def update_output(selected_year, selected_health_indicator):
    if selected_year == 'No Selection' or selected_health_indicator == 'No Selection':
        empty_map = go.Figure()
        #empty_map.update_layout(title="Please select both a year and a health indicator", geo=dict(scope="usa", visible=False))
        # empty_chart = go.Figure()
        # empty_chart.update_layout(title="Please select both a year and a health indicator")
        return empty_map #, empty_chart

    filtered_df = dff_transposed_sorted[dff_transposed_sorted['YearEnd'] == selected_year] if selected_year != 'No Selection' else dff_transposed_sorted
    if selected_health_indicator != 'No Selection':
        # Convert selected health indicator to numeric and handle NaNs dynamically
        filtered_df[selected_health_indicator] = pd.to_numeric(filtered_df[selected_health_indicator], errors='coerce')
        filtered_df = filtered_df.dropna(subset=[selected_health_indicator])

    us_map = px.choropleth(
        filtered_df,
        locations='LocationAbbr',
        locationmode="USA-states",
        color=selected_health_indicator,
        color_continuous_scale=px.colors.sequential.Plasma,
        hover_name='LocationDesc',
        hover_data={'DataSource': True, 'DataValueType': True, 'Demographic': True},
        scope="usa"
    )

    indicator_chart = px.bar(
        filtered_df,
        x='Demographic',
        y=selected_health_indicator,
        labels={'Demographic': 'Demographic'}, #{'original var':'newname'}
        title=f"{selected_health_indicator} by Demographic"
    )
    indicator_chart.update_layout(
        font=dict(size=10),
        width=800,
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),

        yaxis=dict(title='', showticklabels=False)
    )

    return us_map, indicator_chart

if __name__ == '__main__':
    app.run_server(debug=False)


