# File: scraper_github.py (versione Stealth + Consensi)

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import json

# ... (le configurazioni rimangono uguali) ...
BANCHE_TARGET = {
    "Intesa Sanpaolo": "Intesa Sanpaolo",
    "ING": "ING",
    "CheBanca!": "Mediobanca Premier"
}
DURATE = [10, 15, 20, 25, 30]
URL_MUTUI = "https://www.mutuionline.it/mutuo-casa/"

def scrape_tassi():
    print("Avvio scraping da MutuiOnline in modalità STEALTH + CONSENSI...")
    risultati_finali = {banca: {} for banca in BANCHE_TARGET.values()}

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        stealth_sync(page)

        for durata in DURATE:
            try:
                print(f"-> Analizzo durata: {durata} anni...")
                page.goto(URL_MUTUI, timeout=90000)
                page.wait_for_timeout(2000)

                # --- Compilazione Form (Parte 1) ---
                page.locator("#valore-immobile").fill("100000")
                page.locator("#importo-mutuo").fill("80000")
                page.locator(f"label[for='durata-{durata}']").click()
                page.locator("#data-nascita-giorno").fill("01")
                page.locator("#data-nascita-mese").fill("01")
                page.locator("#data-nascita-anno").fill("2000")
                page.locator("label[for='dipendente-tempo-indeterminato']").click()
                page.locator("#reddito-richiedenti").fill("3000")
                page.locator("#provincia-comune").fill("Cagliari (CA)")
                page.locator("#provincia-comune-list-item-0").click()

                # --- Compilazione Form (Parte 2: Dati Personali) ---
                page.locator("#nome").fill("Pino")
                page.locator("#cognome").fill("Lino")
                page.locator("#telefono").fill("3432346478")
                page.locator("#email").fill("sergino@libero.it")

                # --- Spunta Caselle Consenso ---
                print("   Spunto le caselle del consenso...")
                page.locator("label[for='conferma-presa-visione']").click()
                page.locator("label[for='consenso-trattamento-dati']").click()
                page.locator("label[for='conferma-presa-visione-termini']").click()

                # --- Click Finale ---
                page.locator("#button-step1").click()
                page.wait_for_selector(".risultato-prodotto", timeout=90000)
                page.wait_for_timeout(5000)

                # ... (la parte di estrazione dati rimane identica) ...
                prodotti = page.locator(".risultato-prodotto").all()
                for prodotto in prodotti:
                    nome_banca_raw = prodotto.locator(".box-prodotto-logo img").get_attribute("alt")
                    for nome_sito, nome_nostro in BANCHE_TARGET.items():
                        if nome_sito.lower() in nome_banca_raw.lower():
                            tasso_box = prodotto.locator(".box-tipo-tasso:has-text('Fisso')")
                            if tasso_box.count() > 0:
                                tasso_str = tasso_box.locator(".valore-tasso").inner_text()
                                tasso_val = float(tasso_str.replace("%", "").replace(",", ".").strip())
                                risultati_finali[nome_nostro][durata] = tasso_val
                                print(f"   Trovato: {nome_nostro} - {durata} anni - Tasso: {tasso_val}%")
            
            except Exception as e:
                print(f"Errore durante lo scraping per la durata {durata} anni: {e}")
                continue
        
        browser.close()
    
    print("Scraping completato.")
    return risultati_finali

if __name__ == "__main__":
    dati_raccolti = scrape_tassi()
    with open('tassi.json', 'w', encoding='utf-8') as f:
        json.dump(dati_raccolti, f, ensure_ascii=False, indent=4)
    print("File 'tassi.json' creato con successo.")
