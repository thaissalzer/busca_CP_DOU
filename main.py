from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

from weasyprint import HTML
import smtplib
from email.message import EmailMessage

URL = "https://douconsultapublica.manus.space"


# 🔍 1. Extrair cards completos
def rodar_busca():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.click("text=Buscar no DOU")

        print("Aguardando resultados...")
        time.sleep(40)

        cards = page.locator("div:has(a[href*='in.gov.br'])").all()

        itens = []
        vistos = set()

        for card in cards:
            texto = card.inner_text().strip()

            if "consultas públicas encontradas" in texto.lower():
                continue

            link_el = card.locator("a[href*='in.gov.br']")
            link = link_el.first.get_attribute("href") if link_el.count() > 0 else ""

            if not link or link in vistos:
                continue

            vistos.add(link)

            linhas = [l.strip() for l in texto.split("\n") if l.strip()]

            secao = ""
            titulo = ""
            orgao = ""
            descricao = ""

            for l in linhas:
                if "seção" in l.lower() and not secao:
                    secao = l

                elif l.isupper() and len(l) > 8 and not titulo:
                    titulo = l

                elif ("ministério" in l.lower() or "agência" in l.lower()) and not orgao:
                    orgao = l

                elif titulo and not descricao:
                    descricao = l

            # fallback (evita vazio)
            if not titulo and linhas:
                titulo = linhas[0]

            if not descricao and len(linhas) > 1:
                descricao = linhas[1]

            itens.append({
                "secao": secao,
                "titulo": titulo,
                "orgao": orgao,
                "descricao": descricao,
                "link": link
            })

        browser.close()
        return itens


# 🎨 2. Montar HTML (layout limpo)
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
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                border-left: 6px solid #1a3c6e;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .secao {{
                font-size: 11px;
                color: #888;
                margin-bottom: 5px;
            }}
            .titulo {{
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 8px;
            }}
            .orgao {{
                font-size: 12px;
                color: #555;
                margin-bottom: 8px;
            }}
            .descricao {{
                font-size: 13px;
                color: #333;
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
            <div class="secao">{item['secao']}</div>
            <div class="titulo">{item['titulo']}</div>
            <div class="orgao">{item['orgao']}</div>
            <div class="descricao">{item['descricao']}</div>
            <a class="link" href="{item['link']}">Ver publicação completa no DOU</a>
        </div>
        """

    html += "</body></html>"
    return html


# 📄 3. Gerar PDF (CORRIGIDO)
def gerar_pdf(html):
    HTML(string=html).write_pdf("dou.pdf")


# 📩 4. Enviar email
def enviar_email():
    email = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")


    msg = EmailMessage()
    msg["Subject"] = "DOU - Consultas Públicas"
    msg["From"] = email

    destinatarios = [
        "thaissalzer@gmail.com",
        "gleyanne.silva@fazenda.gov.br"
    ]

    msg["To"] = ", ".join(destinatarios)

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





# 🚀 Execução
def job():
    itens = rodar_busca()
    html = montar_html(itens)
    gerar_pdf(html)
    enviar_email()


if __name__ == "__main__":
    job()
