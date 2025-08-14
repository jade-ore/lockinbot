from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Discord bot is hereee"

def run():
    app.run(host="0.0.0.0", port=3609)

def keep_alive():
    t = Thread(target=run)
    t.start()
