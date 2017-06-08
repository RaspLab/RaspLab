from flask import Flask, jsonify
app = Flask(__name__)
import json


diz=json.loads(open("orari.json","r").read())
diz["ore"]=json.loads(open("ore.json","r").read())


@app.route("/get/<string:id>")
def get(id):
    return jsonify(diz[id]) if id in diz else jsonify({"response":"not found"})

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=5001)
