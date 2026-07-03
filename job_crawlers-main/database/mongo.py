import os
import certifi
import pymongo
from urllib.parse import urlparse

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = pymongo.MongoClient(mongo_uri, tlsCAFile=certifi.where())

# Connect to the database and collection
db = client["crawler"]  # Replace with your database name
collection = db["companies"]  # Replace with your collection name

def ensure_company_document(company_name):
    """Ensure a document for the given company exists. Create it if it doesn't exist."""
    if collection.count_documents({"company": company_name}) == 0:
        collection.insert_one({"company": company_name, "jobs": []})
        print(f"Created a new document for {company_name}.")
        return 0
    else:
        print(f"Document for {company_name} already exists.")
        return 1

def _normalize_number(number):
    """Strip query params and fragments from URL-style job numbers."""
    try:
        p = urlparse(number)
        if p.scheme in ("http", "https"):
            return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")
    except Exception:
        pass
    return number

def add_jobs_if_not_exists(jobs_list):
    new_jobs = []
    for job in jobs_list:
        company_name = job['company']
        job_number = _normalize_number(job['number'])
        new_job = {
            "title": job['title'],
            "number": job_number,
            "link": job['link'],
            "company": company_name,
        }
        # Atomic: only pushes if no existing job has this number
        result = collection.update_one(
            {"company": company_name, "jobs.number": {"$ne": job_number}},
            {"$push": {"jobs": new_job}}
        )
        if result.modified_count == 1:
            new_jobs.append(new_job)
            print(f"Added new job {job_number} to {company_name}.")
        else:
            print(f"Job {job_number} already exists in {company_name}.")

    return new_jobs

# Example job details input
# jobs_list = [
#     {'company': 'microsoft', 'title': 'Principal Technical Program Manager, Industrial Controls Transformation', 'number': '1792', 'link': 'https://jobs.careers.microsoft.com/global/en/job/1718892/Principal-Technical-Program-Manager%2C-Industrial-Controls-Transformation'},
#     {'company': 'microsoft', 'title': 'Principal UX Engineering Manager', 'number': '26', 'link': 'https://jobs.careers.microsoft.com/global/en/job/1719326/Principal-UX-Engineering-Manager'},
#     {'company': 'microsoft', 'title': 'Principal Technical Program Manager', 'number': '5', 'link': 'https://jobs.careers.microsoft.com/global/en/job/1711145/Principal-Technical-Program-Manager'},
#     {'company': 'microsoft', 'title': 'Senior Director Software Program Manager', 'number': '121', 'link': 'https://jobs.careers.microsoft.com/global/en/job/1719791/Senior-Director-Software-Program-Manager'},
#     {'company': 'microsoft', 'title': 'Principal Product Manager - Privacy', 'number': '00', 'link': 'https://jobs.careers.microsoft.com/global/en/job/1719983/Principal-Product-Manager---Privacy'}
# ]

# Adding jobs to the database and getting the list of new jobs
# new_jobs = add_jobs_if_not_exists(jobs_list)
# print("New jobs added:", new_jobs)
