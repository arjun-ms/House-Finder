import json

with open("output/results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Type: {type(data)}")

if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
    for key in data:
        val = data[key]
        if isinstance(val, list):
            print(f"\n--- {key}: {len(val)} items ---")
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    name = item.get("name", "?")
                    loc = item.get("location", "?")
                    price = item.get("price", "?")
                    floor = item.get("floor", "N/A")
                    age = item.get("age", "N/A")
                    score = item.get("score", "N/A")
                    print(f"  {i+1}. {name} | {loc} | {price} | floor={floor} | age={age} | score={score}")
                else:
                    print(f"  {i+1}. {str(item)[:120]}")
        else:
            print(f"\n--- {key}: {str(val)[:200]} ---")
elif isinstance(data, list):
    print(f"Length: {len(data)}")
    for i, item in enumerate(data):
        print(f"  {i+1}. {str(item)[:150]}")
