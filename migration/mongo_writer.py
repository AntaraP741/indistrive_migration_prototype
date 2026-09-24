from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import datetime
from decimal import Decimal
import uuid
from urllib.parse import urlparse


class MongoWriter:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[db_name]

        try:
            # Fail fast so the API can return a useful configuration error.
            self.client.admin.command("ping")
        except ServerSelectionTimeoutError as exc:
            host = self._describe_target(uri)
            raise ValueError(
                f"Unable to connect to MongoDB at {host}. "
                f"Start MongoDB or update the target URI/host/port."
            ) from exc
        except PyMongoError as exc:
            raise ValueError(f"MongoDB connection failed: {exc}") from exc

    @staticmethod
    def _describe_target(uri):
        parsed = urlparse(uri)
        if parsed.netloc:
            return parsed.netloc
        return uri or "the configured target"

    def _sanitize_value(self, value):
        """
        Recursively convert values into MongoDB-compatible types.
        """

        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return datetime.datetime(value.year, value.month, value.day)

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._sanitize_value(v) for v in value]

        return value

    def insert_batch(self, collection, documents):

        if not documents:
            return

        cleaned = [self._sanitize_value(doc) for doc in documents]

        self.db[collection].insert_many(cleaned)

    def clear_collection(self, collection):
        self.db[collection].delete_many({})
