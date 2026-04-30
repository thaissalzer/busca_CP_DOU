from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

from weasyprint import HTML
import smtplib
from email.message import EmailMessage

URL = "https://douconsultapublica.manus.space"


# 🔍 1. Extrair itens (título + link)
def rodar_busca():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)

        page.click("text=Buscar no DOU")

        print("Aguardando resultados...")
        time.sleep(40)

        elementos = page.locator("a[href*='in.gov.br']").all()

        itens = []
        for el in elementos:
            titulo = el.inner_text()
            link = el.get_attribute("href")
            itens.append((titulo, link))

        browser.close()

        return itens


# 🎨 2. Montar HTML bonito (com CSS)
def montar_html(itens):
    data = datetime.today().strftime("%d/%m/%Y")

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 30px;
                color: #333;
            }}
            h1 {{
                color: #1a3c6e;
            }}
            .item {{
                margin-bottom: 20px;
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            .titulo {{
                font-weight: bold;
                font-size: 14px;
            }}
            .link {{
                font-size: 12px;
                color: #0066cc;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h1>Monitoramento de Consultas Públicas – DOU</h1>
        <p>Data: {data}</p>
        <hr>
    """

    for i, (titulo, link) in enumerate(itens, 1):
        html += f"""
        <div class="item">
            <div class="titulo">{i}. {titulo}</div>
            <a class="link" href="{link}">Acessar no DOU</a>
        </div>
        """

    html += "</body></html>"

    return html


# 📄 3. Gerar PDF
def gerar_pdf(html):
    HTML(string=html).write_pdf("dou.pdf")


# 📩 4. Enviar email com PDF
def enviar_email():
    email = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")

    msg = EmailMessage()
    msg["Subject"] = "DOU - Consultas Públicas"
    msg["From"] = email
    msg["To"] = "thaissalzer@gmail.com"

    msg.set_content("Segue relatório em PDF.")

    with open("dou.pdf", "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename="dou.pdf"
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email, senha)
        server.send_message(msg)


# 🚀 Fluxo principal
def job():
    itens = rodar_busca()
    html = montar_html(itens)
    gerar_pdf(html)
    enviar_email()


if __name__ == "__main__":
    job()
