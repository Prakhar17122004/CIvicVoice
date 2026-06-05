from flask import Flask, request, jsonify
import requests
import pandas as pd
import json
import os

from math import radians, cos, sin, sqrt, atan2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# =====================================
# OPENROUTER API KEY
# =====================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# =====================================
# LOAD NGO DATA
# =====================================

print("Loading NGO data...")

ngo_df = pd.read_csv("ngo_data.csv")

ngo_df["name"] = ngo_df["ngo_name"].astype(str)

ngo_df["city"] = (
    ngo_df["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)

ngo_df["state"] = (
    ngo_df["state"]
    .astype(str)
    .str.strip()
    .str.lower()
)

ngo_df["category"] = (
    ngo_df["main_category"]
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace("_", " ")
)

ngo_df["sectors"] = (
    ngo_df["sectors"]
    .astype(str)
    .str.strip()
    .str.lower()
)

ngo_df["lat"] = pd.to_numeric(
    ngo_df["latitude"],
    errors="coerce"
)

ngo_df["lng"] = pd.to_numeric(
    ngo_df["longitude"],
    errors="coerce"
)

ngo_df["combined_search"] = (
    ngo_df["category"].fillna("") + " " +
    ngo_df["sectors"].fillna("")
)

ngo_df = ngo_df.dropna(subset=["category"])

print("NGO data loaded successfully!")
print(f"Total NGOs Loaded: {len(ngo_df)}")

# =====================================
# DISTANCE FUNCTION
# =====================================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# =====================================
# CITY COORDINATES
# =====================================

def get_city_coordinates(city_name):

    try:

        url = (
            f"https://nominatim.openstreetmap.org/search"
            f"?q={city_name}&format=json&limit=1"
        )

        headers = {
            "User-Agent": "CivicVoiceAI"
        }

        response = requests.get(
            url,
            headers=headers
        )

        data = response.json()

        if len(data) > 0:

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            return lat, lon

    except Exception as e:

        print("Geocoding Error:", str(e))

    return None, None

# =====================================
# RELATED CATEGORY MAPPING
# =====================================

related_map = {

    "animal welfare": [
        "environment",
        "community development",
        "rural development"
    ],

    "women empowerment": [
        "women development",
        "human rights",
        "legal awareness & aid"
    ],

    "health & family welfare": [
        "nutrition",
        "children",
        "hiv/aids"
    ],

    "education & literacy": [
        "children",
        "skill development",
        "vocational training"
    ],

    "disaster management": [
        "rural development",
        "community development"
    ],

    "human rights": [
        "legal awareness & aid",
        "women empowerment"
    ]
}

# =====================================
# ROOT ROUTE
# =====================================

@app.route("/")
def home():

    return "AI NGO Recommendation API Running"

# =====================================
# PREDICT ROUTE
# =====================================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        # =====================================
        # GET INPUT
        # =====================================

        data = request.get_json()

        text = str(
            data.get("text", "")
        ).strip()

        user_city = str(
            data.get("city", "")
        ).strip().lower()

        user_state = str(
            data.get("state", "")
        ).strip().lower()

        user_lat, user_lng = get_city_coordinates(user_city)

        # =====================================
        # VALIDATION
        # =====================================

        if len(text) < 10:

            return jsonify({
                "error": "Complaint too short"
            }), 400

        # =====================================
        # AI PROMPT
        # =====================================

        prompt = f"""
You are an NGO complaint classification AI.

Analyze the complaint carefully.

Choose ONLY ONE category from this list:

- Education
- Aged/Elderly
- Agriculture
- Animal Welfare
- Children
- Community Development
- Disaster Management
- Drinking Water
- Education & Literacy
- Environment & Forests
- Health & Family Welfare
- HIV/AIDS
- Human Rights
- Legal Awareness & Aid
- Nutrition
- Rural Development
- Skill Development
- Vocational Training
- Women Empowerment
- Youth Affairs

Return ONLY valid JSON.

Complaint:
{text}

Return format:

{{
  "ngo_category": "...",
  "urgency": "...",
  "reason": "..."
}}

Rules:
- ngo_category MUST be from the given list only
- urgency must be Low, Medium, or High
- reason should be short and clear
- support multilingual complaints
"""

        # =====================================
        # OPENROUTER REQUEST
        # =====================================

        try:

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {

                "model": "openrouter/free",

                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )

            response_json = response.json()

            print("\nFULL AI RESPONSE:")
            print(response_json)

            if "choices" not in response_json:

                return jsonify({
                    "error": response_json
                }), 500

            result_text = (
                response_json["choices"][0]["message"]["content"]
            )

            result_text = (
                result_text
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            result = json.loads(result_text)

            ngo_category = (
                result["ngo_category"]
                .strip()
                .lower()
            )

            urgency = result["urgency"]

            reason = result["reason"]

        except Exception as ai_error:

            print("AI Error:", str(ai_error))

            ngo_category = "community development"

            urgency = "Medium"

            reason = (
                "AI service temporarily unavailable. "
                "Fallback classification used."
            )

        print("\nDEBUG")
        print("Category:", ngo_category)
        print("Urgency:", urgency)

        # =====================================
        # FILTER NGOs
        # =====================================

        filtered_ngos = ngo_df[
            ngo_df["combined_search"]
            .str.contains(
                ngo_category,
                case=False,
                na=False
            )
        ].copy()

        if filtered_ngos.empty:

            print("No exact NGO category found")

            filtered_ngos = ngo_df.copy()

        # =====================================
        # SMART LOCATION MATCHING
        # =====================================

        MAX_DISTANCE_KM = 300

        final_ngos = pd.DataFrame()

        # =====================================
        # STEP 1 → EXACT CATEGORY + SAME CITY
        # =====================================

        city_ngos = filtered_ngos[
            filtered_ngos["city"]
            .str.contains(
                user_city,
                case=False,
                na=False
            )
        ]

        if not city_ngos.empty:

            print("Found exact category NGOs in same city")

            final_ngos = city_ngos.copy()

        # =====================================
        # STEP 2 → EXACT CATEGORY + SAME STATE
        # =====================================

        elif user_state:

            state_ngos = filtered_ngos[
                filtered_ngos["state"]
                .str.contains(
                    user_state,
                    case=False,
                    na=False
                )
            ]

            if not state_ngos.empty:

                print("Found exact category NGOs in same state")

                final_ngos = state_ngos.copy()

        # =====================================
        # STEP 3 → RELATED CATEGORY + SAME CITY
        # =====================================

        if final_ngos.empty:

            related_keywords = related_map.get(
                ngo_category.lower(),
                ngo_category.split()
            )

            related_ngos = ngo_df[
                ngo_df["combined_search"]
                .apply(
                    lambda x: any(
                        keyword in str(x).lower()
                        for keyword in related_keywords
                    )
                )
            ]

            related_city_ngos = related_ngos[
                related_ngos["city"]
                .str.contains(
                    user_city,
                    case=False,
                    na=False
                )
            ]

            if not related_city_ngos.empty:

                print("Found related NGOs in same city")

                final_ngos = related_city_ngos.copy()

        # =====================================
        # STEP 4 → RELATED CATEGORY + SAME STATE
        # =====================================

        if final_ngos.empty and user_state:

            related_state_ngos = related_ngos[
                related_ngos["state"]
                .str.contains(
                    user_state,
                    case=False,
                    na=False
                )
            ]

            if not related_state_ngos.empty:

                print("Found related NGOs in same state")

                final_ngos = related_state_ngos.copy()

        # =====================================
        # STEP 5 → GENERAL NEARBY NGOs
        # =====================================

        if final_ngos.empty:

            print("Searching nearby general NGOs")

            nearby_ngos = ngo_df.dropna(
                subset=["lat", "lng"]
            ).copy()

            if (
                user_lat is not None
                and user_lng is not None
            ):

                nearby_ngos["distance"] = (
                    nearby_ngos.apply(
                        lambda row: calculate_distance(
                            user_lat,
                            user_lng,
                            float(row["lat"]),
                            float(row["lng"])
                        ),
                        axis=1
                    )
                )

                nearby_ngos = nearby_ngos[
                    nearby_ngos["distance"]
                    <= MAX_DISTANCE_KM
                ]

                if not nearby_ngos.empty:

                    print("Found nearby general NGOs")

                    final_ngos = nearby_ngos.sort_values(
                        by="distance"
                    )

        # =====================================
        # FINAL FALLBACK
        # =====================================

        if final_ngos.empty:

            print("Using complete NGO fallback")

            final_ngos = ngo_df.copy()

        # =====================================
        # FINAL NGO SELECTION
        # =====================================

        selected_ngos = final_ngos.head(5)

        ngo_list = []

        for _, row in selected_ngos.iterrows():

            ngo_list.append({

                "name": str(
                    row.get(
                        "name",
                        "Unknown NGO"
                    )
                ),

                "address": str(
                    row.get(
                        "address",
                        "No address"
                    )
                ),

                "city": str(
                    row.get(
                        "city",
                        "Unknown"
                    )
                ).title(),

                "category": str(
                    row.get(
                        "category",
                        "Unknown"
                    )
                ).title()
            })

        # =====================================
        # FINAL RESPONSE
        # =====================================

        return jsonify({

            "ngo_category": ngo_category.title(),

            "urgency": urgency,

            "reason": reason,

            "ngo_details": ngo_list
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "error": str(e)
        }), 500

# =====================================
# RUN SERVER
# =====================================

if __name__ == "__main__":

    app.run(
        port=5001,
        debug=True
    )

