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
    COOKIE_STRING = """
    v_udt=Kzk4RjVyd2JWRXBjOEJWQ3A2TUFITnEzNWR0ei0tcGVTUkRHeGxYN3N0emVVeS0tVHhrdTNnQ25lemV3NXNxN0s4cFQxdz09; OptanonAlertBoxClosed=2024-12-22T20:46:15.186Z; eupubconsent-v2=CQKCNRgQKCNRgAcABBENBVFgAAAAAAAAAChQAAAAAAFBIIQACAAFwAUABUADgAHgAQQAyADUAHgARAAmABVADeAHoAPwAhIBDAESAI4ASwAmgBWgDDgGUAZYA2QB3wD2APiAfYB-gEAAIpARcBGACNAFBAKgAVcAuYBigDRAG0ANwAcQBDoCRAE7AKHAUeApEBTYC2AFyALvAXmAw0BkgDJwGXAM5gawBrIDYwG3gN1AcEA5MBy4DxwHtAQhAheEAOgAOABIAOcAg4BPwEegJFASsAm0BT4CwgF5AMQAYtAyEDIwGjANTAbQA24BugDygHyAP3AgIBAyCCIIJgQYAhWBC4cAwAARAA4ADwALgAkAB-AGgAc4A7gCAQEHAQgAn4BUAC9AHSAQgAj0BIoCVgExAJlATaApABSYCuwFqALoAYgAxYBkIDJgGjANNAamA14BtADbAG3AOPgc6Bz4DygHxAPtgfsB-4EDwIIgQYAg2BCsdBLAAXABQAFQAOAAgABdADIANQAeABEACYAFWALgAugBiADeAHoAP0AhgCJAEsAJoAUYArQBhgDKAGiANkAd4A9oB9gH6AP-AigCMAFBAKuAWIAuYBeQDFAG0ANwAcQA6gCHQEXgJEATIAnYBQ4Cj4FNAU2AqwBYoC2AFwALkAXaAu8BeYC-gGGgMeAZIAycBlUDLAMuAZyA1UBrADbwG6gOLAcmA5cB44D2gH1gQBAhaQAJgAIADQAOcAsQCPQE2gKTAXkA1MBtgDbgHPgPKAfEA_YCB4EGAINgQrIQHQAFgAUABcAFUALgAYgA3gB6AEcAO8Af4BFACUgFBAKuAXMAxQBtADqQKaApsBYoC0QFwALkAZOAzkBqoDxwIWkoEQACAAFgAUAA4ADwAIgATAAqgBcADFAIYAiQBHACjAFaANkAd4A_ACrgGKAOoAh0BF4CRAFHgLFAWwAvMBk4DLAGcgNYAbeA9oCB5IAeABcAdwBAACoAI9ASKAlYBNoCkwGLANyAeUA_cCCIEGCkDgABcAFAAVAA4ACCAGQAaAA8ACIAEwAKQAVQAxAB-gEMARIAowBWgDKAGiANkAd8A-wD9AIsARgAoIBVwC5gF5AMUAbQA3ACHQEXgJEATsAocBTYCxQFsALgAXIAu0BeYC-gGGgMkAZPAywDLgGcwNYA1kBt4DdQHBAOTAeOA9oCEIELSgCEAC4AJABHADnAHcAQAAkQBYgDXgHbAP-Aj0BIoCYgE2gKQAU-ArsBdAC8gGLAMmAamA14B5QD4oH7AfuBAwCB4EEwIMAQbAhW.YAAAAAAAAAAA; OTAdditionalConsentString=1~; anonymous-locale=it-fr; anon_id=2c39e9db-c21f-469d-95f2-05a91ec9121b; anon_id=2c39e9db-c21f-469d-95f2-05a91ec9121b; v_uid=182618080; v_sid=f8f16eea-1735127559; domain_selected=true; access_token_web=eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhcHBfaWQiOjQsImNsaWVudF9pZCI6IndlYiIsImF1ZCI6ImZyLmNvcmUuYXBpIiwiaXNzIjoidmludGVkLWlhbS1zZXJ2aWNlIiwic3ViIjoiMTgyNjE4MDgwIiwiaWF0IjoxNzM5NTYyMDU3LCJzaWQiOiJmOGYxNmVlYS0xNzM1MTI3NTU5Iiwic2NvcGUiOiJ1c2VyIiwiZXhwIjoxNzM5NTY5MjU3LCJwdXJwb3NlIjoiYWNjZXNzIiwiYWN0Ijp7InN1YiI6IjE4MjYxODA4MCJ9LCJhY2NvdW50X2lkIjoxMjU1NjI2MzJ9.s4TdymzxhcIY8KQpw4XLXqtOXxOC-UENsBycNrC9sVaCtpa5Y2Q2nn-OOG-GbGi8QMZssxqvlOIjIrbtaLUOq_WF191Nna_QoEHwjBoPCVXWyH4H0iUgRtoee_BQyjNlk6NDTBIvku9vaJzYixdqlISkK0zKIEouO6DxCYFrXu1W1fT4AYH4OqRbU1OOLNIdocVkgPdLW0ZyFg_UoQxMf4rNVvLamnwpZMLvcar2bu1Ek7iy8jfxpQNP9bc4vTM84sb8Ux4FsdR6PufdUzlNDyyFO9rRSHGc0rboMzQX3U2uFokCRD57M9fsoIf4Vk8deQnArBlh7W2lF-qmnGBjCw; refresh_token_web=eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhcHBfaWQiOjQsImNsaWVudF9pZCI6IndlYiIsImF1ZCI6ImZyLmNvcmUuYXBpIiwiaXNzIjoidmludGVkLWlhbS1zZXJ2aWNlIiwic3ViIjoiMTgyNjE4MDgwIiwiaWF0IjoxNzM5NTYyMDU3LCJzaWQiOiJmOGYxNmVlYS0xNzM1MTI3NTU5Iiwic2NvcGUiOiJ1c2VyIiwiZXhwIjoxNzQwMTY2ODU3LCJwdXJwb3NlIjoicmVmcmVzaCIsImFjdCI6eyJzdWIiOiIxODI2MTgwODAifSwiYWNjb3VudF9pZCI6MTI1NTYyNjMyfQ.GPEfqXru6h4ntUGlfwWJbS_XRIMDbVkFep28FzrV2HsMTyhzSFpCYaJhU5ohvoiizTwHydjSdfsNe34cnpx2RcDMA-PZSVzE6zT6FKrRE-CYXR8yGTlkpSV6LVCl30yIA3JhJUuvuFJJt5kB7XQqrerC5ThoHyYji-oWK4XJhYtVhRoiGaaPBMMNMTUIFVYhsOzzfMSMGp74k9qbp4JZ4W0fENI2DjXC1pD-EPiuSunLzre6CVWDU0bmEgx_jzVBoVig6dqTof994qjSAuFBnqZXKPc8lWcPgm9j7LtejKVfV7YiRzkKU3Qgoz-BGbRGwHHvUe7QhH7OS2OpypCzXw; cf_clearance=tgPLTMz0w1vsXZzZGImsuy99iMX56Yz74MxSx9mnPyM-1739565630-1.2.1.1-1h7CQJjw4o8a8w4DSBT5D02Rc3c753HeA6QMt5vq.FTTXUympUgLCAH72iHKJDiNQm7rsOxFPgeZKz7m4QT5u1O9U9CuEeTxNqrnS1bqW9MjBtJ79pyfEeTBklP3y_1BEQVwrsmBKkB.VvGo2a.jWMLjEsyBSUqGzTcWllBq7JT2zuzPVwL0w23qJZqBFmN.GUGPTFNLwrSONbEviqHYHcI32imBR0mTZDkNT0nzzJ5PcfvdzBdGlivjzLisIzI.fhoxrte4RvlmpSUTr1nQjfqgZJcEyz7PKCAJRFG.tT0; viewport_size=426; datadome=cCrZ6hJVPcyhHKGDvjYlvFlNQtswiVCcXGyeEWcIqYYTyohNshAq1XkQVweQToTrP4mQYMZBAE7NHHW9h9~MI09yDCCXxHC7Sy~npWCdtg7h2vFiCIGS6dc4YZOK1Kru; _vinted_fr_session=aFdiL0xnK08rWHh0WkF2UVF4SWVpbmN0bGxpak1POWxDSWk5cTZiWGpySEtYaU5VU2xuZFVtaFd4Q3Rwc0diRFlXUjJuTVlsN1ArUkdRbEMrU3cvMkNlRG9HNnk3Y3Y2ZlFrWm41TXZUVjh6VEhoMC9lSk5WSWV6Vk0xN0QrY1RSRzFXcG9ocS9FaHptaklkR25uZ3Zuc0Nkd2d1Rkhxb2ZHNU5PTXozWERzb2hTNmNUTERvcmMyZ2U1b2NXek1NZXRPNmxtNWVUNmphMFBodFVtT2FMM2diTmJEN3ppV09XUldPSDdUdnNiNXZiVVkvNUhyS3M4SnBVN2Jpc1ZiUm82OWxnMEtFRm91SVRpN3VsN1FvS1E5K2E4dituczBHcGhQZVZNRmVYNkQrRG40ZWxjdnVjamIydXdMU3R6Ui8vZklZWXUzYk5tc2Y5OTZUMjJWN2I5eUpMcDZxSEk0NEZwTGJ1WHBUd21ZVGoyZG83eWR1bkNCbjdoajhhYnJ0MzBnT3AvQUhCOTlFayt3eXNpZTdJZmxIaUZaSEFrbm5PTFpGZFNHaXF1Mi9sRE9uMC81Uys0SVZMaUltVDEvUHZzMVp4VkNhcTFrd2FKZDNibDYyRHRzcnZibTZQaWJsaU1IT0xRY0RQYk02cVpXNHhOTnV5ckcvUzQrM3NEMVR1eUxlYWRCMHJKTU5JQXpYbGtFdmZOR0Z2U2w5YldTeDIxclhwejRQRWVsc2hYcWt4K2J2c25XNEgvWFFvL0h6VythMUxIdFFEd2ZKQUVlNXV3R1ZXanZnY25nb1p2MTdyUllvOUpqcEgyaStqVzFpQ0NzZ2xnWXBRbHNCNU5HK2hVNEs3ZUsxSlhteUwwTVRaQnR4R2wxbENYM3VDRlpYRW1jczNRVi9GRk0vMFE3b290bTQyK28xZGtsSTMxcnFwbnpDREJkeDBYU2E1Z0loSm01aGhGREt4Ymt5WEZ5Y2ZqQmJIRzdub2luSzFFU2ZzZ2R1cFZYWE54QVE5bElXRS9tclJ4MjNpVDBKS2dGdFE0QytVT2YyMmV1QlM4aXgrWFdQUTdNU3BlSENlRlFzczBVSWM1eFNpcEF1a1E4QU9VYVRYY1hIRktJREtEelVmcVVkVWJ4dUwydUdpV1NwaXBmWTN1RTAwcnE0WmZrYkNVQ3lady85VHhHT2VxcjJqN1Rrb3M0MWRQS2R5UVdhcFM1UnlCcWRNZUhaZDYwQXhnejdrMGRtZkw2YWo0MzA1b1RYUnVBUlQxWlRFbWVVSCtBTGEzcDRwU2FPVStRdW84VXBmdm9hcUhUM285ZG14QzJSazUrcEtjcnFNSVlBUTllZDNDYVFlL2h2ZGhTZG02cU9tYUF0NW94QnNrNFpMa2RQZnBSekpkQWJVbnQxWmVNcVhUMHVZOHpGY2gzMlNKWStlTUVFZ1dJVk1oMTdqU2xGMEZGaHRtNGNUQ0w1M2pST1lSTElwNTdwMWZuOWtiVFRIWmY1TW9JOFB6N0tKSXNKZXo5LzVxbEVsWDhZYk1rNDNvWHNHZ3FaRnh6SnMyb0tFNFNFZUM5OGsydUVDNVlETURqLzJqR2JMdlNPdkozNVViZ0xJdlRkV2xOUkRUQk9WbURVa2cwejMxOXk5UDlNWEhTRkFkVU02cmtORVpQTW9lVFJxV1ZlT1ZoMjhoYUw0cnhHKzcxUU1xd3NaenRBRHRZejRNN2FxeVFRQXhaYmRVZUN6YkhWUnprc3dRdHVhVEtteEF2Q25nUkpuZm9RYWltd2hFYm5BMlJJSHhJaUZ3VXlpY2cybzVwVDNmdm85bCthSDVrS3B1TmkxMmhVWEZ2UE56cE1iQmMzK0txZlQveFFwTXJCOThZd3hPV2JiSTdSYzdKTXpqZUJnejFkWXlTQzdlengvUEQxVWppL2dXR0NYc1Z6WFM1Y0hkeHVPUUtacHdnREVHL1ZrWEpSNXhWbE9CbmRoRExvTU13TW13RVZGcE5mMGh0UE4zVEVDUmFVaHZhQjJCbGFYa2xQRTdLcm85YU5qUDBqMXNpOU81OWpVM25vc1JTNGJWWmNQcUJHY1MwMjRCNkNsYWU5OStBWGl3OWw0LzhWK0RrRVZhZmdXREx0bkxJcWZBWUROZ1JBUVlYeTVhdXR6SE45enExYW9OOXZHMjVLR2RGWm85STRxN2ZEVEZDajFzVGNhQTQvWmNtazdWdkpWNzdYa3RWV3MwRXNkbnF5MjlrSHJibC9GNjBwL2Y2eTFGNUxvRG9PNWpScStDSHZBSDRBbXg0U2pjM3JGMEdyMUF1bnZwM1BraVYrK0JsQTA1NGR1R2M3cHA5Yk9PczlSRllnZ1hxMk1YMDdHOHE3OE55VUZsRXM4Tnkzc2M3SFJzbDVpQlJUL0pNMTg4VUd1R3V1TkJFOVYyQUFOTE13M09rRjh4b3MvVmVZcWIvMXBzS0RGN08zNEwzRHAzelhNUm9uMEQrSzNYaWlvUTBGWHVuYlNlejJZQytCU2tuell0UUY4M1FsVmx0Y0NuN2hHc2RXRjdyMUZZb1NUcDR5NjZpcjNNVmdjNTAyTG5ad281Y0M0aFphbU9iN1dOeHBGTHZrVjNWTUJQSkdGRDM3czJDNFljUVJWMWFZZWlFdHNCemlvVHlpbDlQbXF1TUNkdXBXbXBNMnlNbTJUVXBMNW1jcm16NWd6cGhiTUw0YlJqcFFtTzl6Z2R4WmE4QktybEtTOC9qMEtRQTRqdXN0UThhZkc3RUk5aWZXa0xuUXJTSExLdVEyZzN0eFV5ZDF0ZWRUWGV2TzQveFVSUmNxTnB4bCtaNUx0MW1OQ2lHVlRBNzRuSHNUK3RJbjNMaUUxQ1RsdzlGOFRhVHpqNkliWi9uL2Fnc25WeDlQbVZQdC0tNGltYjdLV0JNS29NR3NubVlYM2dOdz09--a9bfda85b047e7403e0c1ece7dcbfa8f10eb5e63; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Feb+14+2025+21%3A48%3A09+GMT%2B0100+(Central+European+Standard+Time)&version=202312.1.0&browserGpcFlag=0&isIABGlobal=false&consentId=182618080&interactionCount=4&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2CC0005%3A0%2CV2STACK42%3A0%2CC0015%3A0%2CC0035%3A0&genVendors=V2%3A0%2CV1%3A0%2C&geolocation=IT%3B72&AwaitingReconsent=false; banners_ui_state=PENDING
    """

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