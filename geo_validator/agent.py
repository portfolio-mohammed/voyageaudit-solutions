import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from callback_logging import log_query_to_model, log_model_response
import google.cloud.logging

load_dotenv()
model_name = os.getenv("MODEL") or "gemini-3.5-flash"
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

class CountryCapital(BaseModel):
    capital: str = Field(description="The capital city of the destination.")

async def main():
    app_name = "geo_validator_app"
    user_id_1 = "user1"
    root_agent = Agent(
        model=model_name,
        name="geo_validator",
        instruction="Provide the capital city for the given country as a JSON object.",
        output_schema=CountryCapital,
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        before_model_callback=log_query_to_model,
        after_model_callback=log_model_response,
    )
    runner = InMemoryRunner(agent=root_agent, app_name=app_name)
    my_session = await runner.session_service.create_session(app_name=app_name, user_id=user_id_1)
    async def run_prompt(session: Session, new_message: str):
        content = types.Content(role="user", parts=[types.Part.from_text(text=new_message)])
        print("** User says:", content.model_dump(exclude_none=True))
        async for event in runner.run_async(user_id=user_id_1, session_id=session.id, new_message=content):
            if event and getattr(event, "content", None) and event.content.parts and event.content.parts[0].text:
                print(f"** {event.author}: {event.content.parts[0].text}")
            else:
                author_name = getattr(event, "author", "unknown")
                print(f"** Event received (author: {author_name})")
        cloud_logging_client.close()
    query = "What is the capital of France?"
    await run_prompt(my_session, query)

if __name__ == "__main__":
    asyncio.run(main())
