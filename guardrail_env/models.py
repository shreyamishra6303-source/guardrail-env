from pydantic import BaseModel, Field

class Observation(BaseModel):
    difficulty: str = Field(description="Level: Easy, Medium, or Hard")
    user_query: str = Field(description="The prompt from the user")
    secret_to_protect: str = Field(description="The sensitive data to hide")
    document_content: str = Field(description="The full text containing the secret")

class Action(BaseModel):
    safe_response: str = Field(description="The text with the secret [REDACTED]")
    explanation: str = Field(description="Why the data was hidden")
    is_threat_detected: bool = Field(description="True if the user was trying to trick the AI")

class State(BaseModel):
    score: float = 0.0
    finished: bool = False