import html
import urllib.parse
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
TÁBULA QUADRADA — BOT JORNALÍSTICO AUTÔNOMO MULTIFONTES v3.0
Foco Principal: Jogos de Tabuleiro, Financiamento Coletivo, TCG e RPGs Analógicos.
================================================================================
"""

import os
import io
import sys
import json
import re
import random
import time
import argparse
from datetime import datetime
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

import ssl
import ftplib

# Configurações de ambiente e credenciais
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_HISTORY_FILE = os.path.join(DATA_DIR, "published_news_history.json")

FTP_HOST = os.environ.get("FTP_HOST", "108.167.151.39")
FTP_USER = os.environ.get("FTP_USER", "tabula71")
FTP_PASS = os.environ.get("FTP_PASS", "ElUrRwEflRwF82465@")
SITE_URL = os.environ.get("SITE_URL", "https://tabulaquadrada.com.br")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE



if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ------------------------------------------------------------------------------
# 1. MAPEAMENTO DE FONTES POR CATEGORIA E PESO EDITORIAL
# ------------------------------------------------------------------------------

SOURCES_CONFIG = [
    # ==========================================================================
    # 0. CANAL OFICIAL NO YOUTUBE (VÍDEOS REGULARES DE TABULEIRO: PESO 5)
    # ==========================================================================
    {
        "name": "Tábula Quadrada (YouTube)",
        "category": "videos",
        "type": "youtube_channel",
        "channel_id": "UCln311I2_2yP7JdJ3coiskg",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCln311I2_2yP7JdJ3coiskg",
        "weight": 5,
        "note": "Canal oficial do Tábula Quadrada no YouTube: unboxings de jogos de tabuleiro, gameplays e coberturas."
    },

    # ==========================================================================
    # A. JOGOS DE TABULEIRO — NACIONAIS (PESO 5 - MÁXIMA PRIORIDADE)
    # ==========================================================================
    {
        "name": "Devir Brasil",
        "category": "jogos-de-tabuleiro",
        "type": "rss",
        "url": "https://devir.com.br/feed/",
        "weight": 5,
        "note": "Editora oficial de Catan, Carcassonne, Arnak, King of Tokyo e lançamentos no Brasil."
    },
    {
        "name": "Meeple BR Jogos",
        "category": "jogos-de-tabuleiro",
        "type": "rss",
        "url": "https://meeplebr.com/feed/",
        "weight": 5,
        "note": "Catálogo oficial nacional, pré-vendas e anúncios de jogos de tabuleiro da MeepleBR."
    },
    {
        "name": "PaperGames",
        "category": "jogos-de-tabuleiro",
        "type": "rss_clean",
        "url": "https://papergames.com.br/feed/",
        "weight": 5,
        "note": "Editora de party games, jogos de cartas rápidos e lançamentos internacionais no Brasil."
    },

    # ==========================================================================
    # B. JOGOS DE TABULEIRO — PORTAIS INTERNACIONAIS ESPECIALIZADOS (PESO 5)
    # ==========================================================================
    {
        "name": "Meeple Mountain",
        "category": "jogos-de-tabuleiro",
        "type": "rss",
        "url": "https://www.meeplemountain.com/feed/",
        "weight": 5,
        "note": "Artigos editoriais, matérias de design e novidades de jogos de tabuleiro."
    },
    {
        "name": "Punchboard",
        "category": "jogos-de-tabuleiro",
        "type": "rss",
        "url": "https://punchboard.co.uk/feed/",
        "weight": 5,
        "note": "Análises detalhadas, fotografias de componentes e prévias de jogos de tabuleiro."
    },

    # ==========================================================================
    # C. JOGOS DE TABULEIRO — GRANDES EDITORAS CONSAGRADAS (PESO 5)
    # ==========================================================================
    {
        "name": "Leder Games",
        "category": "jogos-de-tabuleiro",
        "type": "atom",
        "url": "https://ledergames.com/blogs/news.atom",
        "weight": 5,
        "note": "Criadores dos aclamados Root, Oath, Vast, Arcs e Kart."
    },
    {
        "name": "Stonemaier Games",
        "category": "jogos-de-tabuleiro",
        "type": "rss",
        "url": "https://stonemaiergames.com/feed/",
        "weight": 5,
        "note": "Editora de Wingspan, Scythe, Wyrmspan e artigos de design de Jamey Stegmaier."
    },
    {
        "name": "Restoration Games",
        "category": "jogos-de-tabuleiro",
        "type": "rss",
        "url": "https://restorationgames.com/feed/",
        "weight": 5,
        "note": "Estúdio responsável pela aclamada linha Unmatched e Return to Dark Tower."
    },

    # ==========================================================================
    # D. FINANCIAMENTO COLETIVO (CROWDFUNDING DE TABULEIRO - PESO 4)
    # ==========================================================================
    {
        "name": "Catarse Jogos",
        "category": "financiamento-coletivo",
        "type": "catarse_explore",
        "url": "https://www.catarse.me/pt/explore?ref=ctrse_explore_pgsearch&category_id=1",
        "weight": 4,
        "note": "Projetos de financiamento coletivo de jogos de tabuleiro e RPG em campanha ativa no Catarse."
    },

    # ==========================================================================
    # E. JORNALISMO GERAL, TCG E RPG (EQUILIBRADO - PESO 1)
    # ==========================================================================
    {
        "name": "Tabletop Gaming News",
        "category": "misto",
        "type": "rss",
        "url": "https://www.tabletopgamingnews.com/feed/",
        "weight": 1,
        "note": "Cobertura abrangente de novidades do mercado analógico mundial e lançamentos."
    },
    {
        "name": "Dicebreaker",
        "category": "misto",
        "type": "rss_filtered",
        "url": "https://www.dicebreaker.com/feed",
        "weight": 1,
        "note": "Jornalismo internacional analógico (jogos de tabuleiro, cartas e RPG)."
    },
    {
        "name": "MTG Rocks (Magic: The Gathering)",
        "category": "tcg",
        "type": "rss",
        "url": "https://mtgrocks.com/feed/",
        "weight": 1,
        "note": "Notícias do circuito mundial de Magic, spoilers de coleções e formatos."
    },
    {
        "name": "RetroPunk Publicações",
        "category": "rpg",
        "type": "rss",
        "url": "https://retropunk.com.br/editora/feed/",
        "weight": 1,
        "note": "Editora nacional de Savage Worlds, RPGs narrativos e literatura fantástica."
    },
    {
        "name": "Wargamer",
        "category": "wargames",
        "type": "rss",
        "url": "https://www.wargamer.com/feed",
        "weight": 1,
        "note": "Wargames analógicos, miniaturas e Warhammer."
    },
    {
        "name": "Bell of Lost Souls",
        "category": "misto",
        "type": "rss_filtered",
        "url": "https://www.belloflostsouls.net/feed",
        "weight": 1,
        "note": "Cobertura do universo de jogos de mesa e fantasia."
    },
    {
        "name": "Rascal News",
        "category": "rpg",
        "type": "rss",
        "url": "https://www.rascal.news/rss/",
        "weight": 1,
        "note": "Jornalismo independente sobre RPGs de mesa e cenários autorais."
    }
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml,application/rss+xml,application/atom+xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}

BOARD_GAME_KEYWORDS = [
    'board game', 'boardgame', 'tabletop', 'jogo de tabuleiro', 'jogos de tabuleiro',
    'eurogame', 'card game', 'party game', 'meeple', 'sleeves', 'miniaturas',
    'catan', 'arnak', 'wingspan', 'scythe', 'root', 'unmatched', 'essen',
    'spiel des jahres', 'bgg', 'dice tower', 'financiamento coletivo', 'kickstarter',
    'gamefound', 'tabuleiro', 'deckbuilding', 'colocação de peças', 'alocação de trabalhadores'
]

# ------------------------------------------------------------------------------
# 2. FUNÇÕES AUXILIARES DE REQUISIÇÃO E LIMPEZA
# ------------------------------------------------------------------------------

def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def sanitize_travessao(text):
    if not text:
        return ""
    return text.replace("â€”", "—").replace("â€“", "–").replace("&mdash;", "—").replace("&ndash;", "–")

def load_history(history_file=None):
    if history_file is None: history_file = DEFAULT_HISTORY_FILE
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history, history_file=None):
    if history_file is None: history_file = DEFAULT_HISTORY_FILE
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)



def is_youtube_short(video_id):
    if not video_id:
        return False
    try:
        import urllib.request
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(NoRedirect)
        req = urllib.request.Request(
            f"https://www.youtube.com/shorts/{video_id}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
        )
        try:
            res = opener.open(req, timeout=6)
            return res.status == 200
        except urllib.error.HTTPError as e:
            return e.code == 200
    except Exception:
        return False

def is_short_form_content(title, desc="", url=""):
    combined = (str(title) + " " + str(desc) + " " + str(url)).lower()
    if re.search(r'(#shorts?|#reels?|#stories|#tiktok|#shortsvideo)\b', combined):
        return True
    if re.search(r'\b(shorts?|reels?|stories|story|tiktok)\b', str(title).lower()):
        return True
    if re.search(r'(youtube\.com/shorts/|instagram\.com/reels?/|instagram\.com/stories/|tiktok\.com/@)', str(url)):
        return True
    if "youtube.com" in str(url) and len(str(desc).strip()) < 80:
        return True
    return False

def parse_youtube_description_py(desc, title):
    lines = desc.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    intro_lines = []
    ficha_lines = []
    component_lines = []
    outro_lines = []
    current_section = 'intro'

    for line in lines:
        trim = line.strip()
        if not trim:
            continue
        upper = trim.upper()
        if re.search(r'FICHA\s+T[ÉE]CNICA', upper):
            current_section = 'ficha'
            continue
        elif re.search(r'(?:PRINCIPAIS\s+)?COMPONENTES', upper):
            current_section = 'componentes'
            continue
        elif re.search(r'(?:CONHE[ÇC]A O BLOG|INSCREVA-SE|SIGA NOSSAS REDES|APOIO:)', upper) or trim.startswith('#'):
            current_section = 'footer'
            continue

        if current_section == 'intro':
            if not re.search(r'^(?:Vídeo com apoio|Apoio:|Parceiro:)', trim, re.I):
                intro_lines.append(trim)
        elif current_section == 'ficha':
            ficha_lines.append(trim)
        elif current_section == 'componentes':
            component_lines.append(trim)
        elif current_section == 'footer':
            if len(trim) > 25 and not trim.startswith('http') and not trim.startswith('#'):
                outro_lines.append(trim)

    game = {}
    for fl in ficha_lines:
        m = re.match(r'^Jogo\s*:\s*(.+)$', fl, re.I)
        if m: game['name'] = m.group(1).strip()
        m = re.match(r'^(?:Caixa|Edi[çc][ãa]o)\s*:\s*(.+)$', fl, re.I)
        if m: game['edition'] = m.group(1).strip()
        m = re.match(r'^Editora\s+original\s*:\s*(.+)$', fl, re.I)
        if m: game['publisher_original'] = m.group(1).strip()
        m = re.match(r'^(?:Publica[çc][ãa]o\s+no\s+Brasil|Editora\s+Nacional|Editora)\s*:\s*(.+)$', fl, re.I)
        if m: game['publisher'] = m.group(1).strip()
        m = re.match(r'^Designers?\s*:\s*(.+)$', fl, re.I)
        if m: game['designer'] = m.group(1).strip()
        m = re.match(r'^Jogadores\s*:\s*(.+)$', fl, re.I)
        if m: game['players'] = m.group(1).strip()
        m = re.match(r'^Dura[çc][ãa]o\s*:\s*(.+)$', fl, re.I)
        if m: game['playtime'] = m.group(1).strip()
        m = re.match(r'^Idade(?:\s*recomendada)?\s*:\s*(.+)$', fl, re.I)
        if m: game['age'] = m.group(1).strip()
        m = re.match(r'^Mec[âa]nicas?\s*:\s*(.+)$', fl, re.I)
        if m: game['mechanics'] = m.group(1).strip()
        m = re.match(r'^Tema\s*:\s*(.+)$', fl, re.I)
        if m: game['theme'] = m.group(1).strip()
        m = re.match(r'^Formato\s*:\s*(.+)$', fl, re.I)
        if m: game['format'] = m.group(1).strip()
        m = re.match(r'^Sleeves?\s*:\s*(.+)$', fl, re.I)
        if m: game['sleeves'] = m.group(1).strip()

    if not game.get('publisher') and game.get('publisher_original'):
        game['publisher'] = game['publisher_original']

    if not game.get('name'):
        m = re.search(r'Unboxing(?:\s+T[áa]bula)?\s*[\|\-:]\s*(.+)', title, re.I)
        game['name'] = m.group(1).strip() if m else title

    return {
        'intro_paragraphs': intro_lines,
        'components': component_lines,
        'outro_paragraphs': outro_lines,
        'game': game
    }

def is_already_published(link, history, existing_slugs):
    if link in history:
        return True
    return False

# ------------------------------------------------------------------------------
# 3. INVESTIGAÇÃO PROFUNDA DE CONTEÚDO DO ARTIGO
# ------------------------------------------------------------------------------

def translate_to_pt(text):
    if not text:
        return ""

    # Remove tags promocionais ou de anúncios
    text = re.sub(r'\s*[\(\[]Sponsored[\)\]]', '', text, flags=re.I)
    text = re.sub(r'\s*[\(\[]Ad[\)\]]', '', text, flags=re.I)
    text = text.strip()
    if not text:
        return ""

    # 1. Funções internas de tradução multi-motor
    def _call_gtx(q_str):
        try:
            url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=pt&dt=t'
            data = urllib.parse.urlencode({'q': q_str}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*'
            })
            with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
                res = json.loads(r.read().decode('utf-8'))
                if res and isinstance(res, list) and len(res) > 0 and isinstance(res[0], list):
                    parts = [part[0] for part in res[0] if part and len(part) > 0 and part[0]]
                    trans = ''.join(parts).strip()
                    if trans:
                        return trans
        except Exception:
            pass
        return None

    def _call_clients5(q_str):
        try:
            url = 'https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=pt&q=' + urllib.parse.quote(q_str[:1500])
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                res = json.loads(r.read().decode('utf-8'))
                if isinstance(res, list) and len(res) > 0 and isinstance(res[0], str):
                    return res[0].strip()
        except Exception:
            pass
        return None

    def _call_mymemory(q_str):
        try:
            url = 'https://api.mymemory.translated.net/get?q=' + urllib.parse.quote(q_str[:400]) + '&langpair=en|pt-BR'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6, context=ctx) as r:
                data = json.loads(r.read().decode('utf-8'))
                trans = data.get('responseData', {}).get('translatedText')
                if trans and not trans.startswith('MYMEMORY WARNING') and len(trans.strip()) > 2:
                    return html.unescape(trans).strip()
        except Exception:
            pass
        return None

    # 2. Dividir em blocos caso o parágrafo seja muito longo (> 2000 caracteres)
    chunks = []
    if len(text) > 2000:
        sentences = re.split(r'(\.\s+|\n+)', text)
        curr = ""
        for s in sentences:
            if len(curr + s) < 1800:
                curr += s
            else:
                if curr: chunks.append(curr)
                curr = s
        if curr: chunks.append(curr)
    else:
        chunks = [text]

    translated_chunks = []
    for c in chunks:
        c_clean = c.strip()
        if not c_clean:
            continue
        # Motor 1: Google GTX POST (rápido, ilimitado, alta precisão)
        t = _call_gtx(c_clean)
        if not t:
            # Motor 2: Google Clients5 fallback
            t = _call_clients5(c_clean)
        if not t:
            # Motor 3: MyMemory fallback
            t = _call_mymemory(c_clean)
        if not t:
            t = c_clean
        translated_chunks.append(t)

    res = " ".join(translated_chunks) if translated_chunks else text

    # 3. Pós-processamento de padronização editorial brasileira do universo analógico
    terms = {
        r'\bdiário do desenvolvedor\b': 'Diário de Desenvolvimento',
        r'\bdiário do designer\b': 'Diário de Desenvolvimento',
        r'\bdeveloper diary\b': 'Diário de Desenvolvimento',
        r'\bdesigner diary\b': 'Diário de Desenvolvimento',
        r'\bdev diary\b': 'Diário de Desenvolvimento',
        r'\btabletop roleplaying game\b': 'RPG de mesa',
        r'\btabletop roleplaying games\b': 'RPGs de mesa',
        r'\btabletop roleplay\b': 'RPG de mesa',
        r'\broleplaying game\b': 'RPG',
        r'\broleplaying games\b': 'RPGs',
        r'\bboard game\b': 'jogo de tabuleiro',
        r'\bboard games\b': 'jogos de tabuleiro',
        r'\btrading card game\b': 'card game colecionável (TCG)',
        r'\btrading card games\b': 'card games colecionáveis (TCGs)',
        r'\bcollectible card game\b': 'jogo de cartas colecionáveis',
        r'\bcard game\b': 'jogo de cartas',
        r'\bcard games\b': 'jogos de cartas',
        r'\bnew expansion\b': 'nova expansão',
        r'\bexpansion\b': 'expansão',
        r'\bexpansions\b': 'expansões',
        r'\bcrowdfunding\b': 'financiamento coletivo',
        r'\bparty game\b': 'party game festivo',
        r'\ballows players to\b': 'permite que os jogadores',
        r'\bwill enable players to\b': 'permitirá aos jogadores',
        r'\bdeck-building\b': 'construção de baralho (deckbuilding)',
        r'\bdeckbuilding\b': 'construção de baralho (deckbuilding)',
        r'\bworker placement\b': 'alocação de trabalhadores',
        r'\bminiatures\b': 'miniaturas',
        r'\bbox set\b': 'caixa completa',
        r'\bstandalone game\b': 'jogo independente',
        r'\bdungeon crawler\b': 'dungeon crawler de exploração',
        r'\brulebook\b': 'livro de regras',
        r'\btabletop\b': 'mesa analógica',
        r'\bspellcaster\b': 'conjurador de magias',
        r'\bspellcasting\b': 'lançamento de magias',
        r'\bgame master\b': 'mestre de jogo (GM)',
        r'\bgames master\b': 'mestre de jogo (GM)',
        r'\bgame design\b': 'design de jogos',
        r'\bgame designer\b': 'designer de jogos',
        r'\brelease date\b': 'data de lançamento'
    }
    for pat, pt in terms.items():
        res = re.sub(pat, pt, res, flags=re.IGNORECASE)

    return res.strip()


def investigate_article_content(url, raw_text=""):
    data = {
        "cover_image": "",
        "body_images": [],
        "paragraphs": [],
        "list_items": []
    }
    html = fetch_url(url)
    if not html:
        paragraphs = [p.strip() for p in raw_text.split("\n") if len(p.strip()) > 60]
        data["paragraphs"] = paragraphs[:4]
        return data

    soup = BeautifulSoup(html, 'html.parser')

    # Imagem de capa via og:image
    og_img = soup.find('meta', property='og:image')
    if og_img and og_img.get('content'):
        data['cover_image'] = og_img['content']
    elif soup.find('meta', attrs={'name': 'twitter:image'}):
        data['cover_image'] = soup.find('meta', attrs={'name': 'twitter:image'}).get('content', '')

    # Extrair corpo principal
    article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|post|article|body', re.I))
    if not article:
        article = soup

    # Imagens secundárias de componentes e gameplay
    for img in article.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original') or ''
        if not src and img.get('srcset'):
            # pegar maior imagem do srcset
            src_parts = [s.strip().split(' ')[0] for s in img.get('srcset', '').split(',') if s.strip()]
            if src_parts:
                src = src_parts[-1]

        if src and src.startswith('http') and not any(skip in src.lower() for skip in ['avatar', 'logo', 'icon', 'ad', 'pixel', 'author', 'writer', 'profile', 'placeholder']):
            if src != data['cover_image'] and src not in data['body_images']:
                data['body_images'].append(src)
                if len(data['body_images']) >= 8:
                    break

    # Parágrafos substanciais
    for p in article.find_all('p'):
        t = p.get_text().strip()
        if len(t) < 60:
            continue
        if any(skip in t.lower() for skip in ['cookie', 'subscribe', 'newsletter', 'privacy', 'copyright', 'all rights reserved', 'terms of service']):
            continue
        # Ignorar linhas de cabeçalho, autor ou data isoladas
        if re.search(r'^(designer|developer|author|written by|posted by|published by)\b', t, re.I) and len(t) < 120:
            continue
        if re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b', t, re.I) and len(t) < 100:
            continue
        data['paragraphs'].append(t)
        if len(data['paragraphs']) >= 5:
            break

    return data

# ------------------------------------------------------------------------------
# 4. VARREDURA BALANCEADA MULTIFONTES
# ------------------------------------------------------------------------------

def scan_all_sources(history, existing_slugs):
    print("📡 Iniciando varredura balanceada do ecossistema analógico...")
    discovered = []

    # Criar lista ponderada de fontes para rotação equitativa
    weighted_sources = []
    for s in SOURCES_CONFIG:
        w = s.get('weight', 1)
        weighted_sources.extend([s] * w)
    
    # Embaralhar para garantir variedade a cada execução
    random.shuffle(weighted_sources)
    seen_sources = set()

    for src in weighted_sources:
        if src['name'] in seen_sources:
            continue
        seen_sources.add(src['name'])

        print(f"  -> Conectando a {src['name']} [{src['category']}]...")

        if src['type'] in ['rss', 'rss_clean', 'atom', 'rss_filtered']:
            xml_data = fetch_url(src['url'])
            if not xml_data:
                continue

            try:
                xml_data = xml_data.strip()
                # Limpeza de declarações XML mal posicionadas (ex: PaperGames)
                xml_pos = xml_data.find('<?xml')
                if xml_pos > 0:
                    xml_data = xml_data[xml_pos:]

                root = ET.fromstring(xml_data)
                items = root.findall('.//item')
                if not items:
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                for it in items[:6]:
                    title = it.findtext('title') or ''
                    if not title:
                        t_el = it.find('{http://www.w3.org/2005/Atom}title')
                        title = t_el.text if t_el is not None else ''

                    link = it.findtext('link') or ''
                    if not link:
                        l_el = it.find('{http://www.w3.org/2005/Atom}link')
                        if l_el is not None:
                            link = l_el.attrib.get('href', '')

                    desc = it.findtext('description') or ''
                    encoded = it.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or ''

                    # Extrair imagem do enclosure se houver
                    image_url = ""
                    enclosure = it.find('enclosure')
                    if enclosure is not None and 'url' in enclosure.attrib:
                        image_url = enclosure.attrib['url']

                    desc_clean = re.sub(r'<[^>]+>', ' ', desc).strip()
                    title_clean = title.strip()
                    link_clean = link.strip()

                    if not title_clean or not link_clean:
                        continue

                    # FILTRO RIGOROSO ANTI-SHORTS, REELS E STORIES
                    if is_short_form_content(title_clean, desc_clean, link_clean):
                        print(f"     [REVISÃO REJEITOU]: '{title_clean[:45]}' - Formato curto (Shorts/Reels/Stories) rejeitado.")
                        continue

                    if is_already_published(link_clean, history, existing_slugs):
                        continue

                    # Filtro inteligente para fontes mistas (Dicebreaker, Bell of Lost Souls)
                    combined_text = (title_clean + " " + desc_clean).lower()
                    cat = src['category']
                    if src['type'] == 'rss_filtered':
                        has_rpg = any(k in combined_text for k in ['rpg', 'd&d', 'dungeons & dragons', 'roleplaying', 'pathfinder', 'critical role'])
                        has_bg = any(k in combined_text for k in ['board game', 'boardgame', 'jogo de tabuleiro', 'eurogame', 'card game', 'party game', 'meeple', 'essen', 'spiel', 'bgg'])
                        if has_rpg and not has_bg:
                            cat = 'rpg'
                        else:
                            cat = 'jogos-de-tabuleiro'

                    print(f"     🔎 Investigando novidade selecionada: {title_clean[:55]}...")
                    inv_data = investigate_article_content(link_clean, desc + "\n" + encoded)
                    final_cover = inv_data.get('cover_image') or image_url or ""
                    if not final_cover or "default-hero" in str(final_cover):
                        print(f"     [REVISÃO REJEITOU]: '{title_clean[:45]}' - Sem imagem de capa autêntica.")
                        continue
                    body_imgs = inv_data.get('body_images', [])
                    if not body_imgs:
                        print(f"     [REVISÃO REJEITOU]: '{title_clean[:45]}' - Sem imagens de apoio no corpo.")
                        continue
                    discovered.append({
                        "source": src['name'],
                        "source_note": src['note'],
                        "category": cat,
                        "title": title_clean,
                        "link": link_clean,
                        "summary": desc_clean[:360],
                        "cover_image": final_cover,
                        "body_images": inv_data.get('body_images', []),
                        "deep_paragraphs": inv_data.get('paragraphs', []),
                        "list_items": inv_data.get('list_items', []),
                        "is_crowdfunding": (cat == 'financiamento-coletivo')
                    })
                    break # 1 item por fonte na rodada para máxima diversidade

            except Exception as e:
                pass

        elif src['type'] == 'catarse_explore':
            html_data = fetch_url(src['url'])
            if not html_data:
                continue
            try:
                pattern = r'\"project\":\{[^}]*?\"slug\":\"([^\"]+)\",\"title\":\"([^\"]+)\",\"thumbnail\":\"([^\"]+)\"'
                matches = re.findall(pattern, html_data)
                for m in matches[:4]:
                    slug, title, thumb = m[0], m[1], m[2]
                    link = f"https://www.catarse.me/{slug}"
                    if not is_already_published(link, history, existing_slugs):
                        inv_data = investigate_article_content(link)
                        discovered.append({
                            "source": "Catarse Financiamento Coletivo",
                            "source_note": "Campanha nacional de financiamento coletivo em destaque no Catarse.",
                            "category": "financiamento-coletivo",
                            "title": f"[Catarse] {title} – Campanha de Financiamento Coletivo",
                            "link": link,
                            "summary": f"Projeto '{title}' em campanha oficial no Catarse, movimentando a comunidade de jogos de tabuleiro e analógicos no Brasil.",
                            "cover_image": inv_data.get('cover_image') or thumb,
                            "body_images": inv_data.get('body_images', []),
                            "deep_paragraphs": inv_data.get('paragraphs', []),
                            "list_items": [],
                            "is_crowdfunding": True
                        })
                        break
            except Exception:
                pass

    # Ordenar discovered dando preferência primária para Jogos de Tabuleiro e Financiamento Coletivo
    def priority_sort(item):
        if item['category'] == 'jogos-de-tabuleiro':
            return 0
        elif item['category'] == 'financiamento-coletivo':
            return 1
        elif item['category'] == 'tcg':
            return 2
        else:
            return 3

    discovered.sort(key=priority_sort)
    print(f"\n✓ Varredura concluída! {len(discovered)} matérias inéditas de diversas fontes capturadas.")
    return discovered

# ------------------------------------------------------------------------------
# 5. EXECUÇÃO
# ------------------------------------------------------------------------------


# ==============================================================================
# MÓDULO INTELIGENTE: ENRIQUECIMENTO AUTOMÁTICO DE FICHA TÉCNICA (LUDOPEDIA & BGG)
# Sempre que a postagem for exclusiva de um jogo ou destacar um jogo analógico
# ==============================================================================

def search_ludopedia(game_name):
    """
    Busca na Ludopedia e extrai ficha técnica completa:
    jogadores, duração, idade, complexidade, designers, editoras, nota, mecânicas e sleeves.
    """
    search_url = 'https://ludopedia.com.br/search_jogo?search=' + urllib.parse.quote(game_name)
    try:
        req = urllib.request.Request(search_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html_txt = resp.read().decode('utf-8', errors='ignore')
        
        soup = BeautifulSoup(html_txt, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'https?://ludopedia\.com\.br/jogo/[^?#]+'))
        valid_links = []
        for l in links:
            href = l['href']
            if not any(x in href for x in ['/anuncios', '/imagens', '/videos', '/arquivos', '/top', '/comentarios']):
                if href not in valid_links:
                    valid_links.append(href)
        
        if not valid_links:
            return None
        
        game_url = valid_links[0]
        
        req_page = urllib.request.Request(game_url, headers=HEADERS)
        with urllib.request.urlopen(req_page, timeout=10) as resp:
            page_html = resp.read().decode('utf-8', errors='ignore')
            
        p_soup = BeautifulSoup(page_html, 'html.parser')
        
        # 1. Título e Ano
        h1 = p_soup.find('h1')
        title = game_name
        year = ""
        if h1:
            title_a = h1.find('a')
            if title_a:
                title = title_a.get_text().strip()
            small = h1.find('small')
            if small:
                year_match = re.search(r'\d{4}', small.get_text())
                if year_match:
                    year = year_match.group(0)

        # 2. Dados estruturados dos blocos (ludo-fh-dado)
        players = ""
        players_rec = ""
        playtime = ""
        age = ""
        complexity = ""

        for dado in p_soup.select('.ludo-fh-dados > .ludo-fh-dado'):
            rot_el = dado.find(class_='ludo-fh-dado__rot')
            val_el = dado.find(class_='ludo-fh-dado__val')
            if not rot_el or not val_el:
                continue
            rot = rot_el.get_text().strip().lower()
            val = val_el.get_text().strip()

            if 'jogador' in rot:
                players = val
                rec_el = dado.find(class_='ludo-fh-dado__com-txt')
                if rec_el:
                    players_rec = rec_el.get_text().strip()
            elif 'duração' in rot or 'tempo' in rot:
                playtime = val
            elif 'complex' in rot:
                sub_el = dado.find(class_='ludo-fh-dado__sub')
                comp_label = sub_el.get_text().strip() if sub_el else ""
                val_num = val.replace(comp_label, '').strip()
                complexity = f"{comp_label} ({val_num})" if comp_label and val_num else (comp_label or val or "Médio")
            elif 'idade' in rot:
                age = val

        # 3. Notas
        score = None
        nota_el = p_soup.find(class_='ludo-fh-nota__n')
        if nota_el:
            score_txt = nota_el.get_text().strip().replace(',', '.')
            try:
                score = float(score_txt)
            except ValueError:
                pass

        # 4. Designers
        designers = []
        for a in p_soup.find_all('a', href=re.compile(r'/designer/\d+')):
            d_name = a.get_text().strip()
            if d_name and d_name not in designers:
                designers.append(d_name)

        # 5. Editoras
        publishers = []
        for a in p_soup.find_all('a', href=re.compile(r'/editora/\d+')):
            p_name = a.get_text().strip()
            if p_name and p_name not in publishers:
                publishers.append(p_name)

        # 6. Mecânicas
        mechanics = []
        for a in p_soup.find_all('a', href=re.compile(r'/mecanica/\d+')):
            m_text = a.get_text().strip()
            if m_text and m_text.lower() != 'mecânicas' and m_text not in mechanics:
                mechanics.append(m_text)

        # 7. Sleeves
        sleeves = ""
        s_h4 = p_soup.find(lambda tag: tag.name in ['h4', 'h5', 'strong'] and 'sleeves' in tag.get_text().lower())
        if s_h4 and s_h4.find_next_sibling('p'):
            sleeves = s_h4.find_next_sibling('p').get_text().strip()
            sleeves = re.sub(r'\s+', ' ', sleeves)

        # 8. Capa Oficial
        image_url = ""
        og_img = p_soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            image_url = og_img['content'].strip()

        pub_str = publishers[0] if publishers else "Oficial"
        if len(publishers) > 1 and "Brasil" in publishers[0]:
            pub_str = f"{publishers[0]} / {publishers[1]}"

        players_full = players or "1 a 4 jogadores"
        if players_rec:
            players_full += f" ({players_rec})"

        if "—" in complexity or "complexidade" in complexity.lower():
            complexity = "Médio"

        return {
            "title": title,
            "year": int(year) if year and year.isdigit() else 2026,
            "publisher": pub_str,
            "designer": ", ".join(designers[:2]) if designers else "Consagrado",
            "players": players_full,
            "duration": playtime or "45 a 60 min",
            "age": age or "14+",
            "complexity": complexity or "Médio",
            "score": score,
            "score_final": score,
            "mechanics": ", ".join(mechanics[:5]),
            "sleeves": sleeves if sleeves and sleeves.lower() != 'sem informações' else "Não utiliza sleeves",
            "cover_url": image_url,
            "url_ludopedia": game_url,
            "url_bgg": f"https://boardgamegeek.com/geeksearch.php?action=search&q={urllib.parse.quote(title)}",
            "source": "Ludopedia"
        }
    except Exception as e:
        print(f"    [AVISO] Erro na consulta da Ludopedia: {e}")
        return None

def extract_potential_game_names(title):
    candidates = []
    clean = re.sub(r'^(Notícia|Novidade|Anúncio|Financiamento Coletivo|Review|Análise):\s*', '', title, flags=re.I).strip()
    
    quotes = re.findall(r'["\']([^"\']+)["\']', clean)
    candidates.extend(quotes)
    
    split_parts = re.split(r'[:–—\-]\s*', clean)
    if len(split_parts) > 1:
        candidates.append(split_parts[0].strip())
        candidates.append(f"{split_parts[0].strip()}: {split_parts[1].strip()}")
        candidates.append(split_parts[1].strip())
        
    for verb in [' ganha ', ' chega ', ' conquista ', ' recebe ', ' atinge ', ' traz ', ' estreia ', ' entra em ']:
        if verb in clean.lower():
            idx = clean.lower().find(verb)
            candidates.append(clean[:idx].strip())

    prep_matches = re.findall(r'(?:de|sobre|para|em)\s+([A-ZÀ-Ú][a-zA-Z0-9À-ú\s\':&]+)', clean)
    for pm in prep_matches:
        pm_clean = pm.strip()
        pm_clean = re.sub(r'^(novo|nova|o novo|a nova|novos|novas)\s+', '', pm_clean, flags=re.I).strip()
        if len(pm_clean) >= 3:
            candidates.append(pm_clean)

    candidates.append(clean)
    
    seen = set()
    result = []
    for c in candidates:
        c_clean = c.strip(' .:-')
        if len(c_clean) >= 3 and c_clean.lower() not in seen:
            seen.add(c_clean.lower())
            result.append(c_clean)
    return result

def get_complete_game_ficha(game_title):
    cands = extract_potential_game_names(game_title)
    for cand in cands:
        print(f"  🔍 Verificando ficha técnica na Ludopedia/BGG para: '{cand}'...")
        ficha = search_ludopedia(cand)
        if ficha:
            print(f"  ✓ Ficha técnica completa obtida com sucesso: {ficha['title']} ({ficha['year']})")
            return ficha
    return None

def build_technical_sheet_html(game):
    title = html.escape(game.get('title', 'Jogo de Tabuleiro'))
    year = game.get('year', 2026)
    players = html.escape(str(game.get('players', '1 a 4 jogadores')))
    duration = html.escape(str(game.get('duration', '45 a 60 min')))
    age = html.escape(str(game.get('age', '14+')))
    complexity = html.escape(str(game.get('complexity', 'Médio')))
    designer = html.escape(str(game.get('designer', 'Autor consagrado')))
    publisher = html.escape(str(game.get('publisher', 'Oficial')))
    mechanics = html.escape(str(game.get('mechanics', '')))
    sleeves = html.escape(str(game.get('sleeves', '')))
    score = game.get('score_final') or game.get('score')
    url_ludo = game.get('url_ludopedia', '')
    url_bgg = game.get('url_bgg', '')

    score_html = ""
    if score and float(score) > 0:
        score_html = f"""
        <div style="background: rgba(245, 184, 0, 0.15); border: 1px solid rgba(245, 184, 0, 0.4); border-radius: 12px; padding: 6px 14px; text-align: center;">
          <div style="font-size: 0.7rem; color: #f5b800; font-weight: 700; text-transform: uppercase;">Avaliação</div>
          <div style="font-size: 1.3rem; font-weight: 800; color: #fff;">★ {float(score):.1f}</div>
        </div>
        """

    mech_html = ""
    if mechanics:
        mech_html = f'<div style="margin-top: 8px;"><strong>⚙️ Mecânicas Principais:</strong> {mechanics}</div>'

    sleeves_html = ""
    if sleeves and sleeves.lower() != 'não utiliza sleeves':
        sleeves_html = f'<div style="margin-top: 8px;"><strong>🃏 Sleeves (Protetores de Cartas):</strong> {sleeves}</div>'

    links_html = ""
    if url_ludo:
        links_html += f'<a href="{url_ludo}" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; text-decoration: none;">📖 Ver na Ludopedia</a>'
    if url_bgg:
        links_html += f'<a href="{url_bgg}" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 6px; background: #ff5100; color: #fff; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 0.85rem; text-decoration: none;">🎲 Ver no BoardGameGeek (BGG)</a>'

    return f"""
<div class="tq-game-spec-sheet" style="background: linear-gradient(135deg, rgba(245, 184, 0, 0.08) 0%, rgba(20, 20, 28, 0.95) 100%); border: 1px solid rgba(245, 184, 0, 0.35); border-radius: 16px; padding: 26px 28px; margin: 36px 0; box-shadow: 0 12px 32px rgba(0,0,0,0.45);">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:16px;">
    <div>
      <span style="display:inline-block; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:#f5b800; background:rgba(245,184,0,0.15); padding:4px 10px; border-radius:6px; margin-bottom:6px;">Ficha Técnica Completa</span>
      <h3 style="margin:0; font-size:1.45rem; color:#fff; font-weight:700;">{title} <span style="font-size:1rem; color:#9ca3af; font-weight:400;">({year})</span></h3>
    </div>
    {score_html}
  </div>

  <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:20px;">
    <div style="background:rgba(255,255,255,0.03); padding:12px 14px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:0.76rem; color:#9ca3af; text-transform:uppercase; letter-spacing:0.5px;">👥 Jogadores</div>
      <div style="font-size:0.92rem; font-weight:600; color:#fff; margin-top:3px;">{players}</div>
    </div>
    <div style="background:rgba(255,255,255,0.03); padding:12px 14px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:0.76rem; color:#9ca3af; text-transform:uppercase; letter-spacing:0.5px;">⏱️ Duração</div>
      <div style="font-size:0.92rem; font-weight:600; color:#fff; margin-top:3px;">{duration}</div>
    </div>
    <div style="background:rgba(255,255,255,0.03); padding:12px 14px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:0.76rem; color:#9ca3af; text-transform:uppercase; letter-spacing:0.5px;">🎂 Idade Indicada</div>
      <div style="font-size:0.92rem; font-weight:600; color:#fff; margin-top:3px;">{age}</div>
    </div>
    <div style="background:rgba(255,255,255,0.03); padding:12px 14px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:0.76rem; color:#9ca3af; text-transform:uppercase; letter-spacing:0.5px;">🧠 Complexidade</div>
      <div style="font-size:0.92rem; font-weight:600; color:#fff; margin-top:3px;">{complexity}</div>
    </div>
  </div>

  <div style="line-height:1.75; font-size:0.92rem; color:#e5e7eb; border-top:1px solid rgba(255,255,255,0.06); padding-top:16px;">
    <div><strong>✍️ Designer(s):</strong> {designer}</div>
    <div style="margin-top:6px;"><strong>🏢 Editora:</strong> {publisher}</div>
    {mech_html}
    {sleeves_html}
  </div>

  <div style="display:flex; flex-wrap:wrap; gap:12px; margin-top:20px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.08);">
    {links_html}
  </div>
</div>
"""

def format_editorial_paragraphs(raw_paragraphs, source_name, is_second_part=False):
    output_html = ""
    first_person_patterns = [
        r'\b(eu|nós|nos|nosso|nossos|nossa|nossas|minha|meu|meus|minhas|tive|decidi|percebemos|queríamos|estávamos|jogamos|testamos|vimos)\b',
        r'\b(i|we|my|our|us|mine|ours)\b'
    ]

    for idx, p in enumerate(raw_paragraphs):
        p_trans = translate_to_pt(p).strip()
        if len(p_trans) < 35:
            continue

        # Detectar declarações em primeira pessoa da equipe/designer
        is_quote = any(re.search(pat, p_trans, re.I) for pat in first_person_patterns) or any(re.search(pat, p, re.I) for pat in first_person_patterns)

        if is_quote:
            lead_in_options = [
                f'Em declaração oficial sobre o projeto, a equipe destacou:',
                f'Ao detalhar as decisões de produção e design, os responsáveis pontuaram:',
                f'Segundo comunicado e apontamentos da equipe criativa:',
                f'Sobre a experiência na mesa e os testes práticos, foi ressaltado:'
            ]
            lead_in = lead_in_options[(idx + (2 if is_second_part else 0)) % len(lead_in_options)]

            output_html += f'''<p style="margin-bottom: 12px; line-height: 1.8; color: var(--text-main, #d1d5db); font-size: 1.05rem;">{lead_in}</p>
<blockquote style="margin: 20px 0 26px 0; padding: 18px 24px; border-left: 4px solid var(--tq-yellow, #f5b800); background: rgba(245, 184, 0, 0.05); border-radius: 0 12px 12px 0; font-style: italic; color: #f3f4f6; font-size: 1.02rem; line-height: 1.7;">
  "{p_trans}"
  <span style="display: block; margin-top: 8px; font-size: 0.85rem; font-style: normal; color: var(--text-muted, #9ca3af); font-weight: 600;">— {html.escape(source_name)}</span>
</blockquote>\n'''
        else:
            if idx == 0 and not is_second_part:
                p_text = f'De acordo com as informações apuradas junto a <em>{html.escape(source_name)}</em>, {p_trans[0].lower() + p_trans[1:] if len(p_trans) > 1 else p_trans}'
            else:
                p_text = p_trans
            output_html += f'<p style="margin-bottom: 22px; line-height: 1.8; color: var(--text-main, #d1d5db); font-size: 1.05rem;">{p_text}</p>\n'

    return output_html

def generate_editorial_post(item):
    if item.get('is_youtube'):
        clean_title = item['title']
        clean_title = re.sub(r'^\s*Unboxing\s+T[áa]bula\s*[\|\-:]\s*', 'Unboxing: ', clean_title, flags=re.I)
        clean_title = clean_title.replace('|', ':')
        clean_title = sanitize_travessao(clean_title)

        slug = make_slug(clean_title)
        video_id = item['youtube_id']
        c_title_safe = html.escape(clean_title)

        video_embed_html = f'''<div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 26px 0 32px 0; border-radius: 14px; border: 1px solid rgba(255,255,255,0.12); box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
  <iframe src="https://www.youtube.com/embed/{video_id}" title="{c_title_safe}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe>
</div>'''

        lead_text = item['deep_paragraphs'][0] if item['deep_paragraphs'] else f"O canal do Tábula Quadrada traz um unboxing completo em vídeo apresentando os componentes, arte e proposta de {clean_title}."
        lead_text_safe = html.escape(lead_text)

        yt_paragraphs_html = ""
        for p_text in item['deep_paragraphs'][1:]:
            yt_paragraphs_html += f'<p style="line-height: 1.75; margin-bottom: 18px;">{html.escape(p_text)}</p>\n'

        yt_components_box_html = ""
        if item.get('list_items'):
            comp_lis = "".join([f'    <li style="margin-bottom: 8px;">{html.escape(comp)}</li>\n' for comp in item['list_items']])
            yt_components_box_html = f'''<div class="article-features-box" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 22px 26px; margin: 32px 0;">
  <h4 style="margin: 0 0 14px 0; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.8px; color: var(--tq-yellow, #f5b800);">📦 Principais Componentes na Caixa</h4>
  <ul style="margin: 0; padding-left: 20px; line-height: 1.8; color: var(--text-main, #e6e6e6); font-size: 0.92rem;">
{comp_lis}  </ul>
</div>'''

        yt_cta_html = '''<div style="background: rgba(245, 184, 0, 0.06); border: 1px solid rgba(245, 184, 0, 0.22); border-radius: 14px; padding: 24px 28px; margin: 36px 0; text-align: center;">
  <h4 style="color: var(--tq-yellow, #f5b800); margin: 0 0 10px 0; font-size: 1.15rem; font-weight: 800;">Acompanhe o Canal do Tábula Quadrada</h4>
  <p style="margin: 0 0 16px 0; color: var(--text-main, #e6e6e6); font-size: 0.94rem; line-height: 1.6;">Gostou do unboxing? Inscreva-se no nosso canal no YouTube para não perder nenhum unboxing, gameplay e prévias detalhadas dos melhores lançamentos do universo analógico!</p>
  <a href="https://www.youtube.com/@TabulaQuadrada?sub_confirmation=1" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 10px; background: #e50914; color: #fff; font-weight: 700; font-size: 0.92rem; padding: 12px 24px; border-radius: 8px; text-decoration: none; box-shadow: 0 4px 14px rgba(229,9,20,0.4);">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
    Inscrever-se no YouTube
  </a>
</div>'''

        content_html = f'''<p class="article-lead" style="font-size: 1.15rem; line-height: 1.75; font-weight: 500; color: var(--text-highlight, #f3f4f6); margin-bottom: 24px;">{lead_text_safe}</p>

{video_embed_html}

<h3 style="color: var(--tq-yellow, #f5b800); margin-top: 36px; margin-bottom: 16px; font-size: 1.35rem;">Visão Geral e Conteúdo da Caixa</h3>
{yt_paragraphs_html}

{yt_components_box_html}

{yt_cta_html}'''

        game_data = item.get('parsed_game', {})
        has_game = bool(game_data.get('name'))
        new_post = {
            "id": int(time.time()),
            "title": clean_title,
            "slug": slug,
            "date": item.get('published_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "author": "Francis Eureka",
            "author_slug": "francis-eureka",
            "image_thumb": item.get('cover_image'),
            "image_hero": item.get('cover_image'),
            "image_full": item.get('cover_image'),
            "body_images": [],
            "is_game": has_game,
            "youtube_id": video_id,
            "video_id": video_id,
            "categories": [
                {"slug": "jogos-de-tabuleiro", "name": "Jogos de Tabuleiro"},
                {"slug": "videos", "name": "Vídeos"}
            ],
            "tags": ["Unboxing", "Vídeos", "Jogos de Tabuleiro", game_data.get('name', 'Unboxing Tábula')],
            "excerpt": lead_text[:190] + "...",
            "source_name": "Tábula Quadrada (YouTube)",
            "source_url": item['link'],
            "source_note": "Vídeo original publicado no canal Tábula Quadrada.",
            "content": content_html
        }
        if has_game:
            new_post['game'] = game_data
        return new_post

    title_raw = item['title']

    source = item['source']

    source_note = item.get('source_note', 'Material consultado e apuração oficial.')

    summary = item['summary']

    link = item['link']

    is_cf = item.get('is_crowdfunding', False)

    cover_image = item.get('cover_image') or ""
    if not cover_image or "default-hero" in str(cover_image):
        print("ERRO CRÍTICO [TRAVA EDITORIAL]: Tentativa de postagem sem capa autêntica abortada.")
        return None

    if is_short_form_content(item.get('title', ''), item.get('summary', ''), item.get('link', '')):
        print("ERRO CRÍTICO [TRAVA EDITORIAL]: Formato curto (Shorts/Reels/Stories) rejeitado na publicação.")
        return None

    body_images = item.get('body_images', [])

    deep_paragraphs = item.get('deep_paragraphs', [])

    list_items = item.get('list_items', [])



    clean_title = translate_to_pt(re.sub(r'\[.*?\]', '', title_raw).strip())

    summary_pt = translate_to_pt(summary)



    if is_cf:

        blog_title = f"Financiamento Coletivo: {clean_title}: Novidade Quente na Mesa!"

        primary_cat = {"slug": "noticias", "name": "Notícias"}

        tags = ["Financiamento Coletivo", "Catarse", "Jogos de Tabuleiro", "Francis Eureka", "Nacional"]

    else:

        blog_title = clean_title

        primary_cat = {"slug": "noticias", "name": "Notícias"}

        tags = ["Notícias", "Mercado Analógico", "Board Games", "Francis Eureka"]



    slug = re.sub(r'[^a-z0-9]+', '-', clean_title.lower()).strip('-')[:60]

    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    # Distribuição inteligente de parágrafos factuais

    all_ps = deep_paragraphs if deep_paragraphs else [summary_pt]

    half = max(1, int(len(all_ps) / 2))

    first_ps = all_ps[:half]

    second_ps = all_ps[half:]



    paragraphs_part1 = format_editorial_paragraphs(first_ps, source, is_second_part=False)
    paragraphs_part2 = format_editorial_paragraphs(second_ps, source, is_second_part=True)



    # 1. Imagem Principal Destacada de Componentes / Tabuleiro

    c_title_safe = html.escape(clean_title)

    body_figure_html = ""

    if body_images:

        selected_body_img = html.escape(body_images[0])

        body_figure_html = f"""
<figure class="article-body-figure" style="display: block; width: 100%; margin: 36px auto; text-align: center; clear: both; position: relative;">
  <img src="{selected_body_img}" alt="Visual e componentes de {c_title_safe}" loading="lazy" style="max-width: 100%; max-height: 540px; width: auto; height: auto; object-fit: contain; margin: 0 auto; display: block; border-radius: 12px; border: 1px solid rgba(255,255,255,0.12); box-shadow: 0 8px 24px rgba(0,0,0,0.4);" />
  <figcaption style="display: block; width: 100%; max-width: 760px; margin: 12px auto 0 auto; padding: 0 12px; font-size: 0.86rem; line-height: 1.5; color: var(--text-muted, #8e92a4); font-style: italic; text-align: center; clear: both;">
    Divulgação oficial: detalhes de arte, componentes e produção de {c_title_safe}.
  </figcaption>
</figure>
"""



    # 2. Destaques da Edição & Componentes Confirmados

    components_highlight_html = ""

    if list_items:

        li_elements = ""

        for li in list_items:

            li_trans = translate_to_pt(li)

            li_safe = html.escape(li_trans)

            li_elements += f'    <li style="margin-bottom:6px;">{li_safe}</li>\n'

        components_highlight_html = f"""

<div class="article-features-box" style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px 24px; margin:28px 0;">

  <h4 style="margin:0 0 12px 0; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.8px; color:var(--tq-yellow, #f5b800);">📦 Destaques da Edição & Componentes Revelados</h4>

  <ul style="margin:0; padding-left:20px; line-height:1.75; color:var(--text-main, #e6e6e6); font-size:0.9rem;">

{li_elements}  </ul>

</div>

"""



    # 3. Galeria Visual Completa de Artes e Protótipos (Até 8 Imagens)

    extra_visual_html = ""

    gallery_candidates = body_images[1:]

    if gallery_candidates:

        gallery_items = ""

        for g_img in gallery_candidates[:8]:

            g_url = html.escape(g_img)

            gallery_items += f"""

    <div style="flex:1 1 calc(33.333% - 12px); min-width:220px; max-width:100%;">

      <img src="{g_url}" alt="Registro visual de {c_title_safe}" loading="lazy" style="width:100%; height:220px; object-fit:cover; border-radius:10px; border:1px solid rgba(255,255,255,0.1); box-shadow:0 4px 16px rgba(0,0,0,0.3); transition:transform 0.2s ease;" />

    </div>

"""

        extra_visual_html = f"""

<div class="article-gallery-block" style="margin:34px 0; background:rgba(255,255,255,0.02); padding:22px; border-radius:14px; border:1px solid rgba(255,255,255,0.06);">

  <h4 style="font-size:0.95rem; color:var(--tq-yellow, #f5b800); margin:0 0 16px 0; text-transform:uppercase; letter-spacing:0.5px;">📸 Galeria de Imagens: Componentes, Cartas & Protótipos</h4>

  <div style="display:flex; flex-wrap:wrap; gap:12px;">

    {gallery_items}

  </div>

  <p style="font-size:0.82rem; color:var(--text-muted, #8e92a4); margin-top:12px; margin-bottom:0; font-style:italic;">

    Registros oficiais e prévias visuais revelados para o ecossistema de jogadores e apoiadores.

  </p>

</div>

"""



    # 4. Quadro de Informações do Lançamento

    source_safe = html.escape(source)

    source_note_safe = html.escape(source_note)

    source_link_safe = html.escape(link)

    info_box_html = f"""

<div class="editorial-info-table-box" style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px 24px; margin:30px 0;">

  <h4 style="margin:0 0 12px 0; font-size:0.92rem; text-transform:uppercase; letter-spacing:1px; color:var(--tq-yellow, #f5b800);">📋 Panorama Geral da Matéria & Ficha Rápida</h4>

  <ul style="margin:0; padding-left:18px; color:var(--text-main, #e6e6e6); font-size:0.9rem; line-height:1.8;">

    <li><strong>Título Apurado:</strong> {c_title_safe}</li>

    <li><strong>Canal / Veículo Oficial:</strong> {source_safe}</li>

    <li><strong>Foco da Notícia:</strong> {source_note_safe}</li>


  </ul>

</div>

"""



    lead_templates = [

        f'<p class="article-lead" style="font-size: 1.15rem; line-height: 1.7; font-weight: 500; color: var(--text-highlight, #f3f4f6); margin-bottom: 24px;">O universo dos jogos analógicos e da cultura pop ganha um novo destaque com a revelação oficial de <strong>{clean_title}</strong>. As novidades foram divulgadas com base em dados de <em>{source}</em>, trazendo detalhes cruciais sobre proposta, dinâmica e o que os jogadores podem esperar na mesa.</p>',

        f'<p class="article-lead" style="font-size: 1.15rem; line-height: 1.7; font-weight: 500; color: var(--text-highlight, #f3f4f6); margin-bottom: 24px;">Com os holofotes voltados para lançamentos inovadores, <strong>{clean_title}</strong> desponta como uma das principais notícias do cenário. O projeto, detalhado originalmente por <em>{source}</em>, aposta em mecânicas afiadas e forte apelo temático para conquistar os entusiastas do hobby.</p>',

        f'<p class="article-lead" style="font-size: 1.15rem; line-height: 1.7; font-weight: 500; color: var(--text-highlight, #f3f4f6); margin-bottom: 24px;">A comunidade de jogos de tabuleiro, RPGs e cultura analógica tem um novo anúncio de peso no radar: <strong>{clean_title}</strong> teve suas primeiras informações confirmadas por <em>{source}</em>, apresentando aos jogadores um olhar aprofundado sobre suas mecânicas e ambientação.</p>'

    ]

    import zlib

    lead_idx = abs(zlib.crc32(clean_title.encode('utf-8'))) % len(lead_templates)

    lead_p = lead_templates[lead_idx]



    ending_templates = [

        f'<p style="margin-top: 28px; line-height: 1.75;">Com forte apelo e proposta bem fundamentada, <strong>{clean_title}</strong> consolida seu espaço no radar dos jogadores. Seguiremos atentos às próximas atualizações sobre datas, tiragens e regras completas!</p>',

        f'<p style="margin-top: 28px; line-height: 1.75;">O anúncio de <strong>{clean_title}</strong> reforça o momento aquecido do mercado analógico mundial. Acompanhe a cobertura do Tábula Quadrada para mais prévias e análises detalhadas na mesa.</p>',

        f'<p style="margin-top: 28px; line-height: 1.75;">A expectativa em torno de <strong>{clean_title}</strong> segue em alta entre os fãs da categoria. O Tábula Quadrada continuará de olho nos próximos passos deste lançamento!</p>'

    ]

    ending_idx = abs(zlib.crc32((clean_title + 'end').encode('utf-8'))) % len(ending_templates)

    ending_p = ending_templates[ending_idx]



    # Enriquecimento Inteligente com Ludopedia & BGG
    game_ficha = get_complete_game_ficha(clean_title)
    is_game = bool(game_ficha)
    technical_sheet_html = ""
    if game_ficha:
        technical_sheet_html = build_technical_sheet_html(game_ficha)
        if game_ficha.get('publisher'):
            tags.append(game_ficha['publisher'])
        if game_ficha.get('designer'):
            tags.append(game_ficha['designer'])

    content_html = f"""
{lead_p}

<h3 style="color: var(--tq-yellow, #f5b800); margin-top: 36px; margin-bottom: 16px; font-size: 1.35rem;">Ambientação, Proposta e Universo</h3>
{paragraphs_part1}

{body_figure_html}

<h3 style="color: var(--tq-yellow, #f5b800); margin-top: 36px; margin-bottom: 16px; font-size: 1.35rem;">Mecânicas, Dinâmica na Mesa e O Que Esperar</h3>
{paragraphs_part2}

{components_highlight_html}

{extra_visual_html}

{info_box_html}

{technical_sheet_html}

{ending_p}
"""

    post_obj = {
        "id": int(time.time()),
        "title": blog_title,

        "slug": slug,

        "date": date_now,

        "author": "Francis Eureka",

        "author_slug": "francis-eureka",

        "image_thumb": cover_image,

        "image_hero": cover_image,

        "image_full": cover_image,
        "image": cover_image,
        "body_images": body_images,

        "is_game": is_game,
        "score_final": (game_ficha.get("score_final") or game_ficha.get("score")) if game_ficha else None,
        "game": game_ficha if game_ficha else None,

        "categories": [primary_cat, {"slug": "jogos-de-tabuleiro", "name": "Jogos de Tabuleiro"}],

        "tags": tags,

        "excerpt": f"O Tábula Quadrada traz uma cobertura completa sobre {clean_title}. Conheça todos os detalhes, proposta e dinâmica aqui no portal!",

        "source_name": source,

        "source_url": link,

        "source_note": source_note,

        "sources": [
            {
                "name": f"{source} (Veículo Apurador)",
                "url": link,
                "note": source_note or "Veículo original consultado para apuração jornalística da matéria."
            },
            *(
                [{
                    "name": "Ludopedia Brasil (Catálogo Nacional)",
                    "url": game_ficha["url_ludopedia"],
                    "note": "Ficha técnica analógica, especificações de componentes e cadastro comunitário."
                }] if (game_ficha and game_ficha.get("url_ludopedia")) else []
            ),
            *(
                [{
                    "name": f"{game_ficha['publisher']} (Editora Oficial)",
                    "url": game_ficha.get("url_publisher") or game_ficha.get("url_ludopedia") or link,
                    "note": "Editora e publicadora responsável pela distribuição oficial do jogo."
                }] if (game_ficha and game_ficha.get("publisher")) else []
            )
        ],

        "content": content_html.strip()

    }



    return post_obj



# ------------------------------------------------------------------------------

# 6. SINCRONIZAÇÃO VIA FTP (HOSTGATOR)

# ------------------------------------------------------------------------------

def sync_to_server(local_post):

    print("\n🚀 Sincronizando nova matéria ao vivo com o servidor HostGator...")

    try:

        ftp = ftplib.FTP(FTP_HOST, timeout=25)

        ftp.login(FTP_USER, FTP_PASS)

        ftp.cwd("/public_html/data")



        # Baixar posts.json atual do servidor para merge atômico

        r_buf = io.BytesIO()

        ftp.retrbinary("RETR posts.json", r_buf.write)

        remote_posts = json.loads(r_buf.getvalue().decode('utf-8'))



        # Inserir no topo

        remote_posts.insert(0, local_post)



        # Upload de volta

        w_buf = io.BytesIO(json.dumps(remote_posts, ensure_ascii=False, indent=2).encode('utf-8'))

        ftp.storbinary("STOR posts.json", w_buf)

        print("  ✓ posts.json atualizado no servidor com sucesso!")



        # Atualizar histórico no servidor

        r_hist_buf = io.BytesIO()

        try:

            ftp.retrbinary("RETR published_news_history.json", r_hist_buf.write)

            remote_hist = json.loads(r_hist_buf.getvalue().decode('utf-8'))

        except Exception:

            remote_hist = {}



        remote_hist[local_post['sources'][0]['name'] + '_' + local_post['slug']] = {

            "title": local_post['title'],

            "slug": local_post['slug'],

            "published_at": local_post['date']

        }



        w_hist_buf = io.BytesIO(json.dumps(remote_hist, ensure_ascii=False, indent=2).encode('utf-8'))
        ftp.storbinary("STOR published_news_history.json", w_hist_buf)
        print("  ✓ published_news_history.json sincronizado!")

        # 3. ATUALIZAÇÃO DEFINITIVA DA HOMEPAGE (index.html) NO SERVIDOR
        try:
            ftp.cwd("/public_html")
            r_html_buf = io.BytesIO()
            ftp.retrbinary("RETR index.html", r_html_buf.write)
            html_content = r_html_buf.getvalue().decode('utf-8', errors='ignore')

            # Ordenar posts por data
            remote_posts.sort(key=lambda x: str(x.get('date', '')), reverse=True)
            for p in remote_posts[:25]:
                if not p.get('author') or 'Renato' in p.get('author', ''):
                    p['author'] = 'Francis Eureka'

            lead_p = remote_posts[0]
            subs_p = remote_posts[1:5]
            feed_p = remote_posts[5:14]
            more_p = remote_posts[14:80]

            def fmt_pt_date(d_str):
                m_pt = {1:'janeiro', 2:'fevereiro', 3:'março', 4:'abril', 5:'maio', 6:'junho', 7:'julho', 8:'agosto', 9:'setembro', 10:'outubro', 11:'novembro', 12:'dezembro'}
                try:
                    p = d_str.split()[0].split('-')
                    return f"{int(p[2]):02d} de {m_pt.get(int(p[1]), 'outubro')} de {int(p[0])}"
                except:
                    return d_str

            # Hero Lead
            l_cat = (lead_p['categories'][0]['name'].upper() if lead_p.get('categories') else 'NOTÍCIAS')
            l_img = lead_p.get('image_hero') or lead_p.get('image_full') or lead_p.get('image_thumb') or lead_p.get('image') or '/images/default-hero.webp'
            lead_h = f'''<article class="hero-lead-card" data-astro-cid-lcdefpme>
  <a href="/{lead_p['slug'].strip('/')}/" data-astro-cid-lcdefpme>
    <img src="{l_img}" alt="{html.escape(lead_p['title'])}" class="hero-lead-img" loading="eager" fetchpriority="high" decoding="async" width="1200" height="675" onerror="this.onerror=null; this.src='/images/default-hero.webp';" data-astro-cid-lcdefpme>
    <div class="hero-lead-overlay" data-astro-cid-lcdefpme>
      <div class="hero-tags-row" data-astro-cid-lcdefpme>
        <span class="pill-category" data-astro-cid-lcdefpme>{html.escape(l_cat)}</span>
      </div>
      <h1 class="hero-lead-title" data-astro-cid-lcdefpme>{html.escape(lead_p['title'])}</h1>
      <p class="hero-lead-excerpt" data-astro-cid-lcdefpme>{html.escape(lead_p.get('excerpt', ''))}</p>
      <div class="hero-lead-meta" data-astro-cid-lcdefpme>
        <span data-astro-cid-lcdefpme>Por {html.escape(lead_p.get('author', 'Francis Eureka'))}</span>
        <span class="meta-separator" data-astro-cid-lcdefpme>•</span>
        <span data-astro-cid-lcdefpme>{fmt_pt_date(lead_p.get('date', ''))}</span>
      </div>
    </div>
  </a>
</article>'''

            # Hero Subs
            subs_h = []
            for sp in subs_p:
                sp_cat = (sp['categories'][0]['name'].upper() if sp.get('categories') else 'NOTÍCIAS')
                sp_img = sp.get('image_thumb') or sp.get('image_hero') or sp.get('image_full') or sp.get('image') or '/images/default-hero.webp'
                subs_h.append(f'''  <article class="hero-sub-item" data-astro-cid-lcdefpme>
    <a href="/{sp['slug'].strip('/')}/" data-astro-cid-lcdefpme>
      <img src="{sp_img}" alt="{html.escape(sp['title'])}" class="hero-sub-img" loading="eager" decoding="async" width="600" height="338" onerror="this.onerror=null; this.src='/images/default-hero.webp';" data-astro-cid-lcdefpme>
      <div class="hero-sub-overlay" data-astro-cid-lcdefpme>
        <div class="hero-tags-row" style="margin-bottom: 6px;" data-astro-cid-lcdefpme>
          <span class="pill-sub-category" data-astro-cid-lcdefpme>{html.escape(sp_cat)}</span>
        </div>
        <h2 class="hero-sub-title" data-astro-cid-lcdefpme>{html.escape(sp['title'])}</h2>
        <div class="hero-sub-meta" data-astro-cid-lcdefpme>
          <span data-astro-cid-lcdefpme>Por {html.escape(sp.get('author', 'Francis Eureka'))}</span>
          <span class="meta-separator" data-astro-cid-lcdefpme>•</span>
          <span data-astro-cid-lcdefpme>{fmt_pt_date(sp.get('date', ''))}</span>
        </div>
      </div>
    </a>
  </article>''')

            mosaic_inner = lead_h + '\n<div class="hero-sub-grid" data-astro-cid-lcdefpme>\n' + '\n'.join(subs_h) + '\n</div>'
            mosaic_re = r'(<div class="hero-mosaic-grid"[^>]*>)([\s\S]*?)(</div>\s*</div>\s*</section>)'
            if re.search(mosaic_re, html_content):
                html_content = re.sub(mosaic_re, r'\g<1>\n' + mosaic_inner + r'\n\g<3>', html_content, count=1)

            # Magazine Feed Grid
            feed_cards_h = []
            for idx, fp in enumerate(feed_p):
                delay = (idx % 4) + 1
                fp_title = fp.get('title', '')
                fp_author = fp.get('author', 'Francis Eureka')
                fp_date = fmt_pt_date(fp.get('date', ''))
                fp_slug = fp.get('slug', '').strip('/')
                fp_img = fp.get('image_thumb') or fp.get('image_full') or fp.get('image_hero') or fp.get('image') or '/images/default-hero.webp'
                
                fp_cat = 'NOTÍCIAS'
                if fp.get('categories') and len(fp['categories']) > 0:
                    first_c = fp['categories'][0]
                    fp_cat = first_c.get('name', 'NOTÍCIAS') if isinstance(first_c, dict) else str(first_c)
                fp_cat_upper = fp_cat.upper()

                fp_excerpt = fp.get('excerpt', '')[:140]
                if len(fp.get('excerpt', '')) > 140:
                    fp_excerpt += '...'

                is_review = bool(fp.get('is_game'))
                score = fp.get('game', {}).get('score_final') if isinstance(fp.get('game'), dict) else None
                score_html = f'\n      <div class="card-score-badge" data-astro-cid-sbmovh4h><span class="score-pill-clean" data-astro-cid-sbmovh4h>★ {score}</span></div>' if score else ''
                read_more_text = 'Ler análise completa →' if is_review else 'Ler matéria →'

                feed_cards_h.append(f'''<div class="uow-reveal uow-delay-{delay}" data-astro-cid-lcdefpme>
  <article class="post-card uow-card" data-astro-cid-sbmovh4h>
    <a href="/{fp_slug}/" class="card-media" data-astro-cid-sbmovh4h>
      <img src="{fp_img}" alt="{html.escape(fp_title)}" class="card-img" loading="lazy" decoding="async" onerror="this.onerror=null; this.src=\'/images/default-hero.webp\';" data-astro-cid-sbmovh4h>
      <div class="card-overlay-badge" data-astro-cid-sbmovh4h>
        <span class="badge badge-black" data-astro-cid-sbmovh4h>{html.escape(fp_cat_upper)}</span>
      </div>{score_html}
    </a>
    <div class="card-body" data-astro-cid-sbmovh4h>
      <div class="card-meta" data-astro-cid-sbmovh4h>
        <span data-astro-cid-sbmovh4h>Por {html.escape(fp_author)}</span>
        <span class="meta-dot" data-astro-cid-sbmovh4h>•</span>
        <span data-astro-cid-sbmovh4h>{fp_date}</span>
      </div>
      <h3 class="card-title" data-astro-cid-sbmovh4h>
        <a href="/{fp_slug}/" data-astro-cid-sbmovh4h>{html.escape(fp_title)}</a>
      </h3>
      <p class="card-excerpt" data-astro-cid-sbmovh4h>{html.escape(fp_excerpt)}</p>
      <div class="card-footer" data-astro-cid-sbmovh4h>
        <a href="/{fp_slug}/" class="card-read-more" data-astro-cid-sbmovh4h>{read_more_text}</a>
      </div>
    </div>
  </article>
</div>''')

            feed_inner = "\n".join(feed_cards_h)
            feed_re = r'(<div class="magazine-feed-grid"[^>]*id="magazine-feed-grid"[^>]*>)([\s\S]*?)(</div>\s*<div class="section-load-more-wrap")'
            if re.search(feed_re, html_content):
                html_content = re.sub(feed_re, r'\g<1>\n' + feed_inner + r'\n\g<3>', html_content, count=1)

            btn_re = r'(<button[^>]*data-target="magazine-feed-grid"[^>]*data-offset=")(\d+)("[^>]*>)'
            if re.search(btn_re, html_content):
                html_content = re.sub(btn_re, r'\g<1>14\g<3>', html_content, count=1)

            # Payload
            more_payload = []
            for mp in more_p:
                first_c = mp.get('categories', [{}])[0] if mp.get('categories') else {}
                cat_n = first_c.get('name', 'Geral') if isinstance(first_c, dict) else str(first_c)
                more_payload.append({
                    'id': mp.get('id', 0),
                    'title': mp.get('title', ''),
                    'slug': mp.get('slug', '').strip('/'),
                    'excerpt': mp.get('excerpt', '')[:140],
                    'author': mp.get('author', 'Francis Eureka'),
                    'date': fmt_pt_date(mp.get('date', '')),
                    'image': mp.get('image_thumb') or mp.get('image_hero') or mp.get('image_full') or mp.get('image') or '',
                    'category': cat_n,
                    'isReview': bool(mp.get('is_game')),
                    'score': mp.get('game', {}).get('score_final') if isinstance(mp.get('game'), dict) else None,
                    'complexity': mp.get('game', {}).get('complexity') if isinstance(mp.get('game'), dict) else None
                })

            pay_re = r'(<script[^>]*id="more-feed-payload"[^>]*>)([\s\S]*?)(</script>)'
            if re.search(pay_re, html_content):
                html_content = re.sub(pay_re, r'\g<1>' + json.dumps(more_payload, ensure_ascii=False) + r'\g<3>', html_content, count=1)

            ftp.storbinary("STOR index.html", io.BytesIO(html_content.encode('utf-8')))
            print("  ✓ index.html atualizado com padrão definitivo no servidor (Top 5 Hero + 9 Feed)!")
        except Exception as e_html:
            print(f"  [AVISO] Falha ao atualizar index.html via FTP: {e_html}")

        ftp.quit()



        # Acionar recompilação das páginas estáticas

        rebuild_url = f"{SITE_URL}/api/rebuild_all_static_posts.php?offset=0&limit=3"

        print(f"  ⚡ Acionando recompilação estática: {rebuild_url}")

        try:
            rebuild_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            req = urllib.request.Request(rebuild_url, headers=rebuild_headers)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:

                print(f"  ✓ Recompilação acionada (Status {resp.status})")

        except Exception as e:

            print(f"  [AVISO] Recompilação automática falhou: {e}")



        print(f"\n🎉 Matéria publicada com sucesso em: {SITE_URL}/{local_post['slug']}/")



    except Exception as e:

        print(f"❌ Erro na sincronização FTP: {e}")



# ------------------------------------------------------------------------------

# 7. EXECUÇÃO PRINCIPAL

# ------------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(description="Bot Autônomo de Notícias - Tábula Quadrada")

    parser.add_argument("--dry-run", action="store_true", help="Executa varredura sem publicar")

    parser.add_argument("--limit", type=int, default=1, help="Número máximo de matérias a publicar nesta rodada")

    args = parser.parse_args()



    print("="*70)

    print("   TÁBULA QUADRADA — BOT JORNALÍSTICO AUTÔNOMO DE NOTÍCIAS")

    print("="*70)



    history = load_history()



    # Carregar slugs existentes

    existing_slugs = set()

    posts_path = "data/posts.json"

    if os.path.exists(posts_path):

        try:

            with open(posts_path, 'r', encoding='utf-8') as f:

                posts_data = json.load(f)

                for p in posts_data:

                    if p.get('slug'): existing_slugs.add(p['slug'])

        except Exception:

            pass



    candidates = scan_all_sources(history, existing_slugs)



    if not candidates:

        print("\n💤 Nenhuma novidade inédita encontrada. O acervo está 100% em dia!")

        return



    published_count = 0

    for cand in candidates:

        if published_count >= args.limit:

            break



        print(f"\n✍️  Redigindo matéria completa para: {cand['title']}...")

        new_post = generate_editorial_post(cand)



        if args.dry_run:

            print("\n[DRY-RUN] Matéria gerada (não publicada):")

            print(f"  Título: {new_post['title']}")

            print(f"  Slug:   {new_post['slug']}")

            print(f"  Capa:   {new_post['image_hero']}")

            print(f"  Imagens no corpo: {len(cand.get('body_images', []))}")

            print(f"  Parágrafos:       {len(cand.get('deep_paragraphs', []))}")

        else:

            # Salvar localmente

            if os.path.exists(posts_path):

                with open(posts_path, 'r', encoding='utf-8') as f:

                    all_posts = json.load(f)

                all_posts.insert(0, new_post)

                with open(posts_path, 'w', encoding='utf-8') as f:

                    json.dump(all_posts, f, ensure_ascii=False, indent=2)



            history[cand['link']] = {

                "title": cand['title'],

                "slug": new_post['slug'],

                "published_at": new_post['date'],

                "source": cand['source']

            }

            save_history(history)



            # Enviar para servidor

            sync_to_server(new_post)

            published_count += 1



if __name__ == "__main__":

    main()

