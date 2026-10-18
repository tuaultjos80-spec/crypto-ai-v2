"""Offline educational crypto paper trader. No exchange or network access."""
from dataclasses import dataclass
import math
import random
import pandas as pd

COINS = {'BTC':(58000,.026),'ETH':(3100,.032),'SOL':(138,.045),'ADA':(.47,.042),'XRP':(.54,.038)}
FEE = .001

@dataclass(frozen=True)
class Settings:
    initial_cash: float = 10000
    max_asset_weight: float = .20
    max_total_exposure: float = .60
    stop_drawdown: float = .15
    fast: int = 10
    slow: int = 30
    days: int = 365
    seed: int = 42

def prices_simulated(s: Settings) -> pd.DataFrame:
    """Repeatable synthetic market; shared shocks model some correlation."""
    common = random.Random(s.seed)
    shared = [common.gauss(0, .012) for _ in range(s.days)]
    result = {}
    for j,(symbol,(start,vol)) in enumerate(COINS.items()):
        rng = random.Random(s.seed + 1000*j)
        values=[start]
        for t in range(1,s.days):
            drift=.00015+.002*math.sin(t/25)
            log_return=max(-.30,min(.25,drift+shared[t]+rng.gauss(0,vol*.8)))
            values.append(values[-1]*math.exp(log_return))
        result[symbol]=values
    return pd.DataFrame(result)

def simulate(s: Settings):
    if not (s.initial_cash>0 and 0<s.max_asset_weight<=1 and 0<s.max_total_exposure<=1 and 0<s.stop_drawdown<1 and 2<=s.fast<s.slow and s.days>s.slow+2):
        raise ValueError('Invalid settings')
    prices=prices_simulated(s)
    cash=s.initial_cash
    quantities={k:0.0 for k in COINS}
    costs={k:0.0 for k in COINS}
    peak=s.initial_cash
    halted=False
    trades=[]
    history=[]
    def equity(t):
        return cash+sum(quantities[k]*float(prices.loc[t,k]) for k in COINS)
    for t in range(s.slow, s.days):
        # Record value and check drawdown before any new trades.
        current=equity(t)
        peak=max(peak,current)
        if current <= peak*(1-s.stop_drawdown):
            halted=True
        if halted:
            # Liquidate at current close. Circuit breaker remains latched until reset.
            actions={k:'SELL' if quantities[k]>0 else 'HOLD' for k in COINS}
        else:
            # Signal from PREVIOUS close, execute at CURRENT close.
            actions={}
            for k in COINS:
                h=prices[k].iloc[:t]
                fast=h.iloc[-s.fast:].mean()
                slow=h.iloc[-s.slow:].mean()
                actions[k]='SELL' if quantities[k]>0 and fast<slow else ('BUY' if quantities[k]==0 and fast>slow else 'HOLD')
        # Sells first, so cash freed is available to buy.
        for k in COINS:
            if actions[k]=='SELL' and quantities[k]>0:
                px=float(prices.loc[t,k]); gross=quantities[k]*px; fee=gross*FEE
                cash+=gross-fee
                trades.append({'day':t,'asset':k,'side':'SELL','value_eur':round(gross,2),'fee_eur':round(fee,2),'realized_pnl_eur':round(gross-fee-costs[k],2)})
                quantities[k]=0;costs[k]=0
        if not halted:
            for k in COINS:
                if actions[k]!='BUY': continue
                total=equity(t)
                exposure=sum(quantities[a]*float(prices.loc[t,a]) for a in COINS)
                budget=min(cash,total*s.max_asset_weight,max(0,total*s.max_total_exposure-exposure))
                if budget < 1: continue
                px=float(prices.loc[t,k]); fee=budget*FEE/(1+FEE)
                quantities[k]=(budget-fee)/px
                costs[k]=budget;cash-=budget
                trades.append({'day':t,'asset':k,'side':'BUY','value_eur':round(budget-fee,2),'fee_eur':round(fee,2),'realized_pnl_eur':0.0})
        history.append({'day':t,'portfolio_eur':round(equity(t),2),'cash_eur':round(cash,2),'halted':halted})
    return prices, pd.DataFrame(history), pd.DataFrame(trades), quantities, halted
