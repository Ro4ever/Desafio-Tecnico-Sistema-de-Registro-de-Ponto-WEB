from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import sqlite3
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

from database import init_db, get_db_connection, DATABASE

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui' # Mude para uma chave forte em produção
app.config['SESSION_TYPE'] = 'filesystem' # Para persistir a sessão

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, matricula, nome, perfil):
        self.id = id
        self.matricula = matricula
        self.nome = nome
        self.perfil = perfil

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute("SELECT id, matricula, nome, perfil FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['matricula'], user_data['nome'], user_data['perfil'])
    return None

@app.before_request
def before_request():
    init_db() # Garante que o DB esteja inicializado antes de cada requisição

# --- Funções de Validação de Horário ---
def is_within_window(current_time_str, target_time_str, minutes_before, minutes_after):
    try:
        current_dt = datetime.strptime(current_time_str, '%H:%M')
        target_dt = datetime.strptime(target_time_str, '%H:%M')
        
        lower_bound = target_dt - timedelta(minutes=minutes_before)
        upper_bound = target_dt + timedelta(minutes=minutes_after)
        
        return lower_bound <= current_dt <= upper_bound
    except ValueError:
        return False

# --- Rotas de Autenticação ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.perfil == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))

    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']

        conn = get_db_connection()
        user_data = conn.execute("SELECT id, matricula, nome, senha, perfil FROM users WHERE matricula = ?", (matricula,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['senha'], senha):
            user = User(user_data['id'], user_data['matricula'], user_data['nome'], user_data['perfil'])
            login_user(user)
            if user.perfil == 'admin':
                flash('Login de Administrador bem-sucedido!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Login de Funcionário bem-sucedido!', 'success')
                return redirect(url_for('employee_dashboard'))
        else:
            flash('Matrícula ou senha inválidos. Tente novamente.', 'danger')
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

# --- Rotas de Administrador ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.perfil != 'admin':
        flash('Acesso negado. Você não tem permissão de administrador.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    employees = conn.execute("SELECT matricula, nome FROM users WHERE perfil = 'employee'").fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', employees=employees)

@app.route('/admin/register_employee', methods=['GET', 'POST'])
@login_required
def register_employee():
    if current_user.perfil != 'admin':
        flash('Acesso negado. Você não tem permissão de administrador.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        matricula = request.form['matricula']
        nome = request.form['nome']
        senha = request.form['senha']
        jornada_entrada_manha = request.form['jornada_entrada_manha']
        jornada_saida_manha = request.form['jornada_saida_manha']
        jornada_entrada_tarde = request.form['jornada_entrada_tarde']
        jornada_saida_tarde = request.form['jornada_saida_tarde']

        hashed_password = generate_password_hash(senha)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (matricula, nome, senha, perfil, jornada_entrada_manha, jornada_saida_manha, jornada_entrada_tarde, jornada_saida_tarde) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (matricula, nome, hashed_password, 'employee', jornada_entrada_manha, jornada_saida_manha, jornada_entrada_tarde, jornada_saida_tarde)
            )
            conn.commit()
            flash(f'Funcionário {nome} ({matricula}) cadastrado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        except sqlite3.IntegrityError:
            flash(f'Matrícula {matricula} já existe. Por favor, use outra.', 'danger')
        finally:
            conn.close()
    return render_template('register_employee.html')

@app.route('/admin/report')
@login_required
def generate_report():
    if current_user.perfil != 'admin':
        flash('Acesso negado. Você não tem permissão de administrador.', 'danger')
        return redirect(url_for('login'))

    today_date = datetime.now().strftime('%d/%m/%Y')
    conn = get_db_connection()

    # Obter todos os usuários (funcionários)
    employees = conn.execute("SELECT id, matricula, nome FROM users WHERE perfil = 'employee'").fetchall()
    
    # Dicionário para armazenar os registros do dia para cada funcionário
    daily_records = {}
    for emp in employees:
        daily_records[emp['id']] = {
            'matricula': emp['matricula'],
            'nome': emp['nome'],
            'data': today_date,
            'entrada_manha': 'PENDENTE',
            'saida_manha': 'PENDENTE',
            'entrada_tarde': 'PENDENTE',
            'saida_tarde': 'PENDENTE'
        }
    
    # Obter registros de ponto do dia atual
    records = conn.execute(
        "SELECT user_id, tipo_registro, hora FROM point_records WHERE data = ?", 
        (datetime.now().strftime('%d/%m/%Y'),)
    ).fetchall()
    conn.close()

    for record in records:
        user_id = record['user_id']
        tipo_registro = record['tipo_registro']
        hora = record['hora']
        
        if user_id in daily_records:
            if tipo_registro == 'entrada_manha':
                daily_records[user_id]['entrada_manha'] = hora
            elif tipo_registro == 'saida_manha':
                daily_records[user_id]['saida_manha'] = hora
            elif tipo_registro == 'entrada_tarde':
                daily_records[user_id]['entrada_tarde'] = hora
            elif tipo_registro == 'saida_tarde':
                daily_records[user_id]['saida_tarde'] = hora

    # Preparar dados para o PDF
    data = [['Matrícula', 'Nome', 'Data', 'Entrada Manhã', 'Saída Manhã', 'Entrada Tarde', 'Saída Tarde']]
    for user_id in daily_records:
        record = daily_records[user_id]
        data.append([
            record['matricula'],
            record['nome'],
            record['data'],
            record['entrada_manha'],
            record['saida_manha'],
            record['entrada_tarde'],
            record['saida_tarde']
        ])

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    title_style = styles['h2']
    title_style.alignment = 1 # Center
    title = Paragraph(f"Relatório de Ponto - {today_date}", title_style)

    # Definir estilos da tabela
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    table = Table(data)
    table.setStyle(table_style)

    elements = [title, table]
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, download_name=f'relatorio_ponto_{datetime.now().strftime("%Y%m%d")}.pdf', as_attachment=True, mimetype='application/pdf')


# --- Rotas de Funcionário ---
@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    if current_user.perfil != 'employee':
        flash('Acesso negado. Você não tem permissão de funcionário.', 'danger')
        return redirect(url_for('login'))
    
    current_time = datetime.now().strftime('%H:%M:%S')
    current_date = datetime.now().strftime('%d/%m/%Y')

    conn = get_db_connection()
    user_jornada = conn.execute(
        "SELECT jornada_entrada_manha, jornada_saida_manha, jornada_entrada_tarde, jornada_saida_tarde FROM users WHERE id = ?", 
        (current_user.id,)
    ).fetchone()

    # Ponto do dia atual para o funcionário
    daily_records = conn.execute(
        "SELECT tipo_registro, hora FROM point_records WHERE user_id = ? AND data = ? ORDER BY hora ASC",
        (current_user.id, current_date)
    ).fetchall()
    conn.close()

    recorded_types = [record['tipo_registro'] for record in daily_records]
    
    # Status dos botões e alertas
    can_register = {
        'entrada_manha': True,
        'saida_manha': True,
        'entrada_tarde': True,
        'saida_tarde': True
    }
    
    alert_messages = []

    # Verificar janelas de tempo e registros duplicados
    current_time_str = datetime.now().strftime('%H:%M')

    # Entrada Manhã
    if 'entrada_manha' in recorded_types:
        can_register['entrada_manha'] = False
    elif not is_within_window(current_time_str, user_jornada['jornada_entrada_manha'], 15, 15):
        can_register['entrada_manha'] = False
        alert_messages.append('Fora da janela para Entrada Manhã (07:45 - 08:15)')

    # Saída Manhã
    if 'saida_manha' in recorded_types:
        can_register['saida_manha'] = False
    elif not is_within_window(current_time_str, user_jornada['jornada_saida_manha'], 15, 15):
        can_register['saida_manha'] = False
        alert_messages.append('Fora da janela para Saída Manhã (11:45 - 12:15)')
    
    # Entrada Tarde
    if 'entrada_tarde' in recorded_types:
        can_register['entrada_tarde'] = False
    elif not is_within_window(current_time_str, user_jornada['jornada_entrada_tarde'], 15, 15):
        can_register['entrada_tarde'] = False
        alert_messages.append('Fora da janela para Entrada Tarde (13:45 - 14:15)')

    # Saída Tarde
    if 'saida_tarde' in recorded_types:
        can_register['saida_tarde'] = False
    elif not is_within_window(current_time_str, user_jornada['jornada_saida_tarde'], 15, 15):
        can_register['saida_tarde'] = False
        alert_messages.append('Fora da janela para Saída Tarde (17:45 - 18:15)')

    return render_template('employee_dashboard.html', 
                           user_name=current_user.nome, 
                           current_time=current_time,
                           current_date=current_date,
                           daily_records=daily_records,
                           can_register=can_register,
                           alert_messages=alert_messages)

@app.route('/employee/register_point/<point_type>', methods=['POST'])
@login_required
def register_point(point_type):
    if current_user.perfil != 'employee':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('login'))
    
    current_time_str = datetime.now().strftime('%H:%M')
    current_full_time = datetime.now().strftime('%H:%M:%S')
    current_date = datetime.now().strftime('%d/%m/%Y')

    conn = get_db_connection()
    user_jornada = conn.execute(
        "SELECT jornada_entrada_manha, jornada_saida_manha, jornada_entrada_tarde, jornada_saida_tarde FROM users WHERE id = ?", 
        (current_user.id,)
    ).fetchone()
    
    # Verificar se já existe um registro do mesmo tipo para o dia
    existing_record = conn.execute(
        "SELECT id FROM point_records WHERE user_id = ? AND data = ? AND tipo_registro = ?",
        (current_user.id, current_date, point_type)
    ).fetchone()

    if existing_record:
        flash(f'Você já registrou sua {point_type.replace("_", " ").title()} hoje.', 'warning')
        conn.close()
        return redirect(url_for('employee_dashboard'))

    is_allowed = False
    if point_type == 'entrada_manha':
        is_allowed = is_within_window(current_time_str, user_jornada['jornada_entrada_manha'], 15, 15)
    elif point_type == 'saida_manha':
        is_allowed = is_within_window(current_time_str, user_jornada['jornada_saida_manha'], 15, 15)
    elif point_type == 'entrada_tarde':
        is_allowed = is_within_window(current_time_str, user_jornada['jornada_entrada_tarde'], 15, 15)
    elif point_type == 'saida_tarde':
        is_allowed = is_within_window(current_time_str, user_jornada['jornada_saida_tarde'], 15, 15)

    if is_allowed:
        conn.execute(
            "INSERT INTO point_records (user_id, data, tipo_registro, hora) VALUES (?, ?, ?, ?)",
            (current_user.id, current_date, point_type, current_full_time)
        )
        conn.commit()
        flash(f'Ponto de {point_type.replace("_", " ").title()} registrado com sucesso às {current_full_time}!', 'success')
    else:
        flash(f'Não é possível registrar {point_type.replace("_", " ").title()} agora. Fora da janela permitida.', 'danger')
    
    conn.close()
    return redirect(url_for('employee_dashboard'))

if __name__ == '__main__':
    init_db() # Garante que o banco de dados seja inicializado na primeira execução
    app.run(debug=True) # debug=True para desenvolvimento. Mude para False em produção.