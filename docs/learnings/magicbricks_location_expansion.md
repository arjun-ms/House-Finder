# MagicBricks Search Radius & Location Expansion

**Date:** July 12, 2026
**Topic:** Why locations outside the strict search keyword appear in the final dataset (e.g., Varthur and Krishnarajapura appearing in a "Whitefield" search).

## Overview
When executing a search on MagicBricks for a specific neighborhood (e.g., "Whitefield, Bangalore"), the resulting properties in the final report occasionally include locations that do not explicitly match the requested keyword. This document explains why this happens and the geographical context of these results.

---

## 1. Algorithmic Search Radius Expansion
- **The MagicBricks Algorithm:** MagicBricks does not boundary-fence search results to the exact polygon of the requested neighborhood. To provide buyers with more options, their algorithm automatically includes properties within a short radius of the target location.
- **Scraper Behavior:** Our `browser_agent.py` blindly extracts the property cards that MagicBricks returns on the search results page. Because MagicBricks deliberately injects nearby neighborhoods into the Whitefield search results, our scraper picks them up and feeds them into the pipeline.
- **Resolution:** This is considered expected behavior. If strict boundary enforcement is required in the future, a string-matching filter (e.g., `if "whitefield" not in prop.location.lower(): drop()`) must be added to `data_filter.py`.

## 2. Geographical Context (Bangalore)
Bangalore is a massive mega-city. The locations returned in the search are not separate cities or villages, but rather distinct, heavily interconnected neighborhoods/suburbs within Bangalore. 

### Case Study: Whitefield vs. Varthur & KR Puram
When searching for Whitefield, it is extremely common to see properties from **Varthur** and **Krishnarajapura (KR Puram)**. 
- **Varthur (Varathur):** Directly borders Whitefield to the South. It is practically a continuation of the Whitefield residential zone. Distance to Whitefield tech hubs: **~3 to 5 kilometers**.
- **Krishnarajapura (KR Puram):** Directly borders Whitefield to the North/North-West. It is a major transit hub for professionals commuting into Whitefield. Distance to Whitefield tech hubs: **~6 to 8 kilometers**.

Because these areas directly border Whitefield and serve as primary residential zones for Whitefield's IT workers, MagicBricks highly ranks them as relevant alternatives for a Whitefield rental search.
