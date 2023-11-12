from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

with open("<FILENAME 1 HERE>", "rb") as file:
    file1 = client.files.create(file=file, purpose='assistants')

with open("<FILENAME 2 HERE>", "rb") as file:
    file2 = client.files.create(file=file, purpose='assistants')

assistant = client.beta.assistants.create(
  instructions="<SYSTEM PROMPT HERE>",
  model="gpt-4-1106-preview",
  tools=[{"type": "retrieval"}],
  file_ids=[file1.id, file2.id]
)

thread = client.beta.threads.create()


message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="<USER PROMPT HERE>"
)

run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
)

run_status = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)

print("Run Status:", run_status.status)

# Variable to keep track of the last processed message ID
last_processed_id = None

while True:
    run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        for message in messages.data:
            if message.role == 'assistant' and message.id != last_processed_id:
                response_text = message.content[0].text.value
                annotations = message.content[0].text.annotations
                citations = []

                # Process annotations
                for index, annotation in enumerate(annotations):
                    if 'file_citation' in annotation:
                        file_citation = annotation['file_citation']
                        cited_text = f"[Citation from file: {file_citation['quote']}]"
                        response_text = response_text.replace(annotation['text'], cited_text)
                        citations.append(cited_text)

                        # Update the last processed message ID
                        last_processed_id = message.id

                    elif 'file_path' in annotation:
                        file_path = annotation['file_path']
                        response_text = response_text.replace(annotation['text'], f"[File path: {file_path['file_id']}]")

                # Print the response with citations
                print("Assistant says:", response_text)
                if citations:
                    print("Citations:", '\n'.join(citations))

        # Break after processing all new messages
        break

    print("Waiting for completion...")
    time.sleep(2)  # Wait for 2 seconds before checking again
