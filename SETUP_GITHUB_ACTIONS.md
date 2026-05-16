# GitHub Actions Setup

24/7 ücretsiz çalıştırmak için adımlar. Tek seferlik kurulum, sonra bot kendi başına 5 dk'da bir tetiklenir.

## 1. Token'ı al

Lokalde `.token` dosyasının içeriğini kopyala:

```
cat .token
```

(Token gizli — bu dosyaya hiçbir zaman yazma. `.token` ve `.env` zaten `.gitignore`'da.)

## 2. GitHub'da private repo oluştur

1. https://github.com/new aç
2. Repository name: `ai-trader-bot` (ya da istediğin)
3. **Private** seç (önemli — token public'e çıkmasın)
4. README/gitignore/license **EKLEME**, boş repo lazım
5. "Create repository" → repo URL'sini kopyala (örn `git@github.com:emir/ai-trader-bot.git`)

## 3. Lokal repo'yu push et

Bu klasörde, terminalde:

```
git init
git add .
git commit -m "feat: initial copy-trade bot for ai4trade.ai"
git branch -M main
git remote add origin <REPO_URL>
git push -u origin main
```

`.env` ve `.token` zaten `.gitignore`'da, push'a gitmezler.

## 4. Token'ı Secret olarak ekle

1. GitHub'da repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**:
   - Name: `AI4TRADE_TOKEN`
   - Secret: 1. adımdaki token değeri
3. **Add secret**

## 5. (İsteğe bağlı) DRY_RUN'ı kapat

Aynı sayfada **Variables** sekmesi → **New repository variable**:
- Name: `DRY_RUN`
- Value: `false`

Eklemezsen varsayılan `true`'dur, gerçek follow yapılmaz (sadece log).

## 6. İlk tetikleme

GitHub repo → **Actions** sekmesi → "AI-Trader bot tick" workflow → **Run workflow** → **Run workflow** butonu.

Logu izle. Beklenen son satırlar:

```
agent=emir-bot cash=$100000.00 reputation=0
heartbeat ok notifications=0
feed: 50 signals → 3 candidates
[DRY_RUN] would follow ...   ← veya gerçek follow logları
tick done: 3 new follows, 3 total tracked
```

Sonraki çalışmalar 5 dk'da bir otomatik. Logları yine **Actions** sekmesinden görürsün.

## Sorun çıkarsa

- **"Token rejected"** → token expire olmuş. Lokalde `python register.py` ile yenisini al, GitHub Secret'ı güncelle.
- **Cron 5 dk yerine 10-15 dk geçti** → GitHub'ın bilinen davranışı, peak load'da geciktirir. Heartbeat platformda yeterli olur mu, izleyeceğiz.
- **"Resource not accessible"** → Settings → Actions → General → Workflow permissions → "Read and write" işaretle.
