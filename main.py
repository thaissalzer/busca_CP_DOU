from playwright.sync_api import sync_playwright
import time
import yagmail
from datetime import datetime
import os

URL = "https://douconsultapublica.manus.space"

def rodar_busca():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)

        page.click("text=Buscar no DOU")

        print("Aguardando resultados...")
        time.sleep(40)

        html = page.content()

        browser.close()

        return html


def enviar_email(html):
    email = os.getenv("EMAIL_USER")
    senha = os.getenv("EMAIL_PASS")

    yag = yagmail.SMTP(email, senha)

    hoje = datetime.today().strftime("%d/%m/%Y")

    yag.send(
        to="thaissalzer@gmail.com",
        subject=f"DOU - Consultas Públicas ({hoje})",
        contents=html
    )


def job():
    html = rodar_busca()
    enviar_email(html)


if __name__ == "__main__":
    job()