from fastapi import FastAPI, Request
from chatbot import chatbot
import pandas as pd

app = FastAPI()

df = pd.read_excel("Master_OD_Data.xlsx")

@app.post("/whatsapp")
async def reply(req: Request):

    form = await req.form()
    msg = form.get("Body")

    response = chatbot(msg, df)

    return f"<Response><Message>{response}</Message></Response>"