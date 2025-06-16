from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import plotly
import json
import os

app = Flask(__name__)

# Konfiguracja: klucze nazw i ścieżki do plików CSV
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
# Nazwy datasetów muszą odpowiadać kluczom sprawdzanym w kodzie
DATASETS = {
    'daily': os.path.join(DATA_DIR, 'daily_bikes.csv'),
    'weekday': os.path.join(DATA_DIR, 'weekday_bike.csv'),
    'monthly': os.path.join(DATA_DIR, 'month_bike.csv'),
}

# Wczytywanie wszystkich plików do słownika DataFrame
# Parsujemy pliki bez założenia kolumny Date; ważne, aby zawierały kolumnę 'Total'
def load_all_data(datasets_config):
    dfs = {}
    for name, path in datasets_config.items():
        if os.path.exists(path):
            df = pd.read_csv(path)
            # upewnij się, że kolumna 'Total' istnieje
            if 'Total' not in df.columns:
                print(f"Uwaga: w {path} brakuje kolumny 'Total'")
            dfs[name] = df
        else:
            print(f"Plik nie istnieje: {path}")
    return dfs

# Globalne wczytanie
dataframes = load_all_data(DATASETS)

@app.route('/', methods=['GET'])
def index():
    # Wybór datasetu z parametru GET
    selected = request.args.get('dataset') or next(iter(dataframes.keys()))

    average = 0
    max_count = 0

    fig = None
    if selected in dataframes:
        df = dataframes[selected].copy()
        # Sprawdź, czy kolumna 'Total' jest obecna
        if 'Total' in df.columns:
            # Reset indeksu dla osi X
            df = df.reset_index(drop=True)
            df['Index'] = df.index
            # Rysuj w zależności od klucza
            if selected == 'daily':
                average = int(df['Total'].mean())
                max_count = int(df['Total'].max())
                fig = px.line(df, x='Index', y='Total',
                              title='daily - Średnia dzienna liczba rowerzystów na moście',
                              labels={'Index': 'Dzień', 'Total': 'Średnia'})
            elif selected == 'weekday':
                average = int(df['Total'].mean())
                max_count = int(df['Total'].max())
                # Przyjmujemy, że df ma 7 wierszy dla dni tygodnia w kolejności poniedziałek=0...
                df = df.reset_index(drop=True)
                df['Index'] = df.index
                # Mapowanie indeksu na nazwy dni
                reorder = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                           4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
                df['DayName'] = df['Index'].map(reorder)
                fig = px.line(df, x='DayName', y='Total',
                              title='weekday - Średnia liczba rowerzystów na moście w poszczególne dni tygodnia',
                              labels={'DayName': 'Dzień tygodnia', 'Total': 'Średnia'})
            elif selected == 'monthly':
                average = int(df['Total'].mean())
                max_count = int(df['Total'].max())
                df = df.reset_index(drop=True)
                df['Index'] = df.index
                # Przyjmujemy 12 wierszy: miesiące
                reorder = {0: 'January', 1: 'February', 2: 'March', 3: 'April', 4: 'May',
                           5: 'June', 6: 'July', 7: 'August', 8: 'September', 9: 'October',
                           10: 'November', 11: 'December'}
                df['MonthName'] = df['Index'].map(reorder)
                fig = px.line(df, x='MonthName', y='Total',
                              title='monthly - Średnia liczba rowerzystów na moście w poszczególne miesiące',
                              labels={'MonthName': 'Miesiąc', 'Total': 'Średnia'})
            else:
                # Dla innych datasetów, wykres ogólny
                fig = px.line(df, x='Index', y='Total',
                              title=f'{selected} - wykres kolumny Total',
                              labels={'Index': 'Indeks wiersza', 'Total': 'Total'})
        else:
            fig = px.line(title=f'{selected}: brak kolumny Total w danych')
    else:
        fig = px.line(title='Nie znaleziono wybranego datasetu')

    plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('index.html', dataset_names=list(dataframes.keys()),
                           selected_dataset=selected,
                           plot_json=plot_json,
                           average=average,
                           max_count=max_count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)