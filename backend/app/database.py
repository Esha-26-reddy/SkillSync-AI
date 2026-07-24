from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import settings


# MongoDB connection
client = MongoClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=5000,
)

# Select database
db = client[settings.MONGO_DB_NAME]


# Collections
users_col = db["users"]
employees_col = db["employees"]
projects_col = db["projects"]
contributions_col = db["contributions"]
learning_resources_col = db["learning_resources"]


# Indexes
users_col.create_index("username", unique=True)
employees_col.create_index("email", unique=True)
contributions_col.create_index("employee_id")
learning_resources_col.create_index("skill")


# Default resources for Bridge Learning Plans
DEFAULT_LEARNING_RESOURCES = [
    {
        "skill": "python",
        "title": "Python for Everybody (Coursera)",
        "url": "https://www.coursera.org/specializations/python",
    },
    {
        "skill": "javascript",
        "title": "The Modern JavaScript Tutorial",
        "url": "https://javascript.info/",
    },
    {
        "skill": "typescript",
        "title": "TypeScript Handbook",
        "url": "https://www.typescriptlang.org/docs/handbook/intro.html",
    },
    {
        "skill": "react",
        "title": "React Official Docs — Learn React",
        "url": "https://react.dev/learn",
    },
    {
        "skill": "fastapi",
        "title": "FastAPI Official Tutorial",
        "url": "https://fastapi.tiangolo.com/tutorial/",
    },
    {
        "skill": "sql",
        "title": "SQL Tutorial (Mode Analytics)",
        "url": "https://mode.com/sql-tutorial/",
    },
    {
        "skill": "mongodb",
        "title": "MongoDB University — M001",
        "url": "https://learn.mongodb.com/",
    },
    {
        "skill": "docker",
        "title": "Docker Getting Started Guide",
        "url": "https://docs.docker.com/get-started/",
    },
    {
        "skill": "kubernetes",
        "title": "Kubernetes Basics",
        "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
    },
    {
        "skill": "aws",
        "title": "AWS Cloud Practitioner Essentials",
        "url": "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/",
    },
    {
        "skill": "ci/cd",
        "title": "GitHub Actions Documentation",
        "url": "https://docs.github.com/actions",
    },
    {
        "skill": "machine learning",
        "title": "Machine Learning Crash Course (Google)",
        "url": "https://developers.google.com/machine-learning/crash-course",
    },
    {
        "skill": "devops",
        "title": "DevOps Roadmap",
        "url": "https://roadmap.sh/devops",
    },
    {
        "skill": "security",
        "title": "OWASP Top 10",
        "url": "https://owasp.org/www-project-top-ten/",
    },
    {
        "skill": "testing",
        "title": "pytest Documentation",
        "url": "https://docs.pytest.org/",
    },
    {
        "skill": "api design",
        "title": "REST API Design Best Practices",
        "url": "https://restfulapi.net/",
    },
    {
        "skill": "node.js",
        "title": "Node.js Official Guides",
        "url": "https://nodejs.org/en/learn",
    },
    {
        "skill": "html/css",
        "title": "MDN — Learn HTML and CSS",
        "url": "https://developer.mozilla.org/en-US/docs/Learn",
    },
    {
        "skill": "data engineering",
        "title": "Data Engineering Zoomcamp",
        "url": "https://github.com/DataTalksClub/data-engineering-zoomcamp",
    },
    {
        "skill": "cloud architecture",
        "title": "Microsoft Learn — Cloud Architecture",
        "url": "https://learn.microsoft.com/en-us/training/paths/azure-architect-fundamentals/",
    },
]


def seed_learning_resources_if_empty():
    """
    Insert default learning resources only if they do not already exist.
    """

    for resource in DEFAULT_LEARNING_RESOURCES:
        learning_resources_col.update_one(
            {
                "skill": resource["skill"],
                "title": resource["title"],
            },
            {
                "$set": resource,
            },
            upsert=True,
        )


def test_database_connection():
    """
    Test the MongoDB connection.
    """

    try:
        client.admin.command("ping")
        print("Successfully connected to MongoDB")

    except PyMongoError as error:
        print(f"MongoDB connection failed: {error}")
        raise