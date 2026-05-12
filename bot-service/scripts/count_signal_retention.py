import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymongo import MongoClient
from config import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client["cryptoDB"]
col = db["signals"]

# 1. Total count
total = col.count_documents({})
print(f"\n=== Total Signals: {total} ===")

# 2. Count by timeframe
print("\n--- By Timeframe ---")
pipeline_tf = [
    {"$group": {"_id": "$timeframe", "count": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
]
for doc in col.aggregate(pipeline_tf):
    print(f"  {doc['_id']}: {doc['count']}")

# 3. Count by open/closed status
open_filter = {"tp_hit": {"$ne": True}, "sl_hit": {"$ne": True}}
closed_filter = {"$or": [{"tp_hit": True}, {"sl_hit": True}]}

open_count = col.count_documents(open_filter)
closed_count = col.count_documents(closed_filter)
print("\n--- By Status ---")
print(f"  open:   {open_count}")
print(f"  closed: {closed_count}")

# 4. expires_at exists vs missing
has_expires = col.count_documents({"expires_at": {"$exists": True}})
no_expires = col.count_documents({"expires_at": {"$exists": False}})
print("\n--- expires_at Field ---")
print(f"  exists:  {has_expires}")
print(f"  missing: {no_expires}")

# 5. Timeframe + status + expires_at summary
print("\n--- Timeframe + Status + expires_at ---")
pipeline_summary = [
    {
        "$addFields": {
            "status": {
                "$cond": {
                    "if": {
                        "$or": [
                            {"$eq": ["$tp_hit", True]},
                            {"$eq": ["$sl_hit", True]},
                        ]
                    },
                    "then": "closed",
                    "else": "open",
                }
            },
            "has_expires_at": {"$cond": [{"$gt": ["$expires_at", None]}, True, False]},
        }
    },
    {
        "$group": {
            "_id": {
                "timeframe": "$timeframe",
                "status": "$status",
                "has_expires_at": "$has_expires_at",
            },
            "count": {"$sum": 1},
        }
    },
    {"$sort": {"_id.timeframe": 1, "_id.status": 1, "_id.has_expires_at": 1}},
]
for doc in col.aggregate(pipeline_summary):
    tf = doc["_id"].get("timeframe", "N/A")
    status = doc["_id"]["status"]
    expires = "yes" if doc["_id"]["has_expires_at"] else "no"
    print(f"  timeframe={tf}  status={status}  expires_at={expires}  count={doc['count']}")

client.close()
