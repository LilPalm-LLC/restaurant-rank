# 🍽️ RestaurantRank v1.2

**Discover. Compare. Eat better.**

RestaurantRank is a mobile-first Streamlit restaurant discovery app that helps users quickly decide where to eat using Google Places data plus transparent RestaurantRank scoring.

## What is included

- 📱 Mobile-first layout for iPhone, Android/Samsung, tablet, and desktop
- 🌎 Location architecture designed for worldwide use
- 🔎 Google Places Text Search + Google Geocoding
- 🏆 Bayesian-style RestaurantRank Score (m=50 default)
- 💎 Hidden Gems, Best Value, Most Reviewed, Highest Rated, Closest, Lowest Price, Premium
- ❤️ Favorite collections with Place ID de-duplication
- ⚖️ Compare up to 3 restaurants
- 👤 Lightweight returning-user profiles using a 4-digit PIN
- 🔐 bcrypt PIN hashing, recovery codes, failed-attempt cooldowns
- 💾 JSON backup/restore with Merge and Replace
- 🇺🇸 English + 🇪🇸 Spanish application UI
- 🎨 Rose, Ocean, Fresh, Purple, Sunset themes
- ☀️ Light / 🌙 Dark / ⚙️ System appearance
- 🗺️ List + map result views
- ⚡ API caching, local filtering/sorting, and lazy place-detail/photo requests
- 🐍 Python 3.12 target

## Important persistence note

The app uses a storage abstraction with SQLite. This is reliable for local/self-hosted use and for a continuously running Streamlit instance, but Streamlit Community Cloud does not promise a permanent writable filesystem across app replacement/redeployment. Use the built-in JSON backup regularly for portable persistence. The storage layer is isolated in `services/storage.py`, so a durable hosted backend can be added later without rewriting the UI.

This design deliberately does **not** pretend that a local file is permanent cloud storage.

## Google Maps Platform setup

The only required application secret is:

```toml
GOOGLE_MAPS_API_KEY = "YOUR_API_KEY"
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` for local use. Do not commit `secrets.toml`.

Enable the Google APIs/products required by your Google Maps Platform account, including Places API (New) and Geocoding API, and make sure billing/quota are configured as required by your account.

Google Maps Platform can incur charges depending on current pricing, billing configuration, quotas, and API usage. RestaurantRank reduces usage through caching, local filtering/sorting, and lazy loading.

## Local installation

Python 3.12 is recommended.

### Windows

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app also starts without a Google API key. It will show a friendly setup message rather than a traceback.

## GitHub + Streamlit Community Cloud

1. Create a GitHub repository.
2. Push the project.
3. Do **not** upload `.streamlit/secrets.toml`.
4. Open Streamlit Community Cloud.
5. Connect the repository.
6. Select `app.py` as the entry point.
7. Add the secret below in Streamlit Secrets:

```toml
GOOGLE_MAPS_API_KEY = "YOUR_API_KEY"
```

8. Deploy.

## Profile and recovery model

RestaurantRank is intentionally not a traditional email/password SaaS account system. A profile has a name and a 4-digit PIN. PINs are bcrypt-hashed; raw PINs are never written to backups. A separate cryptographically random recovery code is generated at profile creation and may be downloaded as a text file. Recovery codes are also hashed in storage and never exported in a backup.

A 4-digit PIN is convenience-level authentication, not high-security authentication.

## Backup and restore

A backup contains profile display information, settings, favorite collections, and saved restaurant snapshots. It never includes:

- Google API keys
- secrets
- raw PINs
- recovery codes
- server credentials

Imported files are treated as untrusted JSON and validated before use.

## Ranking

RestaurantRank does not simply copy Google rating order. The default score uses a Bayesian-style confidence adjustment:

`(v/(v+m))*R + (m/(v+m))*C`

Where `R` is the restaurant rating, `v` is review count, `m` is the minimum review threshold (50 by default), and `C` is the average rating of the result set.

The result is explicitly labeled **RestaurantRank Score** and is not a Google rating.

## Data honesty

RestaurantRank does not invent dishes, dietary labels, ratings, review counts, or restaurant information. Google-provided restaurant information stays distinguishable from RestaurantRank calculations. Dish-level recommendations are only presented when supported by the available source data; otherwise the user is directed to the current menu.

## Testing

Run:

```bash
python -m compileall .
pytest -q
```

Tests cover ranking, validation, distance, cuisine normalization, backup validation, security, i18n, and storage.

## Project structure

```text
restaurant-rank-v1.2/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
├── services/
│   ├── google_places.py
│   ├── geocoding.py
│   └── storage.py
├── models/
├── utils/
├── components/
├── i18n/
├── tests/
└── assets/
```
