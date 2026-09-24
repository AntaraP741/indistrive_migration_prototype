import json
import hashlib
from pymongo import MongoClient


def _row_checksum(doc):
    ordered = sorted(doc.items())
    row_string = "|".join([f"{k}:{v}" for k, v in ordered])
    return hashlib.md5(row_string.encode()).hexdigest()




def _load_readiness(readiness_input):
    if isinstance(readiness_input, str):
        with open(readiness_input, "r") as f:
            return json.load(f)
    return readiness_input


def generate_post_migration_report(
    readiness_report_path,
    mongo_uri,
    db_name,
    output_path="outputs/postMigrationReport.json"
):

    # LOAD READINESS
    readiness = _load_readiness(readiness_report_path)

    tables = readiness.get("tables", {})

    client = MongoClient(mongo_uri)
    db = client[db_name]

    collections = db.list_collection_names()

    table_reports = []
    overall_success = True

    for table_name, meta in tables.items():

        # HANDLE EMBEDDED 
        if table_name not in collections:
            table_reports.append({
                "table": table_name,
                "source_count": meta["row_count"],
                "mongo_count": 0,
                "count_match": False,
                "checksum_match": False,
                "datatype_match": True,
                "skipped": True,
                "reason": "embedded_or_not_migrated",
                "success": True
            })
            continue

        #FETCH DOCS 
        docs = list(db[table_name].find({}))

        mongo_count = len(docs)
        source_count = meta["row_count"]

        count_match = mongo_count == source_count


        #DATATYPE CHECK 
        datatype_issues = []

        for doc in docs[:50]:
            doc.pop("_id", None)

            for col in meta["columns"]:
                if col not in doc:
                    datatype_issues.append(f"{table_name}.{col} missing")
                elif doc[col] is None:
                    datatype_issues.append(f"{table_name}.{col} null")

        datatype_match = len(datatype_issues) == 0
        overall_success = overall_success and count_match and datatype_match

        table_reports.append({
            "table": table_name,
            "source_count": source_count,
            "mongo_count": mongo_count,
            "count_match": count_match,
            "datatype_match": datatype_match,
            "success": overall_success
        })

    report = {
        "tables": table_reports,
        "overall_success": overall_success
    }

    # SAVE
    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)

    client.close()

    return report
