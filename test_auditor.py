import asyncio
import os
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types
import google.cloud.logging

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "qwiklabs-gcp-01-13ec630af0bf"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
if not os.getenv("MODEL"):
    os.environ["MODEL"] = "gemini-2.5-pro"

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

from llm_auditor.agent import llm_auditor

async def main():
    app_name = "llm_auditor_app"
    user_id = "user1"

    runner = InMemoryRunner(
        agent=llm_auditor,
        app_name=app_name,
    )

    session = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id
    )

    query = "Audit this travel claim: The Eiffel Tower is located in Berlin, Germany, and was built in 1950."
    content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
    print("** User query:", query)

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        if event and getattr(event, "content", None) and event.content.parts and event.content.parts[0].text:
            print(f"\n** [{event.author}]:\n{event.content.parts[0].text}")

    cloud_logging_client.close()

if __name__ == "__main__":
    asyncio.run(main())
