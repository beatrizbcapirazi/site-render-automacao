from flask import Flask, render_template, request
import requests as rq
from bs4 import BeautifulSoup as bs
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import unicodedata
from lxml.html import document_fromstring
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

# Função para enviar e-mail


def enviar_email(conteudo_html):
    # Configurar servidor SMTP e credenciais
    servidor_smtp = 'smtp-relay.brevo.com'
    porta_smtp = 587
    usuario = 'beatrizbergaminjornalista@gmail.com'
    senha = os.environ.get('SENHA_EMAIL')

    # Dados para o email que será enviado:
    remetente = "beatrizbergaminjornalista@gmail.com"
    destinatarios = ["beatrizbergaminjornalista@gmail.com"]
    titulo = "Radar ESG - suas notícias de bioeconomia"
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Radar ESG - suas notícias de bioeconomia </title>
      </head>
      <body>
        <h1>Radar ESG</h1>
        <p>
          As matérias encontradas em UOL, Estadão e Ministério da Fazenda hoje foram:
          <ul>
    """

    html = conteudo_html

    # Inicia a conexão com o servidor
    server = smtplib.SMTP(servidor_smtp, porta_smtp)
    server.starttls()  # Altera a comunicação para utilizar criptografia
    server.login(usuario, senha)  # Autentica

    # Preparando o objeto da mensagem ("documento" do email):
    mensagem = MIMEMultipart()
    mensagem["From"] = remetente
    mensagem["To"] = ",".join(destinatarios)
    mensagem["Subject"] = titulo
    conteudo_html = MIMEText(html, "html")
    mensagem.attach(conteudo_html)

    # Enviando o email pela conexão já estabelecida:
    server.sendmail(remetente, destinatarios, mensagem.as_string())


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')


@app.route('/infos')
def infos():
    return render_template('infos.html')


@app.route('/projetos')
def projetos():
    return render_template('projetos.html')


@app.route('/publicacoes')
def publicacoes():
    return render_template('publicacoes.html')

# Nova rota para a página dinâmica


@app.route('/radaresg')
def dados():
    termo_pesquisa = request.args.get('termo')
    horario_extracao = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=-3)))

    # Raspagem das notícias do Ministério da Fazenda
    requisicao_fazenda = rq.get(
        'https://www.gov.br/fazenda/pt-br/assuntos/noticias/2024')
    html_fazenda = requisicao_fazenda.content
    sopa_fazenda = bs(html_fazenda, 'html.parser')

    noticias_ministerio = sopa_fazenda.find_all(
        'article', class_='tileItem visualIEFloatFix tile-collective-nitf-content')

    economia_fazenda = []
    for noticia in noticias_ministerio:
        titulo = noticia.find('a').text
        if termo_pesquisa is not None:
            termo_pesquisa = termo_pesquisa.lower()
            link = noticia.find('a').get('href')
            titulo = noticia.find('a').text
            data_consulta = horario_extracao
            data_publicacao1 = noticia.find_all(
                'span', class_='summary-view-icon')
            veiculo = 'Ministério da Fazenda'
            economia_fazenda.append(
                [titulo, link, data_consulta, veiculo, data_publicacao1])

    # Raspagem de dados do UOL
    requisicao_uol = rq.get('https://economia.uol.com.br/ultimas/')
    html_uol = requisicao_uol.content
    sopa_uol = bs(html_uol, 'html.parser')

    noticias_uol = sopa_uol.find_all(
        'div', class_='thumbnails-item no-image align-horizontal list col-xs-8 col-sm-12 small col-sm-24 small')

    economia_uol = []
    for noticia in noticias_uol:
        titulo = noticia.find('a').text
        if termo_pesquisa is not None:
            termo_pesquisa = termo_pesquisa.lower()
            link = noticia.find('a').get('href')
            titulo = noticia.find('a').text
            data_consulta1 = horario_extracao
            data_publicacao2 = noticia.find_all('time', class_='thumb-date')
            veiculo = 'UOL'
            economia_uol.append(
                [titulo, link, data_consulta1, veiculo, data_publicacao2])

    # Raspagem de dados do Estadão
    requisicao_estadao = rq.get('https://www.estadao.com.br/economia/')
    html_estadao = requisicao_estadao.content
    sopa_estadao = bs(html_estadao, 'html.parser')

    noticia_estadao = sopa_estadao.find_all(
        'div', class_='noticias-mais-recenter--item')

    economia_estadao = []
    for link in noticia_estadao:
        titulo = noticia.find('a').text
        if termo_pesquisa is not None:
            termo_pesquisa = termo_pesquisa.lower()
            links = link.find('a').get('href')
            titulo = link.find('a').get('title')
            data_consulta2 = horario_extracao
            data_publicacao3 = link.find_all('span', class_='date')
            veiculo = 'Estadão'
            economia_estadao.append(
                [titulo, links, data_consulta2, veiculo, data_publicacao3])

    # Renderizar o template e enviar por e-mail
    conteudo_html = render_template(
        'radaresg.html', fazenda=economia_fazenda, uol=economia_uol, estadao=economia_estadao)
    enviar_email(conteudo_html)

    return conteudo_html


if __name__ == '__main__':
    app.run(debug=True)
