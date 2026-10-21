# 🎲 Tábula Quadrada — Bot Jornalístico Autônomo de Notícias

Robô autônomo de jornalismo e monitoramento de jogos analógicos para o portal [Tábula Quadrada](https://tabulaquadrada.com.br).

---

## 🚀 Como Funciona

1. **Varredura Multifontes Diária:**
   - Monitora feeds oficiais de editoras nacionais (**Devir Brasil**, **MeepleBR**, **PaperGames**, **Galápagos**, etc.).
   - Monitora portais internacionais especializados (**Meeple Mountain**, **Punchboard**, **Dicebreaker**, **Wargamer**, **BoardGameGeek**, etc.).
   - Monitora campanhas de financiamento coletivo (**Catarse Jogos**, **Kickstarter**, **Gamefound**).
   - Monitora novos vídeos do **Canal Oficial no YouTube**.

2. **Crivo Editorial Rigoroso:**
   - Valida imagens de alta resolução para capas e fotografias reais de componentes no corpo da matéria.
   - Rejeita conteúdos superficiais ou clickbaits.
   - Cruza automaticamente com o acervo da **Ludopedia** e **BGG** para anexar fichas técnicas canônicas (Complexidade, Jogadores, Idade, Duração, Designer, Artista e Editora).

3. **Publicação Direta no Ar:**
   - Registra a matéria em `data/posts.json` via FTP seguro.
   - Atualiza a vitrine da Homepage (`index.html`) estática com layout responsivo.
   - Dispara recompilação estática instantânea no servidor.
   - Registra histórico para garantir **anti-duplicação permanente**.

---

## ⏰ Agendamento Automático (GitHub Actions)

O robô roda automaticamente **3 vezes ao dia** na nuvem através do GitHub Actions:
- **09:15 BRT**
- **14:15 BRT**
- **19:15 BRT**

Também pode ser acionado manualmente a qualquer momento pela aba **Actions** > **Run workflow**.

---

## 🛠️ Execução Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Simulação sem publicar
python scripts/tabula_news_bot.py --dry-run

# Publicar até 2 matérias inéditas
python scripts/tabula_news_bot.py --limit 2
```
