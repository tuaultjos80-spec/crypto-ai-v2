"""Mobile-friendly offline synthetic paper-trading dashboard."""
import streamlit as st
from engine import Settings, simulate
st.set_page_config(page_title='Crypto AI V2 — Simulation',layout='centered')
st.title('Crypto AI V2')
st.warning('Démonstration : prix inventés, aucune IA entraînée, aucun argent réel.')
with st.sidebar:
    st.header('Paramètres')
    capital=st.number_input('Capital virtuel (€)',min_value=100.,value=10000.,step=100.)
    weight=st.slider('Maximum par crypto (%)',5,40,20,5)
    exposure=st.slider('Exposition totale maximale (%)',10,100,60,5)
    drawdown=st.slider('Arrêt si perte depuis le sommet (%)',5,40,15,5)
    seed=st.number_input('Scénario aléatoire',min_value=1,value=42,step=1)
s=Settings(initial_cash=capital,max_asset_weight=weight/100,max_total_exposure=exposure/100,stop_drawdown=drawdown/100,seed=int(seed))
prices,equity,trades,positions,halted=simulate(s)
last=float(equity.portfolio_eur.iloc[-1]); ret=(last/capital-1)*100
c1,c2=st.columns(2)
c1.metric('Portefeuille final',f'{last:,.2f} €')
c2.metric('Rendement fictif',f'{ret:+.2f} %')
st.write('Coupe-circuit activé :', 'Oui' if halted else 'Non')
st.subheader('Évolution du portefeuille')
st.line_chart(equity.set_index('day')['portfolio_eur'])
st.subheader('Positions restantes')
st.dataframe([{'Crypto':k,'Unités':round(v,8)} for k,v in positions.items()],hide_index=True)
st.subheader('Transactions fictives')
st.dataframe(trades,hide_index=True)
st.download_button('Télécharger les transactions CSV',trades.to_csv(index=False).encode('utf-8'),'trades.csv','text/csv')
st.caption('Stratégie SMA fixe. Signal à J-1, exécution à J. Frais fictifs de 0,1 %. Pas de spread/slippage ni d’exchange.')
