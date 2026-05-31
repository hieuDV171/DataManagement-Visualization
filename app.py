import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Bảng điều khiển Superstore",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSV_PATH = os.path.join(os.path.dirname(__file__), "SuperStoreOrders.csv")

COLUMN_LABELS_VI = {
    "order_id": "Mã đơn hàng",
    "order_date": "Ngày đặt hàng",
    "ship_date": "Ngày giao hàng",
    "ship_mode": "Phương thức giao hàng",
    "customer_name": "Tên khách hàng",
    "segment": "Phân khúc",
    "state": "Bang/Tỉnh",
    "country": "Quốc gia",
    "market": "Thị trường",
    "region": "Khu vực",
    "product_id": "Mã sản phẩm",
    "category": "Danh mục",
    "sub_category": "Danh mục con",
    "product_name": "Tên sản phẩm",
    "sales": "Doanh thu",
    "quantity": "Số lượng",
    "discount": "Chiết khấu",
    "profit": "Lợi nhuận",
    "shipping_cost": "Chi phí vận chuyển",
    "order_priority": "Độ ưu tiên",
    "year": "Năm",
    "month": "Tháng",
    "month_start": "Mốc tháng",
    "quarter": "Quý",
    "delivery_days": "Số ngày giao hàng",
    "profit_margin": "Biên lợi nhuận",
    "is_loss": "Đơn lỗ",
    "order_count": "Số đơn",
}


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")
    for col in ["sales", "quantity", "discount", "profit", "shipping_cost", "year"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["order_date", "sales", "profit"])
    df["year"] = df["year"].fillna(df["order_date"].dt.year).astype(int)
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    df["month_start"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["quarter"] = df["order_date"].dt.to_period("Q").astype(str)
    df["delivery_days"] = (df["ship_date"] - df["order_date"]).dt.days
    df["profit_margin"] = df["profit"] / df["sales"].replace(0, pd.NA)
    df["is_loss"] = df["profit"] < 0
    df["order_count"] = 1
    return df


def vn_money(value: float) -> str:
    return f"${value:,.0f}"


def vn_number(value: float) -> str:
    return f"{value:,.0f}"


def apply_vietnamese_labels(frame: pd.DataFrame) -> pd.DataFrame:
    rename_map = {k: v for k, v in COLUMN_LABELS_VI.items() if k in frame.columns}
    return frame.rename(columns=rename_map)


def country_to_iso3(country: str) -> str | None:
    if not isinstance(country, str) or not country.strip():
        return None

    try:
        import pycountry
    except ImportError:
        return None

    try:
        return pycountry.countries.search_fuzzy(country)[0].alpha_3
    except LookupError:
        return None


def reset_filters() -> None:
    st.session_state["f_date_range"] = (min_date, max_date)
    for key, options in [
        ("f_year", year_options),
        ("f_market", market_options),
        ("f_region", region_options),
        ("f_segment", segment_options),
        ("f_category", category_options),
        ("f_ship_mode", ship_mode_options),
    ]:
        st.session_state[key] = list(options)
        for option in options:
            st.session_state[f"{key}_{str(option)}"] = True
    st.rerun()


def compact_multi_select(label: str, options: list, state_key: str):
    if state_key not in st.session_state:
        st.session_state[state_key] = list(options)

    checkbox_keys = [f"{state_key}_{str(option)}" for option in options]
    if not any(key in st.session_state for key in checkbox_keys):
        selected_defaults = set(st.session_state.get(state_key, []))
        for option in options:
            st.session_state[f"{state_key}_{str(option)}"] = option in selected_defaults

    selected = list(st.session_state.get(state_key, []))
    summary = f"{len(selected)} mục đã chọn" if selected else "Chưa chọn mục nào"

    with st.sidebar.popover(f"{label}: {summary}"):
        if st.button(f"Chọn tất cả {label.lower()}", key=f"{state_key}_all", width="stretch"):
            st.session_state[state_key] = list(options)
            for option in options:
                st.session_state[f"{state_key}_{str(option)}"] = True
            st.rerun()
        if st.button(f"Bỏ chọn tất cả {label.lower()}", key=f"{state_key}_none", width="stretch"):
            st.session_state[state_key] = []
            for option in options:
                st.session_state[f"{state_key}_{str(option)}"] = False
            st.rerun()

        chosen = []
        with st.container(height=260, border=False):
            for option in options:
                option_label = str(option)
                checkbox_key = f"{state_key}_{option_label}"
                if checkbox_key in st.session_state:
                    checked = st.checkbox(option_label, key=checkbox_key)
                else:
                    checked = st.checkbox(option_label, value=(option in selected), key=checkbox_key)
                if checked:
                    chosen.append(option)

        if chosen != selected:
            st.session_state[state_key] = chosen
            st.rerun()

    return selected


if not os.path.exists(CSV_PATH):
    st.error(f"Không tìm thấy tệp dữ liệu: {CSV_PATH}")
    st.stop()


df = load_data(CSV_PATH)
min_date = df["order_date"].min().date()
max_date = df["order_date"].max().date()

st.markdown(
    """
    <style>
    .block-container { padding-top: 3.5rem; padding-bottom: 2.5rem; overflow: visible; }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #38bdf8 100%);
        color: white;
        border-radius: 24px;
        padding: 1.35rem 1.5rem;
        margin-bottom: 1.5rem; /* thêm khoảng cách để không chèn tabs */
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
        overflow: visible;
    }
    .hero h1 { font-size: 2rem; margin-bottom: 0.25rem; }
    .hero p { margin: 0; opacity: 0.9; font-size: 0.98rem; }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0.25rem 0 0.5rem 0;
    }
    .section-subtitle {
        color: #64748b;
        font-size: 0.88rem;
        margin-bottom: 0.75rem;
    }
    .metric-card {
        background: white;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 1rem 1rem 0.85rem 1rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    }
    .metric-label { color: #64748b; font-size: 0.82rem; margin-bottom: 0.25rem; }
    .metric-value { color: #0f172a; font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
    .metric-delta { color: #475569; font-size: 0.78rem; margin-top: 0.25rem; }
    .insight-box {
        background: #eff6ff;
        border-left: 5px solid #2563eb;
        border-radius: 14px;
        padding: 0.95rem 1rem;
        margin-top: 0.25rem;
    }
    .insight-box strong { color: #1d4ed8; }
    .filter-card {
        background: white;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 0.85rem 0.9rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
        margin-bottom: 0.75rem;
    }
    .insight-box { position: relative; z-index: 10; margin-top: 1rem; }
    .metric-card { margin-bottom: 1rem; }
    .main, [data-testid="stAppViewContainer"], .reportview-container { overflow: visible; }
    div[data-testid="stHorizontalBlock"] .stButton button {
        width: 100%;
        border-radius: 999px;
        padding: 0.62rem 0.9rem;
        background: #f1f5f9;
        border: 1px solid rgba(15, 23, 42, 0.10);
        color: #0f172a;
        font-weight: 600;
        box-shadow: 0 1px 6px rgba(15,23,42,0.04);
    }
    div[data-testid="stHorizontalBlock"] .stButton button:hover {
        background: #e2e8f0;
        border-color: rgba(15, 23, 42, 0.14);
    }
    div[data-testid="stHorizontalBlock"] .stButton button:focus:not(:focus-visible) {
        border-color: rgba(15, 23, 42, 0.10);
        box-shadow: 0 1px 6px rgba(15,23,42,0.04);
    }
    div[data-testid="stHorizontalBlock"] .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
        border-color: #1e40af;
        color: #ffffff;
        box-shadow: 0 10px 22px rgba(37,99,235,0.18);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>Bảng điều khiển hiệu suất bán hàng Superstore</h1>
        <p>Phân tích doanh thu, lợi nhuận, chiết khấu, địa lý, sản phẩm và vận hành.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

year_options = sorted(df["year"].dropna().astype(int).unique().tolist())
market_options = sorted(df["market"].dropna().unique().tolist())
region_options = sorted(df["region"].dropna().unique().tolist())
segment_options = sorted(df["segment"].dropna().unique().tolist())
category_options = sorted(df["category"].dropna().unique().tolist())
ship_mode_options = sorted(df["ship_mode"].dropna().unique().tolist())

st.sidebar.header("Bộ lọc")
if st.sidebar.button("Đặt lại bộ lọc", width="stretch"):
    reset_filters()

st.sidebar.markdown("<div class='filter-card'>", unsafe_allow_html=True)
selected_date_range = st.sidebar.date_input(
    "Khoảng ngày đặt hàng",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="f_date_range",
)
selected_years = compact_multi_select("Năm", year_options, "f_year")
selected_markets = compact_multi_select("Thị trường", market_options, "f_market")
selected_regions = compact_multi_select("Khu vực", region_options, "f_region")
selected_segments = compact_multi_select("Phân khúc", segment_options, "f_segment")
selected_categories = compact_multi_select("Danh mục", category_options, "f_category")
selected_ship_modes = compact_multi_select("Phương thức giao hàng", ship_mode_options, "f_ship_mode")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date, end_date = min_date, max_date

filtered = df[
    df["order_date"].dt.date.between(start_date, end_date)
    & df["year"].isin(selected_years)
    & df["market"].isin(selected_markets)
    & df["region"].isin(selected_regions)
    & df["segment"].isin(selected_segments)
    & df["category"].isin(selected_categories)
    & df["ship_mode"].isin(selected_ship_modes)
].copy()

if filtered.empty:
    st.warning("Không còn dữ liệu sau khi lọc. Hãy điều chỉnh bộ lọc ở thanh bên.")
    st.stop()

sales = float(filtered["sales"].sum())
profit = float(filtered["profit"].sum())
margin = profit / sales if sales else 0
orders = int(filtered["order_id"].nunique())
avg_order_value = sales / orders if orders else 0
avg_discount = float(filtered["discount"].mean())
shipping_cost = float(filtered["shipping_cost"].sum())
loss_orders = int(filtered.loc[filtered["is_loss"], "order_id"].nunique())
delivery_avg = float(filtered["delivery_days"].mean())

c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    ("Tổng doanh thu", vn_money(sales), f"{len(filtered):,} dòng dữ liệu"),
    ("Tổng lợi nhuận", vn_money(profit), f"{loss_orders:,} đơn lỗ"),
    ("Biên lợi nhuận", f"{margin:.1%}", f"Chiết khấu TB {avg_discount:.1%}"),
    ("Số đơn hàng", vn_number(orders), f"AOV {vn_money(avg_order_value)}"),
    ("Chi phí vận chuyển", vn_money(shipping_cost), f"TG giao hàng TB {delivery_avg:.1f} ngày"),
]
for col, metric in zip([c1, c2, c3, c4, c5], metrics):
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{metric[0]}</div>
                <div class="metric-value">{metric[1]}</div>
                <div class="metric-delta">{metric[2]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

best_category = filtered.groupby("category", dropna=False)["sales"].sum().sort_values(ascending=False).head(1)
best_region = filtered.groupby("region", dropna=False)["profit"].sum().sort_values(ascending=False).head(1)
peak_month = filtered.groupby("month_start", dropna=False)["sales"].sum().sort_values(ascending=False).head(1)
worst_subcat = filtered.groupby("sub_category", dropna=False)["profit"].sum().sort_values().head(1)
top_loss_subcats = filtered.groupby("sub_category", as_index=False)["profit"].sum().sort_values("profit").head(8)
pareto = filtered.groupby("sub_category", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
pareto["cum_sales"] = pareto["sales"].cumsum() / pareto["sales"].sum()
region_category = filtered.pivot_table(index="region", columns="category", values="sales", aggfunc="sum", fill_value=0)
category_profit = filtered.groupby("category", as_index=False)["profit"].sum().sort_values("profit", ascending=False)

insight_left, insight_right = st.columns([1.2, 1])
with insight_left:
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Nhận định chính:</strong> Danh mục <b>{best_category.index[0]}</b> dẫn đầu về doanh thu,
            khu vực <b>{best_region.index[0]}</b> tạo lợi nhuận cao nhất,
            trong khi nhóm <b>{worst_subcat.index[0]}</b> đang yếu nhất về lợi nhuận.
        </div>
        """,
        unsafe_allow_html=True,
    )
with insight_right:
    st.markdown(
        f"""
        <div class="insight-box">
            <strong>Tháng đỉnh:</strong> {peak_month.index[0].strftime('%m/%Y')} với doanh thu <b>{vn_money(float(peak_month.iloc[0]))}</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

tab_names = ["Tổng quan", "Địa lý", "Sản phẩm", "Khách hàng", "Vận hành"]
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = tab_names[0]

st.markdown('<div style="margin-top: 0.9rem;"></div>', unsafe_allow_html=True)
tab_columns = st.columns(len(tab_names), gap="small")
for tab_name, column in zip(tab_names, tab_columns):
    with column:
        st.button(
            tab_name,
            key=f"tab_{tab_name}",
            use_container_width=True,
            type="primary" if st.session_state["active_tab"] == tab_name else "secondary",
            on_click=lambda name=tab_name: st.session_state.__setitem__("active_tab", name),
        )

active_tab = st.session_state["active_tab"]

if active_tab == "Tổng quan":
    st.markdown('<div class="section-title">Tổng quan điều hành</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tập trung vào xu hướng và điểm nhấn quản trị.</div>', unsafe_allow_html=True)

    left, right = st.columns([1.4, 1])
    with left:
        monthly = filtered.groupby("month_start", as_index=False).agg({"sales": "sum", "profit": "sum"}).sort_values("month_start")
        monthly_long = monthly.melt(id_vars="month_start", value_vars=["sales", "profit"], var_name="metric", value_name="value")
        fig_trend = px.line(
            monthly_long,
            x="month_start",
            y="value",
            color="metric",
            markers=True,
            title="Xu hướng doanh thu và lợi nhuận theo tháng",
            color_discrete_map={"sales": "#2563eb", "profit": "#16a34a"},
        )
        fig_trend.update_layout(legend_title_text="", xaxis_title="", yaxis_title="USD", hovermode="x unified")
        fig_trend.for_each_trace(lambda trace: trace.update(name="Doanh thu" if trace.name == "sales" else "Lợi nhuận"))
        st.plotly_chart(fig_trend, width="stretch", key="chart_trend")

    with right:
        by_segment = filtered.groupby("segment", as_index=False).agg({"sales": "sum", "profit": "sum"}).sort_values("profit", ascending=False)
        fig_segment = px.bar(
            by_segment,
            x="segment",
            y="profit",
            color="sales",
            color_continuous_scale="Blues",
            title="Lợi nhuận theo phân khúc",
            text_auto=True,
        )
        fig_segment.update_layout(xaxis_title="", yaxis_title="Lợi nhuận", coloraxis_colorbar_title="Doanh thu")
        st.plotly_chart(fig_segment, width="stretch", key="chart_segment")

if active_tab == "Địa lý":
    st.markdown('<div class="section-title">Phân tích địa lý</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Khu vực nào tạo doanh thu và lợi nhuận tốt nhất.</div>', unsafe_allow_html=True)

    geo_left, geo_right = st.columns([1.15, 0.85])
    with geo_left:
        top_countries = filtered.groupby("country", as_index=False).agg({"sales": "sum", "profit": "sum"}).sort_values("sales", ascending=False).head(12)
        fig_country = px.bar(
            top_countries.sort_values("sales"),
            x="sales",
            y="country",
            orientation="h",
            color="profit",
            color_continuous_scale="RdYlGn",
            title="Top quốc gia theo doanh thu",
        )
        fig_country.update_layout(xaxis_title="Doanh thu", yaxis_title="", coloraxis_colorbar_title="Lợi nhuận")
        st.plotly_chart(fig_country, width="stretch", key="chart_country")

    with geo_right:
        map_df = filtered.groupby("country", as_index=False).agg({"sales": "sum", "profit": "sum"})
        map_df["iso3"] = map_df["country"].apply(country_to_iso3)
        map_df = map_df.dropna(subset=["iso3"])
        fig_map = px.choropleth(
            map_df,
            locations="iso3",
            locationmode="ISO-3",
            color="sales",
            hover_name="country",
            color_continuous_scale="Viridis",
            title="Doanh thu theo quốc gia",
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=45, b=0))
        st.plotly_chart(fig_map, width="stretch", key="chart_map")

    st.markdown('<div class="section-title">Heatmap khu vực x danh mục</div>', unsafe_allow_html=True)
    heat_df = region_category.reset_index()
    fig_heat = px.imshow(
        heat_df.set_index("region"),
        text_auto=True,
        color_continuous_scale="Blues",
        title="Doanh thu theo khu vực và danh mục",
        aspect="auto",
    )
    fig_heat.update_layout(xaxis_title="Danh mục", yaxis_title="Khu vực")
    st.plotly_chart(fig_heat, width="stretch", key="chart_heatmap")

if active_tab == "Sản phẩm":
    st.markdown('<div class="section-title">Phân tích sản phẩm</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Xem top danh mục con, mức chiết khấu và đóng góp lợi nhuận.</div>', unsafe_allow_html=True)

    prod_left, prod_right = st.columns([1, 1])
    with prod_left:
        top_sub = (
            filtered.groupby("sub_category", as_index=False)
            .agg({"sales": "sum", "profit": "sum", "discount": "mean"})
            .sort_values("sales", ascending=False)
            .head(10)
        )
        fig_sub = px.bar(
            top_sub.sort_values("sales"),
            x="sales",
            y="sub_category",
            orientation="h",
            title="Top danh mục con theo doanh thu",
            color="profit",
            color_continuous_scale="Blues",
            text_auto=True,
        )
        fig_sub.update_layout(xaxis_title="Doanh thu", yaxis_title="", coloraxis_colorbar_title="Lợi nhuận")
        st.plotly_chart(fig_sub, width="stretch", key="chart_subcategory")

    with prod_right:
        scatter = px.scatter(
            filtered,
            x="discount",
            y="profit",
            color="category",
            size="sales",
            hover_data=["order_id", "sub_category", "segment", "country"],
            title="Mối quan hệ giữa chiết khấu và lợi nhuận",
            trendline="ols",
            trendline_scope="overall",
        )
        scatter.update_layout(xaxis_title="Chiết khấu", yaxis_title="Lợi nhuận")
        st.plotly_chart(scatter, width="stretch", key="chart_discount_profit")

    prod_left2, prod_right2 = st.columns([1, 1])
    with prod_left2:
        pareto_fig = go.Figure()
        pareto_fig.add_bar(x=pareto["sub_category"], y=pareto["sales"], name="Doanh thu", marker_color="#2563eb")
        pareto_fig.add_scatter(
            x=pareto["sub_category"],
            y=pareto["cum_sales"],
            name="Tỷ trọng lũy kế",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#ef4444", width=3),
        )
        pareto_fig.update_layout(
            title="Pareto doanh thu theo danh mục con",
            xaxis_title="Danh mục con",
            yaxis=dict(title="Doanh thu"),
            yaxis2=dict(title="Tỷ trọng lũy kế", overlaying="y", side="right", tickformat=".0%", range=[0, 1]),
            legend_title_text="",
            margin=dict(t=60),
        )
        st.plotly_chart(pareto_fig, width="stretch", key="chart_pareto")

    with prod_right2:
        fig_box = px.box(
            filtered,
            x="category",
            y="discount",
            color="category",
            title="Phân phối chiết khấu theo danh mục",
            points="outliers",
        )
        fig_box.update_layout(xaxis_title="Danh mục", yaxis_title="Chiết khấu", showlegend=False)
        st.plotly_chart(fig_box, width="stretch", key="chart_discount_box")

    st.markdown('<div class="section-title">Cấu trúc danh mục</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Danh mục lớn ở ngoài, danh mục con nằm bên trong theo doanh thu.</div>', unsafe_allow_html=True)
    treemap_df = filtered.groupby(["category", "sub_category"], as_index=False).agg({"sales": "sum", "profit": "sum"})
    fig_tree = px.treemap(
        treemap_df,
        path=[px.Constant("Tất cả danh mục"), "category", "sub_category"],
        values="sales",
        color="profit",
        color_continuous_scale="RdYlGn",
        title="Bản đồ cây doanh thu theo danh mục",
        hover_data={"sales": ":,.0f", "profit": ":,.0f"},
    )
    fig_tree.update_layout(margin=dict(t=55, l=10, r=10, b=10))
    st.plotly_chart(fig_tree, width="stretch", key="chart_treemap_category")

if active_tab == "Khách hàng":
    st.markdown('<div class="section-title">Phân tích khách hàng</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">So sánh phân khúc và nhóm khách hàng theo hiệu suất.</div>', unsafe_allow_html=True)

    cust_left, cust_right = st.columns([1, 1])
    with cust_left:
        segment_tbl = filtered.groupby("segment", as_index=False).agg({"sales": "sum", "profit": "sum", "order_id": "nunique"}).rename(columns={"order_id": "orders"})
        fig_seg_profit = px.bar(
            segment_tbl,
            x="segment",
            y="profit",
            color="sales",
            color_continuous_scale="Blues",
            title="Lợi nhuận theo phân khúc",
            text_auto=True,
        )
        fig_seg_profit.update_layout(xaxis_title="", yaxis_title="Lợi nhuận", coloraxis_colorbar_title="Doanh thu")
        st.plotly_chart(fig_seg_profit, width="stretch", key="chart_segment_profit")

    with cust_right:
        customer_top = filtered.groupby("customer_name", as_index=False).agg({"sales": "sum", "profit": "sum"}).sort_values("sales", ascending=False).head(10)
        fig_customer = px.bar(
            customer_top.sort_values("sales"),
            x="sales",
            y="customer_name",
            orientation="h",
            color="profit",
            color_continuous_scale="RdYlGn",
            title="Top khách hàng theo doanh thu",
        )
        fig_customer.update_layout(xaxis_title="Doanh thu", yaxis_title="", coloraxis_colorbar_title="Lợi nhuận")
        st.plotly_chart(fig_customer, width="stretch", key="chart_customer_top")

    ins1, ins2 = st.columns(2)
    with ins1:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Phân khúc tốt nhất:</strong> {segment_tbl.sort_values('profit', ascending=False).iloc[0]['segment']}.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with ins2:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Đơn lỗ:</strong> {loss_orders:,} đơn, cần kiểm tra nhóm chiết khấu cao và chi phí vận chuyển.
            </div>
            """,
            unsafe_allow_html=True,
        )

if active_tab == "Vận hành":
    st.markdown('<div class="section-title">Phân tích vận hành</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Kiểm tra tác động của ship mode, shipping cost và các đơn lỗ.</div>', unsafe_allow_html=True)

    op_left, op_right = st.columns([1, 1])
    with op_left:
        ship_tbl = (
            filtered.groupby("ship_mode", as_index=False)
            .agg({"sales": "sum", "profit": "sum", "shipping_cost": "sum", "delivery_days": "mean"})
            .sort_values("profit", ascending=False)
        )
        fig_ship = px.bar(
            ship_tbl,
            x="ship_mode",
            y="profit",
            color="shipping_cost",
            color_continuous_scale="Tealgrn",
            title="Lợi nhuận theo phương thức giao hàng",
            text_auto=True,
        )
        fig_ship.update_layout(xaxis_title="", yaxis_title="Lợi nhuận", coloraxis_colorbar_title="Chi phí vận chuyển")
        st.plotly_chart(fig_ship, width="stretch", key="chart_ship_mode")

    with op_right:
        fig_loss = px.bar(
            top_loss_subcats.sort_values("profit"),
            x="profit",
            y="sub_category",
            orientation="h",
            title="Top danh mục con lỗ nhiều nhất",
            color="profit",
            color_continuous_scale="Reds",
        )
        fig_loss.update_layout(xaxis_title="Lợi nhuận", yaxis_title="")
        st.plotly_chart(fig_loss, width="stretch", key="chart_loss_subcategory")

    waterfall = go.Figure(
        go.Waterfall(
            name="Lợi nhuận",
            orientation="v",
            measure=["relative"] * len(category_profit),
            x=category_profit["category"],
            y=category_profit["profit"],
            connector={"line": {"color": "#94a3b8"}},
        )
    )
    waterfall.update_layout(title="Cầu nối lợi nhuận theo danh mục", yaxis_title="Lợi nhuận", xaxis_title="Danh mục")
    st.plotly_chart(waterfall, width="stretch", key="chart_waterfall")

st.markdown('<div class="section-title">Xem trước dữ liệu</div>', unsafe_allow_html=True)
preview_cols = [
    "order_id",
    "order_date",
    "ship_date",
    "customer_name",
    "segment",
    "country",
    "region",
    "category",
    "sub_category",
    "sales",
    "profit",
    "discount",
    "shipping_cost",
]
st.dataframe(apply_vietnamese_labels(filtered[preview_cols].head(20)), width="stretch")

st.caption(
    f"Số dòng sau lọc: {len(filtered):,} | Số dòng gốc: {len(df):,} | Dữ liệu cập nhật: {pd.Timestamp.now():%d/%m/%Y %H:%M}"
)
