"""Prediction Market: trade who wins the next race with play money. Crowd prices against the model."""
from datetime import datetime, timezone

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import picks
import prediction_market as M
from app_data import get_upcoming, run_upcoming
from charts import dress
from predictor import RESULTS_CSV, clean_name, current_season, get_race_start
from style import stat_strip, team_info
from ui_kit import GOOD, POOR, banner, board, section

COOKIE = "pp_player"


def player():
    if "player" not in st.session_state:
        st.session_state.player = picks.clean_code(st.context.cookies.get(COOKIE)) or picks.new_player_code()
    return st.session_state.player


def remember(code):
    if picks.clean_code(st.context.cookies.get(COOKIE)) != code:
        components.html(f"<script>document.cookie = '{COOKIE}={code}; path=/; max-age=63072000; SameSite=Lax';</script>",
                        height=0)


@st.cache_data(ttl=3600)
def start_of(season, rnd):
    return get_race_start(season, rnd)


@st.cache_data(ttl=10)
def load_trades(season, rnd=None):
    return M.trades(season, rnd)


@st.cache_data(ttl=600)
def winners(season):
    r = pd.read_csv(RESULTS_CSV, usecols=["season", "round", "race_name", "driver", "finish_position"])
    r = r[(r["season"] == season) & (r["finish_position"] == 1)]
    return {int(x.round): (x.driver, x.race_name) for x in r.itertuples()}


me = player()
season = current_season()
try:
    up = get_upcoming(season)
except Exception:
    up = pd.DataFrame()

# ---------- the market for the next race ----------
if up.empty:
    st.info("No races left this season: the market reopens for the first race of the next one.")
else:
    rnd, race_name = int(up["round"].iloc[0]), up["race_name"].iloc[0]
    try:
        table = run_upcoming(season, rnd)["table"]
    except Exception as error:
        table = None
        st.warning(f"The model's prediction for the {race_name} isn't ready yet ({error}).")
    if table is not None:
        owner = dict(zip(table["driver"], table["constructor"]))
        p0 = M.prior(dict(zip(table["driver"], table["win_chance"])))
        try:
            all_trades = load_trades(season, rnd)
            db_error = None
        except Exception as error:
            all_trades, db_error = [], error
        q = M.book(all_trades)
        price = M.prices(p0, q)
        cash, held = M.position(all_trades, me)
        start = start_of(season, rnd)
        open_ = datetime.now(timezone.utc) < start
        left = start - datetime.now(timezone.utc)
        stat_strip([
            ("Market", race_name.replace(" Grand Prix", ""), f"Round {rnd}, {season}", True),
            ("Your coins", f"{cash:,.0f}", f"of {M.BANK:,.0f} for this race", False),
            ("Your shares are worth", f"{sum(price[d] * s for d, s in held.items()):,.0f}", "at today's prices", False),
            ("Closes", f"{left.days} d {left.seconds // 3600} h" if open_ else "Closed", "at lights out", False),
        ])
        if db_error:
            st.warning(picks.describe_error(db_error, M.TABLE))

        section("The board", "Price = the crowd's chance that the driver wins, in coins per 100. Opened at the model's chance.")
        rows = []
        for d in sorted(price, key=lambda d: -price[d]):
            model = 100 * p0[d]
            gap = round(price[d] - model, 1) + 0.0
            rows.append({"colour": team_info(owner[d])[1],
                         "cells": [(clean_name(d), team_info(owner[d])[0]), f"{model:.1f}", (price[d], f"{price[d]:.1f}"),
                                   (gap, f"{gap:+.1f}"),
                                   f"{held[d]:.1f}" if d in held else ""]})
        board([("Driver", "label"), ("Model", "num"), ("Crowd price", "bar"), ("Crowd vs model", "delta"),
               ("Your shares", "num")], rows)

        if open_ and not db_error:
            section("Trade", "Each share pays 100 coins if the driver wins. Buying pushes the price up; selling brings it down.")
            c1, c2, c3 = st.columns([2, 1, 1], vertical_alignment="bottom")
            order = sorted(price, key=lambda d: -price[d])
            d = c1.selectbox("Driver", order, format_func=lambda k: f"{clean_name(k)} · {price[k]:.1f}", key="pm_driver")
            coins = c2.number_input("Coins", 10, int(max(cash, 10)), min(100, int(max(cash, 10))), 10, key="pm_coins")
            n_est = M.shares_for(p0, q, d, min(coins, cash)) if cash >= 1 else 0.0
            c1.caption(f"{coins} coins buy about {n_est:.1f} shares (pays {100 * n_est:,.0f} if {clean_name(d)} wins).")
            nick = st.text_input("Name on the table", max_chars=20, key="pm_nick", placeholder="Anonymous")
            if c3.button("Buy", type="primary", use_container_width=True, key="pm_buy"):
                try:
                    n, cost = M.trade(me, season, rnd, p0, d, coins=coins, nickname=nick)
                    remember(me)
                    load_trades.clear()
                    st.toast(f"Bought {n:.1f} shares of {clean_name(d)} for {cost:,.0f} coins.")
                    st.rerun()
                except ValueError as error:
                    st.warning(str(error))
                except Exception as error:
                    st.warning(picks.describe_error(error, M.TABLE))
            if held:
                s1, s2, s3 = st.columns([2, 1, 1], vertical_alignment="bottom")
                ds = s1.selectbox("Sell shares in", list(held), format_func=lambda k: f"{clean_name(k)} · you hold {held[k]:.1f}",
                                  key="pm_sell_driver")
                n_sell = s2.number_input("Shares", 0.1, float(held[ds]), float(held[ds]), 0.1, key=f"pm_sell_n_{ds}")
                s1.caption(f"Selling returns about {-M.quote(p0, q, ds, -n_sell):,.0f} coins.")
                if s3.button("Sell", use_container_width=True, key="pm_sell"):
                    try:
                        n, cost = M.trade(me, season, rnd, p0, ds, shares=n_sell, nickname=nick)
                        load_trades.clear()
                        st.toast(f"Sold {-n:.1f} shares for {-cost:,.0f} coins.")
                        st.rerun()
                    except ValueError as error:
                        st.warning(str(error))
                    except Exception as error:
                        st.warning(picks.describe_error(error, M.TABLE))

        if all_trades:
            section("How the prices moved", "The crowd's price for the five favourites after every trade.")
            top = sorted(price, key=lambda d: -price[d])[:5]
            hist, qq = [], {}
            for k, t in enumerate([None] + all_trades):
                if t:
                    qq[t["driver"]] = qq.get(t["driver"], 0.0) + float(t["shares"])
                pr = M.prices(p0, qq)
                hist += [{"Trade": k, "Driver": clean_name(d), "Price": pr[d]} for d in top]
            chart = alt.Chart(pd.DataFrame(hist)).mark_line(interpolate="step-after", strokeWidth=2.5).encode(
                x=alt.X("Trade:Q", title="Trades so far"), y=alt.Y("Price:Q", title="Crowd price"),
                color=alt.Color("Driver:N", scale=alt.Scale(domain=[clean_name(d) for d in top],
                                                            range=[team_info(owner[d])[1] for d in top]),
                                legend=alt.Legend(orient="top", title=None)))
            st.altair_chart(dress(chart).properties(height=240), use_container_width=True)

# ---------- the season table ----------
section(f"The {season} table", "Profit from every settled race: what you ended with, minus the 1,000 coins you started with.")
try:
    season_trades = load_trades(season)
except Exception:
    season_trades = []
won = winners(season)
totals, races_by = {}, {}
for rnd_, (winner, name) in won.items():
    tr = [t for t in season_trades if t["round"] == rnd_]
    for p, (profit, nick) in M.settle(tr, winner).items():
        a = totals.setdefault(p, [0.0, nick, 0])
        a[0] += profit
        a[1] = nick or a[1]
        a[2] += 1
if totals:
    rows = [{"colour": "#e10600" if p == me else None,
             "cells": [(v[1] or "Anonymous", "you" if p == me else ""), f"{v[2]}", (round(v[0]), f"{v[0]:+,.0f}")]}
            for p, v in sorted(totals.items(), key=lambda x: -x[1][0])[:20]]
    board([("Trader", "label"), ("Races", "num"), ("Profit", "delta")], rows, ranked=True)
    if me in totals:
        banner("💰", f"You're {totals[me][0]:+,.0f} coins this season", "Across the settled races you traded.",
               GOOD if totals[me][0] >= 0 else POOR)
else:
    st.caption("No settled races with trades yet this season.")

st.caption("Play money only: nothing is bought or sold. How the prices work is in About.")
