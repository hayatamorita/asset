# -*- coding: utf-8 -*-
# 保存して `streamlit run app.py` で起動してください

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="人生資産シミュレーション", layout="wide")

# ============ ヘッダー ============
st.title("🏠💹 人生資産シミュレーション（UTF-8 / 万円ベース）")
st.caption("※ 本ツールは簡易モデルです。税・社保・控除・減価は概算で、実態と乖離する場合があります。サイドバーで前提を調整してください。")

# ============ サイドバー（全パラメータ） ============
with st.sidebar:
    st.header("⚙️ 前提・パラメータ設定")

    # 期間・初期
    colA, colB = st.columns(2)
    with colA:
        current_age = st.number_input("現在年齢", 20, 80, 30, 1)
        target_age  = st.number_input("目標年齢（終了）", 40, 90, 60, 1)
    with colB:
        initial_assets = st.number_input("現在の金融資産（万円）", 0, 999999, 100, 10)

    # 年収（額面）推移
    st.subheader("年収（額面）の推移")
    col1, col2, col3 = st.columns(3)
    with col1:
        income_now = st.number_input("現在年収（万円）", 0, 99999, 800, 10)
    with col2:
        years_to_raise = st.number_input("何年後に年収UP", 0, 20, 3, 1)
        income_after   = st.number_input("UP後の年収（万円）", 0, 99999, 1000, 10)
    with col3:
        raise_until_age = st.number_input("年収の年率上昇 適用上限年齢", 30, 70, 40, 1)
        raise_rate      = st.number_input("年率上昇（%）", 0.0, 10.0, 1.0, 0.1)

    # 税・社会保険（簡易）
    st.subheader("税・社会保険（簡易モデル・調整可）")
    colt1, colt2, colt3 = st.columns(3)
    with colt1:
        salary_deduction_rate = st.number_input("給与所得控除率（%/額面）", 0.0, 50.0, 20.0, 0.5)
        salary_deduction_min  = st.number_input("給与所得控除の下限（万円）", 0, 1000, 55, 5)
    with colt2:
        basic_deduction       = st.number_input("基礎控除（万円）", 0, 200, 48, 1)
        resident_tax_rate     = st.number_input("住民税率（%・一律）", 0.0, 20.0, 10.0, 0.5)
    with colt3:
        income_tax_eff_rate   = st.number_input("所得税 実効率（%・概算）", 0.0, 40.0, 8.0, 0.5)
        social_ins_rate       = st.number_input("社会保険料率（%・概算）", 0.0, 30.0, 15.0, 0.5)

    # 住宅（資産評価を含める）
    st.subheader("住宅（総資産に土地・建物を計上、ローンは負債）")
    colh1, colh2, colh3 = st.columns(3)
    with colh1:
        house_age   = st.number_input("購入年齢", 25, 70, 37, 1)
        house_price = st.number_input("購入価格（万円）", 0, 999999, 5000, 50)  # 5000万円
        down_payment = st.number_input("頭金（万円）", 0, 999999, 500, 50)
    with colh2:
        mortgage_rate  = st.number_input("住宅ローン金利（年%）", 0.0, 5.0, 1.0, 0.1)
        mortgage_years = st.number_input("ローン年数", 5, 45, 35, 1)
        prop_tax_annual = st.number_input("固定資産税・維持費/年（万円）", 0, 300, 30, 5)
    with colh3:
        land_ratio = st.number_input("土地比率（%・購入価格に対して）", 0.0, 100.0, 40.0, 1.0)
        land_appreciation = st.number_input("土地 年率変動（%）", -5.0, 10.0, 0.0, 0.1)
        bldg_decline = st.number_input("建物 年率変動（%・マイナス推奨）", -10.0, 10.0, -1.0, 0.1)

    # 子ども・教育費（1人あたり/年）
    st.subheader("子ども・教育費（1人あたり/年）")
    colc1, colc2 = st.columns(2)
    with colc1:
        child1_birth_age = st.number_input("第一子 出産（親の年齢）", 20, 60, 30, 1)
        child2_birth_age = st.number_input("第二子 出産（親の年齢）", 20, 60, 33, 1)
        kg_cost   = st.number_input("幼稚園（3〜6歳）", 0, 500, 70, 5)
        elem_cost = st.number_input("小学校（7〜12歳）", 0, 500, 60, 5)
    with colc2:
        jhs_cost  = st.number_input("中学（13〜15歳）", 0, 500, 150, 5)
        hs_cost   = st.number_input("高校（16〜18歳）", 0, 500, 150, 5)
        univ_cost = st.number_input("大学（19〜22歳）", 0, 800, 250, 10)
        living_add = st.number_input("大学 仕送り等 追加", 0, 800, 50, 10)

    peak_threshold = st.number_input("“教育費ピーク”判定（合計/年）", 0, 2000, 300, 10)

    # 貯蓄と投資
    st.subheader("貯蓄と投資")
    mode = st.radio("貯蓄方法", ["割合で指定", "固定額で指定"], horizontal=True)
    if mode == "割合で指定":
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

# ============ 補助関数 ============
def annuity_payment(principal, annual_rate_pct, years):
    """元利均等返済の年額（万円）"""
    r = annual_rate_pct / 100.0
    n = int(years)
    if principal <= 0 or n <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

def income_at_age(age, start_age, inc0, inc_after, years_to_after, raise_until, raise_pct):
    """年齢ごとの額面年収（万円）"""
    years_from_now = age - start_age
    if years_from_now < years_to_after:
        return inc0
    inc = inc_after
    extra = max(0, min(age, raise_until) - (start_age + years_to_after))
    return inc * ((1 + raise_pct/100.0) ** extra)

def child_cost_by_age(child_age, kg, elem, jhs, hs, univ, live_add):
    """子1人の年齢に応じた教育費（万円/年）"""
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

# ============ シミュレーション ============
years = list(range(current_age, target_age + 1))

# 初期値
fin_asset = float(initial_assets)   # 金融資産
loan_balance = 0.0                  # 住宅ローン残高
annual_payment = 0.0                # 年返済額（元利）
land_value0 = house_price * (land_ratio/100.0)
bldg_value0 = house_price - land_value0
land_value = 0.0
bldg_value = 0.0

# 資産・収入・費用トラック
gross_incomes, net_incomes = [], []
income_taxes, resident_taxes, social_ins = [], [], []
edu_costs, house_costs, contribs = [], [], []
fin_assets, total_assets, loan_balances = [], [], []
land_values, bldg_values = [], []

for age in years:
    # 年収（額面）
    gross = income_at_age(age, current_age, income_now, income_after, years_to_raise, raise_until_age, raise_rate)

    # 社会保険
    si = gross * (social_ins_rate/100.0)

    # 給与所得控除
    salary_ded = max(salary_deduction_min, gross * (salary_deduction_rate/100.0))

    # 課税所得（概算）
    taxable_base = max(0.0, gross - si - salary_ded - basic_deduction)

    # 税（概算）
    itax = taxable_base * (income_tax_eff_rate/100.0)       # 所得税（実効）
    rtax = max(0.0, (gross - si - salary_ded) * (resident_tax_rate/100.0))  # 住民税（概算）

    # 手取り
    net = gross - (si + itax + rtax)

    # 教育費
    c1_age = age - child1_birth_age
    c2_age = age - child2_birth_age
    edu1 = child_cost_by_age(c1_age, kg_cost, elem_cost, jhs_cost, hs_cost, univ_cost, living_add) if c1_age >= 0 else 0
    edu2 = child_cost_by_age(c2_age, kg_cost, elem_cost, jhs_cost, hs_cost, univ_cost, living_add) if c2_age >= 0 else 0
    edu_total = edu1 + edu2

    # 住宅：購入年に頭金控除・ローン設定・資産計上
    if age == house_age and house_price > 0:
        fin_asset -= down_payment
        loan_balance = max(0.0, house_price - down_payment)
        annual_payment = annuity_payment(loan_balance, mortgage_rate, mortgage_years)
        land_value = land_value0
        bldg_value = bldg_value0

    # 住宅費（返済＋固定資産税等）
    housing_cost = 0.0
    if house_age <= age < house_age + mortgage_years and loan_balance > 0:
        # 年利計算（単純化：年次）
        interest = loan_balance * (mortgage_rate/100.0)
        principal_pay = max(0.0, annual_payment - interest)
        principal_pay = min(principal_pay, loan_balance)  # 最終年調整
        loan_balance -= principal_pay
        housing_cost += annual_payment
    if age >= house_age and house_price > 0:
        housing_cost += prop_tax_annual
        # 資産価値変動
        land_value *= (1 + land_appreciation/100.0) if land_value > 0 else 0
        bldg_value *= (1 + bldg_decline/100.0) if bldg_value > 0 else 0

    # 拠出（貯蓄）
    if mode == "割合で指定":
        if age < house_age:
            srate = save_rate_pre
        else:
            srate = save_rate_peak if edu_total >= peak_threshold else save_rate_post
        contrib = gross * (srate/100.0)
    else:
        if age < house_age:
            contrib = float(save_amt_pre)
        else:
            contrib = float(save_amt_peak) if edu_total >= peak_threshold else float(save_amt_post)

    # 金融資産の運用（年次複利）
    r = invest_return / 100.0
    fin_asset = fin_asset * (1 + r) + contrib

    # 総資産（= 金融資産 + 不動産価値 - ローン残高）
    real_estate_value = land_value + bldg_value
    net_worth = fin_asset + real_estate_value - loan_balance

    # 記録
    gross_incomes.append(round(gross, 1))
    income_taxes.append(round(itax, 1))
    resident_taxes.append(round(rtax, 1))
    social_ins.append(round(si, 1))
    net_incomes.append(round(net, 1))
    edu_costs.append(round(edu_total, 1))
    house_costs.append(round(housing_cost, 1))
    contribs.append(round(contrib, 1))
    fin_assets.append(round(fin_asset, 1))
    total_assets.append(round(net_worth, 1))
    loan_balances.append(round(loan_balance, 1))
    land_values.append(round(land_value, 1))
    bldg_values.append(round(bldg_value, 1))

# 結果テーブル
df = pd.DataFrame({
    "年齢": years,
    "年収（額面・万円）": gross_incomes,
    "所得税（万円）": income_taxes,
    "住民税（万円）": resident_taxes,
    "社会保険（万円）": social_ins,
    "手取り（万円）": net_incomes,
    "教育費（万円）": edu_costs,
    "住宅費（万円/年）": house_costs,
    "投資拠出（万円）": contribs,
    "金融資産（万円）": fin_assets,
    "土地価値（万円）": land_values,
    "建物価値（万円）": bldg_values,
    "住宅ローン残高（万円）": loan_balances,
    "総資産（万円）": total_assets,
})

# ============ サマリー ============
st.metric("🎯 最終時点の総資産（万円）", f"{df.iloc[-1]['総資産（万円）']:,}")
st.metric("💰 最終時点の金融資産（万円）", f"{df.iloc[-1]['金融資産（万円）']:,}")
st.metric("🏡 不動産純資産（万円）", f"{(df.iloc[-1]['土地価値（万円）'] + df.iloc[-1]['建物価値（万円）'] - df.iloc[-1]['住宅ローン残高（万円）']):,}")

st.download_button(
    "📥 結果CSVダウンロード（UTF-8）",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="simulation.csv",
    mime="text/csv",
)

# ============ グラフ（全て expander 内） ============
with st.expander("📈 年齢 × 資産（金融資産・不動産・総資産）", expanded=True):
    st.line_chart(
        df.set_index("年齢")[["金融資産（万円）", "土地価値（万円）", "建物価値（万円）", "住宅ローン残高（万円）", "総資産（万円）"]]
    )

with st.expander("📊 年齢 × 費用（教育費・住宅費）", expanded=True):
    st.area_chart(
        df.set_index("年齢")[["教育費（万円）", "住宅費（万円/年）"]]
    )

with st.expander("💼 年齢 × 年収（額面）と手取り", expanded=False):
    st.line_chart(
        df.set_index("年齢")[["年収（額面・万円）", "手取り（万円）"]]
    )

with st.expander("🧾 年齢 × 税金推移（所得税・住民税・社会保険）", expanded=False):
    st.area_chart(
        df.set_index("年齢")[["所得税（万円）", "住民税（万円）", "社会保険（万円）"]]
    )

# 明細テーブル
st.divider()
st.subheader("年次明細（万円）")
st.dataframe(df, use_container_width=True)

