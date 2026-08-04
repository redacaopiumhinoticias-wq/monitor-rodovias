import requests
import time
from datetime import datetime, timezone, timedelta

# ==========================================
# CONFIGURE COM OS SEUS DADOS AQUI:
# ==========================================
TELEGRAM_TOKEN = "8675469110:AAHTggtzuhJPJAT7NB75nlFrzdaJpiboBV0"
CHAT_ID = "885516854"

# Área de cobertura (250 KM ao redor de Piumhi-MG)
BOTTOM_LEFT = "-22.7,-48.2"
TOP_RIGHT = "-18.2,-43.7"

# URL de integração do Waze / Google Maps
WAZE_URL = f"https://www.waze.com/row-rtserver/web/TGeoRSS?left={BOTTOM_LEFT.split(',')[1]}&bottom={BOTTOM_LEFT.split(',')[0]}&right={TOP_RIGHT.split(',')[1]}&top={TOP_RIGHT.split(',')[0]}&types=alerts"

# Lista em memória para evitar o envio de alertas repetidos
alertas_enviados = set()

def enviar_notificacao_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": texto, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar no Telegram: {e}")

def verificar_rodovias():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resposta = requests.get(WAZE_URL, headers=headers, timeout=10)
        dados = resposta.json()
        alertas = dados.get('alerts', [])

        for alerta in alertas:
            id_alerta = alerta.get('uuid')
            tipo = alerta.get('type')        # ACCIDENT, HAZARD, ROAD_CLOSED, etc.
            subtipo = alerta.get('subtype', 'Alerta na Pista')
            rua = alerta.get('street', 'Rodovia não identificada')
            cidade = alerta.get('city', 'Região de Piumhi/MG')
            localizacao = alerta.get('location', {})

            # Filtra por acidentes, perigos/buracos, obras ou bloqueios de pista
            if tipo in ["ACCIDENT", "HAZARD", "ROAD_CLOSED", "CONSTRUCTION"] and id_alerta not in alertas_enviados:
                
                # Conversão do horário do relato para o fuso horário do Brasil (UTC-3)
                pub_millis = alerta.get('pubMillis', 0)
                data_utc = datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
                data_brasil = data_utc.astimezone(timezone(timedelta(hours=-3)))
                hora_formatada = data_brasil.strftime('%H:%M:%S')
                
                # Cálculo do tempo decorrido desde o registro
                agora = datetime.now(timezone(timedelta(hours=-3)))
                minutos_atras = max(0, int((agora - data_brasil).totalseconds() // 60))

                # Coordenadas geográficas para gerar o link do Google Maps
                lat, lon = localizacao.get('y'), localizacao.get('x')
                link_gmaps = f"https://www.google.com/maps?q={lat},{lon}"

                # Dicionário de tradução dos alertas comuns
                traducoes = {
                    "HAZARD_ON_ROAD_POT_HOLE": "🕳️ Buraco na pista",
                    "HAZARD_ON_SHOULDER_CAR_STOPPED": "🚗 Veículo parado no acostamento",
                    "HAZARD_ON_ROAD_CAR_STOPPED": "⚠️ Veículo quebrado na pista",
                    "ACCIDENT_MAJOR": "💥 Acidente Grave",
                    "ACCIDENT_MINOR": "🚗 Colisão / Acidente Leve",
                    "HAZARD_ON_ROAD_OBJECT": "📦 Objeto/Obstáculo na pista",
                    "CONSTRUCTION": "🚧 Obras na rodovia",
                    "ROAD_CLOSED_HAZARD": "🚫 Pista Interditada"
                }

                detalhe_final = traducoes.get(subtipo, subtipo.replace("_", " ").title())

                # Montagem do texto formatado enviado para o Telegram
                mensagem = (
                    f"🚨 *ALERTA NAS RODOVIAS*\n\n"
                    f"📍 *Local:* {rua} ({cidade})\n"
                    f"⚠️ *Ocorrência:* {detalhe_final}\n"
                    f"🕒 *Relatado às:* {hora_formatada} (há {minutos_atras} min)\n\n"
                    f"🗺️ [Ver local exato no Google Maps]({link_gmaps})"
                )

                enviar_notificacao_telegram(mensagem)
                alertas_enviados.add(id_alerta)

    except Exception as e:
        print(f"Erro ao checar dados das rodovias: {e}")

# Execução automática contínua
print("Sistema de monitoramento ativo na MG-050, MG-341 e região...")
while True:
    verificar_rodovias()
    time.sleep(300) # Checa por novas ocorrências a cada 5 minutos (300 segundos)
