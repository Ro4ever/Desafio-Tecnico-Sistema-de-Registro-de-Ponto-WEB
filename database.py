import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'ponto_eletronico.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Tabela de Usuários (funcionários e admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL, -- 'admin' ou 'employee'
            jornada_entrada_manha TEXT,
            jornada_saida_manha TEXT,
            jornada_entrada_tarde TEXT,
            jornada_saida_tarde TEXT
        )
    ''')

    # Tabela de Registros de Ponto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS point_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            tipo_registro TEXT NOT NULL, -- 'entrada_manha', 'saida_manha', 'entrada_tarde', 'saida_tarde'
            hora TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Criar um usuário admin padrão se não existir
    try:
        cursor.execute("INSERT INTO users (matricula, nome, senha, perfil) VALUES (?, ?, ?, ?)",
                       ('admin', 'Administrador', generate_password_hash('admin123'), 'admin'))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Admin already exists

    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Retorna linhas como dicionários
    return conn

if __name__ == '__main__':
    init_db()
    print("Banco de dados inicializado com sucesso!")