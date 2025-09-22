import csv
from datetime import datetime
from typing import Optional
import pymongo
import certifi
from pydantic import BaseModel

client = pymongo.MongoClient(
    'mongodb+srv://dillon-local:4YL1yp5ZpkuQVVPV@production.xwwgilj.mongodb.net/',
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
)

db = client['Processing']
col = db['Total Billed by Invoice ID']

# Sample the collection to discover available top-level fields (columns)
print("Sampling collection to list top-level fields (columns)...")
sample_keys = set()
for doc in col.find().limit(200):
    sample_keys.update(doc.keys())
print("Top-level fields (sample):", sorted(sample_keys))

# Build report for ALL invoices (no date filter)
# If you want to reintroduce a date filter later, change col.find() to
# col.find({'included_in_date': 'YYYYMMDD'})

invoices_ids = set()
# Fetch all invoices
col_data = list(col.find())
for invoice in col_data:
    invoices_ids.add(invoice['_id'].split('-')[0])

orders = list(db["WorkOrders"].find({'_id': {'$in': list(invoices_ids)}}))

orders_map = {x['_id']: x for x in orders}

# Helper to extract page counts from multiple possible locations
def get_page_counts(order_doc):
    """Return (predupe, postdupe) page counts if present, else (None, None).

    Checks a variety of likely locations/field names in the WorkOrders doc.
    """
    pre = None
    post = None

    # 1) Top-level fields commonly used
    pre = pre or order_doc.get('predupe_page_count')
    post = post or order_doc.get('postdupe_page_count')

    # 2) Alternate casing/naming
    pre = pre or order_doc.get('preDupePageCount')
    post = post or order_doc.get('postDupePageCount')

    pre = pre or order_doc.get('predupe')
    post = post or order_doc.get('postdupe')

    # 3) Generic page_count if only one exists (assign to post by convention)
    if post is None:
        single = order_doc.get('page_count') or order_doc.get('pageCount')
        if isinstance(single, int):
            post = single

    # 4) Nested under tristar_json
    tj = order_doc.get('tristar_json', {}) or {}
    if isinstance(tj, dict):
        if pre is None:
            pre = tj.get('predupe_page_count') or tj.get('preDupePageCount')
        if post is None:
            post = tj.get('postdupe_page_count') or tj.get('postDupePageCount')

        # 5) Possibly grouped under pageCounts
        pc = tj.get('pageCounts', {}) if isinstance(tj, dict) else {}
        if isinstance(pc, dict):
            if pre is None:
                pre = pc.get('preDupe') or pc.get('predupe') or pc.get('pre')
            if post is None:
                post = pc.get('postDupe') or pc.get('postdupe') or pc.get('post')

    # Ensure ints where possible
    def to_int(x):
        try:
            return int(x)
        except (TypeError, ValueError):
            return None

    pre = to_int(pre)
    post = to_int(post)

    # If only one of them exists, it's okay to copy to both per user's request
    if pre is None and post is not None:
        pre = post
    if post is None and pre is not None:
        post = pre

    return pre, post

class ShirleiReport(BaseModel):
    id: str
    date_received: datetime
    Insurer: str
    RequestType: str
    Claimant: str
    ClaimNumber: str
    ExaminerEmail: str
    FlatRate: str
    PageCost: str
    Shipping: str
    SalesTax: str
    Handling: str
    ROIFees: str
    TotalInvoice: str
    PredupePageCount: Optional[int]
    PostDupePageCount: Optional[int]
    QMESavings: Optional[str]
    NetSavingsToClient: Optional[str]

final_data = []
for invoice in col_data:
    order = orders_map[invoice['_id'].split('-')[0]]
    pre_count, post_count = get_page_counts(order)

    report_row = ShirleiReport(
        id=invoice['_id'],
        date_received=invoice['date_received'],
        Insurer=order['tristar_json'].get('insurerName', ''),
        RequestType=order['tristar_json']['orderType'],
        Claimant=order['tristar_json']['claimantName'],
        ClaimNumber=order['tristar_json']['claimNumber'],
        ExaminerEmail=order['tristar_json'].get('examinerEmail', ''),
        FlatRate="$" + str(invoice['flat_rate']),
        PageCost="$" + str(invoice['page_cost']),
        Shipping="$" + str(invoice['shipping']),
        SalesTax="$" + str(invoice['sales_tax']),
        Handling="$" + str(invoice['handling']),
        ROIFees="$" + str(invoice.get('roi_fees', '$0.00')),
        TotalInvoice="$" + str(invoice['total_invoice']),
        PredupePageCount=pre_count,
        PostDupePageCount=post_count,
        QMESavings="",
        NetSavingsToClient="",
    )
    final_data.append(report_row)

with open(f"shirlei_report_all.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "date_received", "Insurer", "RequestType", "Claimant", "ClaimNumber", "ExaminerEmail", "FlatRate", "PageCost", "Shipping", "SalesTax", "Handling", "ROIFees", "TotalInvoice", "PredupePageCount", "PostDupePageCount", "QMESavings", "NetSavingsToClient"])
    writer.writeheader()
    for row in final_data:
        writer.writerow(row.model_dump())
    f.flush()
