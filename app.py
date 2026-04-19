import streamlit as st
import pandas as pd

# -----------------------------
# Session state
# -----------------------------
if "campaigns" not in st.session_state:
    st.session_state.campaigns = []

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Campaign OS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Premium CSS
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0c1020 0%, #131a2e 100%);
        color: #f5f7ff;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b31 0%, #1d2440 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.25rem;
        color: #ffffff;
        letter-spacing: -0.02em;
    }

    .sub-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #cfd6ff;
        margin-bottom: 1rem;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(113, 86, 255, 0.22), rgba(58, 201, 255, 0.12));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.30);
        margin-bottom: 20px;
    }

    .soft-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.20);
        margin-bottom: 16px;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 22px;
        padding: 18px 20px;
        min-height: 120px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.18);
    }

    .kpi-label {
        font-size: 0.85rem;
        color: #aeb9e1;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
    }

    .kpi-sub {
        font-size: 0.9rem;
        color: #bfc9f3;
        margin-top: 8px;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .section-caption {
        color: #b8c3eb;
        font-size: 0.95rem;
        margin-bottom: 6px;
    }

    .empty-card {
        background: linear-gradient(180deg, rgba(56, 93, 255, 0.14), rgba(255,255,255,0.03));
        border: 1px dashed rgba(159, 175, 255, 0.35);
        border-radius: 22px;
        padding: 28px;
        text-align: center;
        color: #dce3ff;
        margin-top: 16px;
    }

    .mini-pill {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 8px;
        margin-bottom: 8px;
        background: rgba(255,255,255,0.08);
        color: #e8edff;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
    }

    .card-text {
        color: #b9c4eb;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    div.stButton > button {
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        background: linear-gradient(135deg, #6d5dfc, #4fa7ff) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.1rem !important;
        box-shadow: 0 10px 30px rgba(79,167,255,0.20) !important;
    }

    div.stButton > button:hover {
        filter: brightness(1.05);
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 14px;
        border-radius: 18px;
    }

    .divider-space {
        height: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
def calculate_campaign_metrics(
    channel: str,
    budget: float,
    estimated_traffic: int,
    website_conversion_rate: float,
    estimated_offline_reach: int,
    campaign_duration_days: int,
    average_purchase_value: float,
    estimated_purchase_value_uplift: float,
    baseline_daily_store_traffic: int,
    estimated_traffic_uplift: float,
):
    is_offline = channel == "Offline"

    if not is_offline:
        digital_revenue = (
            estimated_traffic
            * (website_conversion_rate / 100)
            * average_purchase_value
        )
    else:
        digital_revenue = 0.0

    additional_store_visits = (
        baseline_daily_store_traffic
        * campaign_duration_days
        * (estimated_traffic_uplift / 100)
    )

    uplifted_purchase_value = average_purchase_value * (
        1 + estimated_purchase_value_uplift / 100
    )

    offline_revenue = additional_store_visits * uplifted_purchase_value
    total_revenue = digital_revenue + offline_revenue

    roi = ((total_revenue - budget) / budget) * 100 if budget > 0 else 0.0

    score = 1

    if roi > 50:
        score += 4
    elif roi > 20:
        score += 3
    elif roi > 0:
        score += 2
    elif roi > -20:
        score += 1

    if not is_offline:
        if website_conversion_rate >= 5:
            score += 2
        elif website_conversion_rate >= 2:
            score += 1

    if estimated_traffic_uplift >= 20:
        score += 2
    elif estimated_traffic_uplift >= 10:
        score += 1

    if estimated_purchase_value_uplift >= 15:
        score += 1

    if budget > 0 and total_revenue / budget >= 3:
        score += 2
    elif budget > 0 and total_revenue / budget >= 1.5:
        score += 1

    score = min(score, 10)

    if roi > 30:
        recommendation = "RUN"
    elif roi >= 0:
        recommendation = "TEST"
    else:
        recommendation = "STOP"

    insights = []

    if not is_offline and estimated_traffic > 0 and website_conversion_rate >= 3:
        insights.append("Digital campaign setup shows healthy online conversion potential.")

    if is_offline and estimated_offline_reach > 0:
        insights.append("Offline campaign includes estimated reach based on media exposure assumptions.")

    if estimated_traffic_uplift >= 15:
        insights.append("Campaign is expected to generate a meaningful uplift in store traffic.")

    if estimated_purchase_value_uplift > 0:
        insights.append("Campaign may also improve average purchase value per customer.")

    if is_offline:
        insights.append("Offline campaigns are evaluated using reach and store uplift assumptions instead of direct website conversion tracking.")

    if roi > 30:
        insights.append("Strong overall ROI potential.")
    elif roi < 0:
        insights.append("Estimated return may not justify the current budget.")

    if additional_store_visits < 100:
        insights.append("Offline impact is relatively limited based on current uplift assumptions.")

    if budget > total_revenue:
        insights.append("Budget currently exceeds estimated total revenue.")

    if not insights:
        insights.append("Balanced campaign profile with moderate potential.")

    return {
        "digital_revenue": digital_revenue,
        "offline_revenue": offline_revenue,
        "total_revenue": total_revenue,
        "roi": roi,
        "score": score,
        "recommendation": recommendation,
        "additional_store_visits": additional_store_visits,
        "uplifted_purchase_value": uplifted_purchase_value,
        "insights": insights,
    }


def recommendation_box(recommendation: str, text: str):
    if recommendation == "RUN":
        st.success(text)
    elif recommendation == "TEST":
        st.warning(text)
    else:
        st.error(text)


def campaign_dataframe():
    if not st.session_state.campaigns:
        return pd.DataFrame()
    return pd.DataFrame(st.session_state.campaigns)


def kpi_card(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def soft_section(title: str, caption: str = ""):
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="section-title">{title}</div>
            <div class="section-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## 📊 Campaign OS")
st.sidebar.caption("Premium marketing decision-support prototype")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "New Campaign", "Campaign Library", "Quick Simulator"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div class="soft-card">
        <div class="card-title">Product Mode</div>
        <div class="card-text">
            Evaluate campaigns across digital and offline channels with a hybrid ROI model.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# App header
# -----------------------------
st.markdown(
    """
    <div class="hero-card">
        <div class="main-title">📊 Campaign Decision Engine</div>
        <div class="sub-title">Marketing ROI & Strategy Tool</div>
        <span class="mini-pill">Digital + Offline</span>
        <span class="mini-pill">ROI Modeling</span>
        <span class="mini-pill">Decision Support</span>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Dashboard
# -----------------------------
if page == "Dashboard":
    st.markdown("## 🏠 Dashboard")
    st.write("Overview of campaign performance, strategic recommendations, and next best actions.")

    df = campaign_dataframe()

    if df.empty:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(
                """
                <div class="soft-card">
                    <div class="card-title">➕ Create Campaign</div>
                    <div class="card-text">Build a new campaign scenario and evaluate ROI potential.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_b:
            st.markdown(
                """
                <div class="soft-card">
                    <div class="card-title">⚡ Quick Simulation</div>
                    <div class="card-text">Stress-test assumptions with sliders and real-time ROI updates.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_c:
            st.markdown(
                """
                <div class="soft-card">
                    <div class="card-title">📂 Campaign Library</div>
                    <div class="card-text">Store and compare campaigns once they are calculated.</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            """
            <div class="empty-card">
                <h3 style="margin-bottom:8px;">No campaigns saved yet</h3>
                <p style="margin-top:0;">Start by creating your first campaign in <b>New Campaign</b>.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        total_campaigns = len(df)
        avg_roi = df["ROI (%)"].mean()
        best_campaign = df.loc[df["ROI (%)"].idxmax(), "Campaign Name"]
        avg_score = df["Efficiency Score"].mean()

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi_card("Total Campaigns", str(total_campaigns), "Scenarios stored in library")
        with k2:
            kpi_card("Average ROI", f"{avg_roi:.2f}%", "Cross-campaign average")
        with k3:
            kpi_card("Average Score", f"{avg_score:.1f}/10", "Efficiency benchmark")
        with k4:
            kpi_card("Best Campaign", best_campaign, "Top ROI performer")

        st.markdown('<div class="divider-space"></div>', unsafe_allow_html=True)
        st.markdown("### Strategic Snapshot")

        top_row = df.loc[df["ROI (%)"].idxmax()]
        low_row = df.loc[df["ROI (%)"].idxmin()]

        snap1, snap2 = st.columns(2)
        with snap1:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">🔥 Best Performer</div>
                    <div class="card-text"><b>{top_row['Campaign Name']}</b> delivers the strongest ROI at <b>{top_row['ROI (%)']:.2f}%</b>.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with snap2:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">⚠ Lowest Performer</div>
                    <div class="card-text"><b>{low_row['Campaign Name']}</b> currently shows the weakest ROI at <b>{low_row['ROI (%)']:.2f}%</b>.</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("### Campaign Overview")
        st.dataframe(
            df[["Campaign Name", "Channel", "Campaign Type", "ROI (%)", "Efficiency Score", "Recommendation"]],
            use_container_width=True
        )

# -----------------------------
# New Campaign
# -----------------------------
elif page == "New Campaign":
    st.markdown("## ✨ Create New Campaign")
    st.write("Build a campaign scenario using a hybrid digital + offline evaluation model.")

    basics_col, finance_col = st.columns(2)

    with basics_col:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Campaign Basics</div>
                <div class="section-caption">Set the core campaign parameters and execution context.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        campaign_name = st.text_input(
            "Campaign Name",
            placeholder="e.g. Spring Promo 2026"
        )

        channel = st.selectbox(
            "Channel",
            ["Social Media", "Google Ads", "Email", "Influencer", "Display Ads", "Offline"]
        )

        budget = st.number_input(
            "Budget (€)",
            min_value=0.0,
            value=1000.0,
            step=100.0
        )

        campaign_type = st.selectbox(
            "Campaign Type",
            ["Branding", "Performance", "Promotion"]
        )

        campaign_duration_days = st.number_input(
            "Campaign Duration (days)",
            min_value=1,
            value=7,
            step=1
        )

    with finance_col:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Financial Assumptions</div>
                <div class="section-caption">Model transaction value and basket uplift assumptions.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        average_purchase_value = st.number_input(
            "Average Purchase Value (€)",
            min_value=0.0,
            value=50.0,
            step=5.0
        )
        st.caption("Average value per customer transaction (online or in-store)")

        estimated_purchase_value_uplift = st.number_input(
            "Estimated Purchase Value Uplift (%)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=1.0
        )
        st.caption("Estimated increase in average purchase value due to campaign")

    st.markdown('<div class="divider-space"></div>', unsafe_allow_html=True)

    digital_col, offline_col = st.columns(2)
    is_offline = channel == "Offline"

    with digital_col:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Digital Performance</div>
                <div class="section-caption">Traffic and website conversion assumptions for digital channels.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if is_offline:
            estimated_offline_reach = st.number_input(
                "Estimated Offline Reach",
                min_value=0,
                value=50000,
                step=1000
            )
            st.caption("Estimated number of people exposed to the offline campaign")

            estimated_traffic = 0
            website_conversion_rate = 0.0

            st.markdown(
                """
                <div class="empty-card" style="padding:18px;">
                    Digital traffic and website conversion are not used for offline campaigns.
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            estimated_traffic = st.number_input(
                "Estimated Digital Traffic",
                min_value=0,
                value=10000,
                step=1000
            )
            st.caption("Estimated number of website visits generated by the campaign")

            website_conversion_rate = st.number_input(
                "Website Conversion Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=2.5,
                step=0.1
            )
            st.caption("Estimated share of website visitors who convert")
            estimated_offline_reach = 0

    with offline_col:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Offline Impact</div>
                <div class="section-caption">Store traffic baseline and uplift assumptions.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        baseline_daily_store_traffic = st.number_input(
            "Baseline Daily Store Traffic",
            min_value=0,
            value=1000,
            step=100
        )
        st.caption("Average number of in-store visitors without campaign")

        estimated_traffic_uplift = st.number_input(
            "Estimated Traffic Uplift (%)",
            min_value=0.0,
            max_value=500.0,
            value=10.0,
            step=1.0
        )
        st.caption("Estimated increase in store visits due to campaign")

    st.markdown("---")

    left_btn, right_btn = st.columns([1, 1])

    calculate_clicked = False
    with left_btn:
        calculate_clicked = st.button("Calculate Campaign Potential")

    if calculate_clicked:
        metrics = calculate_campaign_metrics(
            channel=channel,
            budget=budget,
            estimated_traffic=estimated_traffic,
            website_conversion_rate=website_conversion_rate,
            estimated_offline_reach=estimated_offline_reach,
            campaign_duration_days=campaign_duration_days,
            average_purchase_value=average_purchase_value,
            estimated_purchase_value_uplift=estimated_purchase_value_uplift,
            baseline_daily_store_traffic=baseline_daily_store_traffic,
            estimated_traffic_uplift=estimated_traffic_uplift,
        )

        st.session_state["latest_campaign"] = {
            "Campaign Name": campaign_name if campaign_name else "Untitled Campaign",
            "Channel": channel,
            "Campaign Type": campaign_type,
            "Budget (€)": budget,
            "Estimated Digital Traffic": estimated_traffic,
            "Estimated Offline Reach": estimated_offline_reach,
            "Website Conversion Rate (%)": website_conversion_rate,
            "Campaign Duration (days)": campaign_duration_days,
            "Average Purchase Value (€)": average_purchase_value,
            "Purchase Value Uplift (%)": estimated_purchase_value_uplift,
            "Baseline Daily Store Traffic": baseline_daily_store_traffic,
            "Traffic Uplift (%)": estimated_traffic_uplift,
            "Total Revenue (€)": metrics["total_revenue"],
            "Digital Revenue (€)": metrics["digital_revenue"],
            "Offline Revenue (€)": metrics["offline_revenue"],
            "ROI (%)": metrics["roi"],
            "Efficiency Score": metrics["score"],
            "Recommendation": metrics["recommendation"],
            "Additional Store Visits": metrics["additional_store_visits"],
            "Insights": metrics["insights"],
        }

        st.markdown("### Result Summary")
        r1, r2, r3, r4 = st.columns(4)

        with r1:
            kpi_card("Total Revenue", f"€{metrics['total_revenue']:,.0f}", "Combined projected value")
        with r2:
            kpi_card("ROI", f"{metrics['roi']:.2f}%", "Return against budget")
        with r3:
            kpi_card("Score", f"{metrics['score']}/10", "Efficiency score")
        with r4:
            kpi_card("Recommendation", metrics["recommendation"], "Decision support output")

        st.markdown("### Revenue Breakdown")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Digital Revenue", f"€{metrics['digital_revenue']:,.2f}" if not is_offline else "N/A")
        with m2:
            st.metric("Offline Revenue", f"€{metrics['offline_revenue']:,.2f}")
        with m3:
            st.metric("Additional Store Visits", f"{metrics['additional_store_visits']:,.0f}")

        recommendation_box(metrics["recommendation"], f"Recommendation: {metrics['recommendation']}")

        st.markdown("### Key Insights")
        for insight in metrics["insights"]:
            st.write(f"- {insight}")

    latest = st.session_state.get("latest_campaign")
    if latest:
        with right_btn:
            if st.button("Save Campaign"):
                already_exists = any(
                    c["Campaign Name"] == latest["Campaign Name"] and
                    c["Channel"] == latest["Channel"] and
                    c["Budget (€)"] == latest["Budget (€)"]
                    for c in st.session_state.campaigns
                )
                if not already_exists:
                    st.session_state.campaigns.append(latest.copy())
                    st.success("Campaign saved to library.")
                else:
                    st.warning("This campaign is already saved.")

# -----------------------------
# Campaign Library
# -----------------------------
elif page == "Campaign Library":
    st.markdown("## 📂 Campaign Library")
    st.write("Review, compare, and inspect stored campaign scenarios.")

    df = campaign_dataframe()

    if df.empty:
        st.markdown(
            """
            <div class="empty-card">
                <h3 style="margin-bottom:8px;">No campaigns in library</h3>
                <p style="margin-top:0;">Create and save a campaign to unlock comparison view.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        top1, top2, top3 = st.columns(3)
        with top1:
            kpi_card("Stored Campaigns", str(len(df)), "Library size")
        with top2:
            kpi_card("Best ROI", f"{df['ROI (%)'].max():.2f}%", "Top saved scenario")
        with top3:
            kpi_card("Average ROI", f"{df['ROI (%)'].mean():.2f}%", "Across saved campaigns")

        st.markdown("### Saved Campaigns")
        st.dataframe(
            df[[
                "Campaign Name",
                "Channel",
                "Campaign Type",
                "Budget (€)",
                "Total Revenue (€)",
                "ROI (%)",
                "Efficiency Score",
                "Recommendation"
            ]],
            use_container_width=True
        )

        st.markdown("### Campaign Detail View")
        selected_name = st.selectbox("Select Campaign", df["Campaign Name"].tolist())
        selected_row = df[df["Campaign Name"] == selected_name].iloc[0]

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            kpi_card("Budget", f"€{selected_row['Budget (€)']:,.0f}", "Allocated amount")
        with d2:
            kpi_card("Revenue", f"€{selected_row['Total Revenue (€)']:,.0f}", "Estimated return")
        with d3:
            kpi_card("ROI", f"{selected_row['ROI (%)']:.2f}%", "Scenario performance")
        with d4:
            kpi_card("Score", f"{selected_row['Efficiency Score']}/10", selected_row["Recommendation"])

        recommendation_box(
            selected_row["Recommendation"],
            f"Recommendation: {selected_row['Recommendation']}"
        )

        st.markdown("### Stored Insights")
        for insight in selected_row["Insights"]:
            st.write(f"- {insight}")

# -----------------------------
# Quick Simulator
# -----------------------------
elif page == "Quick Simulator":
    st.markdown("## ⚡ Quick Simulator")
    st.write("Adjust key assumptions in real time and test campaign viability fast.")

    sim_left, sim_right = st.columns(2)

    with sim_left:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Simulation Inputs</div>
                <div class="section-caption">Use sliders to explore how assumptions influence ROI.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        sim_budget = st.slider("Budget (€)", 100, 20000, 2400, 100)
        sim_traffic = st.slider("Estimated Digital Traffic", 0, 100000, 10000, 1000)
        sim_conversion = st.slider("Website Conversion Rate (%)", 0.0, 10.0, 2.5, 0.1)

    with sim_right:
        st.markdown(
            """
            <div class="soft-card">
                <div class="section-title">Commercial Assumptions</div>
                <div class="section-caption">Test changes in purchase value, uplift, and timing.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        sim_purchase = st.slider("Average Purchase Value (€)", 5, 500, 50, 5)
        sim_uplift = st.slider("Traffic Uplift (%)", 0.0, 100.0, 10.0, 1.0)
        sim_days = st.slider("Campaign Duration (days)", 1, 60, 7, 1)

    sim_metrics = calculate_campaign_metrics(
        channel="Social Media",
        budget=float(sim_budget),
        estimated_traffic=int(sim_traffic),
        website_conversion_rate=float(sim_conversion),
        estimated_offline_reach=0,
        campaign_duration_days=int(sim_days),
        average_purchase_value=float(sim_purchase),
        estimated_purchase_value_uplift=0.0,
        baseline_daily_store_traffic=1000,
        estimated_traffic_uplift=float(sim_uplift),
    )

    st.markdown("### Simulation Results")
    s1, s2, s3 = st.columns(3)
    with s1:
        kpi_card("Total Revenue", f"€{sim_metrics['total_revenue']:,.0f}", "Projected return")
    with s2:
        kpi_card("ROI", f"{sim_metrics['roi']:.2f}%", "Return on budget")
    with s3:
        kpi_card("Recommendation", sim_metrics["recommendation"], "Decision support")

    recommendation_box(
        sim_metrics["recommendation"],
        f"Recommendation: {sim_metrics['recommendation']}"
    )

    st.markdown("### Simulation Insight")
    if sim_metrics["roi"] > 30:
        st.markdown(
            """
            <div class="soft-card">
                <div class="card-title">Strong Scenario</div>
                <div class="card-text">This simulation suggests strong performance potential under the selected assumptions.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif sim_metrics["roi"] >= 0:
        st.markdown(
            """
            <div class="soft-card">
                <div class="card-title">Test Candidate</div>
                <div class="card-text">This scenario may justify testing, but assumptions should be validated carefully.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="soft-card">
                <div class="card-title">Weak Scenario</div>
                <div class="card-text">This simulation suggests weak return potential under the current assumptions.</div>
            </div>
            """,
            unsafe_allow_html=True
        )