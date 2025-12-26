import requests
import json
import time
import random
from collections import Counter
import logging
from datetime import datetime

def setup_logging():
    """Configuro basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_sonny_angel_sellers(min_price=12.0, max_price=50.0, max_retries=3):
    """
    Scraper per utenti che vendono piu' Sonny Angels in un certo range di prezzo. TRA 12 E 50 SONO I SELLERS POTENZIALMENTE AFFIDABILI, CON I POTENZIALI SCAMMER è STATO FATTO UN ALTRO SCRIPT LEGGERMENTE DIVERSO
    returna utenti che hanno messo in vendita almeno 2 articoli.
    """
    setup_logging()
    
    base_url = "https://www.vinted.it/api/v2/catalog/items"
    user_listings_count = Counter()
    items_per_page = 96
    num_pages = 10  # numero di pagine da scansionare, limite del server, 96 per pagina e MAX 10 PAGINE, attualmente non permette oltre il server.
    
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",    #nel caso degli scammer ho usato più user agent a rotazione
        "accept": "application/json",
        "accept-language": "it-IT",
    }
    
    # INSERIRE MANUALMENTE IL COOKIE DI VINTED QUI SOTTO OGNI VOLTA PRIMA DI ESEGUIRE LO SCRIPT, DA DEVTOOL DI CHROME
    cookies = {
        'cookie': 'v_udt=Sllxd2dwSGNjZVdkSkxsYUlFYko5dE15OEltSC0tMmdzanBUWVFhYUdOSnVjYS0tbEVLMmQ3M2VlOGRJaHNTOVUzd3VVQT09; anonymous-locale=it-fr; domain_selected=true; OptanonAlertBoxClosed=2025-02-15T00:54:10.196Z; eupubconsent-v2=CQM3e1gQM3e1gAcABBENBcFgAAAAAAAAAChQAAAAAAFBIIIACAAFwAUABUADgAHgAQQAyADUAHgARAAmABVADeAHoAPwAhIBDAESAI4ASwAmgBWgDDgGUAZYA2QB3wD2APiAfYB-gEAAIpARcBGACNAFBAKgAVcAuYBigDRAG0ANwAcQBDoCRAE7AKHAUeApEBTYC2AFyALvAXmAw0BkgDJwGXAM5gawBrIDYwG3gN1AcmA5cB44D2gIQgQvCAHQAHAAkAHOAQcAn4CPQEigJWATaAp8BYQC8gGIAMWgZCBkYDRgGpgNoAbcA3QB5QD5AH7gQEAgZBBEEEwIMAQrAhcOAYAAIgAcAB4AFwASAA_ADQAOcAdwBAICDgIQAT8AqABegDpAIQAR6AkUBKwCYgEygJtAUgApMBXYC1AF0AMQAYsAyEBkwDRgGmgNTAa8A2gBtgDbgHHwOdA58B5QD4gH2wP2A_cCB4EEQIMAQbAhWOglAALgAoACoAHAAQAAugBkAGoAPAAiABMACrAFwAXQAxABvAD0AH6AQwBEgCWAE0AKMAVoAwwBlADRAGyAO8Ae0A-wD9gIoAjABQQCrgFiALmAXkAxQBtADcAHEAOoAh0BF4CRAEyAJ2AUOAo-BTQFNgKsAWKAtgBcAC5AF2gLvAXmAvoBhoDHgGSAMnAZVAywDLgGcgNVAawA28BuoDiwHJgOXAeOA9oB9YEAQIWkACYACAA0ADnALEAj0BNoCkwF5ANTAbYA24Bz4DygHxAP2AgeBBgCDYEKyEBwABYAFAAXABVAC4AGIAN4AegBHADvAIoASkAoIBVwC5gGKANoAdSBTQFNgLFAWiAuABcgDJwGcgNVAeOBC0lAiAAQAAsACgAHAAeABEACYAFUALgAYoBDAESAI4AUYArQBsgDvAH4AVcAxQB1AEOgIvASIAo8BYoC2AF5gMnAZYAzkBrADbwHtAQPJADwALgDuAIAAVABHoCRQErAJtAUmAxYBuQDygH7gQRAgwUgbgALgAoACoAHAAQQAyADQAHgARAAmABSACqAGIAP0AhgCJAFGAK0AZQA0QBsgDvgH2AfoBFgCMAFBAKuAXMAvIBigDaAG4AQ6Ai8BIgCdgFDgKbAWKAtgBcAC5AF2gLzAX0Aw0BkgDJ4GWAZcAzmBrAGsgNvAbqA5MB44D2gIQgQtKAIQALgAkAEcAOcAdwBAACRAFiANeAdsA_4CPQEigJiATaApABT4CuwF0ALyAYsAyYBqYDXgHlAPigfsB-4EDAIHgQTAgwBBsCFYAAA.YAAAAAAAAAAA; OTAdditionalConsentString=1~; anon_id=2c39e9db-c21f-469d-95f2-05a91ec9121b; v_uid=182618080; v_sid=b1fa17d3-1739580855; anon_id=2c39e9db-c21f-469d-95f2-05a91ec9121b; access_token_web=eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhcHBfaWQiOjQsImNsaWVudF9pZCI6IndlYiIsImF1ZCI6ImZyLmNvcmUuYXBpIiwiaXNzIjoidmludGVkLWlhbS1zZXJ2aWNlIiwic3ViIjoiMTgyNjE4MDgwIiwiaWF0IjoxNzM5NjMzNTgzLCJzaWQiOiJiMWZhMTdkMy0xNzM5NTgwODU1Iiwic2NvcGUiOiJ1c2VyIiwiZXhwIjoxNzM5NjQwNzgzLCJwdXJwb3NlIjoiYWNjZXNzIiwiYWN0Ijp7InN1YiI6IjE4MjYxODA4MCJ9LCJhY2NvdW50X2lkIjoxMjU1NjI2MzJ9.lpu6_zYeJ-MYMJ0mrDiYpM_YFpEU8s7h5l9kJE0xO-2TNI59pFJBcs7HoH6MRRpfmKlBNvUpmellsON1EH6GnHTMdyvsDEAt7RHVgm3TlmyFhdRQx-9p5Ar3V-yZE_GV5EqgSKb48RJw12rgNmYTBR2qD9kEiITy7_jNYyQaE60-mMso-cDHwKcgdewsjKCZ_U4knRK_Qw-2PxDptgPkU8SErhWHdN44eVhWWAD9hrsAvcn9shNIOY9vaT6K__iKgR5FcRMzeCJh8TK8Lxv2stxKebms34MbyOYrNXmz8TGtPmFV2IeGiZudAHxx4YUBbRutnmQHX_UJ5GwHQUt-XA; refresh_token_web=eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhcHBfaWQiOjQsImNsaWVudF9pZCI6IndlYiIsImF1ZCI6ImZyLmNvcmUuYXBpIiwiaXNzIjoidmludGVkLWlhbS1zZXJ2aWNlIiwic3ViIjoiMTgyNjE4MDgwIiwiaWF0IjoxNzM5NjMzNTgzLCJzaWQiOiJiMWZhMTdkMy0xNzM5NTgwODU1Iiwic2NvcGUiOiJ1c2VyIiwiZXhwIjoxNzQwMjM4MzgzLCJwdXJwb3NlIjoicmVmcmVzaCIsImFjdCI6eyJzdWIiOiIxODI2MTgwODAifSwiYWNjb3VudF9pZCI6MTI1NTYyNjMyfQ.Sxsceey_b5XObu2xKMt2zXFG_EBlFEj-eTKw5iu8jTNmaYiILtJ4I3h4r6o_yn-jcorNU_3D9aKANnL91223d5rasyMnOamsDM_pWYmuDxhEzplN2LzWxI0OXiRHTMMDP3bOgf4SGNDbEf8MjGae9Mj0P0KUJI8cQX5vLv0JOmez8jGJ465uIxc6Elfcvsd-T591oki1G42C3BzeujXCftFXlNu13jXpaCYpwibgJNO9zmo8E2NcFm-gIpwxZBKYGiZ-sZZ8u76GMHAlBo_yO1dyNSfMK_1s-o5QKTzMZYQxBx7zr9zP_woWKbZacIFKkPOQuu_BvCHPiblI2y8Ypg; cf_clearance=J0DyDR8wehm25WqHK3VQJTagEdjEKo05bfQtfcgdry8-1739634404-1.2.1.1-vo2W2KR54cBmBOuwlLE3yL5zlLJcX18KHozE1HkKMEy4toHhCuSod5vzPrQ7kGCRHEMaovlxlWaxDwGXqXJo4zLSBNUGd7DOyPUDGryeUMRr9.VnZ5RqTKcg4BhOTY4kvjcQvicMUuL8.Vt_CRDaUG62FbCxrlD6He6TBSASAvNejqzjOhspGA6FZvVy46d1agVmOBn6CblxmsqklcRqE4rSbHgmNUcMiUufc8eckmxSjXbyOKYYkOtBE2I_eZ8b.sm6RNA4Dt1d_uqhugEhsJ3.5ikN9o4cGKBXcN4Rm3A; OptanonConsent=consentId=182618080&datestamp=Sat+Feb+15+2025+16%3A46%3A44+GMT%2B0100+(Central+European+Standard+Time)&version=202312.1.0&interactionCount=3&isGpcEnabled=0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0003%3A0%2CC0004%3A0%2CC0005%3A0%2CV2STACK42%3A0%2CC0015%3A0%2CC0035%3A0&genVendors=V2%3A0%2CV1%3A0%2C&geolocation=IT%3B72&AwaitingReconsent=false; banners_ui_state=SUCCESS; viewport_size=851; datadome=a_L~xFgg4Aow49J~TbOxe9kx547ehgn8l~uj0lIWbXZqa~~S3usVgO2ri1WXwlnoxWQkHknDiOsv3s0Z681dut7m9xNkGO7GI_lwVV96cwLfycE7BzlSma~uy6JGMZxs; _vinted_fr_session=YS9sVzNUeTN4VHhYWXVKZ2NwRWp2QlM4Z1BMQXNOMUFubWs1aXlQVFViWmZpWi9MT1pCY0ZJYXZJRWpSZFdneFZyTm1NSVFGQzQ5NEE4RkhWYzNWcm1aR096UkphL2k1YkdIOVRvNStwalBCdDMzWXI4VXYvMVUrRENMNmtYSlBoZlB6SXl2Rkl0VE4yd0N3QkVQak42a0VMdFpEaWN2ak4xTXdCdFpmMHBsY3BwUFZFVGFMRWdob2RMUHdHZ1cyNEZNVnB3MHRFZllucnVZQ2lOMkhrVjExUU9DbnlwSVAycEpIdWtNY05LK0hnNGRNS3QwUzgxS1piVWJSQUk5eGhtOG54VmN1SUd1QUYwV1VoQlVRNzE5cGtETzREZ1BtTmdlcWNhRlR2cHdYUVA4UGZNVkRKZC9zSUNDOSt0eE0wRTVLRVRlN3BEdjlRb1dUZXdDL2hSQnRiNVc2UUhwdlUyVnAwRkpUQTJwd0VSZlRxKzh3Vk9FQUgxK2krVUdjREY5SXBRYzZyTjlOcU83eitOcGw2bllqc04vbVJoK1pueXh1OTRuTFpjOUJTY1BTZ2pkRE9TdHVONWwvOTdUR0JadEc1bmJYbFhLUzZpNUJDRmFOR0xpMElCWThNYmx3MXkyeEpNMlJ1c0Z1Nk1HMGJYWVVIckZsQmFuTy9wNmNJMElscEluZkZjU2o5MUFUZzJZSVhEN2JWMGR1a0QrbHM5czd3b3IvQnplS0JrbzE4RHIyQzVrQkNsNDNjT0VObHRTQ25xbGZUYS8wYUtlSEpUV3dlY0kyemNtWmNpWnB6L3lNOVlIMTZJa0hyd3hZZWFMUnpjZjN6eXNFOFpFVzQrdnpTMEFjVllQdDd3a2tjWFZuZGlUNUUyOHBVV01EUC84UWJmU0lhQTU3NFJLNlQrbWxqaDlrZ085aDVaazUvbER2RE0raXBrZEFLSzVEc1EwTU91QlB5eE9lK1dqcW5JWXBBTUlQandIeEQyemJNSDQ5RkNYL0NCcXBhcnllc0VhYk5MRTl4TTMxQm1Fa3J1Z0NLeEoxTHZNc00zRksvdXlvTnEvSytnUWtadnVJdFdrZHZMeExIUEsxUzFLaUdQcGwxa0NsTktvV1dFajdtRjBrTk9YVVlvb01QOEZGcm1WOThyb2Zzczc1ZlVxU01KUFNpTU5CQkkvZmQxMm5DZFVHMno4Z0NDVnpCajV1UmZkd1JpSGM1SU1aVS8yZnZUbkluQWdwU0xkSFJDcnhtTDVZVmt6Vi8zd2QxV0pnaGt0SUNmcGlVNHExT1lwRHNkcHB1aUpNU00vVFF4V3N5ZkZ0U08zUmpFWDN0UjdWRHhhQzBqWHVWbHR3b2ZpYTEzc05zbGRtZFVqNFFLWW9zZUcybEJybU54UWsybnd2RFE1Nit4bWFyL0hxYWtiLzhtOC8xVjUvaXp5WEVoWWhlZkc2bGMyeFVQUmlrb20vamxtRDJaYWU3d0hGOXdaOFkrL0xQWUt6QmpFMW8xTE1QbEphUHU3L2hxdTVMU2lnSnpoR3FTbG1TMzdNNm54OW8zb3c3YnpIRWR0S0h5Y2RJKy9ORDd3MVViY3FDcDAyUHRCZmF4K3FMWldjZThZL2VUY2RkMlNPWlc3TWRvZ1kwczFJeXkxL1ZzNWtDL2oyVGduZU1zVytxOWgxeGdjMEh4K1hLbTBhVDk1NDgvNEdHbG9BVmhSekJ0Z05mT1hOby9adE1QNVNBc0RBZURtTjk4T1ZHTkhwdUJscWxxNlRPS2tlZy9KcnNjdUNKeGtSaHM5L29UdVRvY0lCRkNEWk9ibUdURWxtNHo4a3JGT1FzUjBzeDhPRm9PcVZveHRMcTRxdUx2eE13QTEzOUYvZWVqZWgvYlJjU0I4ZjIwUEsxcm4zakYxc0hMYnNJQXcySmVuT3p2cUxhbzZiMytndjUrSGIwUTFmdkRXRC9yY1N0NlNUazl6aTJJcU1KY2ZmQjdmblJKMGwrZjFxekc5ZHhuK0ZnVHlWVUM2N25vbkJGS2k3a0p2L3FJaGU2OFZPRUduUHZzSjM3RjB0N1FHMnMwT1dNODZOYzhqYnBjVjE0Z0FJckcvUzNHdU1uZGl5VU9BT2U3Y0JLNERYc3pBL1QzRTlqUGRqZ08wOS9wdG9WOWJTU1EweUJTT1FYY2ZMYS9jeE9IZENTOUhvNGJoemM1c1o4eUs3OENGanRGWFFNN0RVMkpWaTlvV3F6WThzKzkwRVBUbHM3ano4SUphS2RteTBDUjNlWWZHV0FUTWhKR0JHVnBuQWZrSmlQVU9aYkVLRS9DZFMvaUNzVU1uY21qTWdRVnpJMEg5cTJxVHMxbXV1WXI4cjB1YzFtNFNBMkpCclpzTlJuTzAzNlo4WlRDMlhOUUIxdFVTNUNYbzgzOFEydHRZZE5KMVFjMnF4QXN4RE43VVFCR3hwMjRvbUV3SDlzb3hTOFBSOEw4V0hWSmJUdStIWmpBSWxZN0JEVXZXMUpmWS95a09WRUl1M1M5ZEdBajc3Q2VXTmhXNDRmSUpCdTd3eHM5SDlxY0txUzEvdFFTYzcwcmtucWpoeG83OFdqek5PbThOa1FRcTBhUmw5SXI2ZXNma3pjSVd4TnZOdGF1T2swTmhuTDcxUS0tV3V4TVU0UHNOeVFDR0d1dmJVVFU5dz09--88d75f31d137c11d048113e0720db0d9c54f05b1'  # Insert your Vinted cookie here
    }
    
    if not cookies['cookie']:
        logging.error("Please set your Vinted cookie before running")
        return {}
    
    # Scrape all pages
    for page in range(1, num_pages + 1):
        logging.info(f"Scanning page {page}")
        
        params = {
            "search_text": "sonny+angels",
            "price_from": min_price,
            "price_to": max_price,
            "page": page,
            "per_page": items_per_page,
            "currency": "EUR",
            "order": "newest_first"
        }
        
        # provo a fare la richiesta con retry in caso di fallimento
        for attempt in range(max_retries):
            try:
                response = session.get(
                    base_url,
                    params=params,
                    headers=headers,
                    cookies=cookies,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                # Processa items codesta pagina
                items = data.get("items", [])
                if not items:
                    logging.info("No more items found")
                    return {k: v for k, v in user_listings_count.items() if v >= 2}
                
                # Count listings per user
                for item in items:
                    if "user" in item and "id" in item["user"]:
                        user_id = item["user"]["id"]
                        user_listings_count[user_id] += 1
                
                break  # va alla pagina successiva se tutto ok
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to get page {page}: {e}")
                    return {k: v for k, v in user_listings_count.items() if v >= 2}
                time.sleep(2 ** attempt + random.uniform(1, 3))
        
        # Rispetta rate limits o mi bannano malamente
        time.sleep(random.uniform(2, 4))
    
    # Returna solo utenti con almeno 2 listings; con gli scammer facevo diversamente, consideravo solo quelli con molti piu listings!
    return {k: v for k, v in user_listings_count.items() if v >= 2}

if __name__ == "__main__":
    # Get and display results
    seller_data = get_sonny_angel_sellers()
    
    print("\nSellers with multiple Sonny Angels listings:")
    print("User ID : Number of listings")
    print("-" * 30)
    
    for user_id, count in sorted(seller_data.items(), key=lambda x: x[1], reverse=True):
        print(f"{user_id}: {count}")