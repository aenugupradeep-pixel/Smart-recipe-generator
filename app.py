"""
app.py
======
Streamlit User Interface for the Smart Recipe Generator from Leftover Ingredients.

Features:
1. Full single-column layout with output displayed directly below the submit button.
2. Leftover ingredients input + Cuisine Type (Indian, Chinese, Italian, etc.), Meal Type, and Dietary constraints.
3. Sidebar LLM Configuration (Groq / Google Gemini, Model, Temperature, Max Tokens).
4. Rendered Recipe Card displaying:
   - Title, Description, Prep Time, Servings, Difficulty
   - Ingredients used + basic pantry items
   - Step-by-step instructions strictly IN OR UNDER 6 STEPS
   - Chef's Pro Tip callout

Designed with clean, student-friendly code structure!
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Import backend logic and system prompt
from llm import generate_recipe
from prompts import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Recipe Generator",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for compact single-column dashboard layout & custom badges
st.markdown(
    """
    <style>
        /* Compact page margins with top spacing so header isn't cut off */
        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 900px !important;
        }

        /* Adjust spacing between blocks */
        div[data-testid="stVerticalBlock"] {
            gap: 0.8rem !important;
        }

        /* Header styling with vibrant gradient visible in both Light and Dark mode */
        .main-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
            text-align: center;
        }
        .sub-title {
            font-size: 1.05rem;
            color: #94A3B8;
            margin-bottom: 1.5rem;
            text-align: center;
        }

        /* Recipe Card Header Banner Styling */
        .recipe-header-card {
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
            color: white;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(255, 107, 107, 0.25);
            margin-top: 15px;
            margin-bottom: 15px;
        }
        .recipe-title {
            font-size: 1.7rem;
            font-weight: 800;
            margin: 0;
            color: #FFFFFF !important;
        }
        .recipe-desc {
            font-size: 1rem;
            opacity: 0.95;
            margin-top: 6px;
            color: #FFF5F5 !important;
        }

        /* Badge styles */
        .badge-container {
            display: flex;
            gap: 10px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .badge {
            background-color: rgba(255, 255, 255, 0.25);
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 0.88rem;
            font-weight: 600;
            color: #FFFFFF !important;
            backdrop-filter: blur(4px);
        }

        /* Step Card Styling compatible with dark and light mode */
        .step-card {
            background-color: rgba(255, 255, 255, 0.05);
            border-left: 4px solid #FF6B6B;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 10px;
            font-size: 0.98rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .step-number {
            font-weight: 700;
            color: #FF6B6B;
            margin-right: 6px;
        }

        /* Chef Tip Box styling */
        .chef-tip-box {
            background-color: rgba(245, 158, 11, 0.15);
            border: 1px solid #F59E0B;
            color: #FBBF24;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
            margin-top: 15px;
        }

        /* Submit Button styling */
        .stButton button {
            height: 48px;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. Sidebar Configuration (LLM Provider & Parameters)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Model Settings")
    st.markdown("Configure your AI Chef LLM engine:")

    # Provider Selection
    provider = st.selectbox(
        "Select Provider",
        ["Groq", "Gemini"],
        index=0,
        help="Groq offers ultra-fast inference; Gemini provides Google's multimodal AI models.",
    )

    # Dynamic Model Options depending on Provider
    if provider == "Groq":
        model_options = [
             "openai/gpt-oss-20b",
             "openai/gpt-oss-120b",
]
        api_key_env = "GROQ_API_KEY"
    else:
        model_options = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
        ]
        api_key_env = "GEMINI_API_KEY"

    model = st.selectbox("Select Model", model_options, index=0)

    st.divider()

    # Hyperparameters
    temperature = st.slider(
        "Temperature (Creativity)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Higher values make recipe ideas more creative; lower values keep it strictly conventional.",
    )

    max_tokens = st.slider(
        "Max Tokens",
        min_value=256,
        max_value=2048,
        value=1024,
        step=128,
        help="Maximum length of the model output.",
    )

    st.divider()

    # API Key Status Check Indicator
    has_key = bool(os.getenv(api_key_env))
    if has_key:
        st.success(f"🔑 {provider} API Key Detected")
    else:
        st.error(f"⚠️ {api_key_env} is missing in `.env`")
        st.caption("Please add your key to `.env` file to generate recipes.")

    st.caption("💡 Recipes are strictly constrained to **<= 6 steps**!")

# -----------------------------------------------------------------------------
# 3. Main Dashboard Layout (Single Column, Output Below Input)
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">🍳 Smart Recipe Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Turn your leftover ingredients into delicious meals in <b>6 steps or fewer</b>!</div>',
    unsafe_allow_html=True,
)

# Ingredient Text Input Area
user_ingredients = st.text_area(
    "🛒 What leftover ingredients do you have?",
    value="",
    height=120,
    placeholder="e.g. 3 eggs, boiled potatoes, half a onion, spinach, cheddar cheese, butter, garlic...",
    help="Type any ingredients you have lying around in your fridge or pantry!",
)

# Preference Options Row (Cuisine Type, Meal Type, Dietary Preference)
opt_col1, opt_col2, opt_col3 = st.columns(3)

with opt_col1:
    cuisine_type = st.selectbox(
        "🍛 Cuisine Type",
        [
            "Any Cuisine",
            "Indian",
            "Chinese",
            "Italian",
            "Mexican",
            "Continental",
            "Mediterranean",
            "Thai",
            "Japanese",
            "American",
        ],
        index=0,
    )

with opt_col2:
    meal_type = st.selectbox(
        "🍽️ Meal Type",
        ["Any Meal", "Breakfast", "Lunch", "Dinner", "Quick Snack"],
        index=0,
    )

with opt_col3:
    diet_pref = st.selectbox(
        "🥗 Dietary Preference",
        ["None", "Vegetarian", "Vegan", "Gluten-Free", "High Protein"],
        index=0,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Primary Submit Action Button
generate_btn = st.button(
    "👨‍🍳 Generate Recipe (In or Under 6 Steps)",
    type="primary",
    use_container_width=True,
)

# -----------------------------------------------------------------------------
# 4. Recipe Output Render Area (Displayed Directly Below Submit Button)
# -----------------------------------------------------------------------------
if generate_btn:
    if not user_ingredients.strip():
        st.warning("⚠️ Please enter your leftover ingredients above before submitting!")
    else:
        with st.spinner(f"Chef LLM ({provider} - {model}) is crafting your recipe..."):
            try:
                # Call backend LLM function
                recipe_data = generate_recipe(
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=SYSTEM_PROMPT,
                    ingredients=user_ingredients,
                    cuisine_type=cuisine_type,
                    meal_type=meal_type,
                    diet_pref=diet_pref,
                )

                # Store result in session state to persist across interactions
                st.session_state["last_recipe"] = recipe_data

            except Exception as e:
                st.error(f"❌ Recipe Generation Failed: {e}")

# Display persistent recipe result below submit button if available
if "last_recipe" in st.session_state and st.session_state["last_recipe"]:
    recipe = st.session_state["last_recipe"]

    st.markdown("---")

    # Extract recipe data fields
    title = recipe.get("recipe_title", "Delicious Leftover Dish")
    desc = recipe.get("description", "")
    prep_time = recipe.get("prep_time", "15 mins")
    servings = recipe.get("servings", "1-2 servings")
    difficulty = recipe.get("difficulty", "Easy")
    used_items = recipe.get("ingredients_used", [])
    pantry_items = recipe.get("additional_pantry_items", [])
    steps = recipe.get("steps", [])
    chef_tip = recipe.get("chef_tip", "")

    # 1. Recipe Header Banner Card
    st.markdown(
        f"""
        <div class="recipe-header-card">
            <div class="recipe-title">🍽️ {title}</div>
            <div class="recipe-desc">{desc}</div>
            <div class="badge-container">
                <span class="badge">⏱️ {prep_time}</span>
                <span class="badge">👥 {servings}</span>
                <span class="badge">🔥 {difficulty}</span>
                <span class="badge">📌 {len(steps)} / 6 Max Steps</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Ingredients Breakdown
    with st.expander("🥗 **View Ingredients Breakdown**", expanded=True):
        ing_col1, ing_col2 = st.columns(2)
        with ing_col1:
            st.markdown("**Used Leftovers:**")
            for item in used_items:
                st.markdown(f"- ✅ {item}")
        with ing_col2:
            st.markdown("**Basic Pantry Staples:**")
            for item in pantry_items:
                st.markdown(f"- 🧂 {item}")

    # 3. Step-by-Step Instructions (Max 6 Steps)
    st.markdown(f"### 👩‍🍳 Recipe Instructions ({len(steps)} Steps)")

    for idx, step_text in enumerate(steps, start=1):
        # Clean redundant "Step X:" if model included it inside string
        clean_step = step_text
        if clean_step.lower().startswith(f"step {idx}:"):
            clean_step = clean_step[len(f"step {idx}:"):].strip()

        st.markdown(
            f"""
            <div class="step-card">
                <span class="step-number">Step {idx}:</span> {clean_step}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. Chef Pro Tip Callout
    if chef_tip:
        st.markdown(
            f"""
            <div class="chef-tip-box">
                <strong>💡 Chef's Pro Tip:</strong> {chef_tip}
            </div>
            """,
            unsafe_allow_html=True,
        )
