import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import google.generativeai as genai

# Configura a API do Gemini
genai.configure(api_key=os.getenv("AIzaSyARPQ_5OEhkkAyyoXvfba_AW_oce_9SC8k"))

app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configuração do banco de dados
db_config = {
    'user': 'root',       
    'password': 'Fone@123g',  
    'host': 'localhost',   
    'database': 'mercado'  
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Rota da página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para visualizar todos os produtos
@app.route('/produtos')
def listar_produtos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('produtos.html', produtos=produtos)

# Rota para cadastro de produto
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO produtos (nome, preco) VALUES (%s, %s)', (nome, preco))
        conn.commit()
        conn.close()

        flash('Produto cadastrado com sucesso!')
        return redirect(url_for('listar_produtos'))
    
    return render_template('cadastro.html')

# Rota para consulta de produtos
@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    produtos = []
    if request.method == 'POST':
        nome = request.form['nome']
        cursor.execute('SELECT * FROM produtos WHERE nome LIKE %s', ('%' + nome + '%',))
        produtos = cursor.fetchall()

    conn.close()
    
    produto_nao_encontrado = len(produtos) == 0
    return render_template('consulta.html', produtos=produtos, produto_nao_encontrado=produto_nao_encontrado)

# Rota para deletar produto
@app.route('/deletar/<int:id>')
def deletar_produto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM produtos WHERE id = %s', (id,))
    conn.commit()
    conn.close()
    flash('Produto excluído com sucesso!')
    return redirect(url_for('listar_produtos'))

# Rota para exibir o formulário de edição
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        cursor.execute('UPDATE produtos SET nome = %s, preco = %s WHERE id = %s', (nome, preco, id))
        conn.commit()
        conn.close()
        flash('Produto atualizado com sucesso!')
        return redirect(url_for('listar_produtos'))

    cursor.execute('SELECT * FROM produtos WHERE id = %s', (id,))
    produto = cursor.fetchone()
    conn.close()
    return render_template('editar.html', produto=produto)

# Rota para a página de sensores
@app.route('/sensores')
def sensores():
    return render_template('sensores.html')

@app.route('/sensores', methods=['GET', 'POST'])
def cadastrar_dados_sensor():
    if request.method == 'POST':
        temperatura = request.form['temperatura']
        umidade = request.form['umidade']
        
        # Insere os dados no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO sensor_data (temperatura, umidade) VALUES ( %s, %s)', ( temperatura, umidade))
        conn.commit()
        conn.close()

        # Verifica se os campos foram preenchidos corretamente
        if not temperatura or not umidade:
            flash('Por favor, preencha todos os campos.')
            return redirect(url_for('cadastrar_dados_sensor'))

        flash('Dados do sensor enviados com sucesso!')  # Mensagem de sucesso
        return redirect(url_for('cadastrar_dados_sensor'))

    return render_template('sensores.html')

@app.route('/api/sensor_data', methods=['GET'])
def listar_dados_sensor():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC')
    dados = cursor.fetchall()
    conn.close()

    # Retorna os dados em formato JSON para o frontend
    return jsonify(dados)



# Configurações do modelo
generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction="Vou te fornecer dados de um sensor de temperatura e umidade de uma câmara fria que armazena carnes congeladas, então preciso de um retorno que analise se é ideal a temperatura e umidade fornecida e qual pode ser o problema, é interessante que os dados históricos sejam armazenados para analises preditivas ou diagnósticas de forma resumida. ",
)

history = []

@app.route('/api/analisar_dados', methods=['POST'])
def analisar_dados():
    user_input = request.json.get('input')
    
    # Inicia a sessão de chat com o modelo
    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(user_input)
    
    model_response = response.text

    # Armazena a interação na história
    history.append({"role": "user", "parts": [user_input]})
    history.append({"role": "assistant", "parts": [model_response]})

    return jsonify({'response': model_response})

if __name__ == '__main__':
    app.run(debug=True)
