from dash import Dash, html, dcc, dash_table, Input, Output, State
from utils import get_studies, process_studies
import pandas as pd

app = Dash()

app.layout = html.Div(
    [
        html.H1(
            "ClinDash",
            style={
                "textAlign": "left",
                "color": "#0074D9",
                "fontFamily": "Roboto",
                "marginBottom": "20px",
                "marginTop": "20px",
            },
        ),
        html.Div(
            [
                "Open-Source Clinical Trials Dashboard using available records from ",
                html.A(
                    "Clinicaltrials.gov",
                    href="https://clinicaltrials.gov/",
                    target="_blank",
                    style={
                        "color": "#2813E0",
                        "textDecoration": "underline",
                        "fontFamily": "Roboto",
                    },
                ),
            ],
            style={"textAlign": "center", "color": "#000000", "fontFamily": "Roboto"},
        ),
        dcc.Input(
            id="usr_searchexpr", placeholder="Search Expression", type="text", value=""
        ),
        html.Button("Go", id="submit-btn", n_clicks=0),
        html.Div(id="results_div"),
    ]
)


@app.callback(
    Output("results_div", "children"),
    Input("submit-btn", "n_clicks"),
    State("usr_searchexpr", "value"),
)
def run_search(n_clicks, search_expr):
    if n_clicks == 0:
        return ""
    if not search_expr:
        return "Please enter a search expression."

    api_result = get_studies(search_expr)
    df = process_studies(api_result, type="general")

    table = dash_table.DataTable(
        id="results_div",
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
    )

    return table


if __name__ == "__main__":
    app.run(debug=True)
