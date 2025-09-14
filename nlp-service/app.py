from fastapi import FastAPI
app = FastAPI()

@app.post("/parse")
def parse(payload: dict):
    # TODO: implement rules for track/param/dB parsing
    return {"intent":"set_parameter","targets":[{"track":"Track 1","plugin":None,"parameter":"volume"}],"operation":{"type":"absolute","value":-6,"unit":"dB"}}

@app.post("/howto")
def howto(payload: dict):
    return {"answer":"(placeholder) How-to steps go here."}
