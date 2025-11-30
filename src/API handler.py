from bson import ObjectId
from pymongo import MongoClient
from redis import Redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv
from json import loads

load_dotenv()
templates = Jinja2Templates(directory="webpage")
REDIS_CLIENT = Redis.from_url(os.environ['REDIS_URL'])
client = MongoClient(os.environ["MONGO_URI"])
database = client[os.environ["DB_NAME"]]
CONSULTATIONS = database[os.environ["CONSULTATIONS_COLLECTION"]]

app = FastAPI()
@app.get("/pay/{token}")
def get_payment_page(token: str, request:Request):
    try:
        #check if data on redis
        value_string = REDIS_CLIENT.get(f"token_{token}")
        if not value_string:
            raise HTTPException(status_code=404, detail="Invalid payment link.")
        else:
            value = loads(value_string)
            return templates.TemplateResponse("payment_page.html", {"request":request,"email":value['email'], "price":value["price"]})
    except HTTPException as e:
        raise e
    except Exception as e:
        print("exception", e)
        raise HTTPException(status_code=500, detail="Internal Server Error.")

@app.post("/pay/{token}")
def process_payment(token: str):
    try:
        # check if data on redis
        value_string = REDIS_CLIENT.get(f"token_{token}")
        if not value_string:
            raise HTTPException(status_code=404, detail="Invalid payment link.")
        else:
            value = loads(value_string)
            CONSULTATIONS.update_one({"_id":ObjectId(value["consultation_id"])}, {"$set":{"status": "booked", "payment":"received"}})
            REDIS_CLIENT.delete(f"token_{token}")
            return {"success": True}

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)