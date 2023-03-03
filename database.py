import config
from pymongo import MongoClient

client = MongoClient(config.DB_HOST, int(config.DB_PORT))
db = client['calendar']
collection = db['calendar']


def insert_document(data):
    return collection.insert_one(data).inserted_id


def update_document(query_elements, new_values):
    collection.update_one(query_elements, {'$set': new_values})


def delete_document(query):
    collection.delete_one(query)


def check_and_update(query, new_document):
    if not collection.find_one_and_update(query, new_document):
        insert_document(new_document["$set"])


def get_owner_name(id):
    return db['telegrams'].find_one({"user_id": id}).get('full_name')


def get_all_employees():
    return db['telegrams'].find({})
