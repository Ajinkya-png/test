# Agents Overview

This project contains multiple autonomous agents, each responsible for a slice of the voice-based food delivery flow:

- **customer_order_agent** — conversational ordering assistant.
- **restaurant_agent** — coordinates with restaurants (prep time, availability).
- **driver_agent** — assigns drivers and sends pickup/delivery details.
- **tracking_agent** — real-time updates & ETA.
- **support_agent** — handles complaints, refunds, escalations.
- **post_delivery_agent** — follow-ups, feedback, promotions.

Each agent extends `app.agents.base_agent.BaseAgent` and uses tools via `app.tools.registry.ToolRegistry`.
