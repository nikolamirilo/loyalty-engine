import os

# The regression scripts break email delivery and the database on purpose.
# Keep that out of Sentry even when api/.env has a DSN: load_dotenv() does not
# overwrite a variable that already exists, even an empty one.
os.environ["SENTRY_DSN"] = ""
