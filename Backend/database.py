from pymongo import MongoClient
import datetime

mongo_client = None
db = None
chats_collection = None
user_collection = None

def init_db():
    global mongo_client, db, chats_collection, user_collection
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db = mongo_client["chat_db"]
    chats_collection = db["chat_sessions"]
    user_collection = db["user_session"]
    print("MongoDB initialized")

def get_chats_collection():
    return chats_collection

def get_user_collection():
    return user_collection
