from google import genai

keys = [
    ("AIzaSyAAhkUGSYBOj4ZvfvCvNIh7PGhtFb-orVM", "key1"),
    ("AIzaSyAUkD0JEumRAt0cFSSdlKS-utciPkegV28", "key2"),
    ("AIzaSyCSE1UYqVmHI5jkI30DSBjy5KikEaQhhEQ", "key3"),
]

models = ["gemini-2.0-flash-lite", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

for k, name in keys:
    for m in models:
        try:
            c = genai.Client(api_key=k)
            r = c.models.generate_content(model=m, contents="pong")
            print(f"{name} + {m}: OK")
        except Exception as e:
            s = str(e)[:80]
            print(f"{name} + {m}: {s}")
