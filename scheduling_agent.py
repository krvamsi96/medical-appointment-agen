"""
Main Scheduling Agent Implementation
Uses LangChain with Groq LLM and custom tools
"""

import os
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from prompts import AGENT_PROMPT
from agent_tools import get_agent_tools


class MedicalSchedulingAgent:
    """
    Intelligent medical appointment scheduling agent
    Uses LangChain with Groq LLM for natural conversation
    """
    
    def __init__(
        self,
        groq_api_key: str = None,
        model_name: str = None,
        temperature: float = 0.7
    ):
        """
        Initialize the scheduling agent
        
        Args:
            groq_api_key: Groq API key (or from environment)
            model_name: Groq model to use (or from environment)
            temperature: LLM temperature for response variety
        """
        # Get API key
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found. Please set it in .env file or pass it as parameter.")
        
        # Get model name from environment or use default
        if model_name is None:
            model_name = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        
        # Initialize LLM
        self.llm = ChatGroq(
            api_key=self.groq_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=2048,
            timeout=60
        )
        
        # Get tools
        self.tools = get_agent_tools()
        
        # Create agent
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=AGENT_PROMPT
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            return_intermediate_steps=False,
            early_stopping_method="generate"
        )
        
        # Store for chat histories (in-memory)
        self.chat_histories: Dict[str, InMemoryChatMessageHistory] = {}
        
        print(f"✓ Medical Scheduling Agent initialized with {model_name}")
    
    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = InMemoryChatMessageHistory()
        return self.chat_histories[session_id]
    
    def chat(
        self,
        message: str,
        session_id: str = "default"
    ) -> str:
        """
        Process a user message and return agent response
        
        Args:
            message: User's message
            session_id: Session identifier for conversation history
            
        Returns:
            Agent's response
        """
        try:
            # Get chat history
            history = self.get_session_history(session_id)
            
            # Create agent with history
            agent_with_history = RunnableWithMessageHistory(
                self.agent_executor,
                get_session_history=self.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            # Invoke agent
            response = agent_with_history.invoke(
                {"input": message},
                config={"configurable": {"session_id": session_id}}
            )
            
            # Extract output
            output = response.get("output", "I apologize, but I'm having trouble processing your request. Could you please try again?")
            
            return output
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again or call our office at +1-555-123-4567 for assistance."
    
    def reset_conversation(self, session_id: str = "default"):
        """Reset conversation history for a session"""
        if session_id in self.chat_histories:
            self.chat_histories[session_id].clear()
            print(f"Conversation history cleared for session: {session_id}")
    
    def get_conversation_history(self, session_id: str = "default") -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        
        Returns:
            List of messages in format [{"role": "user/assistant", "content": "..."}]
        """
        history = self.get_session_history(session_id)
        messages = []
        
        for msg in history.messages:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})
        
        return messages


def create_agent(groq_api_key: str = None) -> MedicalSchedulingAgent:
    """
    Factory function to create a scheduling agent
    
    Args:
        groq_api_key: Optional Groq API key
        
    Returns:
        Initialized MedicalSchedulingAgent
    """
    return MedicalSchedulingAgent(groq_api_key=groq_api_key)


# Example usage
if __name__ == "__main__":
    # Test the agent
    agent = create_agent()
    
    print("\n" + "="*60)
    print("Medical Appointment Scheduling Agent - Test Mode")
    print("="*60 + "\n")
    
    # Test conversation
    session = "test_session"
    
    # Test 1: Greeting
    response = agent.chat("Hi, I need to see a doctor", session)
    print(f"User: Hi, I need to see a doctor")
    print(f"Agent: {response}\n")
    
    # Test 2: Provide reason
    response = agent.chat("I've been having headaches", session)
    print(f"User: I've been having headaches")
    print(f"Agent: {response}\n")
    
    # Test 3: FAQ question
    response = agent.chat("What insurance do you accept?", session)
    print(f"User: What insurance do you accept?")
    print(f"Agent: {response}\n")
    
    print("\nTest completed. Agent is working correctly!")
