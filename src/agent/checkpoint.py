from datetime import datetime
import os
from typing import Any, cast
import uuid
import logging
from pymongo import MongoClient
from langgraph.store.memory import InMemoryStore

logger = logging.getLogger(__name__)

db_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(db_uri)
mongo_db = mongo_client.checkpointing_db

store = InMemoryStore()


def chat_stream_message(thread_id: str, message: str, finish_reason: str):
    try:
        store_ns = ("messages", thread_id)
        cursor = store.get(store_ns, "cursor")
        index = 0
        if cursor is None:
            store.put(store_ns, "cursor", { "index": 0 })
        else:
            index = int(cursor.value.get("index",0)) + 1
            store.put(store_ns, "cursor", { "index": index })
        store.put(store_ns, f"chunk_{index}",message)
        if finish_reason == "stop" or finish_reason == "interrupt":
            update_replay(thread_id,index + 1)
            memories = store.search(store_ns,limit=index+1)
            messages = [item.dict().get("value", "") for item in memories]
            # Convert messages to byte data
            messages_bytes = []
            for msg in messages:
                if isinstance(msg, str):
                    messages_bytes.append(msg.encode('utf-8'))
                else:
                    messages_bytes.append(str(msg).encode('utf-8'))
            
            collection = mongo_db.chat_streams
            # Try to find existing document
            existing = collection.find_one({"thread_id": thread_id})
            if existing:
                # Update existing document - append message to messages array
                result = collection.update_one(
                    {"thread_id": thread_id},
                    {"$set": {"messages": messages,"ts": datetime.now()}},
                )
                logger.info(
                    f"Updated thread {thread_id}: {result.modified_count} documents modified"
                )
            else:
                # Insert new document
                result = collection.insert_one(
                    {
                        "thread_id": thread_id,
                        "messages": messages,
                        "ts": datetime.now(),
                        "id": uuid.uuid4().hex,
                    }
                )
                logger.info("chat stream created: %s", result.inserted_id)
            
    except Exception as e:
        logger.error("Error writing chat stream message: %s", e)

def update_replay(thread_id: str, messages: int):
    try:
        collection = mongo_db.replays
        # Try to find existing document
        existing = collection.find_one({"thread_id": thread_id})
        if existing:
            # Update existing document - increment messages count
            result = collection.update_one(
                {"thread_id": thread_id},
                {"$set": {"messages": messages,"ts": datetime.now()}},
            )
            logger.info(f"Updated replay {thread_id}: {result.modified_count} documents modified")
        else:
            logger.warning(f"No replay found for thread_id: {thread_id}")
    except Exception as e:
        logger.error("Error updating replay: %s", e)
def write_replay(thread_id:str,research_topic:str,report_style:str):
    try:
        collection = mongo_db.replays
        result = collection.insert_one(
                {
                    "thread_id": thread_id,
                    "research_topic": research_topic,
                    "messages": 0,
                    "report_style": report_style.title(),
                    "ts": datetime.now(),
                    "id": uuid.uuid4().hex,
                }
            )
        logger.info(f"replay created:  {result.inserted_id}")
    except Exception as e:
        logger.error("Error writing replay: %s", e)

def search_replays(limit: int,sort: str = "ts"):
    collection = mongo_db.replays
    cursor = collection.find().sort(sort, -1).limit(limit)
    replays = list(cursor) if cursor is not None else []
    return replays


def sanitize_args(args: Any) -> str:
    """
    Sanitize tool call arguments to prevent special character issues.

    Args:
        args: Tool call arguments string

    Returns:
        str: Sanitized arguments string
    """
    if not isinstance(args, str):
        return ""
    else:
        return (
            args.replace("[", "&#91;")
            .replace("]", "&#93;")
            .replace("{", "&#123;")
            .replace("}", "&#125;")
        )
        
def get_replay_by_id(thread_id: str):
    """Retrieve a replay document by thread_id."""
    collection = mongo_db.chat_streams
    stream_message = collection.find_one({"thread_id": thread_id})
    if stream_message is None:
        logger.warning(f"No replay found for thread_id: {thread_id}")
        return ""

    messages = cast(list,stream_message.get("messages", []))
    # remove the first message which is usually the system prompt
    if messages and isinstance(messages, list) and len(messages) > 0:
        # Decode byte messages back to strings
        decoded_messages = []
        for message in messages:
            if isinstance(message, bytes):
                decoded_messages.append(message.decode('utf-8'))
            else:
                decoded_messages.append(str(message))
        
        # Return all messages except the first one
        valid_messages = []
        for message in decoded_messages:
            if str(message).find("event:") ==-1 and str(message).find("data:") ==-1:
                continue
            if str(message).find("message_chunk") >-1 :
                if str(message).find("content") > -1 or str(message).find("reasoning_content") > -1 or str(message).find("finish_reason") > -1:
                    valid_messages.append(message)
            
            else:
                valid_messages.append(message)
        return "".join(valid_messages) if valid_messages else ""
    elif messages and isinstance(messages, str):
        # If messages is a single string, return it directly
        return messages
    else:
        # If no messages found, return an empty string
        return ""

def write_event(thread_id:str,event:str,level:str,message:dict):
    try:
        collection = mongo_db.events
        result = collection.insert_one(
            {
                "thread_id":thread_id,
                "event":event,
                "level": level,
                "message": message,
                "ts": datetime.now(),
                "id": uuid.uuid4().hex,
            }
        )
        logger.info(f"event created:  {result.inserted_id}")
    except Exception as e:
        logger.error("Error writing event: %s", e)
