"""
Database integration - SQLite support with backward compatibility
"""
import os
from config import DATABASE_PATH

# Check if we should use SQLite or MongoDB
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # Import SQLite functions
    from .sqlite_database import (
        present_user, add_user, db_verify_status, 
        db_update_verify_status, full_userbase, del_user,
        # Category functions
        create_category, get_category, get_categories, 
        update_category, delete_category,
        # File functions
        add_file, get_file, get_files_by_category, search_files,
        create_file_link, get_file_by_link_code
    )
else:
    # Keep original MongoDB implementation
    import motor.motor_asyncio
    from config import DB_URI, DB_NAME

    dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
    database = dbclient[DB_NAME]

    user_data = database['users']

    default_verify = {
        'is_verified': False,
        'verified_time': 0,
        'verify_token': "",
        'link': ""
    }

    def new_user(id):
        return {
            '_id': id,
            'verify_status': {
                'is_verified': False,
                'verified_time': "",
                'verify_token': "",
                'link': ""
            }
        }

    async def present_user(user_id: int):
        found = await user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(user_id: int):
        user = new_user(user_id)
        await user_data.insert_one(user)
        return

    async def db_verify_status(user_id):
        user = await user_data.find_one({'_id': user_id})
        if user:
            return user.get('verify_status', default_verify)
        return default_verify

    async def db_update_verify_status(user_id, verify):
        await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

    async def full_userbase():
        user_docs = user_data.find()
        user_ids = [doc['_id'] async for doc in user_docs]
        return user_ids

    async def del_user(user_id: int):
        await user_data.delete_one({'_id': user_id})
        return
