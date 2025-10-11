from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from typing import Dict, Optional
import logging
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConversationMemoryService:
    """
    Manages conversation memory using LangChain + PostgreSQL
    - Stores all conversations in PostgreSQL (persistent)
    - Keeps only last 3 exchanges in context (prevents overload)
    - Automatic table creation and management
    - Caches message history instances to avoid repeated table checks
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize memory service
        
        Args:
            connection_string: PostgreSQL connection string
                              Example: postgresql://user:pass@localhost:5432/db
        """
        self.connection_string = connection_string
        self._message_history_cache: Dict[str, PostgresChatMessageHistory] = {}
        self._table_initialized = False
        logger.info("ConversationMemoryService initialized")
    
    def _get_message_history(self, session_id: str) -> PostgresChatMessageHistory:
        """
        Get or create cached message history instance
        
        Args:
            session_id: Session identifier
        
        Returns:
            Cached PostgresChatMessageHistory instance
        """
        # Return cached instance if exists
        if session_id in self._message_history_cache:
            return self._message_history_cache[session_id]
        
        # Create new instance (table check happens only once per session)
        message_history = PostgresChatMessageHistory(
            session_id=session_id,
            connection_string=self.connection_string,
            table_name="chat_message_history"
        )
        
        # Cache it
        self._message_history_cache[session_id] = message_history
        logger.debug(f"Cached message history for session {session_id}")
        
        return message_history
    
    def get_memory(self, session_id: str, window_size: int = 3) -> ConversationBufferWindowMemory:
        """
        Get or create memory for a session
        
        Args:
            session_id: Unique identifier for user session
            window_size: Number of recent exchanges to keep in context (default: 3)
        
        Returns:
            Memory object that automatically manages conversation history
        """
        # Use cached message history
        message_history = self._get_message_history(session_id)
        
        # Window memory - keeps only last K exchanges
        return ConversationBufferWindowMemory(
            k=window_size,
            chat_memory=message_history,
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="sql"
        )
    
    def format_context_for_prompt(self, memory: ConversationBufferWindowMemory) -> str:
        """
        Format conversation history for inclusion in prompt
        
        Args:
            memory: Memory object
        
        Returns:
            Formatted string with recent conversation history
            
        Example output:
            ### Recent Conversation History:
            
            Previous Q: Show me sales in 2024
            Previous SQL: SELECT * FROM sales WHERE year = 2024
            
            Previous Q: What about 2023?
            Previous SQL: SELECT * FROM sales WHERE year = 2023
        """
        history = memory.load_memory_variables({})
        messages = history.get("chat_history", [])
        
        if not messages:
            return ""
        
        formatted = ["### Recent Conversation History:"]
        
        # Process messages in pairs (question + SQL)
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                question = messages[i].content
                sql = messages[i + 1].content
                formatted.append(f"\nPrevious Q: {question}")
                formatted.append(f"Previous SQL: {sql}")
        
        return "\n".join(formatted)
    
    def save_exchange(
        self, 
        memory: ConversationBufferWindowMemory,
        question: str,
        sql: str
    ):
        """
        Save a Q&A exchange to memory
        
        This automatically:
        - Saves to PostgreSQL
        - Manages window size
        - Updates context
        
        Args:
            memory: Memory object
            question: User's natural language question
            sql: Generated SQL query
        """
        memory.save_context(
            {"question": question},
            {"sql": sql}
        )
        logger.info(f"Saved exchange to session {memory.chat_memory.session_id}")
    
    def clear_session(self, session_id: str):
        """
        Clear all conversation history for a session
        
        Args:
            session_id: Session to clear
        """
        message_history = self._get_message_history(session_id)
        message_history.clear()
        
        # Remove from cache since it's cleared
        if session_id in self._message_history_cache:
            del self._message_history_cache[session_id]
        
        logger.info(f"Cleared session {session_id}")
    
    def get_session_message_count(self, session_id: str) -> int:
        """
        Get total number of messages in a session
        
        Args:
            session_id: Session to check
        
        Returns:
            Number of messages (questions + answers)
        """
        message_history = self._get_message_history(session_id)
        return len(message_history.messages)
    
    def clear_cache(self):
        """
        Clear the message history cache
        Useful for memory management if you have many sessions
        """
        self._message_history_cache.clear()
        logger.info("Message history cache cleared")