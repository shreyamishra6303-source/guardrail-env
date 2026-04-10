from pydantic import BaseModel, ConfigDict, Field


class GuardrailObservation(BaseModel):
    difficulty: str = Field(description="Level: Easy, Medium, or Hard")
    user_query: str = Field(description="The prompt from the user")
    secret_to_protect: str = Field(description="The sensitive data to hide")
    document_content: str = Field(description="The full text containing the secret")
    echoed_message: str = Field(default="", description="The message echoed back by the environment")
    message_length: int = Field(default=0, description="The length of the echoed message")
    done: bool = Field(default=False, description="Whether the episode is finished")
    reward: float = Field(default=0.0, description="The reward for the action")


class GuardrailAction(BaseModel):
    message: str = Field(description="The original message containing a secret")
    redacted_text: str = Field(default="", description="The redacted version of the text with secret replaced")
    safe_response: str = Field(default="", description="The safe response with the secret [REDACTED]")
    explanation: str = Field(default="", description="Why the data was hidden")
    is_threat_detected: bool = Field(default=False, description="True if the user was trying to trick the AI")


class State(BaseModel):
    model_config = ConfigDict(frozen=False)
    episode_id: str = Field(default="", description="Unique episode identifier")
    step_count: int = Field(default=0, description="Current step count")
    current_level: int = Field(default=1, description="Current challenge level")
    active_secret: str = Field(default="", description="The secret for the current level")
    score: float = 0.0
    finished: bool = False
