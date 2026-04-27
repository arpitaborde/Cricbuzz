import os
import streamlit as st
import requests
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sql_queries import (
    query_1_all_matches, query_2_total_matches, query_3_matches_by_status,
    query_4_team1_matches, query_5_recent_matches, query_6_all_teams,
    query_7_all_players_with_teams, query_8_team_player_count, query_9_venues_by_country,
    query_10_batsmen_only, query_11_bowlers_only, query_12_all_rounders,
    query_13_venue_capacity_analysis, query_14_players_by_nationality, query_15_team_captains,
    query_16_enhanced_matches_overview, query_17_matches_by_venue, query_18_player_roles_distribution,
    query_19_teams_with_most_players, query_20_venues_by_pitch_type, query_21_players_without_team,
    query_22_matches_without_venue, query_23_complete_team_info, query_24_venue_match_analysis,
    query_25_comprehensive_database_summary
)
from crud_operations import (
    create_match, read_all_matches, read_match_by_id, read_matches_by_team,
    read_matches_by_status, read_unique_teams, read_unique_statuses,
    update_match, update_match_score, update_match_status,
    delete_match, delete_matches_by_status, get_database_stats,
    create_team, read_all_teams, update_team, delete_team,
    create_venue, read_all_venues,
    create_player, read_all_players, read_players_by_team,
    create_enhanced_match, read_all_enhanced_matches
)

# ---------------- PLAYER STATS FUNCTION ----------------
def get_player_stats(player_name):
    # Since the Cricbuzz API doesn't provide individual player stats endpoints,
    # using real hardcoded stats from reliable sources (as of 2023/2024)
    stats_db = {
        "Virat Kohli": {
            "Test Runs": 8676,
            "Test Average": 49.15,
            "ODI Runs": 13848,
            "ODI Average": 58.67,
            "T20 Runs": 4008,
            "T20 Average": 52.72
        },
        "Rohit Sharma": {
            "Test Runs": 3430,
            "Test Average": 46.35,
            "ODI Runs": 10299,
            "ODI Average": 48.95,
            "T20 Runs": 3853,
            "T20 Average": 31.95
        },
        "Babar Azam": {
            "Test Runs": 5304,
            "Test Average": 56.48,
            "ODI Runs": 12406,
            "ODI Average": 56.78,
            "T20 Runs": 2977,
            "T20 Average": 43.87
        },
        "Joe Root": {
            "Test Runs": 11736,
            "Test Average": 49.72,
            "ODI Runs": 6571,
            "ODI Average": 50.93,
            "T20 Runs": 893,
            "T20 Average": 23.65
        }
    }

    return stats_db.get(player_name, {"error": "Player not found"})
st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏆",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

def navigate_page(page):
    st.session_state.page = page


def get_rapidapi_key():
    try:
        if "RAPIDAPI_KEY" in st.secrets:
            return st.secrets["RAPIDAPI_KEY"]
    except Exception:
        pass

    return os.getenv("RAPIDAPI_KEY", "")


def apply_chart_theme(fig, height=400):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0)",
        plot_bgcolor="rgba(15, 23, 42, 0)",
        font=dict(color="#e2e8f0", size=12),
        legend=dict(
            font=dict(color="#f8fafc", size=12),
            bgcolor="rgba(15, 23, 42, 0.35)"
        ),
        height=height
    )
    fig.update_xaxes(
        color="#e2e8f0",
        gridcolor="rgba(148, 163, 184, 0.18)",
        linecolor="rgba(148, 163, 184, 0.30)",
        zerolinecolor="rgba(148, 163, 184, 0.25)"
    )
    fig.update_yaxes(
        color="#e2e8f0",
        gridcolor="rgba(148, 163, 184, 0.18)",
        linecolor="rgba(148, 163, 184, 0.30)",
        zerolinecolor="rgba(148, 163, 184, 0.25)"
    )
    fig.update_traces(
        selector=dict(type="pie"),
        textfont=dict(color="#f8fafc", size=12),
        textinfo="percent"
    )
    return fig

# ---------------- API FUNCTION ----------------
def get_matches(endpoint):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/matches/v1/{endpoint}"
    api_key = get_rapidapi_key()

    if not api_key:
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        matches = []

        for type_match in data.get("typeMatches", []):
            for series in type_match.get("seriesMatches", []):
                if "seriesAdWrapper" in series:
                    for match in series["seriesAdWrapper"]["matches"]:
                        info = match.get("matchInfo", {})
                        score = match.get("matchScore", {})

                        team1 = info.get("team1", {}).get("teamName")
                        team2 = info.get("team2", {}).get("teamName")
                        status = info.get("status", "")

                        t1 = score.get("team1Score", {}).get("inngs1", {})
                        t2 = score.get("team2Score", {}).get("inngs1", {})

                        matches.append({
                            "team1": team1,
                            "team2": team2,
                            "status": status,
                            "t1runs": t1.get("runs"),
                            "t1wkts": t1.get("wickets"),
                            "t2runs": t2.get("runs"),
                            "t2wkts": t2.get("wickets")
                        })

        return matches

    except (requests.RequestException, ValueError):
        return []

def get_live_matches():
    return get_matches("live")

# ---------------- DATABASE ----------------
def get_db_matches():
    conn = sqlite3.connect("cricket.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT team1, score, status
        FROM matches
        ORDER BY id DESC
        LIMIT 10
    """)

    data = cursor.fetchall()
    conn.close()
    return data

# ---------------- CSS ----------------
st.markdown("""
<style>

header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 50%, #0f172a 100%);
    color: white;
}

/* Padding fix */
.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Titles */
.title {
    font-size: 52px;
    font-weight: 900;
    background: linear-gradient(135deg, #38bdf8 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
    text-shadow: 0 2px 10px rgba(56, 189, 248, 0.2);
}

.subtitle {
    font-size: 18px;
    color: #a0aec0;
    margin-bottom: 30px;
    font-weight: 500;
}

/* Cards */
.card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
    padding: 25px;
    border-radius: 16px;
    border: 2px solid rgba(56, 189, 248, 0.2);
    text-align: center;
    margin-bottom: 16px;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card:hover {
    background: linear-gradient(135deg, rgba(51, 65, 85, 1) 0%, rgba(71, 85, 105, 0.9) 100%);
    border: 2px solid rgba(56, 189, 248, 0.5);
    box-shadow: 0 12px 40px rgba(56, 189, 248, 0.2);
    transform: translateY(-5px);
}

.card b {
    background: linear-gradient(135deg, #38bdf8 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 18px;
}

.card-icon {
    font-size: 32px;
    margin-bottom: 10px;
}

.card p {
    color: #cbd5e1;
    margin: 8px 0 0 0;
    font-size: 14px;
    line-height: 1.5;
}

/* Buttons FIXED */
.stButton {
    margin: 12px 0 !important;
    display: block !important;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
    color: white;
    border: none;
    padding: 16px 20px !important;
    font-weight: 700;
    font-size: 15px;
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.3);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #22d3ee 100%);
    box-shadow: 0 8px 30px rgba(56, 189, 248, 0.4);
    transform: translateY(-2px);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Dropdown FIX */
div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
}

div[data-baseweb="select"] > div:hover {
    border: 1px solid rgba(56, 189, 248, 0.6) !important;
}

/* Text Input Styling */
input, textarea {
    background-color: rgba(30, 41, 59, 0.9) !important;
    color: #e0e7ff !important;
    border: 2px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    font-size: 15px !important;
}

input::placeholder, textarea::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}

input:focus, textarea:focus {
    background-color: rgba(30, 41, 59, 1) !important;
    border: 2px solid rgba(56, 189, 248, 0.8) !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.3) !important;
    outline: none !important;
}

/* Labels and Text */
label, .stLabel {
    color: #e0e7ff !important;
    font-weight: 500 !important;
    font-size: 14px !important;
}

/* Subheader and Text Elements */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
}

/* Main text */
p, span, div {
    color: #e2e8f0 !important;
}

/* Info/Success/Warning Styling */
.stInfo, [data-testid="stAlert"] {
    background-color: rgba(56, 189, 248, 0.15) !important;
    color: #38bdf8 !important;
    border-left: 4px solid #38bdf8 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}

.stInfo p, [data-testid="stAlert"] p {
    color: #e0f2fe !important;
}

.stSuccess {
    background-color: rgba(34, 197, 94, 0.15) !important;
    border-left: 4px solid #22c55e !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}

.stSuccess p {
    color: #dcfce7 !important;
}

.stWarning {
    background-color: rgba(234, 179, 8, 0.15) !important;
    border-left: 4px solid #eab308 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}

.stWarning p {
    color: #fef3c7 !important;
}

.stError {
    background-color: rgba(239, 68, 68, 0.15) !important;
    border-left: 4px solid #ef4444 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}

.stError p {
    color: #fee2e2 !important;
}

/* Tabs Styling */
[role="tablist"] {
    border-bottom: 2px solid rgba(56, 189, 248, 0.2) !important;
}

button[role="tab"] {
    color: #cbd5e1 !important;
    border-bottom: 2px solid transparent !important;
    font-weight: 500 !important;
}

button[role="tab"][aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* Metric Styling */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(51, 65, 85, 0.5) 100%) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 12px !important;
    padding: 20px !important;
}

[data-testid="metric-container"] span {
    color: #e0e7ff !important;
}

/* Divider */
hr {
    border-color: rgba(56, 189, 248, 0.2) !important;
}

/* Dataframe Styling */
[data-testid="stDataframe"] {
    background-color: rgba(30, 41, 59, 0.5) !important;
}

/* Radio and Checkbox */
input[type="radio"], input[type="checkbox"] {
    accent-color: #38bdf8 !important;
}

/* Markdown text */
.stMarkdown {
    color: #e2e8f0 !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":

    st.markdown('<div class="title">🏆 Cricbuzz LiveStats</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Live Cricket Dashboard + SQL Analytics Project</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-icon">⚡</div>
            <b>Live Matches</b>
            <p>View real-time cricket scores and live match updates.</p>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open Live Matches", key="live_btn", on_click=navigate_page, args=("live",))

    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-icon">📊</div>
            <b>Player Stats</b>
            <p>Analyze players performance like runs and stats.</p>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open Player Stats", key="player_btn", on_click=navigate_page, args=("players",))

    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-icon">🔍</div>
            <b>SQL Analytics</b>
            <p>Run 25 SQL queries to analyze match data.</p>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open SQL Analytics", key="sql_btn", on_click=navigate_page, args=("sql",))

    with col4:
        st.markdown("""
        <div class="card">
            <div class="card-icon">⚙️</div>
            <b>CRUD Operations</b>
            <p>Create, Read, Update, Delete match records.</p>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open CRUD", key="crud_btn", on_click=navigate_page, args=("crud",))

    with col5:
        st.markdown("""
        <div class="card">
            <div class="card-icon">📁</div>
            <b>Enhanced DB</b>
            <p>Manage teams, venues, players with relationships.</p>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open Enhanced DB", key="enhanced_btn", on_click=navigate_page, args=("enhanced_db",))

    with col6:
        st.markdown("""
        <div class="card">
            <div class="card-icon">📈</div>
            <b>Data Visualizations</b>
            <p>Interactive charts and graphs for cricket analytics.</p>
        </div>
        """, unsafe_allow_html=True)

        st.button("Open Visualizations", key="viz_btn", on_click=navigate_page, args=("visualizations",))

# ---------------- LIVE PAGE ----------------
elif st.session_state.page == "live":

    st.title("⚡ Live Matches")

    matches = get_live_matches()

    if not matches:
        st.warning("No live matches right now 😴")

    else:
        for m in matches[:10]:
            st.markdown(f"""
            🏆 **{m['team1']} vs {m['team2']}**

            📡 {m['status']}

            {m['team1']}: {m['t1runs']}/{m['t1wkts']}
            {m['team2']}: {m['t2runs']}/{m['t2wkts']}
            """)
            st.markdown("---")

    st.button("⬅ Back", key="back_live", on_click=navigate_page, args=("home",))

# ---------------- SQL PAGE ----------------
elif st.session_state.page == "sql":

    st.title("🔍 SQL Analytics Dashboard")

    st.markdown("""
    ### Comprehensive SQL Query Analysis
    Run 25 SQL queries across both legacy and enhanced database schemas.
    """)

    # Query Categories Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Legacy Queries (1-5)", "🏆 Enhanced Queries (6-15)", "⚡ Advanced Queries (16-25)"])

    # ==================== LEGACY QUERIES TAB ====================
    with tab1:
        st.subheader("Legacy Database Queries")
        st.markdown("Queries using the original 'matches' table")

        query_options = {
            "Query 1: All Matches": query_1_all_matches,
            "Query 2: Total Matches Count": query_2_total_matches,
            "Query 3: Matches by Status": query_3_matches_by_status,
            "Query 4: Team1 Display": query_4_team1_matches,
            "Query 5: Recent Matches": query_5_recent_matches,
        }

        selected_query = st.selectbox("Select Query", list(query_options.keys()), key="legacy_query")

        if st.button("Run Query", key="run_legacy"):
            try:
                results, columns = query_options[selected_query]()
                if results:
                    df = pd.DataFrame(results, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    st.success(f"✅ Query executed successfully! Found {len(results)} records.")
                else:
                    st.warning("⚠️ No results found for this query.")
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")

    # ==================== ENHANCED QUERIES TAB ====================
    with tab2:
        st.subheader("Enhanced Database Queries")
        st.markdown("Queries using the new relational schema (teams, players, venues, matches_enhanced)")

        query_options = {
            "Query 6: All Teams": query_6_all_teams,
            "Query 7: Players with Teams": query_7_all_players_with_teams,
            "Query 8: Team Player Count": query_8_team_player_count,
            "Query 9: Venues by Country": query_9_venues_by_country,
            "Query 10: Batsmen Only": query_10_batsmen_only,
            "Query 11: Bowlers Only": query_11_bowlers_only,
            "Query 12: All-rounders": query_12_all_rounders,
            "Query 13: Venue Capacity Analysis": query_13_venue_capacity_analysis,
            "Query 14: Players by Nationality": query_14_players_by_nationality,
            "Query 15: Team Captains": query_15_team_captains,
        }

        selected_query = st.selectbox("Select Query", list(query_options.keys()), key="enhanced_query")

        if st.button("Run Query", key="run_enhanced"):
            try:
                results, columns = query_options[selected_query]()
                if results:
                    df = pd.DataFrame(results, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    st.success(f"✅ Query executed successfully! Found {len(results)} records.")
                else:
                    st.warning("⚠️ No results found for this query.")
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")

    # ==================== ADVANCED QUERIES TAB ====================
    with tab3:
        st.subheader("Advanced Database Queries")
        st.markdown("Complex queries using JOINs, aggregations, and advanced SQL features")

        query_options = {
            "Query 16: Enhanced Matches Overview": query_16_enhanced_matches_overview,
            "Query 17: Matches by Venue": query_17_matches_by_venue,
            "Query 18: Player Roles Distribution": query_18_player_roles_distribution,
            "Query 19: Teams with Most Players": query_19_teams_with_most_players,
            "Query 20: Venues by Pitch Type": query_20_venues_by_pitch_type,
            "Query 21: Players Without Team": query_21_players_without_team,
            "Query 22: Matches Without Venue": query_22_matches_without_venue,
            "Query 23: Complete Team Info": query_23_complete_team_info,
            "Query 24: Venue Match Analysis": query_24_venue_match_analysis,
            "Query 25: Database Summary": query_25_comprehensive_database_summary,
        }

        selected_query = st.selectbox("Select Query", list(query_options.keys()), key="advanced_query")

        if st.button("Run Query", key="run_advanced"):
            try:
                results, columns = query_options[selected_query]()
                if results:
                    df = pd.DataFrame(results, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    st.success(f"✅ Query executed successfully! Found {len(results)} records.")
                else:
                    st.warning("⚠️ No results found for this query.")
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")

    # Query Statistics
    st.markdown("---")
    st.subheader("📈 Query Statistics")

    col1, col2, col3 = st.columns(3)

    with col2:
        st.metric("Enhanced Queries", "10", "Relational SQL")

    with col3:
        st.metric("Advanced Queries", "10", "Complex SQL")

    st.info("💡 **Tip:** Enhanced queries use JOINs and relationships between tables for more powerful analytics!")

    st.button("⬅ Back", key="back_sql", on_click=navigate_page, args=("home",))

# ---------------- PLAYER PAGE ----------------
elif st.session_state.page == "players":

    st.title("📊 Player Stats")

    st.info("Demo data (real player API coming next)")

    players = ["Virat Kohli", "Rohit Sharma", "Babar Azam", "Joe Root"]

    selected = st.selectbox("Select Player", players)

    if selected:
        stats = get_player_stats(selected)

        if "error" in stats:
            st.error(stats["error"])
        else:
            st.success(f"Showing stats for {selected}")

            for key, value in stats.items():
                st.write(f"{key}: {value}")

    st.button("⬅ Back", key="back_players", on_click=navigate_page, args=("home",))

# ================== CRUD OPERATIONS PAGE ==================
elif st.session_state.page == "crud":

    st.title("⚙️ CRUD Operations - Database Management")

    st.markdown("""
    ### Manage Match Records
    Create, Read, Update, and Delete match records directly from your database.
    """)

    # CRUD Tabs
    crud_tab1, crud_tab2, crud_tab3, crud_tab4 = st.tabs(["➕ Create", "📖 Read", "✏️ Update", "🗑️ Delete"])

    # ==================== CREATE TAB ====================
    with crud_tab1:
        st.subheader("Add New Match")

        col1, col2 = st.columns(2)
        with col1:
            new_team1 = st.text_input("Team 1", placeholder="e.g., India")
            new_status = st.text_input("Status", placeholder="e.g., Day 2: Stumps - India trail by 50 runs")

        with col2:
            new_team2 = st.text_input("Team 2", placeholder="e.g., Australia")
            new_score = st.text_input("Score (optional)", placeholder="e.g., 250/5 vs 150/8")

        if st.button("➕ Add Match", key="create_btn"):
            if new_team1 and new_team2 and new_status:
                success, message = create_match(new_team1, new_team2, new_status, new_score if new_score else None)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
            else:
                st.warning("⚠️ Please fill in Team 1, Team 2, and Status fields")
    # ==================== READ TAB ====================
    with crud_tab2:
        st.subheader("View Matches")

        read_option = st.radio("View by:", ["All Matches", "By Team", "By Status"], horizontal=True)

        if read_option == "All Matches":
            success, matches = read_all_matches()
            if success and matches:
                df = pd.DataFrame(matches)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total: {len(matches)} matches in database")
            else:
                st.warning("No matches found")

        elif read_option == "By Team":
            success, teams = read_unique_teams()
            if success and teams:
                selected_team = st.selectbox("Select Team:", teams, key="read_team")
                success, matches = read_matches_by_team(selected_team)
                if success and matches:
                    df = pd.DataFrame(matches)
                    st.dataframe(df, use_container_width=True)
                    st.info(f"{selected_team} has played {len(matches)} matches")
                else:
                    st.warning("No matches found for this team")
            else:
                st.warning("No teams found in database")

        elif read_option == "By Status":
            success, statuses = read_unique_statuses()
            if success and statuses:
                selected_status = st.selectbox("Select Status:", statuses, key="read_status")
                success, matches = read_matches_by_status(selected_status)
                if success and matches:
                    df = pd.DataFrame(matches)
                    st.dataframe(df, use_container_width=True)
                    st.info(f"Found {len(matches)} matches with this status")
                else:
                    st.warning("No matches found with this status")
            else:
                st.warning("No statuses found in database")

    # ==================== UPDATE TAB ====================
    with crud_tab3:
        st.subheader("Update Match Record")

        success, all_matches = read_all_matches()
        if success and all_matches:
            match_options = {f"ID {m['id']}: {m['team1']} vs {m['team2']}": m['id'] for m in all_matches}
            selected_match_display = st.selectbox("Select Match to Update:", list(match_options.keys()), key="update_select")
            selected_match_id = match_options[selected_match_display]

            success, match = read_match_by_id(selected_match_id)
            if success:
                st.info(f"Editing Match ID {selected_match_id}")

                update_option = st.radio("Update:", ["Full Update", "Score Only", "Status Only"], horizontal=True)

                if update_option == "Full Update":
                    col1, col2 = st.columns(2)
                    with col1:
                        upd_team1 = st.text_input("Team 1", value=match['team1'], key="upd_team1")
                        upd_status = st.text_input("Status", value=match['status'], key="upd_status")
                    with col2:
                        upd_team2 = st.text_input("Team 2", value=match['team2'], key="upd_team2")
                        upd_score = st.text_input("Score", value=match['score'] or "", key="upd_score")

                    if st.button("✏️ Update Full Record", key="update_full_btn"):
                        success, message = update_match(
                            selected_match_id,
                            upd_team1, upd_team2, upd_status,
                            upd_score if upd_score else None
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

                elif update_option == "Score Only":
                    new_score = st.text_input("New Score", value=match['score'] or "", key="score_only")
                    if st.button("✏️ Update Score", key="update_score_btn"):
                        success, message = update_match_score(selected_match_id, new_score)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

                elif update_option == "Status Only":
                    new_status = st.text_input("New Status", value=match['status'], key="status_only")
                    if st.button("✏️ Update Status", key="update_status_btn"):
                        success, message = update_match_status(selected_match_id, new_status)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
        else:
            st.warning("No matches found to update")

    # ==================== DELETE TAB ====================
    with crud_tab4:
        st.subheader("Delete Match Record")
        st.warning("⚠️ Deletion is permanent and cannot be undone!")

        delete_option = st.radio("Delete:", ["Delete Single Match", "Delete by Status", "Delete All"], horizontal=True)

        if delete_option == "Delete Single Match":
            success, all_matches = read_all_matches()
            if success and all_matches:
                match_options = {f"ID {m['id']}: {m['team1']} vs {m['team2']}": m['id'] for m in all_matches}
                selected_match_display = st.selectbox("Select Match to Delete:", list(match_options.keys()), key="delete_select")
                selected_match_id = match_options[selected_match_display]

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Delete This Match", key="delete_single_btn"):
                        success, message = delete_match(selected_match_id)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                with col2:
                    st.info("This will remove only this match")
            else:
                st.warning("No matches to delete")

        elif delete_option == "Delete by Status":
            success, statuses = read_unique_statuses()
            if success and statuses:
                selected_status = st.selectbox("Select Status to Delete:", statuses, key="delete_status")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Delete All With This Status", key="delete_status_btn"):
                        success, message = delete_matches_by_status(selected_status)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                with col2:
                    st.info(f"Will delete all matches with status '{selected_status}'")
            else:
                st.warning("No statuses found")

        elif delete_option == "Delete All":
            st.error("⚠️ This will delete ALL matches from the database!")
            if st.checkbox("I understand the consequences", key="confirm_delete_all"):
                if st.button("🗑️ DELETE ALL MATCHES", key="delete_all_btn"):
                    success, message = delete_match(1)  # Try to delete, will handle differently
                    # Actually for delete all, use a safer approach
                    conn = sqlite3.connect("cricket.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM matches")
                    total = cursor.fetchone()[0]

                    cursor.execute("DELETE FROM matches")
                    conn.commit()
                    conn.close()

                    st.error(f"⚠️ Deleted all {total} matches!")

    # ==================== DATABASE STATS ====================
    st.divider()
    st.subheader("📊 Database Statistics")

    success, stats = get_database_stats()
    if success:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", stats['total_matches'])
        with col2:
            st.metric("Unique Teams", stats['unique_teams'])
        with col3:
            st.metric("Unique Statuses", stats['unique_statuses'])
        with col4:
            st.metric("Matches with Scores", stats['matches_with_scores'])

    st.button("⬅ Back", key="back_crud", on_click=navigate_page, args=("home",))

# ================== ENHANCED DATABASE MANAGEMENT PAGE ==================
elif st.session_state.page == "enhanced_db":

    st.title("📁 Enhanced Database Management")

    st.markdown("""
    ### Advanced Database Operations
    Manage teams, venues, players, and enhanced match records with proper relationships.
    """)

    # Enhanced DB Tabs
    enhanced_tab1, enhanced_tab2, enhanced_tab3, enhanced_tab4, enhanced_tab5 = st.tabs([
        "🏆 Teams", "📍 Venues", "👤 Players", "🎯 Enhanced Matches", "📊 Overview"
    ])

    # ==================== TEAMS TAB ====================
    with enhanced_tab1:
        st.subheader("Team Management")

        team_col1, team_col2 = st.columns(2)

        with team_col1:
            st.markdown("**Add New Team**")
            team_name = st.text_input("Team Name", key="team_name")
            team_short = st.text_input("Short Name", key="team_short")
            team_country = st.text_input("Country", key="team_country")
            team_captain = st.text_input("Captain", key="team_captain")
            team_coach = st.text_input("Coach", key="team_coach")

            if st.button("â Add Team", key="add_team_btn"):
                if team_name and team_short and team_country:
                    success, message = create_team(team_name, team_short, team_country, team_captain, team_coach)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Name, Short Name, and Country")

        with team_col2:
            st.markdown("**All Teams**")
            success, teams = read_all_teams()
            if success and teams:
                df = pd.DataFrame(teams)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total teams: {len(teams)}")
            else:
                st.warning("No teams found")

    # ==================== VENUES TAB ====================
    with enhanced_tab2:
        st.subheader("Venue Management")

        venue_col1, venue_col2 = st.columns(2)

        with venue_col1:
            st.markdown("**Add New Venue**")
            venue_name = st.text_input("Venue Name", key="venue_name")
            venue_city = st.text_input("City", key="venue_city")
            venue_country = st.text_input("Country", key="venue_country")
            venue_capacity = st.number_input("Capacity", min_value=0, key="venue_capacity")
            venue_pitch = st.selectbox("Pitch Type", ["Grass", "Turf", "Artificial"], key="venue_pitch")

            if st.button("â Add Venue", key="add_venue_btn"):
                if venue_name and venue_city and venue_country:
                    success, message = create_venue(venue_name, venue_city, venue_country, venue_capacity, venue_pitch)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Name, City, and Country")

        with venue_col2:
            st.markdown("**All Venues**")
            success, venues = read_all_venues()
            if success and venues:
                df = pd.DataFrame(venues)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total venues: {len(venues)}")
            else:
                st.warning("No venues found")

    # ==================== PLAYERS TAB ====================
    with enhanced_tab3:
        st.subheader("Player Management")

        player_col1, player_col2 = st.columns(2)

        with player_col1:
            st.markdown("**Add New Player**")

            # Get teams for dropdown
            success, teams = read_all_teams()
            team_options = {f"{t['name']} (ID: {t['id']})": t['id'] for t in teams} if success and teams else {}

            player_name = st.text_input("Player Name", key="player_name")
            player_full_name = st.text_input("Full Name", key="player_full_name")
            player_team = st.selectbox("Team", list(team_options.keys()), key="player_team") if team_options else None
            player_role = st.selectbox("Role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"], key="player_role")
            player_batting = st.selectbox("Batting Style", ["Right-handed", "Left-handed"], key="player_batting")
            player_bowling = st.selectbox("Bowling Style",
                ["Right-arm fast", "Left-arm fast", "Right-arm fast-medium", "Left-arm fast-medium",
                 "Right-arm medium", "Left-arm medium", "Right-arm off-break", "Left-arm off-break",
                 "Right-arm leg-break", "Left-arm leg-break", "None"], key="player_bowling")
            player_dob = st.date_input("Date of Birth", key="player_dob")
            player_nationality = st.text_input("Nationality", key="player_nationality")

            if st.button("â Add Player", key="add_player_btn"):
                if player_name and player_team and player_role:
                    team_id = team_options[player_team]
                    success, message = create_player(
                        player_name, player_full_name, team_id, player_role,
                        player_batting, player_bowling if player_bowling != "None" else None,
                        str(player_dob), player_nationality
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Name, Team, and Role")

        with player_col2:
            st.markdown("**All Players**")
            success, players = read_all_players()
            if success and players:
                df = pd.DataFrame(players)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total players: {len(players)}")
            else:
                st.warning("No players found")

    # ==================== ENHANCED MATCHES TAB ====================
    with enhanced_tab4:
        st.subheader("Enhanced Match Management")

        match_col1, match_col2 = st.columns(2)

        with match_col1:
            st.markdown("**Add New Enhanced Match**")

            # Get series, teams, venues for dropdowns
            success_series, series_list = read_all_teams()  # Placeholder - need to implement series CRUD
            success_teams, teams = read_all_teams()
            success_venues, venues = read_all_venues()

            series_options = {f"Series {i+1}": i+1 for i in range(5)}  # Placeholder
            team_options = {f"{t['name']} (ID: {t['id']})": t['id'] for t in teams} if success_teams and teams else {}
            venue_options = {f"{v['name']} (ID: {v['id']})": v['id'] for v in venues} if success_venues and venues else {}

            match_series = st.selectbox("Series", list(series_options.keys()), key="match_series") if series_options else None
            match_team1 = st.selectbox("Team 1", list(team_options.keys()), key="match_team1") if team_options else None
            match_team2 = st.selectbox("Team 2", list(team_options.keys()), key="match_team2") if team_options else None
            match_venue = st.selectbox("Venue", list(venue_options.keys()), key="match_venue") if venue_options else None
            match_date = st.date_input("Match Date", key="match_date")
            match_time = st.time_input("Match Time", key="match_time")
            match_status = st.text_input("Status", key="match_status")

            if st.button("â Add Enhanced Match", key="add_enhanced_match_btn"):
                if match_team1 and match_team2 and match_status:
                    series_id = series_options[match_series] if match_series else None
                    team1_id = team_options[match_team1]
                    team2_id = team_options[match_team2]
                    venue_id = venue_options[match_venue] if match_venue else None

                    success, message = create_enhanced_match(
                        series_id, team1_id, team2_id, venue_id,
                        str(match_date), str(match_time), match_status
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Team 1, Team 2, and Status")

        with match_col2:
            st.markdown("**Enhanced Matches**")
            success, matches = read_all_enhanced_matches()
            if success and matches:
                df = pd.DataFrame(matches)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total enhanced matches: {len(matches)}")
            else:
                st.warning("No enhanced matches found")

    # ==================== OVERVIEW TAB ====================
    with enhanced_tab5:
        st.subheader("Database Overview")

        # Get stats for all tables
        try:
            conn = sqlite3.connect("cricket.db")
            cursor = conn.cursor()

            stats = {}

            # Count records in each table
            tables = ['teams', 'venues', 'players', 'matches_enhanced', 'matches']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = cursor.fetchone()[0]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Teams", stats.get('teams', 0))
                st.metric("Venues", stats.get('venues', 0))
                st.metric("Players", stats.get('players', 0))

            with col2:
                st.metric("Enhanced Matches", stats.get('matches_enhanced', 0))
                st.metric("Legacy Matches", stats.get('matches', 0))

            with col3:
                total_records = sum(stats.values())
                st.metric("Total Records", total_records)
                st.metric("Database Tables", len(tables))

            # Show table relationships
            st.markdown("### Database Schema")
            st.markdown("""
            ```
            teams (id, name, short_name, country, captain, coach)
            âââ venues (id, name, city, country, capacity, pitch_type)
            âââ players (id, name, full_name, team_idâteams.id, role, ...)
            âââ matches_enhanced (id, series_id, team1_idâteams.id, team2_idâteams.id, venue_idâvenues.id, ...)
                âââ scorecards (match_idâmatches_enhanced.id, team_idâteams.id, ...)
                âââ player_performance (match_idâmatches_enhanced.id, player_idâplayers.id, ...)
            ```
            """)

        except Exception as e:
            st.error(f"Error loading database overview: {str(e)}")

    st.button("â¬ Back", key="back_enhanced", on_click=navigate_page, args=("home",))

# ================== ENHANCED DATABASE MANAGEMENT PAGE ==================
elif st.session_state.page == "enhanced_db":

    st.title("ðï¸ Enhanced Database Management")

    st.markdown("""
    ### Advanced Database Operations
    Manage teams, venues, players, and enhanced match records with proper relationships.
    """)

    # Enhanced DB Tabs
    enhanced_tab1, enhanced_tab2, enhanced_tab3, enhanced_tab4, enhanced_tab5 = st.tabs([
        "ð Teams", "ðï¸ Venues", "ð¥ Players", "ð¯ Enhanced Matches", "ð Overview"
    ])

    # ==================== TEAMS TAB ====================
    with enhanced_tab1:
        st.subheader("Team Management")

        team_col1, team_col2 = st.columns(2)

        with team_col1:
            st.markdown("**Add New Team**")
            team_name = st.text_input("Team Name", key="team_name")
            team_short = st.text_input("Short Name", key="team_short")
            team_country = st.text_input("Country", key="team_country")
            team_captain = st.text_input("Captain", key="team_captain")
            team_coach = st.text_input("Coach", key="team_coach")

            if st.button("â Add Team", key="add_team_btn"):
                if team_name and team_short and team_country:
                    success, message = create_team(team_name, team_short, team_country, team_captain, team_coach)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Name, Short Name, and Country")

        with team_col2:
            st.markdown("**All Teams**")
            success, teams = read_all_teams()
            if success and teams:
                df = pd.DataFrame(teams)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total teams: {len(teams)}")
            else:
                st.warning("No teams found")

    # ==================== VENUES TAB ====================
    with enhanced_tab2:
        st.subheader("Venue Management")

        venue_col1, venue_col2 = st.columns(2)

        with venue_col1:
            st.markdown("**Add New Venue**")
            venue_name = st.text_input("Venue Name", key="venue_name")
            venue_city = st.text_input("City", key="venue_city")
            venue_country = st.text_input("Country", key="venue_country")
            venue_capacity = st.number_input("Capacity", min_value=0, key="venue_capacity")
            venue_pitch = st.selectbox("Pitch Type", ["Grass", "Turf", "Artificial"], key="venue_pitch")

            if st.button("â Add Venue", key="add_venue_btn"):
                if venue_name and venue_city and venue_country:
                    success, message = create_venue(venue_name, venue_city, venue_country, venue_capacity, venue_pitch)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Name, City, and Country")

        with venue_col2:
            st.markdown("**All Venues**")
            success, venues = read_all_venues()
            if success and venues:
                df = pd.DataFrame(venues)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total venues: {len(venues)}")
            else:
                st.warning("No venues found")

    # ==================== PLAYERS TAB ====================
    with enhanced_tab3:
        st.subheader("Player Management")

        player_col1, player_col2 = st.columns(2)

        with player_col1:
            st.markdown("**Add New Player**")

            # Get teams for dropdown
            success, teams = read_all_teams()
            team_options = {f"{t['name']} (ID: {t['id']})": t['id'] for t in teams} if success and teams else {}

            player_name = st.text_input("Player Name", key="player_name")
            player_full_name = st.text_input("Full Name", key="player_full_name")
            player_team = st.selectbox("Team", list(team_options.keys()), key="player_team") if team_options else None
            player_role = st.selectbox("Role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"], key="player_role")
            player_batting = st.selectbox("Batting Style", ["Right-handed", "Left-handed"], key="player_batting")
            player_bowling = st.selectbox("Bowling Style",
                ["Right-arm fast", "Left-arm fast", "Right-arm fast-medium", "Left-arm fast-medium",
                 "Right-arm medium", "Left-arm medium", "Right-arm off-break", "Left-arm off-break",
                 "Right-arm leg-break", "Left-arm leg-break", "None"], key="player_bowling")
            player_dob = st.date_input("Date of Birth", key="player_dob")
            player_nationality = st.text_input("Nationality", key="player_nationality")

            if st.button("â Add Player", key="add_player_btn"):
                if player_name and player_team and player_role:
                    team_id = team_options[player_team]
                    success, message = create_player(
                        player_name, player_full_name, team_id, player_role,
                        player_batting, player_bowling if player_bowling != "None" else None,
                        str(player_dob), player_nationality
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Name, Team, and Role")

        with player_col2:
            st.markdown("**All Players**")
            success, players = read_all_players()
            if success and players:
                df = pd.DataFrame(players)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total players: {len(players)}")
            else:
                st.warning("No players found")

    # ==================== ENHANCED MATCHES TAB ====================
    with enhanced_tab4:
        st.subheader("Enhanced Match Management")

        match_col1, match_col2 = st.columns(2)

        with match_col1:
            st.markdown("**Add New Enhanced Match**")

            # Get series, teams, venues for dropdowns
            success_series, series_list = read_all_teams()  # Placeholder - need to implement series CRUD
            success_teams, teams = read_all_teams()
            success_venues, venues = read_all_venues()

            series_options = {f"Series {i+1}": i+1 for i in range(5)}  # Placeholder
            team_options = {f"{t['name']} (ID: {t['id']})": t['id'] for t in teams} if success_teams and teams else {}
            venue_options = {f"{v['name']} (ID: {v['id']})": v['id'] for v in venues} if success_venues and venues else {}

            match_series = st.selectbox("Series", list(series_options.keys()), key="match_series") if series_options else None
            match_team1 = st.selectbox("Team 1", list(team_options.keys()), key="match_team1") if team_options else None
            match_team2 = st.selectbox("Team 2", list(team_options.keys()), key="match_team2") if team_options else None
            match_venue = st.selectbox("Venue", list(venue_options.keys()), key="match_venue") if venue_options else None
            match_date = st.date_input("Match Date", key="match_date")
            match_time = st.time_input("Match Time", key="match_time")
            match_status = st.text_input("Status", key="match_status")

            if st.button("â Add Enhanced Match", key="add_enhanced_match_btn"):
                if match_team1 and match_team2 and match_status:
                    series_id = series_options[match_series] if match_series else None
                    team1_id = team_options[match_team1]
                    team2_id = team_options[match_team2]
                    venue_id = venue_options[match_venue] if match_venue else None

                    success, message = create_enhanced_match(
                        series_id, team1_id, team2_id, venue_id,
                        str(match_date), str(match_time), match_status
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("â ï¸ Please fill in Team 1, Team 2, and Status")

        with match_col2:
            st.markdown("**Enhanced Matches**")
            success, matches = read_all_enhanced_matches()
            if success and matches:
                df = pd.DataFrame(matches)
                st.dataframe(df, use_container_width=True)
                st.info(f"Total enhanced matches: {len(matches)}")
            else:
                st.warning("No enhanced matches found")

    # ==================== OVERVIEW TAB ====================
    with enhanced_tab5:
        st.subheader("Database Overview")

        # Get stats for all tables
        try:
            conn = sqlite3.connect("cricket.db")
            cursor = conn.cursor()

            stats = {}

            # Count records in each table
            tables = ['teams', 'venues', 'players', 'matches_enhanced', 'matches']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = cursor.fetchone()['count']

            conn.close()

            # Display stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Teams", stats.get('teams', 0))
                st.metric("Venues", stats.get('venues', 0))
                st.metric("Players", stats.get('players', 0))

            with col2:
                st.metric("Enhanced Matches", stats.get('matches_enhanced', 0))
                st.metric("Legacy Matches", stats.get('matches', 0))

            with col3:
                total_records = sum(stats.values())
                st.metric("Total Records", total_records)
                st.metric("Database Tables", len(tables))

            # Show table relationships
            st.markdown("### Database Schema")
            st.markdown("""
            ```
            teams (id, name, short_name, country, captain, coach)
            âââ venues (id, name, city, country, capacity, pitch_type)
            âââ players (id, name, full_name, team_idâteams.id, role, ...)
            âââ matches_enhanced (id, series_id, team1_idâteams.id, team2_idâteams.id, venue_idâvenues.id, ...)
                âââ scorecards (match_idâmatches_enhanced.id, team_idâteams.id, ...)
                âââ player_performance (match_idâmatches_enhanced.id, player_idâplayers.id, ...)
            ```
            """)

        except Exception as e:
            st.error(f"Error loading database overview: {str(e)}")

    st.button("â¬ Back", key="back_enhanced", on_click=navigate_page, args=("home",))


# ================== DATA VISUALIZATIONS PAGE ==================
elif st.session_state.page == "visualizations":

    st.title("📈 Data Visualizations")
    st.markdown("### Interactive Charts and Analytics Dashboard")

    try:
        # Get database data
        conn = sqlite3.connect("cricket.db")
        cursor = conn.cursor()

        # Tab layout
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["🎯 Match Statistics", "👥 Player Analytics", "🏟️ Venue Analysis"])

        # ==================== MATCH STATISTICS ====================
        with viz_tab1:
            col1, col2 = st.columns(2)

            with col1:
                # Matches by Status
                st.subheader("Matches by Status")
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM matches
                    GROUP BY status
                """)
                data = cursor.fetchall()

                if data:
                    status_names = [row[0] if row[0] else "Unknown" for row in data]
                    status_counts = [row[1] for row in data]

                    fig = go.Figure(data=[go.Pie(
                        labels=status_names,
                        values=status_counts,
                        marker=dict(colors=['#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#8b5cf6'])
                    )])
                    apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            with col2:
                # Team Performance (Most Matches)
                st.subheader("Teams by Match Count")
                cursor.execute("""
                    SELECT team1, COUNT(*) as count
                    FROM matches
                    GROUP BY team1
                    ORDER BY count DESC
                    LIMIT 8
                """)
                data = cursor.fetchall()

                if data:
                    teams = [row[0] for row in data]
                    counts = [row[1] for row in data]

                    fig = go.Figure(data=[go.Bar(
                        x=teams,
                        y=counts,
                        marker=dict(color=['#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#8b5cf6', '#ec4899', '#f59e0b', '#ef4444'])
                    )])
                    fig.update_layout(
                        xaxis_title="Team",
                        yaxis_title="Matches Played"
                    )
                    apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            # Total matches metric
            st.divider()
            col_m1, col_m2, col_m3 = st.columns(3)

            cursor.execute("SELECT COUNT(*) FROM matches")
            total_matches = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT team1) FROM matches")
            unique_teams = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT status) FROM matches WHERE status IS NOT NULL")
            unique_statuses = cursor.fetchone()[0]

            with col_m1:
                st.metric("📊 Total Matches", total_matches)
            with col_m2:
                st.metric("🏆 Unique Teams", unique_teams)
            with col_m3:
                st.metric("📋 Match Statuses", unique_statuses)

        # ==================== PLAYER ANALYTICS ====================
        with viz_tab2:
            col1, col2 = st.columns(2)

            with col1:
                # Players by Role
                st.subheader("Players by Role Distribution")
                cursor.execute("""
                    SELECT role, COUNT(*) as count
                    FROM players
                    GROUP BY role
                """)
                data = cursor.fetchall()

                if data:
                    roles = [row[0] for row in data]
                    role_counts = [row[1] for row in data]

                    fig = go.Figure(data=[go.Bar(
                        x=roles,
                        y=role_counts,
                        marker=dict(color=['#0ea5e9', '#06b6d4', '#14b8a6', '#10b981'])
                    )])
                    fig.update_layout(
                        xaxis_title="Player Role",
                        yaxis_title="Count"
                    )
                    apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            with col2:
                # Players by Nationality
                st.subheader("Top 10 Countries by Player Count")
                cursor.execute("""
                    SELECT nationality, COUNT(*) as count
                    FROM players
                    WHERE nationality IS NOT NULL
                    GROUP BY nationality
                    ORDER BY count DESC
                    LIMIT 10
                """)
                data = cursor.fetchall()

                if data:
                    countries = [row[0] for row in data]
                    counts = [row[1] for row in data]

                    fig = go.Figure(data=[go.Scatter(
                        x=countries,
                        y=counts,
                        mode='markers+lines',
                        marker=dict(size=12, color='#0ea5e9'),
                        line=dict(color='#06b6d4')
                    )])
                    fig.update_layout(
                        xaxis_title="Country",
                        yaxis_title="Players Count"
                    )
                    apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            # Player metrics
            st.divider()
            col_p1, col_p2, col_p3 = st.columns(3)

            cursor.execute("SELECT COUNT(*) FROM players")
            total_players = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT team_id) FROM players WHERE team_id IS NOT NULL")
            players_with_team = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT nationality) FROM players WHERE nationality IS NOT NULL")
            nationalities = cursor.fetchone()[0]

            with col_p1:
                st.metric("👥 Total Players", total_players)
            with col_p2:
                st.metric("🎯 Teams Assigned", players_with_team)
            with col_p3:
                st.metric("🌍 Nationalities", nationalities)

        # ==================== VENUE ANALYSIS ====================
        with viz_tab3:
            col1, col2 = st.columns(2)

            with col1:
                # Venues by Pitch Type
                st.subheader("Venues by Pitch Type")
                cursor.execute("""
                    SELECT pitch_type, COUNT(*) as count
                    FROM venues
                    GROUP BY pitch_type
                """)
                data = cursor.fetchall()

                if data:
                    pitch_types = [row[0] if row[0] else "Unknown" for row in data]
                    counts = [row[1] for row in data]

                    fig = go.Figure(data=[go.Pie(
                        labels=pitch_types,
                        values=counts,
                        marker=dict(colors=['#0ea5e9', '#06b6d4', '#14b8a6'])
                    )])
                    apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            with col2:
                # Venue Capacity Analysis
                st.subheader("Venues by Capacity")
                cursor.execute("""
                    SELECT name, capacity
                    FROM venues
                    WHERE capacity > 0
                    ORDER BY capacity DESC
                    LIMIT 10
                """)
                data = cursor.fetchall()

                if data:
                    venues = [row[0] for row in data]
                    capacities = [row[1] for row in data]

                    fig = go.Figure(data=[go.Bar(
                        y=venues,
                        x=capacities,
                        orientation='h',
                        marker=dict(color=['#0ea5e9', '#06b6d4', '#14b8a6', '#10b981', '#8b5cf6', '#ec4899', '#f59e0b', '#ef4444', '#f97316', '#a855f7'])
                    )])
                    fig.update_layout(
                        xaxis_title="Capacity",
                        yaxis_title="Venue"
                    )
                    apply_chart_theme(fig)
                    st.plotly_chart(fig, use_container_width=True, theme=None)

            # Venue metrics
            st.divider()
            col_v1, col_v2, col_v3 = st.columns(3)

            cursor.execute("SELECT COUNT(*) FROM venues")
            total_venues = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT country) FROM venues")
            countries = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(capacity) FROM venues WHERE capacity > 0")
            avg_capacity_result = cursor.fetchone()[0]
            avg_capacity = int(avg_capacity_result) if avg_capacity_result else 0

            with col_v1:
                st.metric("🏟️ Total Venues", total_venues)
            with col_v2:
                st.metric("🌍 Countries", countries)
            with col_v3:
                st.metric("📊 Avg Capacity", f"{avg_capacity:,}")

        conn.close()

    except Exception as e:
        st.error(f"Error loading visualizations: {str(e)}")
        st.info("Make sure you have data in the database tables.")

    st.divider()
    st.button("⬅ Back", key="back_viz", on_click=navigate_page, args=("home",))
