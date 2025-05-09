# multiagents/agents/__init__.py

from .email_agent import detect as email
from .pesel_agent import detect as pesel
from .credit_card_agent import detect as credit_card
from .ml_agent import detect as ml

__all__ = ["email", "pesel", "credit_card", "ml"]
