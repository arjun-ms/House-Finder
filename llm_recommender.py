"""
LLM Recommender - Gemini 2.0 Flash integration for property ranking.

Takes shortlisted properties as structured JSON, scores them on weighted
criteria, and returns a ranked list with top 3 and best pick.
"""

import json
import os

from dotenv import load_dotenv
from google.genai import types
from google import genai

import config

# Load API key from .env
load_dotenv()


def get_gemini_client():
    """Initialize and return the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. "
            "Create a .env file with GEMINI_API_KEY=your_key_here "
            "(see .env.example)"
        )
    client = genai.Client(api_key=api_key)
    return client


def build_prompt(properties: list[dict]) -> str:
    """Build the prompt for Gemini to rank properties."""

    user_requirements = f"""
USER REQUIREMENTS:
- Looking for: 2BHK apartment for RENT
- Location: Whitefield, Bangalore (or within 5km)
- Budget: Rs {config.MIN_BUDGET:,} - Rs {config.MAX_BUDGET:,} per month
- Floor: {config.MIN_FLOOR}th floor and above preferred
- Property Age: {config.MAX_PROPERTY_AGE} years or newer preferred
- Must have: Balcony
"""

    scoring_criteria = f"""
SCORING CRITERIA (use these weights):
- Rent Value for Money (rent vs area, furnishing quality): {config.SCORING_WEIGHTS['rent_value']*100:.0f}%
- Floor Preference (higher floors preferred, {config.MIN_FLOOR}+ ideal): {config.SCORING_WEIGHTS['floor_preference']*100:.0f}%
- Property Age (newer is better, under {config.MAX_PROPERTY_AGE} years ideal): {config.SCORING_WEIGHTS['property_age']*100:.0f}%
- Location Quality (closer to Whitefield center is better): {config.SCORING_WEIGHTS['location_quality']*100:.0f}%
- Amenities & Extras (balcony, gym, parking, swimming pool, etc.): {config.SCORING_WEIGHTS['amenities']*100:.0f}%
"""

    properties_json = json.dumps(properties, indent=2, default=str)

    prompt = f"""You are a real estate analyst helping a tenant find the best 2BHK rental apartment in Whitefield, Bangalore.

{user_requirements}

{scoring_criteria}

INSTRUCTIONS:
1. Analyze each property below against the user's requirements
2. Score each property on a scale of 1-10 based on the weighted criteria above
3. Properties with missing data (null/None fields) should be scored conservatively (lower) but not automatically ranked last
4. Select the TOP 10 properties as the shortlist
5. From those 10, identify the TOP 3 best properties
6. Declare the single BEST property with a detailed explanation

PROPERTIES DATA:
{properties_json}

IMPORTANT: Respond with ONLY valid JSON in the exact format below. No markdown, no explanation outside the JSON.

{{
  "shortlisted_10": [
    {{
      "rank": 1,
      "property_name": "name from data",
      "listing_url": "url from data",
      "score": 8.5,
      "price": "price from data",
      "location": "location from data",
      "floor_number": "floor from data or unknown",
      "property_age": "age from data or unknown",
      "strengths": ["strength 1", "strength 2"],
      "weaknesses": ["weakness 1"]
    }}
  ],
  "top_3": [
    {{
      "rank": 1,
      "property_name": "name",
      "listing_url": "url",
      "score": 9.0,
      "recommendation_reason": "2-3 sentence explanation of why this property is recommended"
    }}
  ],
  "best_pick": {{
    "property_name": "name",
    "listing_url": "url",
    "score": 9.0,
    "why": "Detailed paragraph (4-6 sentences) explaining why this is the absolute best choice, covering rent value, floor, age, location, and amenities."
  }}
}}
"""
    return prompt


def rank_properties(properties: list[dict]) -> dict:
    """
    Send properties to Gemini for ranking and recommendation.
    Returns structured ranking data.
    """
    print(f"\n[*] Sending {len(properties)} properties to Gemini for ranking...")

    client = get_gemini_client()
    prompt = build_prompt(properties)

    # Call Gemini with structured JSON output
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,  # Low temp for consistent ranking
                ),
            )

            # Parse the response
            response_text = response.text.strip()

            # Clean up response if wrapped in markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first and last lines (```json and ```)
                response_text = "\n".join(lines[1:-1])

            result = json.loads(response_text)

            # Validate structure
            if "shortlisted_10" not in result or "top_3" not in result or "best_pick" not in result:
                raise ValueError("Response missing required fields")

            print(f"[*] Gemini ranking complete!")
            print(f"    Shortlisted: {len(result['shortlisted_10'])} properties")
            print(f"    Top 3 identified")
            print(f"    Best pick: {result['best_pick']['property_name']}")

            return result

        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries - 1:
                print(f"[!] Attempt {attempt + 1} failed ({e}), retrying...")
                continue
            else:
                print(f"[!] All attempts failed. Returning raw response.")
                return {
                    "error": str(e),
                    "raw_response": response_text if "response_text" in dir() else "No response",
                    "shortlisted_10": [],
                    "top_3": [],
                    "best_pick": {"property_name": "Error", "why": str(e)},
                }

        except Exception as e:
            print(f"[!] Gemini API error: {e}")
            raise
    
    raise RuntimeError("rank_properties failed to return a result")
