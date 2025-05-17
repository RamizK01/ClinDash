from dash import Dash, html

app = Dash() 

app.layout = html.Div([
    html.H1("Hello Dash"),
    html.Div("Dash: A web application framework for Python."),
    html.Div("This is a simple Dash app.")])

if __name__ == '__main__':
    app.run(debug=True)