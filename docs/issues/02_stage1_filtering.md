# Issue 2: Implement Stage 1 UI-Level Filtering

## Description
Extend the browser agent to interact with the MagicBricks search form. The agent must emulate human interaction to fill out the search criteria exactly as specified.

## Requirements
- Click on the location input and type "Whitefield".
- Select the appropriate dropdown suggestions for the Whitefield radius.
- Set the property type to "Rent".
- Set the BHK configuration to "2 BHK".
- Input the budget range: Rs. 50,000 (Min) to Rs. 60,000 (Max).
- Submit the search form.

## Acceptance Criteria
- The agent successfully interacts with all form fields without raising element-not-found errors.
- The resulting search page correctly reflects the chosen location, budget, and BHK criteria.
