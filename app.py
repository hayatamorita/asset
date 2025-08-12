# -*- coding: utf-8 -*-
# 保存して: streamlit run app.py

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="人生資産シミュレーション", layout="wide")

# ---------------------- CSS（入力ボックスの高さを揃える・モバイル最適化） ----------------------
st.markdown("""
<style>
/* ラベル高さの最小化で段ズレを抑える */
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stRadio"] label {
    min-height: 1.8rem; display: flex; align-items: center;
}
/* 入力欄の高さを揃える（ざっくり） */
div[data-baseweb="input"] > div { min-height: 40px; }
/* サイドバーの見出し間の余白 */
section[data-testid="stSidebar"] .block-container { padding-top: .5rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------- ヘッダー ----------------------
st.title("🏠 人生資産シミュレーション（UTF-8）")
st.caption("※ 簡易モデル：税・社保・控除・資産評価・減価償却は概算。ご自身の状況に合わせて調整してください。単位は『万円/年』。")

# ---------------------- サイドバー（全パラメータ） ----------------------
with st.sidebar:
    st.header("⚙️ パラメータ設定（すべてここで調整）")

    st.subheader("期間・初期値")
    colA, colB = st.columns(2)
    with colA:
        current_age = st.number_input("現在年齢", 20, 80, 30, 1)
        target_age  = st.number_input("目標年齢（終了）", 40, 90, 60, 1)
    with colB:
        initial_assets = st.number_input("現在の金融資産（万円）", 0, 999999, 100, 10)

    st.subheader("本人の額面年収の推移")
    col1, col2, col3 = st.columns(3)
    with col1:
        income_now = st.number_input("現在年収（万円）", 0, 99999, 800, 10)
    with col2:
        years_to_raise = st.number_input("何年後に年収UP", 0, 20, 3, 1)
        income_after   = st.number_input("UP後の年収（万円）", 0, 99999, 1000, 10)
    with col3:
        raise_until_age = st.number_input("年収の年率上昇 適用上限年齢", 30, 70, 40, 1)
        raise_rate      = st.number_input("年率上昇（%）", 0.0, 10.0, 1.0, 0.1)

    st.subheader("妻（配偶者）の年収")
    colw1, colw2, colw3 = st.columns(3)
    with colw1:
        spouse_start_age = st.number_input("妻の就業開始年齢", 20, 80, 32, 1)
    with colw2:
        spouse_income    = st.number_input("妻の年収（万円/年）", 0, 99999, 300, 10)
    with colw3:
        spouse_growth    = st.number_input("妻の年収 年率上昇（%）", 0.0, 10.0, 0.0, 0.1)

    st.subheader("税・社会保険（簡易・世帯共通率）")
    colt1, colt2, colt3 = st.columns(3)
    with colt1:
        salary_deduction_rate = st.number_input("給与所得控除率（%/額面）", 0.0, 50.0, 20.0, 0.5)
        salary_deduction_min  = st.number_input("給与所得控除の下限（万円）", 0, 1000, 55, 5)
    with colt2:
        basic_deduction       = st.number_input("基礎控除（万円）", 0, 200, 48, 1)
        resident_tax_rate     = st.number_input("住民税率（%・概算）", 0.0, 20.0, 10.0, 0.5)
    with colt3:
        income_tax_eff_rate   = st.number_input("所得税 実効率（%・概算）", 0.0, 40.0, 8.0, 0.5)
        social_ins_rate       = st.number_input("社会保険料率（%・概算）", 0.0, 30.0, 15.0, 0.5)

    st.subheader("住宅（総資産に土地・建物を計上／ローンは負債）")
    colh1, colh2, colh3 = st.columns(3)
    with colh1:
        house_age   = st.number_input("購入年齢", 25, 70, 37, 1)
        house_price = st.number_input("購入価格（万円）", 0, 999999, 5000, 50)  # 5000万円
        down_payment = st.number_input("頭金（万円）", 0, 999999, 500, 50)
    with colh2:
        mortgage_rate  = st.number_input("住宅ローン金利（年%）", 0.0, 5.0, 1.0, 0.1)
        mortgage_years = st.number_input("ローン年数", 5, 45, 35, 1)
        prop_tax_annual = st.number_input("固定資産税・基本維持費（万円/年）", 0, 300, 30, 5)
    with colh3:
        land_ratio = st.number_input("土地比率（%）", 0.0, 100.0, 40.0, 1.0)
        land_appreciation = st.number_input("土地 年率変動（%）", -5.0, 10.0, 0.0, 0.1)
        bldg_decline = st.number_input("建物 年率変動（%・負推奨）", -10.0, 10.0, -2.0, 0.1)

    # 30年間維持費（デフォ800万円） → 30等分して年加算
    maint_30yr_total = st.number_input("住宅の30年間維持費 合計（万円）", 0, 100000, 800, 10)

    st.subheader("子ども・教育費（1人あたり/年）")
    colc1, colc2 = st.columns(2)
    with colc1:
        child1_birth_age = st.number_input("第一子 出産（親の年齢）", 20, 60, 30, 1)
        child2_birth_age = st.number_input("第二子 出産（親の年齢）", 20, 60, 33, 1)
        kg_cost   = st.number_input("幼稚園（3〜6歳）", 0, 500, 10, 5)
        elem_cost = st.number_input("小学校（7〜12歳）", 0, 500, 30, 5)
    with colc2:
        jhs_cost  = st.number_input("中学（13〜15歳）", 0, 500, 50, 5)
        hs_cost   = st.number_input("高校（16〜18歳）", 0, 500, 30, 5)
        univ_cost = st.number_input("大学（19〜22歳）", 0, 800, 80, 10)
        living_add = st.number_input("大学 仕送り等 追加", 0, 800, 60, 10)

    peak_threshold = st.number_input("“教育費ピーク”判定（合計/年）", 0, 2000, 300, 10)

    st.subheader("貯蓄と投資")
    mode = st.radio("貯蓄方法", ["割合で指定（世帯額面ベース）", "固定額で指定（世帯合計）"], index=1)
    if mode == "割合で指定（世帯額面ベース）":
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            save_rate_pre  = st.number_input("購入前の貯蓄率（%）", 0.0, 90.0, 25.0, 1.0)
        with colp2:
            save_rate_post = st.number_input("購入後の貯蓄率（%）", 0.0, 90.0, 20.0, 1.0)
        with colp3:
            save_rate_peak = st.number_input("教育費ピークの貯蓄率（%）", 0.0, 90.0, 15.0, 1.0)
        save_amt_pre = save_amt_post = save_amt_peak = None
    else:
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            save_amt_pre  = st.number_input("購入前の貯蓄額（万円/年）", 0, 100000, 200, 10)
        with colp2:
            save_amt_post = st.number_input("購入後の貯蓄額（万円/年）", 0, 100000, 200, 10)
        with colp3:
            save_amt_peak = st.number_input("教育費ピークの貯蓄額（万円/年）", 0, 100000, 120, 10)
        save_rate_pre = save_rate_post = save_rate_peak = None

    invest_return = st.number_input("投資年率（税引後, %）", 0.0, 20.0, 4.0, 0.1)

    st.subheader("車（購入イベント）")
    colv1, colv2, colv3 = st.columns(3)
    with colv1:
        car1_age  = st.number_input("車① 購入年齢", 18, 90, 38, 1)
        car1_cost = st.number_input("車① 価格（万円）", 0, 100000, 400, 10)
    with colv2:
        car2_age  = st.number_input("車② 購入年齢", 18, 90, 50, 1)
        car2_cost = st.number_input("車② 価格（万円）", 0, 100000, 0, 10)
    with colv3:
        car_running_cost = st.number_input("車 維持費（万円/年, 目安）", 0, 1000, 20, 1)

    st.caption("※ 全パラメータをサイドバーに集約。グラフはPlotlyでスマホでもピンチ/ドラッグ操作可。")

# ---------------------- 補助関数 ----------------------
def annuity_payment(principal, annual_rate_pct, years):
    r = annual_rate_pct / 100.0
    n = int(years)
    if principal <= 0 or n <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

def income_at_age(age, start_age, inc0, inc_after, years_to_after, raise_until, raise_pct):
    years_from_now = age - start_age
    if years_from_now < years_to_after:
        return inc0
    inc = inc_after
    extra = max(0, min(age, raise_until) - (start_age + years_to_after))
    return inc * ((1 + raise_pct/100.0) ** extra)

def spouse_income_at_age(age, spouse_start, base, growth):
    if age < spouse_start:
        return 0.0
    extra = age - spouse_start
    return base * ((1 + growth/100.0) ** max(0, extra))

def child_cost_by_age(child_age, kg, elem, jhs, hs, univ, live_add):
    if child_age < 3:
        return 0
    if 3 <= child_age <= 6:
        return kg
    if 7 <= child_age <= 12:
        return elem
    if 13 <= child_age <= 15:
        return jhs
    if 16 <= child_age <= 18:
        return hs
    if 19 <= child_age <= 22:
        return univ + live_add
    return 0

def taxes_and_net(gross, salary_ded_rate, salary_ded_min, basic_ded, resident_rate, itax_eff, social_rate):
    si = gross * (social_rate/100.0)
    salary_ded = max(salary_ded_min, gross * (salary_ded_rate/100.0))
    taxable = max(0.0, gross - si - salary_ded - basic_ded)
    itax = taxable * (itax_eff/100.0)
    rtax = max(0.0, (gross - si - salary_ded) * (resident_rate/100.0))
    net = gross - (si + itax + rtax)
    return si, itax, rtax, net

# ---------------------- シミュレーション ----------------------
years = list(range(current_age, target_age + 1))

fin_asset = float(initial_assets)   # 金融資産（万円）
loan_balance = 0.0                 # 住宅ローン残高
annual_payment = 0.0               # 住宅の元利返済（万円/年）

land0 = house_price * (land_ratio/100.0)
bldg0 = house_price - land0
land_val = 0.0
bldg_val = 0.0

# 30年維持費を年割り
annual_maint_extra = (maint_30yr_total / 30.0) if house_price > 0 else 0.0

# トラッキング
gross_incomes, spouse_incomes, hh_incomes = [], [], []
income_taxes, resident_taxes, social_ins = [], [], []
net_incomes = []
edu_costs, house_costs, car_costs, contribs = [], [], [], []
fin_assets, total_assets, loan_balances = [], [], []
land_values, bldg_values = [], []
free_cash_annual = []  # 年間の自由に使えるお金
car_purchases_dict = {car1_age: car1_cost, car2_age: car2_cost}

for age in years:
    # 本人・妻の額面年収
    gross_self = income_at_age(age, current_age, income_now, income_after, years_to_raise, raise_until_age, raise_rate)
    gross_sp   = spouse_income_at_age(age, spouse_start_age, spouse_income, spouse_growth)
    gross_hh   = gross_self + gross_sp

    # 税・社保（本人＋妻それぞれ計算→合算）
    si1, it1, rt1, net1 = taxes_and_net(gross_self, salary_deduction_rate, salary_deduction_min,
                                        basic_deduction, resident_tax_rate, income_tax_eff_rate, social_ins_rate)
    si2, it2, rt2, net2 = taxes_and_net(gross_sp, salary_deduction_rate, salary_deduction_min,
                                        basic_deduction, resident_tax_rate, income_tax_eff_rate, social_ins_rate)

    si = si1 + si2
    itax = it1 + it2
    rtax = rt1 + rt2
    net_income = net1 + net2

    # 教育費
    c1_age = age - child1_birth_age
    c2_age = age - child2_birth_age
    edu1 = child_cost_by_age(c1_age, kg_cost, elem_cost, jhs_cost, hs_cost, univ_cost, living_add) if c1_age >= 0 else 0
    edu2 = child_cost_by_age(c2_age, kg_cost, elem_cost, jhs_cost, hs_cost, univ_cost, living_add) if c2_age >= 0 else 0
    edu_total = edu1 + edu2

    # 住宅：購入イベント
    if age == house_age and house_price > 0:
        fin_asset -= down_payment
        loan_balance = max(0.0, house_price - down_payment)
        annual_payment = annuity_payment(loan_balance, mortgage_rate, mortgage_years)
        land_val = land0
        bldg_val = bldg0

    # 住宅費（元利返済＋固定資産税等＋30年維持費の年割り）
    housing_cost = 0.0
    if house_age <= age < house_age + mortgage_years and loan_balance > 0:
        interest = loan_balance * (mortgage_rate/100.0)
        principal_pay = max(0.0, annual_payment - interest)
        principal_pay = min(principal_pay, loan_balance)
        loan_balance -= principal_pay
        housing_cost += annual_payment
    if age >= house_age and house_price > 0:
        housing_cost += prop_tax_annual + annual_maint_extra
        # 不動産価値変動
        land_val *= (1 + land_appreciation/100.0) if land_val > 0 else 0
        bldg_val *= (1 + bldg_decline/100.0) if bldg_val > 0 else 0

    # 車の購入（年一括支出・資産計上はしない）
    car_purchase = car_purchases_dict.get(age, 0.0)
    car_cost_year = car_running_cost + (car_purchase if car_purchase else 0.0)

    # 世帯の年間拠出（貯蓄）
    if mode.startswith("割合"):
        # 教育費ピーク年は低い貯蓄率
        if age < house_age:
            srate = save_rate_pre
        else:
            srate = save_rate_peak if edu_total >= peak_threshold else save_rate_post
        contrib = gross_hh * (srate/100.0)
    else:
        if age < house_age:
            contrib = float(save_amt_pre)
        else:
            contrib = float(save_amt_peak) if edu_total >= peak_threshold else float(save_amt_post)

    # 金融資産の運用（複利）＋拠出
    r = invest_return / 100.0
    fin_asset = fin_asset * (1 + r) + contrib
    # 車購入は金融資産から差し引く（現金支出）
    if car_purchase > 0:
        fin_asset -= car_purchase

    # 総資産（金融資産＋不動産−ローン）
    real_estate_value = land_val + bldg_val
    net_worth = fin_asset + real_estate_value - loan_balance

    # 年間の自由に使えるお金（手取り−住宅費−教育費−車維持費−拠出）
    free_cash = net_income - housing_cost - edu_total - car_running_cost - contrib
    # 車購入の年はさらに減る（購入分）
    free_cash -= (car_purchase if car_purchase else 0.0)

    # 記録
    gross_incomes.append(round(gross_hh, 1))
    spouse_incomes.append(round(gross_sp, 1))
    hh_incomes.append(round(gross_hh, 1))
    income_taxes.append(round(itax, 1))
    resident_taxes.append(round(rtax, 1))
    social_ins.append(round(si, 1))
    net_incomes.append(round(net_income, 1))
    edu_costs.append(round(edu_total, 1))
    house_costs.append(round(housing_cost, 1))
    car_costs.append(round(car_cost_year, 1))
    contribs.append(round(contrib, 1))
    fin_assets.append(round(fin_asset, 1))
    total_assets.append(round(net_worth, 1))
    loan_balances.append(round(loan_balance, 1))
    land_values.append(round(land_val, 1))
    bldg_values.append(round(bldg_val, 1))
    free_cash_annual.append(round(free_cash, 1))

# 結果テーブル
df = pd.DataFrame({
    "年齢": years,
    "世帯年収（額面・万円）": hh_incomes,
    "妻年収（万円）": spouse_incomes,
    "所得税（万円）": income_taxes,
    "住民税（万円）": resident_taxes,
    "社会保険（万円）": social_ins,
    "手取り（万円）": net_incomes,
    "教育費（万円）": edu_costs,
    "住宅費（万円/年）": house_costs,
    "車費用（万円/年：維持＋購入年は購入費含む）": car_costs,
    "投資拠出（万円）": contribs,
    "金融資産（万円）": fin_assets,
    "土地価値（万円）": land_values,
    "建物価値（万円）": bldg_values,
    "住宅ローン残高（万円）": loan_balances,
    "総資産（万円）": total_assets,
    "自由に使えるお金（万円/年）": free_cash_annual,
})

# ---------------------- サマリー（右側に可処分/自由額も表示） ----------------------
left, right = st.columns([1, 1], gap="large")

with left:
    st.metric(f"🎯 {target_age}歳の総資産（万円）", f"{df.iloc[-1]['総資産（万円）']:,}")
    st.metric(f"💰 {target_age}歳の金融資産（万円）", f"{df.iloc[-1]['金融資産（万円）']:,}")
    st.metric(f"🏡 不動産純資産（万円）", f"{(df.iloc[-1]['土地価値（万円）'] + df.iloc[-1]['建物価値（万円）'] - df.iloc[-1]['住宅ローン残高（万円）']):,}")

with right:
    latest_free = df.iloc[-1]["自由に使えるお金（万円/年）"]
    st.metric("🆓 自由に使えるお金（最新年・万円/年）", f"{latest_free:,}")
    st.caption("＝手取り −（住宅費 + 教育費 + 車維持費 + 投資拠出） −（購入年は車購入費）")
    # 月次換算
    st.metric("🗓️ 自由に使えるお金（最新年・万円/月）", f"{round(latest_free/12.0,1):,}")

st.download_button(
    "📥 結果CSVダウンロード（UTF-8）",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="simulation.csv",
    mime="text/csv",
)

# ---------------------- グラフ（すべて expander 内・Plotly でタッチ操作可） ----------------------
with st.expander("📈 年齢 × 資産（金融資産・不動産・ローン・総資産）", expanded=True):
    fig_assets = px.line(
        df, x="年齢",
        y=["金融資産（万円）", "土地価値（万円）", "建物価値（万円）", "住宅ローン残高（万円）", "総資産（万円）"],
        markers=True
    )
    fig_assets.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_assets, use_container_width=True, config={"responsive": True, "displayModeBar": True})

with st.expander("📊 年齢 × 費用（教育費・住宅費・車費用）", expanded=True):
    fig_costs = px.area(
        df, x="年齢",
        y=["教育費（万円）", "住宅費（万円/年）", "車費用（万円/年：維持＋購入年は購入費含む）"],
    )
    fig_costs.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_costs, use_container_width=True, config={"responsive": True, "displayModeBar": True})

with st.expander("💼 年齢 × 年収（額面）・手取り・自由に使えるお金", expanded=False):
    fig_income = px.line(
        df, x="年齢",
        y=["世帯年収（額面・万円）", "手取り（万円）", "自由に使えるお金（万円/年）"],
        markers=True
    )
    fig_income.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_income, use_container_width=True, config={"responsive": True, "displayModeBar": True})

with st.expander("🧾 年齢 × 税金推移（所得税・住民税・社会保険）", expanded=False):
    fig_tax = px.area(
        df, x="年齢",
        y=["所得税（万円）", "住民税（万円）", "社会保険（万円）"],
    )
    fig_tax.update_layout(legend_title_text="", hovermode="x unified")
    st.plotly_chart(fig_tax, use_container_width=True, config={"responsive": True, "displayModeBar": True})

with st.expander("📜 年次明細（万円）", expanded=False):
    st.dataframe(df, use_container_width=True)
