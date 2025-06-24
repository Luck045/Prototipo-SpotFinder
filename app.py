from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)

# Trie para indexação
class TrieNode:
    def __init__(self): 
        self.filho = {} #Dicionario que manda cada caractere para um nó filho
        self.IDs_musicas = set() #IDs de musicas que têm prefixo em comum e passam por esse nó
        self.finalizado = False #Nó que indica se uma palavra termina aqui

class Trie:
    def __init__(self):
        self.raiz = TrieNode()

    def insert(self, palavra, ID_musica):
        node = self.raiz
        for char in palavra:
            if char not in node.filho:
                node.filho[char] = TrieNode()
            node = node.filho[char]
            node.IDs_musicas.add(ID_musica)
        node.finalizado = True

    def busca_prefixo(self, prefix):
        node = self.raiz
        for char in prefix:
            if char not in node.filho:
                return set()
            node = node.filho[char]
        return node.IDs_musicas

# Classe Musica
class Musica:
    def __init__(self, ID_musica, title, artist, year, style, instruments, singer_gender):
        #Atributos da música
        self.ID_musica = ID_musica
        self.title = title.lower()
        self.artist = artist.lower()
        self.year = str(year)
        self.style = style.lower()
        self.instruments = [i.lower().strip() for i in instruments.split(',')] if isinstance(instruments, str) else []
        self.singer_gender = singer_gender.lower()

        #Cópia do valor original para não aparecer minusculo
        self.title_original = title
        self.artist_original = artist
        self.style_original = style
        self.instruments_original = instruments
        self.singer_gender_original = singer_gender

    #Dicionario para o json
    def to_dict(self):
        return {
            'ID_musica': self.ID_musica,
            'title': self.title_original,
            'artist': self.artist_original,
            'year': self.year,
            'style': self.style_original,
            'instruments': self.instruments_original,
            'singer_gender': self.singer_gender_original
        }

    #Representação para debug
    def __repr__(self):
        return f"[{self.ID_musica}] {self.title} by {self.artist} ({self.year}) - {self.style}"

#Faz uma lista com as musicas a partir do CSV
def load_music_data(csv_path):
    data = pd.read_csv(csv_path)
    lista_musicas = []
    for idx, (_, row) in enumerate(data.iterrows(), start=1):
        musica = Musica(
            ID_musica=idx,
            title=row['track_title'],
            artist=row['artist_name'],
            year=row['track_date_created'],
            style=row['track_genre_top'] if pd.notna(row['track_genre_top']) else "unknown",
            instruments=row['instruments'] if 'instruments' in row and pd.notna(row['instruments']) else "",
            singer_gender=row['singer_gender'] if 'singer_gender' in row and pd.notna(row['singer_gender']) else "unknown"
        )
        lista_musicas.append(musica)
    return lista_musicas

#Cria Tries para cada categoria
def build_tries(lista_musicas):
    trie_title = Trie()
    trie_style = Trie()
    trie_gender = Trie()
    trie_instrument = Trie()
    trie_artist = Trie()

    for musica in lista_musicas:
        trie_title.insert(musica.title, musica.ID_musica)
        trie_style.insert(musica.style, musica.ID_musica)
        trie_gender.insert(musica.singer_gender, musica.ID_musica)
        trie_artist.insert(musica.artist, musica.ID_musica)
        for inst in musica.instruments:
            trie_instrument.insert(inst, musica.ID_musica)

    return trie_title, trie_style, trie_gender, trie_instrument, trie_artist

#Configurações do Flask
csv_path = "data.csv"
lista_musicas = load_music_data(csv_path)
trie_title, trie_style, trie_gender, trie_instrument, trie_artist = build_tries(lista_musicas)
ID_mapeia = {m.ID_musica: m for m in lista_musicas}

#Rota principal: envia para o index.html as listas ordenadas
@app.route('/')
def index():
    styles = sorted(set(m.style for m in lista_musicas))
    genders = sorted(set(m.singer_gender for m in lista_musicas))
    instruments = sorted({inst for m in lista_musicas for inst in m.instruments})
    return render_template('index.html', styles=styles, genders=genders, instruments=instruments)

#Rota para a busca por texto com autocomplete
@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify([])

    #Busca nas tries 
    IDs_title = trie_title.busca_prefixo(query)
    IDs_style = trie_style.busca_prefixo(query)
    IDs_gender = trie_gender.busca_prefixo(query)
    IDs_instruments = trie_instrument.busca_prefixo(query)
    IDs_artist = trie_artist.busca_prefixo(query)

    #Une os IDs que se relacionam
    matched_IDs = IDs_title | IDs_style | IDs_gender | IDs_instruments | IDs_artist

    #Converte para dicionários ordenando por título
    results = [ID_mapeia[m_id].to_dict() for m_id in matched_IDs]
    results = sorted(results, key=lambda m: m['title'])[:10]    #Retorna os 10 primerios
    return jsonify(results)

#Rota para os filtros avançados
@app.route('/filter_results')
def filter_results():
    # Recupera os filtros da requisição
    styles = [s.lower() for s in request.args.getlist('style')]
    genders = [g.lower() for g in request.args.getlist('singer_gender')]
    instruments = [i.lower() for i in request.args.getlist('instruments')]

    try:
        time_min = int(request.args.get('time_min', 1900))
        time_max = int(request.args.get('time_max', 2023))
    except ValueError:
        time_min = 1900
        time_max = 2023

    # Filtra diretamente a lista de músicas
    filtrados_music = lista_musicas

    if styles:
        filtrados_music = [m for m in filtrados_music if m.style in styles]

    if genders:
        filtrados_music = [m for m in filtrados_music if m.singer_gender in genders]

    if instruments:
        filtrados_music = [
            m for m in filtrados_music
            if any(inst in m.instruments for inst in instruments)
        ]

    # Filtra por intervalo de tempo
    filtrados_music = [
        m for m in filtrados_music
        if m.year.isdigit() and time_min <= int(m.year) <= time_max
    ]

    # Obter ano mínimo e máximo para o slider
    todos_years = [int(m.year) for m in lista_musicas if m.year.isdigit()]
    year_min_csv = min(todos_years) if todos_years else 1900
    year_max_csv = max(todos_years) if todos_years else 2023

    filtrados_music.sort(key=lambda m: m.title)

    return render_template(
        'filter_results.html',
        filtrados=filtrados_music,
        styles_todos=sorted(set(m.style for m in lista_musicas)),
        genders_todos=sorted(set(m.singer_gender for m in lista_musicas)),
        instruments_todos=sorted({inst for m in lista_musicas for inst in m.instruments}),
        selecionados_styles=styles,
        selecionados_genders=genders,
        selecionados_instruments=instruments,
        year_min=year_min_csv,
        year_max=year_max_csv,
        time_min=time_min,
        time_max=time_max
    )

if __name__ == "__main__":
    app.run(debug=True)
