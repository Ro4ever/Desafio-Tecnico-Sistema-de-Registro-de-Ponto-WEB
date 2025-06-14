````markdown
# Sistema de Ponto Eletrônico

Este é um sistema web de registro de ponto eletrônico para funcionários, desenvolvido com **Flask**. Ele permite o cadastro de funcionários, controle de horários de entrada e saída, e geração de relatórios em PDF.

## Funcionalidades

- Autenticação de usuários (Admin e Funcionários)
- Registro de ponto com validação de horários
- Interface separada para administradores e funcionários
- Cadastro de novos funcionários com jornada de trabalho
- Geração de relatórios de ponto diário em PDF
- Interface responsiva com HTML, CSS e JavaScript

## Tecnologias Utilizadas

- Python 3.x
- Flask
- Flask-Login
- Flask-Session
- SQLite
- HTML5, CSS3, JavaScript
- ReportLab (para geração de PDF)

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/Ro4ever/ponto-eletronico.git
cd ponto-eletronico
````

2. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute a aplicação:

```bash
python app.py
```

A aplicação estará disponível em `http://127.0.0.1:5000/`.

## Usuário Padrão (Admin)

* **Matrícula:** `admin`
* **Senha:** `admin123`

> É recomendado alterar essa senha em produção.

## Estrutura do Projeto

```
├── app.py                 # Lógica principal da aplicação Flask
├── database.py           # Inicialização e conexão com o banco de dados SQLite
├── ponto_eletronico.db   # Arquivo de banco de dados SQLite
├── requirements.txt      # Dependências do projeto
├── static/
│   ├── style.css         # Estilos CSS
│   └── scripts.js        # JavaScript para relógio em tempo real
├── templates/            # Arquivos HTML (não incluídos aqui)
```

## Observações

* O sistema valida a marcação de ponto dentro de janelas de tempo específicas (±15 minutos).
* Um funcionário pode registrar os seguintes tipos de ponto por dia:

  * Entrada Manhã
  * Saída Manhã
  * Entrada Tarde
  * Saída Tarde
 
## Imagens

![Captura de tela 2025-06-14 171724](https://github.com/user-attachments/assets/e55d9264-2ca2-4ed2-b53b-d145496b2579)
![Captura de tela 2025-06-14 171644](https://github.com/user-attachments/assets/531946f1-dc59-468a-b416-3392d8cd3292)
![Captura de tela 2025-06-14 171809](https://github.com/user-attachments/assets/3ad5296a-de8f-47a2-a9fe-29a91fd866b1)
