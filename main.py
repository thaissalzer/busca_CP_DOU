from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

from weasyprint import HTML
import smtplib
from email.message import EmailMessage

URL = "https://douconsultapublica.manus.space"


# 🔍 1. Extrair TODOS os itens (sem filtro)
def rodar_busca():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)

        page.click("text=Buscar no DOU")

        print("Aguardando resultados...")
        time.sleep(40)

        # 👇 pega o CARD completo (não só link)
        cards = page.locator("div:has-text('Ver publicação completa no DOU')").all()

        itens = []
        vistos = set()

        for card in cards:
            texto = card.inner_text().strip()

            link_el = card.locator("a[href*='in.gov.br']")
            link = link_el.first.get_attribute("href") if link_el.count() > 0 else ""

            if link in vistos:
                continue

            vistos.add(link)

            itens.append({
                "texto": texto,
                "link": link
            })

        browser.close()

        return itens

# 🎨 2. Montar HTML bonito
def montar_html(itens):
    data = datetime.today().strftime("%d/%m/%Y")

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 30px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #1a3c6e;
            }}
            .card {{
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                border-left: 6px solid #1a3c6e;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .texto {{
                font-size: 13px;
                white-space: pre-line;
                margin-bottom: 10px;
            }}
            .link {{
                color: #007bff;
                font-weight: bold;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h1>Monitoramento de Consultas Públicas – DOU</h1>
        <p><b>Data:</b> {data}</p>
        <hr>
    """

    if not itens:
        html += "<p>Nenhum resultado encontrado.</p>"

    for item in itens:
        html += f"""
        <div class="card">
            <div class="texto">{item['texto']}</div>
            <a class="link" href="{item['link']}">Ver publicação completa no DOU</a>
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
