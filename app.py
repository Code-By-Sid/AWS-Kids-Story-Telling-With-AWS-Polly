from flask import Flask, render_template, request, redirect
import requests

app = Flask(__name__)

API = "https://2fq45ybfoi.execute-api.ap-south-1.amazonaws.com/default"


@app.route("/")
def home():

    try:
        response = requests.get(API + "/stories")
        data = response.json()
        stories = data.get("stories", [])
    except Exception:
        stories = []

    return render_template(
        "index.html",
        stories=stories
    )


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["story"]

    payload = {
        "filename": file.filename,
        "story": file.read().decode("utf-8")
    }

    requests.post(
        API + "/upload",
        json=payload
    )

    return redirect("/")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=2000,
        debug=True
    )