import datetime as dt
import pandas as pd
import streamlit as st
from engine import COINS, fetch_prices, portfolio_value

st.set_page_config(page_title="Crypto AI V3", page_icon="📈", layout="wide")
st.title("📈 Crypto AI V3")
st.warning("Simulation uniquement : cours réels indicatifs, argent virtuel, aucune IA prédictive et aucun ordre réel.")
st.caption("Source : API publique CoinGecko. Les cours peuvent être différés, limités ou indisponibles.")

START_CASH = 10_000.0
FEE_RATE = 0.001  # Hypothèse de frais : 0,1 % par opération

if "cash" not in st.session_state:
    st.session_state.cash = START_CASH
    st.session_state.positions = {symbol: 0.0 for symbol in COINS}
    st.session_state.trades = []

@st.cache_data(ttl=90, show_spinner=False)
def prices_cached():
    return fetch_prices()

if st.button("🔄 Actualiser les cours"):
    prices_cached.clear()

try:
    prices = prices_cached()
except Exception as exc:
    st.error("Impossible de récupérer les prix réels actuellement. Réessaie dans quelques minutes (limite API ou connexion).")
    st.caption(f"Détail technique : {exc}")
    st.stop()

st.subheader("Marché crypto — EUR")
market = []
for symbol, data in prices.items():
    market.append({"Crypto": symbol, "Nom": data["name"], "Prix (€)": data["price"], "Variation 24 h (%)": data["change_24h"]})
st.dataframe(pd.DataFrame(market), hide_index=True, use_container_width=True,
             column_config={"Prix (€)": st.column_config.NumberColumn(format="%.4f"),
                            "Variation 24 h (%)": st.column_config.NumberColumn(format="%.2f")})

value = portfolio_value(st.session_state.cash, st.session_state.positions, prices)
col1, col2, col3 = st.columns(3)
col1.metric("Portefeuille virtuel", f"{value:,.2f} €")
col2.metric("Liquidités virtuelles", f"{st.session_state.cash:,.2f} €")
col3.metric("Performance simulée", f"{(value / START_CASH - 1) * 100:+.2f} %")

st.subheader("Effectuer une transaction virtuelle")
with st.form("trade_form"):
    symbol = st.selectbox("Cryptomonnaie", list(COINS))
    side = st.radio("Opération", ["Acheter", "Vendre"], horizontal=True)
    amount = st.number_input("Montant de l'opération (€)", min_value=1.0, value=100.0, step=10.0)
    submitted = st.form_submit_button("Valider la transaction virtuelle")

if submitted:
    price = prices[symbol]["price"]
    fee = amount * FEE_RATE
    if side == "Acheter":
        total = amount + fee
        if total > st.session_state.cash + 1e-8:
            st.error("Liquidités virtuelles insuffisantes (frais inclus).")
        else:
            st.session_state.cash -= total
            st.session_state.positions[symbol] += amount / price
            st.session_state.trades.append({"Date UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "Crypto": symbol, "Action": "ACHAT", "Montant (€)": amount, "Prix (€)": price, "Frais (€)": fee})
            st.rerun()
    else:
        qty = amount / price
        if qty > st.session_state.positions[symbol] + 1e-10:
            st.error("Quantité virtuelle insuffisante pour vendre ce montant.")
        else:
            st.session_state.positions[symbol] -= qty
            st.session_state.cash += amount - fee
            st.session_state.trades.append({"Date UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "Crypto": symbol, "Action": "VENTE", "Montant (€)": amount, "Prix (€)": price, "Frais (€)": fee})
            st.rerun()

st.caption("Frais simulés : 0,1 % par opération. Aucun spread, slippage ou impôt modélisé.")
st.subheader("Positions virtuelles")
rows = [{"Crypto": symbol, "Unités": qty, "Valeur actuelle (€)": qty * prices[symbol]["price"]}
        for symbol, qty in st.session_state.positions.items()]
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

st.subheader("Historique des transactions virtuelles")
if st.session_state.trades:
    history = pd.DataFrame(st.session_state.trades)
    st.dataframe(history.iloc[::-1], hide_index=True, use_container_width=True)
    st.download_button("📥 Exporter les transactions CSV", history.to_csv(index=False).encode("utf-8-sig"),
                       file_name="transactions_virtuelles.csv", mime="text/csv")
else:
    st.info("Aucune transaction pour le moment.")

if st.button("Réinitialiser le portefeuille virtuel"):
    st.session_state.cash = START_CASH
    st.session_state.positions = {symbol: 0.0 for symbol in COINS}
    st.session_state.trades = []
    st.rerun()

st.info("Les transactions sont conservées uniquement dans la session Streamlit : un redémarrage peut effacer le portefeuille. Ce prototype ne fournit ni conseil financier ni signaux de trading.")
