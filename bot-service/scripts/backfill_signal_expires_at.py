import sys
import os
import argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymongo import MongoClient
from config import MONGODB_URI

RETENTION = {
    "15m": timedelta(days=3),
    "1h":  timedelta(days=7),
    "4h":  timedelta(days=15),
    "1d":  timedelta(days=30),
}

BATCH_SIZE = 100


def is_closed(doc):
    return doc.get("tp_hit") is True or doc.get("sl_hit") is True


def get_base_date(doc):
    if is_closed(doc):
        for field in ("outcome_checked_at", "updated_at", "created_at", "opened_at"):
            val = doc.get(field)
            if isinstance(val, datetime):
                return val
    else:
        for field in ("opened_at", "created_at", "updated_at"):
            val = doc.get(field)
            if isinstance(val, datetime):
                return val
    return None


def main():
    parser = argparse.ArgumentParser(description="Backfill expires_at for signals missing the field.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes.")
    args = parser.parse_args()

    dry_run = args.dry_run

    client = MongoClient(MONGODB_URI)
    db = client["cryptoDB"]
    col = db["signals"]

    now = datetime.now(timezone.utc)

    missing_filter = {"expires_at": {"$exists": False}}
    total_missing = col.count_documents(missing_filter)

    print(f"\ndry_run          : {dry_run}")
    print(f"total_missing    : {total_missing}")

    would_update = 0
    updated = 0
    skipped = 0
    would_expire_immediately = 0
    counts_by_timeframe: dict[str, int] = {}
    expire_immediately_detail: dict[tuple, int] = {}  # (timeframe, status) -> count

    cursor = col.find(missing_filter, no_cursor_timeout=False)

    batch_ids = []
    batch_expires = []

    def flush_batch():
        nonlocal updated
        if not batch_ids:
            return
        for doc_id, expires_at in zip(batch_ids, batch_expires):
            col.update_one(
                {"_id": doc_id, "expires_at": {"$exists": False}},
                {"$set": {"expires_at": expires_at}},
            )
            updated += 1
        batch_ids.clear()
        batch_expires.clear()

    for doc in cursor:
        timeframe = doc.get("timeframe")
        retention = RETENTION.get(timeframe)

        if retention is None:
            skipped += 1
            continue

        base_date = get_base_date(doc)
        if base_date is None:
            skipped += 1
            continue

        # Ensure base_date is timezone-aware
        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=timezone.utc)

        expires_at = base_date + retention

        would_update += 1
        counts_by_timeframe[timeframe] = counts_by_timeframe.get(timeframe, 0) + 1

        if expires_at <= now:
            would_expire_immediately += 1
            status = "closed" if is_closed(doc) else "open"
            key = (timeframe, status)
            expire_immediately_detail[key] = expire_immediately_detail.get(key, 0) + 1

        if not dry_run:
            batch_ids.append(doc["_id"])
            batch_expires.append(expires_at)
            if len(batch_ids) >= BATCH_SIZE:
                flush_batch()

    if not dry_run:
        flush_batch()

    cursor.close()
    client.close()

    print(f"would_update     : {would_update}")
    if not dry_run:
        print(f"updated          : {updated}")
    print(f"skipped          : {skipped}")
    print(f"would_expire_immediately: {would_expire_immediately}")

    if dry_run and expire_immediately_detail:
        print("\n--- would_expire_immediately by timeframe + status ---")
        for tf in ("15m", "1h", "4h", "1d"):
            for status in ("open", "closed"):
                count = expire_immediately_detail.get((tf, status), 0)
                if count:
                    print(f"  {tf:>3}  {status:<6}: {count}")
        other_keys = {k: v for k, v in expire_immediately_detail.items() if k[0] not in RETENTION}
        for (tf, status), count in sorted(other_keys.items()):
            print(f"  {tf} (unknown retention)  {status}: {count}")

    print("\n--- Counts by timeframe ---")
    for tf in ("15m", "1h", "4h", "1d"):
        count = counts_by_timeframe.get(tf, 0)
        print(f"  {tf:>3}: {count}")
    other_tfs = {k: v for k, v in counts_by_timeframe.items() if k not in RETENTION}
    for tf, count in sorted(other_tfs.items()):
        print(f"  {tf} (unknown retention): {count}")


if __name__ == "__main__":
    main()
