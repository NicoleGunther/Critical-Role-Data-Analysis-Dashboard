import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Critical Role Dashboard", layout="wide")

# Load cleaned dataset
@st.cache_data
def load_data():
    df = pd.read_csv("critrole_c2_cleaned.csv")
    return df

df = load_data()

# ==== PAGE TITLE ====
col_title, col_logo = st.columns([8, 1])

with col_title:
    st.title("Critical Role: Mighty Nein Dice Analysis")
    st.markdown("""
                Welcome to the **Critical Role Campaign 2 Dashboard**, where we break down every dice roll made by the *Mighty Nein* in their epic journey. Explore roll patterns, dice luck, pacing, and combat performance across 141 episodes of *absolute shenanigans*. Use the filters on the left to dive into the data your way.
                """)
    st.caption("Nicole Gunther Guerrero | ID: 23202583 | UCD Interactive Dashboards Python | 2025")

with col_logo:
    st.image("logo.png", width=90) 

st.markdown("#### Advanced Features Highlights")
st.markdown("""
- **Connected visualisations**: Episode range slider filters all charts.
- **Conditional content**: Chart layout switches based on filters.
- **Animated radar chart**: Displays changing roll categories by episode.
- **Chart-specific filters**: Local character selection built into individual charts.
""")

# ==== SIDEBAR ====
st.sidebar.header("Dashboard Controls")
main_characters = ["Beau", "Fjord", "Jester", "Veth", "Caleb", "Yasha", "Caduceus", "Molly"]

# Global episode range filter
min_ep, max_ep = int(df["Episode_Num"].min()), int(df["Episode_Num"].max())
episode_range = st.sidebar.slider("Select Episode Range", min_value=min_ep, max_value=max_ep, value=(min_ep, max_ep))

# Character filter for Roll Type Breakdown (used locally in pie chart)
selected_character = st.sidebar.selectbox("Select a Character (for Roll Breakdown)", df["Character"].unique())

# Include Guests/NPCs checkbox
include_guests = st.sidebar.checkbox("Include Guests & NPCs", value=True)

# ==== Apply Filters to Data ====
df_slider = df[(df["Episode_Num"] >= episode_range[0]) & (df["Episode_Num"] <= episode_range[1])]
if not include_guests:
    df_slider = df_slider[df_slider["Character"].isin(main_characters)]

# ==== Main area feedback ====
st.markdown(f"Currently viewing episodes {episode_range[0]} to {episode_range[1]}. All visualisations reflect this range.")

# Filter data for main characters
chart_df = df_slider[df_slider["Character"].isin(main_characters)]

# --- Roll Type Breakdown (Pie Chart) ---
char_data = df_slider[df_slider["Character"] == selected_character]
roll_type_counts = char_data["Roll Category"].value_counts().reset_index()
roll_type_counts.columns = ["Roll Category", "Count"]

fig_pie = px.pie(
    roll_type_counts,
    names="Roll Category",
    values="Count",
    title=f"Roll Type Distribution: {selected_character}",
    hole=0.4
)
fig_pie.update_traces(textinfo="percent+label")
fig_pie.update_layout(height=500)

# --- Nat 1s vs Nat 20s (Grouped Bar Chart) ---
nat_counts = chart_df.groupby("Character")[["Is_Nat1", "Is_Nat20"]].sum().reset_index()
nat_counts = pd.melt(nat_counts, id_vars="Character", value_vars=["Is_Nat1", "Is_Nat20"],
                     var_name="Roll Type", value_name="Count")
nat_counts["Roll Type"] = nat_counts["Roll Type"].map({"Is_Nat1": "Nat 1", "Is_Nat20": "Nat 20"})

fig_nat = px.bar(
    nat_counts,
    x="Character",
    y="Count",
    color="Roll Type",
    barmode="group",
    text="Count",
    color_discrete_map={"Nat 1": "#FF6666", "Nat 20": "#66FF99"},
    title="Nat 1s vs Nat 20s by Character"
)
fig_nat.update_layout(height=500)

# --- Display Side-by-Side ---
col_pie, col_nat = st.columns(2)

with col_pie:
    st.markdown(f"### Roll Type Breakdown: {selected_character}")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_nat:
    st.markdown("### Natural 1s vs 20s")
    st.plotly_chart(fig_nat, use_container_width=True)

# ==== Roll Frequency Over Time ====
st.subheader("Roll Frequency Across Episodes")
# Count rolls per episode
roll_freq = df_slider.groupby("Episode_Num").size().reset_index(name="Roll Count")
roll_freq = roll_freq.sort_values("Episode_Num")

# Create trend line using Plotly
fig_line = px.line(
    roll_freq,
    x="Episode_Num",
    y="Roll Count",
    title="Total Rolls Per Episode (Trend Included)",
    markers=True
)

roll_freq["Rolling Avg"] = roll_freq["Roll Count"].rolling(window=7, center=True).mean()
fig_line.add_scatter(
    x=roll_freq["Episode_Num"],
    y=roll_freq["Rolling Avg"],
    mode="lines",
    name="Episode Trend",
    line=dict(color="firebrick", dash="dash")
)

fig_line.update_layout(height=500, xaxis_title="Episode", yaxis_title="Number of Rolls")
st.plotly_chart(fig_line, use_container_width=True)


# ==== ANIMATED RADAR CHART: Roll Type Profile by Episode ====  https://docs.streamlit.io/develop/concepts/design/animate
st.subheader("Animated Radar Chart: Roll Type Distribution by Episode")
st.markdown("This animated radar chart shows how the distribution of roll types changes across episodes. It reveals pacing shifts and evolving playstyle as the campaign progresses.")

# Prepare data
radar_df = df_slider.groupby(["Episode_Num", "Roll Category"]).size().reset_index(name="Count")
all_categories = sorted(df_slider["Roll Category"].unique())
all_episodes = sorted(radar_df["Episode_Num"].unique())

# Make sure every episode has all categories
filled_data = []
for ep in all_episodes:
    ep_data = radar_df[radar_df["Episode_Num"] == ep].set_index("Roll Category").reindex(all_categories, fill_value=0)
    ep_data = ep_data.reset_index()
    ep_data["Episode_Num"] = ep
    filled_data.append(ep_data)
radar_full = pd.concat(filled_data)

# Initialise the figure
fig = go.Figure(
    frames=[
        go.Frame(
            data=[
                go.Scatterpolar(
                    r=radar_full[radar_full["Episode_Num"] == ep]["Count"],
                    theta=all_categories,
                    fill='toself'
                )
            ],
            name=str(ep)
        ) for ep in all_episodes
    ]
)

# Add the initial data (first episode)
initial_r = radar_full[radar_full["Episode_Num"] == all_episodes[0]]["Count"]

fig.add_trace(go.Scatterpolar(
    r=initial_r,
    theta=all_categories,
    fill='toself',
    line=dict(color="mediumpurple", width=3)
))

# Layout with animation controls
fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 130])
    ),
    title="Roll Category Radar (Animated by Episode)",
    updatemenus=[{
        "type": "buttons",
        "buttons": [
            {
                "label": "Play",
                "method": "animate",
                "args": [None, {
                    "frame": {"duration": 1000, "redraw": True},
                    "fromcurrent": True,
                    "transition": {"duration": 500, "easing": "cubic-in-out"}
                }]
            },
            {
                "label": "Pause",
                "method": "animate",
                "args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}]
            }
        ]
    }],
    sliders=[{
        "steps": [{
            "method": "animate",
            "args": [[str(ep)], {"mode": "immediate", "frame": {"duration": 500}, "transition": {"duration": 300}}],
            "label": f"Ep {ep}"
        } for ep in all_episodes],
        "currentvalue": {"prefix": "Episode: "}
    }],
    height=600
)
st.plotly_chart(fig, use_container_width=True)

# ==== DAMAGE / KILL BARS ====
# Filter only main characters for visual consistency
combat_df = df_slider[df_slider["Character"].isin(main_characters)]

# ==== Damage Data ====
damage_data = combat_df.groupby("Character")["Damage"].sum().reset_index()
damage_data = damage_data.sort_values("Damage", ascending=False)

fig_dmg = px.bar(
    damage_data,
    x="Character",
    y="Damage",
    text="Damage",
    color="Damage",
    color_continuous_scale="Reds",
)
fig_dmg.update_layout(height=500, margin=dict(t=50))
fig_dmg.update_traces(textposition="outside")

# ==== Kill Data ====
kill_data = combat_df.groupby("Character")["Kills"].sum().reset_index()
kill_data = kill_data.sort_values("Kills", ascending=False)

fig_kill = px.bar(
    kill_data,
    x="Character",
    y="Kills",
    text="Kills",
    color="Kills",
    color_continuous_scale="Purples",
)
fig_kill.update_layout(height=500, margin=dict(t=50))
fig_kill.update_traces(textposition="outside")

# ==== Display Side-by-Side ====
col_dmg, col_kill = st.columns(2)

with col_dmg:
    st.markdown("### Total Damage by Character")
    st.plotly_chart(fig_dmg, use_container_width=True)

with col_kill:
    st.markdown("### Total Kills by Character")
    st.plotly_chart(fig_kill, use_container_width=True)

# ==== SUMMARY TABLE ====
st.subheader("Character Summary Table")
main_df = df[df["Character"].isin(main_characters)]
summary_table = main_df.groupby("Character").agg(
    Total_Rolls=("Total Value", "count"),
    Avg_Roll=("Total Value", "mean"),
    Nat_1s=("Is_Nat1", "sum"),
    Nat_20s=("Is_Nat20", "sum"),
    Total_Damage=("Damage", "sum"),
    Kills=("Kills", "sum")
).reset_index()

summary_table["Avg_Roll"] = summary_table["Avg_Roll"].round(2)
st.dataframe(summary_table)

st.markdown("---")

# ==== SUMMARY METRICS ====
col1, col2, col3 = st.columns(3)
col1.metric("🎲 Total Rolls", f"{len(df)}")
col2.metric("🗡️ Total Damage", int(df['Damage'].sum()))
top_killer = df.groupby("Character")["Kills"].sum().idxmax()
col3.metric("💀 Top Killer", top_killer)

# ==== INSIGHTS ====
st.markdown("### Key Takeaways")
st.markdown("- **Beau** was the most consistent damage-dealer, with high roll counts and total damage.")
st.markdown("- **Caleb** and **Veth** led in confirmed kills, showing their deadly potential.")
st.markdown("- The unluckies player by far was **Jester** with who rolled more nat 1's than 20's, and **Beau** rolled the most amounts of nat 1's overall.")
st.markdown("- The pacing of rolls shows spikes during major arc finales.")


# ==== FOOTER ====
st.markdown("---")
st.caption("Nicole Gunther Guerrero | UCD Interactive Dashboards Python | 2025")
