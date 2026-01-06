import requests
import time
import random
from collections import defaultdict, Counter
import logging

logging.basicConfig(
    filename='vinted_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class VintedScraper:
    def __init__(self, cookie_string):
        self.base_url = "https://www.vinted.it/api/v2"
        self.session = requests.Session()
        self._setup_headers()
        self._parse_cookies(cookie_string)
        self.user_listings = defaultdict(int)
        self.city_counts = Counter()
        self.total_listings = 0

    def _setup_headers(self):
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "referer": "https://www.vinted.it/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "User-Agent": random.choice([       #2 user agents per variare vanno bene, ma si possono aggiungere altri
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
            ])
        }

    def _parse_cookies(self, cookie_string):
        self.cookies = {}
        for chunk in cookie_string.split(';'):
            if '=' in chunk:
                key, value = chunk.strip().split('=', 1)
                self.cookies[key] = value

    def _make_request(self, url, params=None, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=15
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request failed (attempt {attempt+1}): {str(e)}")
                time.sleep(2 ** attempt)
        return None

    def fetch_items(self, min_price, max_price):
        page = 1
        while True:
            params = {
                "page": page,
                "per_page": 96,
                "search_text": "sonny angel",
                "price_from": min_price,
                "price_to": max_price,
                "currency": "EUR",
                "order": "newest_first"
            }

            data = self._make_request(f"{self.base_url}/catalog/items", params) #endpoint per gli annunci con i filtri per fare le ricerche
            if not data or not data.get('items'):
                break

            self.process_items(data['items'])
            self.total_listings += len(data['items'])

            if page >= data.get('pagination', {}).get('total_pages', 1):
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.5))

    def process_items(self, items):
        for item in items:
            if 'user' in item and (user_id := item['user'].get('id')):
                self.user_listings[user_id] += 1

    def fetch_user_locations(self):
        filtered_users = {uid: cnt for uid, cnt in self.user_listings.items() if cnt > 1}
        
        for user_id in filtered_users:
            data = self._make_request(f"{self.base_url}/users/{user_id}")   #endpoint per i dettagli utente
            if data and data.get('user'):
                user = data['user']
                if user.get('expose_location') and user.get('city'):    #controlla se l'utente ha permesso di mostrare la località ed eventualmente la conta
                    self.city_counts[user['city']] += 1
            time.sleep(random.uniform(1, 2))

    def run(self):
        # Scansiona tutti gli intervalli di prezzo
        for i in range(5):
            self.fetch_items(i, i+1)   #tipo voltmetro a scaglioni, 0-1, 1-2, 2-3, ...
            time.sleep(random.uniform(5, 10))   #pausa più lunga tra gli intervalli di prezzo per evitare di essere bloccati
        
        self.fetch_user_locations()
        return self.city_counts, self.user_listings, self.total_listings

if __name__ == "__main__":
    # INCOLLA QUI LA TUA STRINGA DI COOKIE COMPLETA OGNI VOLTA CHE ESEGUI LO SCRIPT, ottenendo da DEVTOOLS del browser
    COOKIE_STRING = "v_udt=ZnY3R1V5Z1FHYmdpYlRkbWx5M1pQZ1Byc09iTi0tYjRwM3BrOTN1VDFKcUMzaC0td3lCOWdMdTN2THp0U3o0Nkk4Y0Jodz09; anonymous-locale=it-fr; anon_id=2c39e9db-c21f-469d-95f2-05a91ec9121b; domain_selected=true; __podscribe_vinted_referrer=_; __podscribe_vinted_landing_url=https://www.vinted.it/session-refresh?ref_url=%2F; __podscribe_did=pscrb_ec83be48-531e-48ea-a9ca-14f3a6db9582; OTAdditionalConsentString=1~; _ga=GA1.1.2137466703.1749491726; _ga_KVH0QH2Q98=GS2.1.s1750535018$o2$g1$t1750535018$j60$l0$h0; _ga_ZJHK1N3D75=GS2.1.s1750535018$o3$g1$t1750535018$j60$l0$h0; OptanonAlertBoxClosed=2025-07-24T09:14:15.569Z; eupubconsent-v2=CQVDZHAQVDZHAAcABBITB0FgAAAAAEPgAChQAAAWZABMNCogjLIgBCJQMAIEACgrCACgQBAAAkDRAQAmDApyBgAusJkAIAUAAwQAgABBgACAAASABCIAKACAQAAQCBQABgAQBAQAMDAAGACwEAgABAdAxTAggECwASMyKDTAlAASCAlsqEEgCBBXCEIs8AggREwUAAAIABQEAADwWAhJICViQQBcQTQAAEAAAUQIECKRswBBQGaLQXgyfRkaYBg-YJklMgyAJgjIyTYhN-Ew8chRAAAA.YAAACHwAAAAA; supports_webp=true; v_uid=182618080; v_sid=1796215e-1756114209; is_shipping_fees_applied_info_banner_dismissed=false; seller_header_visits=6; non_dot_com_www_domain_cookie_buster=1; refresh_token_web=eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhY2NvdW50X2lkIjoxMjU1NjI2MzIsImFwcF9pZCI6NCwiYXVkIjoiZnIuY29yZS5hcGkiLCJjbGllbnRfaWQiOiJ3ZWIiLCJleHAiOjE3NjgzMDQ0NjksImlhdCI6MTc2NzY5OTY2OSwiaXNzIjoidmludGVkLWlhbS1zZXJ2aWNlIiwicHVycG9zZSI6InJlZnJlc2giLCJzY29wZSI6InVzZXIiLCJzaWQiOiIxNzk2MjE1ZS0xNzU2MTE0MjA5Iiwic3ViIjoiMTgyNjE4MDgwIiwiY2MiOiJJVCIsImFuaWQiOiIyYzM5ZTlkYi1jMjFmLTQ2OWQtOTVmMi0wNWE5MWVjOTEyMWIiLCJhY3QiOnsic3ViIjoiMTgyNjE4MDgwIn19.VkaoR5R5htR6l8e2Wh5BqjrbaY_jq29J3Bd9arxVS4bLoxrTjh3RBnX5wc9L5PKfOBzwtxsAEyJBAHQ1BU4mx16-yMZfmtbE4ftxO0svHABqtacj3WGti1PZ45k1ptgUafNQg4gZwY4-ndW7cNJUSuW5odPaOixLhtFxTBw9iEfTBs073hA1Cl29SwfvHR9h4XrDCdga7M115IhjtwB1gZ3_61bdxGPNZGYzJZMPoLSKdl8LR7zAERiMidrrN8n3kIzBReB3XaVHHWIf4yLIFVjYzNUtCA1hKLxgcvWs-cYaPds2EyheI86gwYnWYDLTlmw5OHQBATEENexbrTKZcg; access_token_web=eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhY2NvdW50X2lkIjoxMjU1NjI2MzIsImFwcF9pZCI6NCwiYXVkIjoiZnIuY29yZS5hcGkiLCJjbGllbnRfaWQiOiJ3ZWIiLCJleHAiOjE3Njc3MDY4NjksImlhdCI6MTc2NzY5OTY2OSwiaXNzIjoidmludGVkLWlhbS1zZXJ2aWNlIiwicHVycG9zZSI6ImFjY2VzcyIsInNjb3BlIjoidXNlciIsInNpZCI6IjE3OTYyMTVlLTE3NTYxMTQyMDkiLCJzdWIiOiIxODI2MTgwODAiLCJjYyI6IklUIiwiYW5pZCI6IjJjMzllOWRiLWMyMWYtNDY5ZC05NWYyLTA1YTkxZWM5MTIxYiIsImFjdCI6eyJzdWIiOiIxODI2MTgwODAifX0.KbYaHAUvg6ntKsl-M7p62tDBeP481A_GIg2CYCh6by1D5G3NtLJMyVA8NXevFwk9jYRxRJUxE_k5hVgWLLIxn4-FXU9xzXO8rw9Xv9yGKjSRNgPIQIQVONS-vNw-XUCZjL1azUdd-WKzPKI77ip2O7h6raFTJk40prJ_rH50X1sD3umoGaGIc7idXChU-FIovgS-rJrV-xXgET2XpJBM0ltfQ2FODbXuH2RvbREaIUElcuUTS8uukvBG7tQG-3qpuVR914YjZQpRSnMtDLIcKO_bbN0ZHtTgPXsGkoeN3b0OA4GU21LmTCGneXtmBTURt0xPbHRD0rSJBm-FGKtU4A; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Jan+06+2026+12%3A58%3A26+GMT%2B0100+(Central+European+Standard+Time)&version=202508.2.0&browserGpcFlag=0&isIABGlobal=false&consentId=182618080&interactionCount=8&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2CC0005%3A0%2CV2STACK42%3A0%2CC0015%3A0%2CC0035%3A0%2CC0038%3A0&genVendors=V2%3A0%2CV1%3A0%2C&geolocation=IT%3B72&AwaitingReconsent=false&isAnonUser=1&intType=2&identifierType=Cookie+Unique+Id; banners_ui_state=SUCCESS; cf_clearance=WKKW07MkZvM_CPVmrgvNd_dr2ZRRIgBpbqV3wK68ibQ-1767700707-1.2.1.1-F7_kyAcmM3GcT5WX0VrHOfFLyC3QpI90CrEEu6ynS4EPRit4WmNCAV.AjgLWiTvJ8un5yRr8UFqDieGaikbrdZrUoRKI0m5PelXE2jj0AX40cDhrOwSE9qjHP239O7F.pMEbjoaPNFp1AaISnbndK0oQP5SgG0fdoRBbt_PncaMuGyRYZH68ZBzvizBzUyw4b0sdYbD03f5c7InxsS6aV4owOeCHNWDpJO97qeiA68o; _vinted_fr_session=Ymh5SnJUc2hnenM1M2ZhVWhLUHQ0bHJQUU1aVXJhQjk3MnN0OFBkZ2FUT3lYcGRlbnBzTWNhV0M0OUtOU0hWMHpvTk9GdnlrZDQySWN6K2pIZHZyV240eEltT2U4NVFIeUU5NGlubXRnSDFPNTVuak9nb2N0Y29BbnRtRUdXZ0s4c21jQUd0ZkNKd09jUXRIOStBVEZWeWt2SUExZE4zQStjVEJueVJUTUJaZWl4dU9zam5nRXVtSEJNWUNOaUJXN01pOFJ0Z1pFaWhDTVAxSWg4eVB0M0Yra2NNcWNMU2FQRXN2aGp1WWFBYUNYVFVtMk5qUFQ0TFR4WEFNVGtxQS0tV24xckcrK0pRdzEvcHd0MlNFOUhEUT09--0271cfc85562fef8bd8482e3e396df6d0cdefd32; datadome=uTAUKr38hvhOzxYUSgt3kEy56EAqN3m8tu7Mk~PWDf8kS2CYVCM5x2rTYD4oHKU9uq2UQ0FPClG4UEVvPUXiFb4flYQmK2WVN5d6tyNvS4EjR08qzd5FjRuQuiWvYCg0; viewport_size=968"
    

    scraper = VintedScraper(COOKIE_STRING)
    cities, users, total = scraper.run()

    print("\n Località degli utenti:")
    for city, count in cities.most_common():
        print(f"  - {city}: {count} utenti")

    print("\n Utenti con più inserzioni:")
    for user_id, count in sorted(users.items(), key=lambda x: x[1], reverse=True)[:50]:
        print(f"  - ID {user_id}: {count} inserzioni")

    print(f"\n Totale annunci analizzati: {total}")
    print(f" Utenti trovati con 2+ inserzioni: {len(users)}")