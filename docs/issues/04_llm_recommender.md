# Issue 4: Integrate LLM Recommender (Gemini 2.0 Flash)

## Description
Pass the shortlisted properties to a Large Language Model (`llm_recommender.py`) to rank them based on predefined weighted criteria, simulating a human decision-making process.

## Requirements
- Construct a structured prompt containing the shortlisted properties in JSON format.
- Call the Google Gemini 2.0 Flash API using the provided API key.
- Apply the following evaluation weights:
  - Rent Value (30%)
  - Floor Preference (25%)
  - Property Age (20%)
  - Location Quality (15%)
  - Amenities (10%)
- The LLM must output a ranked list, selecting the top 3 properties and identifying the absolute "Best Pick."
- The LLM must provide detailed reasoning for its choices.

## Acceptance Criteria
- API calls to Gemini succeed and return a properly formatted response.
- The response clearly ranks the properties and highlights the top 3.
- The reasoning provided aligns with the specified weights.
