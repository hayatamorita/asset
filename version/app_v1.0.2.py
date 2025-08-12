# -*- coding: utf-8 -*-
# 保存して `streamlit run app.py` で起動してください

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="人生資産シミュレーション", layout="wide")

# --------- ちょいCSS（入力ボックスの高さ・レイアウト微調整） ----------
st.markdown("""
<style>
/* number_input の高さを揃える（おおよそ） */
div[data-baseweb="input"] input {
  min-height: 38px;
}
/* サイドバー見出しの間隔 */
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h2 {
  margin-top: 0.5rem;
}
/* 凡例を下に余裕を持たせる */
.vega-embed details, .vega-embed .vega-actions { display: none; }
</style>
""", unsafe_allow_html=True)

# =========================
# ヘッダー
# =========================
st.title("🏠💹 人生資産シミュレーション（UTF-8）")
st.caption("※ 本ツールは簡易モデルです。税・社保・控除・資産評価は概算。必要に応じて調整してください。")

# =========================
# サイドバー（すべての設定パラメータ）
# =========================
with st.sidebar:
    st.header("⚙️ パラメータ設定")

    # 期間・初期資産
    st.subheader("期間・初期資産")
    colA, colB = st.columns(2)
    with colA:
        current_age = st.number_input("現在年齢", 20, 80, 30, 1)
        target_age  = st.number_input("目標年齢（終了）", 40, 90, 60, 1)
    with colB:
        initial_assets = st.number_input("現在の金融資産（万円）", 0, 999999, 100, 10)

    # 本人の年収（額面）
    st.subheader("本人：年収（額面）推移")
    col1, col2, col3 = st.columns(3)
    with col1:
        income_now = st.number_input("現在年収（万円）", 0, 99999, 800, 10)
    with col2:
        years_to_raise = st.number_input("何年後に年収UP", 0, 20, 3, 1)
        income_after   = st.number_input("UP後の年収（万円）", 0, 99999, 1000, 10)
    with col3:
        raise_until_age = st.number_input("年収の年率上昇 適用上限年齢", 30, 70, 40, 1)
        raise_rate      = st.number_input("年率上昇（%）", 0.0, 10.0, 1.0, 0.1)

    # 妻の年収（額面）
    st.subheader("妻：年収（額面）")
    colw1, colw2 = st.columns(2)
    with colw1:
        spouse_start_age = st.number_input("開始年齢（妻の就労開始）", 20, 80, 32, 1)
    with colw2:
        spouse_income = st.number_input("妻の年収（万円）", 0, 99999, 300, 10)

    # 税・社会保険（概算）
    st.subheader("税・社会保険（概算パラメータ）")
    colt1, colt2, colt3 = st.columns(3)
    with colt1:
        salary_deduction_rate = st.number_input("給与所得控除率（%/額面）", 0.0, 50.0, 20.0, 0.5)
        salary_deduction_min  = st.number_input("給与所得控除の下限（万円）", 0, 1000, 55, 5)
    with colt2:
        basic_deduction       = st.number_input("基礎控除（万円）", 0, 200, 48, 1)
        resident_tax_rate     = st.number_input("住民税率（%・一律）", 0.0, 20.0, 10.0, 0.5)
    with colt3:
        income_tax_eff_rate   = st.number_input("所得税 実効率（%）", 0.0, 40.0, 8.0, 0.5)
        social_ins_rate       = st.number_input("社会保険料率（%）", 0.0, 30.0, 15.0, 0.5)

    # 住宅（資産・負債・維持費）
    st.subheader("住宅（総資産に土地・建物を計上、ローンは負債）")
    colh1, colh2, colh3 = st.columns(3)
    with colh1:
        house_age   = st.number_input("購入年齢", 25, 70, 37, 1)
        house_price = st.number_input("購入価格（万円）", 0, 999999, 5000, 50)  # 5000万円
        down_payment = st.number_input("頭金（万円）", 0, 999999, 500, 50)
    with colh2:
        mortgage_rate  = st.number_input("住宅ローン金利（年%）", 0.0, 5.0, 1.0, 0.1)
        mortgage_years = st.number_input("ローン年数", 5, 45, 35, 1)
        prop_tax_annual = st.number_input("固定資産税/年（万円）", 0, 300, 20, 5)
    with colh3:
        land_ratio = st.number_input("土地比率（%/購入額）", 0.0, 100.0, 40.0, 1.0)
        land_appreciation = st.number_input("土地 年率変動（%）", -5.0, 10.0, 0.0, 0.1)
        bldg_decline = st.number_input("建物 年率変動（%・マイナス推奨）", -10.0, 10.0, -2.0, 0.1)

    colm = st.columns(2)
    with colm[0]:
        maintain_30yr_total = st.number_input("30年維持費 合計（万円）", 0, 100000, 800, 10)
    with colm[1]:
        misc_house_annual = st.number_input("その他 住宅維持費/年（万円）", 0, 1000, 10, 5)

    # 教育費（1人あたり/年）
    st.subheader("教育費（1人あたり・万円/年）")
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

    # 車
    st.subheader("車の購入")
    colv1, colv2 = st.columns(2)
    with colv1:
        car_buy_age = st.number_input("購入年齢（車）", 20, 80, 38, 1)
    with colv2:
        car_price   = st.number_input("購入価格（万円）", 0, 99999, 400, 10)

    # 貯蓄と投資
    st.subheader("貯蓄と投資")
    mode = st.radio("貯蓄方法", ["割合で指定", "固定額で指定"], horizontal=True, index=1)
    if mode == "割合で指定":
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            save_rate_pre  = st.number_input("購入前の貯蓄率（%）", 0.0, 90.0, 25.0, 1.0)
        with colp2:
            save_rate_post = st.number_input("購入後の貯蓄率（%）", 0.0, 90.0, 20.0, 1.0)
        with colp3:
            save_rate_peak = st.number_input("教育費ピーク時の貯蓄率（%）", 0.0, 90.0, 15.0, 1.0)
        save_amt_pre = save_amt_post = save_amt_peak = None
    else:
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            save_amt_pre  = st.number_input("購入前の貯蓄額（万円/年）", 0, 100000, 150, 10)
        with colp2:
            save_amt_post = st.number_input("購入後の貯蓄額（万円/年）", 0, 100000, 150, 10)
        with colp3:
            save_amt_peak = st.number_input("教育費ピーク時の貯蓄額（万円/年）", 0, 100000, 100, 10)
        save_rate_pre = save_rate_post = save_rate_peak = None

    invest_return = st.number_input("投資年率（税引後, %）", 0.0, 20.0, 4.0, 0.1)

# =========================
# 補助関数
# =========================
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
    extra = max(0, min(age, raise_until) - (start_age + years_to_after))
    return inc_after * ((1 + raise_pct/100.0) ** extra)

def taxes_and_net(gross, salary_deduction_rate, salary_deduction_min, basic_deduction,
                  income_tax_eff_rate, resident_tax_rate, social_ins_rate):
    si = gross * (social_ins_rate/100.0)
    salary_ded = max(salary_deduction_min, gross * (salary_deduction_rate/100.0))
    taxable_base = max(0.0, gross - si - salary_ded - basic_deduction)
    itax = taxable_base * (income_tax_eff_rate/100.0)
    rtax = max(0.0, (gross - si - salary_ded) * (resident_tax_rate/100.0))
    net = gross - (si + itax + rtax)
    return si, itax, rtax, net

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

# =========================
# シミュレーション
# =========================
years = list(range(current_age, target_age + 1))

# 初期状態
fin_asset = float(initial_assets)     # 金融資産
loan_balance = 0.0                    # 住宅ローン残
annual_payment = 0.0                  # 年返済
land_value = 0.0
bldg_value = 0.0
land_value0 = house_price * (land_ratio/100.0)
bldg_value0 = house_price - land_value0
maint_per_year = (maintain_30yr_total / 30.0) if maintain_30yr_total > 0 else 0.0

# 記録
gross_incomes, net_incomes = [], []
income_taxes, resident_taxes, social_ins = [], [], []
gross_incomes_sp, net_incomes_sp = [], []
income_taxes_sp, resident_taxes_sp, social_ins_sp = [], [], []

edu_costs, house_costs, contribs = [], [], []
fin_assets, total_assets, loan_balances = [], [], []
land_values, bldg_values = [], []
discretionary_month = []  # 月々の自由に使える金額（万円/月）

for age in years:
    # 本人の額面年収
    gross_self = income_at_age(age, current_age, income_now, income_after, years_to_raise, raise_until_age, raise_rate)

    # 妻の額面年収
    gross_spouse = spouse_income if age >= spouse_start_age else 0.0

    # 税・社会保険（個人別に計算）
    si_s, itx_s, rtx_s, net_s = taxes_and_net(
        gross_self, salary_deduction_rate, salary_deduction_min, basic_deduction,
        income_tax_eff_rate, resident_tax_rate, social_ins_rate
    )
    si_p, itx_p, rtx_p, net_p = taxes_and_net(
        gross_spouse, salary_deduction_rate, salary_deduction_min, basic_deduction,
        income_tax_eff_rate, resident_tax_rate, social_ins_rate
    )

    gross_total = gross_self + gross_spouse
    net_total   = net_s + net_p

    # 教育費
    c1_age = age - child1_birth_age
    c2_age = age - child2_birth_age
    edu1 = child_cost_by_age(c1_age, kg_cost, elem_cost, jhs_cost, hs_cost, univ_cost, living_add) if c1_age >= 0 else 0
    edu2 = child_cost_by_age(c2_age, kg_cost, elem_cost, jhs_cost, hs_cost, univ_cost, living_add) if c2_age >= 0 else 0
    edu_total = edu1 + edu2

    # 住宅：購入処理
    if age == house_age and house_price > 0:
        fin_asset -= down_payment
        loan_balance = max(0.0, house_price - down_payment)
        annual_payment = annuity_payment(loan_balance, mortgage_rate, mortgage_years)
        land_value = land_value0
        bldg_value = bldg_value0

    # 住宅費（返済＋税＋維持）
    housing_cost = 0.0
    if house_age <= age < house_age + mortgage_years and loan_balance > 0:
        interest = loan_balance * (mortgage_rate/100.0)
        principal_pay = max(0.0, min(annual_payment - interest, loan_balance))
        loan_balance -= principal_pay
        housing_cost += annual_payment
    if age >= house_age and house_price > 0:
        housing_cost += prop_tax_annual + misc_house_annual + maint_per_year
        # 資産価値の変動
        if land_value > 0:
            land_value *= (1 + land_appreciation/100.0)
        if bldg_value > 0:
            bldg_value *= (1 + bldg_decline/100.0)

    # 車購入（支出扱い）
    if age == car_buy_age and car_price > 0:
        fin_asset -= car_price  # 単純に支出として計上

    # 拠出（貯蓄）
    if mode == "割合で指定":
        if age < house_age:
            srate = save_rate_pre
        else:
            srate = save_rate_peak if edu_total >= peak_threshold else save_rate_post
        contrib = gross_total * (srate/100.0)
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

    # 月の自由に使える金額（万円/月）
    free_month = max(0.0, (net_total - edu_total - housing_cost - contrib) / 12.0)

    # 記録
    gross_incomes.append(round(gross_self, 1))
    income_taxes.append(round(itx_s, 1))
    resident_taxes.append(round(rtx_s, 1))
    social_ins.append(round(si_s, 1))
    net_incomes.append(round(net_s, 1))

    gross_incomes_sp.append(round(gross_spouse, 1))
    income_taxes_sp.append(round(itx_p, 1))
    resident_taxes_sp.append(round(rtx_p, 1))
    social_ins_sp.append(round(si_p, 1))
    net_incomes_sp.append(round(net_p, 1))

    edu_costs.append(round(edu_total, 1))
    house_costs.append(round(housing_cost, 1))
    contribs.append(round(contrib, 1))
    fin_assets.append(round(fin_asset, 1))
    total_assets.append(round(net_worth, 1))
    loan_balances.append(round(loan_balance, 1))
    land_values.append(round(land_value, 1))
    bldg_values.append(round(bldg_value, 1))
    discretionary_month.append(round(free_month, 2))

# 結果テーブル
df = pd.DataFrame({
    "年齢": years,
    "本人 年収（額面・万円）": gross_incomes,
    "本人 所得税（万円）": income_taxes,
    "本人 住民税（万円）": resident_taxes,
    "本人 社会保険（万円）": social_ins,
    "本人 手取り（万円）": net_incomes,

    "妻 年収（額面・万円）": gross_incomes_sp,
    "妻 所得税（万円）": income_taxes_sp,
    "妻 住民税（万円）": resident_taxes_sp,
    "妻 社会保険（万円）": social_ins_sp,
    "妻 手取り（万円）": net_incomes_sp,

    "教育費（万円）": edu_costs,
    "住宅費（万円/年）": house_costs,
    "投資拠出（万円）": contribs,
    "金融資産（万円）": fin_assets,
    "土地価値（万円）": land_values,
    "建物価値（万円）": bldg_values,
    "住宅ローン残高（万円）": loan_balances,
    "総資産（万円）": total_assets,
    "自由に使える金額（万円/月）": discretionary_month,
})

# =========================
# サマリー＆右側のメトリクス
# =========================
left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("サマリー")
    st.metric(f"🎯 {target_age}歳時点の総資産（万円）", f"{df.iloc[-1]['総資産（万円）']:,}")
    st.metric(f"💰 {target_age}歳時点の金融資産（万円）", f"{df.iloc[-1]['金融資産（万円）']:,}")
    re_net = df.iloc[-1]['土地価値（万円）'] + df.iloc[-1]['建物価値（万円）'] - df.iloc[-1]['住宅ローン残高（万円）']
    st.metric(f"🏡 不動産純資産（万円）", f"{re_net:,}")

with right:
    st.subheader("今月の自由に使える金額（目標年齢時点・万円/月）")
    st.metric("自由に使える金額", f"{df.iloc[-1]['自由に使える金額（万円/月）']:,}")

# =========================
# グラフ（右側・2列・expander 内 / Altair interactive）
# =========================
c1, c2 = st.columns(2, gap="large")

def line_chart_altair(df_long, x, y, color, title):
    return (alt.Chart(df_long)
            .mark_line()
            .encode(
                x=alt.X(x, title="年齢"),
                y=alt.Y(y, title=None),
                color=alt.Color(color, title=None, legend=alt.Legend(orient='bottom')),
                tooltip=[x, color, y]
            )
            .properties(title=title, height=280)
            .interactive())

def area_chart_altair(df_long, x, y, color, title, stack=True):
    return (alt.Chart(df_long)
            .mark_area(opacity=0.7)
            .encode(
                x=alt.X(x, title="年齢"),
                y=alt.Y(y, stack=stack, title=None),
                color=alt.Color(color, title=None, legend=alt.Legend(orient='bottom')),
                tooltip=[x, color, y]
            )
            .properties(title=title, height=280)
            .interactive())

# データ整形（ロング）
def to_long(df, value_cols, var_name="系列", value_name="値"):
    d = df[["年齢"] + value_cols].melt("年齢", var_name=var_name, value_name=value_name)
    return d

with c1:
    with st.expander("📈 年齢 × 資産（金融資産・不動産・総資産・ローン残）", expanded=True):
        cols = ["金融資産（万円）", "土地価値（万円）", "建物価値（万円）", "住宅ローン残高（万円）", "総資産（万円）"]
        d = to_long(df, cols, "資産項目", "金額（万円）")
        st.altair_chart(line_chart_altair(d, "年齢", "金額（万円）", "資産項目", "資産の推移"), use_container_width=True)

    with st.expander("💼 年齢 × 年収（額面）と手取り（本人・妻）", expanded=False):
        cols = ["本人 年収（額面・万円）", "本人 手取り（万円）", "妻 年収（額面・万円）", "妻 手取り（万円）"]
        d = to_long(df, cols, "年収項目", "金額（万円）")
        st.altair_chart(line_chart_altair(d, "年齢", "金額（万円）", "年収項目", "年収と手取りの推移"), use_container_width=True)

with c2:
    with st.expander("📊 年齢 × 費用（教育費・住宅費・投資拠出）", expanded=True):
        cols = ["教育費（万円）", "住宅費（万円/年）", "投資拠出（万円）"]
        d = to_long(df, cols, "費用項目", "金額（万円/年）")
        st.altair_chart(area_chart_altair(d, "年齢", "金額（万円/年）", "費用項目", "費用の推移"), use_container_width=True)

    with st.expander("🧾 年齢 × 税金推移（本人・妻）", expanded=False):
        cols = ["本人 所得税（万円）", "本人 住民税（万円）", "本人 社会保険（万円）",
                "妻 所得税（万円）", "妻 住民税（万円）", "妻 社会保険（万円）"]
        d = to_long(df, cols, "税項目", "金額（万円/年）")
        st.altair_chart(area_chart_altair(d, "年齢", "金額（万円/年）", "税項目", "税金の推移", stack=False), use_container_width=True)

# 明細テーブル
st.divider()
st.subheader("年次明細（万円）")
st.dataframe(df, use_container_width=True)

# 一番下：CSVダウンロード（UTF-8）
st.download_button(
    "📥 結果CSVダウンロード（UTF-8）",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="simulation.csv",
    mime="text/csv",
)
