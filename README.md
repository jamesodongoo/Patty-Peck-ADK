## Patty Peck Honda – ADK Multi-Agent Project

This project contains a **Google ADK** multi-agent setup for **Patty Peck Honda**.

The main production agent lives in the `multi_tool_agent` package and is designed to run under the ADK CLI (`adk run` / `adk web`).

---

## Project Structure

```text
ADK/
├─ README.md                 # This file
├─ multi_tool_agent/
│  ├─ __init__.py            # Exports root_agent and sub-agents
│  └─ agent.py               # All agent + tool definitions for Patty Peck Honda
└─ myenv/                    # Local Python virtual environment with ADK installed
```

### The main agent package: `multi_tool_agent`

- `agent.py`
  - Defines tools (`show_directions`, `product_search`, `send_sms`, `notify_team`, `create_ticket`, `create_appointment`, etc.).
  - Defines four ADK agents:
    - `patty_peck_assistant` – root **orchestrator**, routes only (no direct answers).
    - `faq_agent` – business FAQ, hours, directions, warranty info, general questions.
    - `product_agent` – vehicle/product search via n8n.
    - `appointment_support_agent` – appointments and support / ticketing.
- `__init__.py`
  - Re-exports:
    - `root_agent` (alias of `patty_peck_assistant`)
    - All three sub-agents for optional direct use.

## Requirements

- **Python**: 3.13 (as configured in `myenv`)
- **Google ADK**: installed into the `myenv` virtual environment
- **httpx**: already installed in `myenv` (used for webhooks / HTTP calls)

Assuming `myenv` is already created (it is in this project), you do **not** need to install packages globally.

---

## Running the Agent

Open a terminal in the project root (`ADK` folder) and activate the virtual environment:

```bash
cd /path/to/ADK
myenv\Scripts\activate
```

### CLI chat (`adk run`)

```bash
myenv\Scripts\adk.exe run multi_tool_agent
```

This opens an interactive CLI where you can type messages and see which agent responds (FAQ, Product, or Appointment & Support).

### Web UI (`adk web`)

```bash
myenv\Scripts\adk.exe web multi_tool_agent
```

Then open the printed URL (usually `http://127.0.0.1:8000`) in your browser to use the ADK Web UI for testing.

---

## Agents Overview

### Root Orchestrator – `patty_peck_assistant` (exported as `root_agent`)

- Model: `gemini-2.5-flash`
- **Purpose**: Route each user message to the correct specialist agent.
- **Important**:
  - Never answers user questions directly.
  - Only calls `transfer_to_agent` with one of:
    - `faq_agent`
    - `product_agent`
    - `appointment_support_agent`

Routing rules:

- General Patty Peck Honda questions (hours, location, directions, service, finance, warranty, recalls, trade-in, general support) → **`faq_agent`**
- Product / vehicle / inventory search (“red truck”, “show me SUVs”, “Civic LX”, etc.) → **`product_agent`**
- Appointments (book/reschedule/cancel/search) or “talk to a human” or clear escalation → **`appointment_support_agent`**
- If unsure → **`faq_agent`**

### `faq_agent`

- Handles:
  - Hours, location, directions.
  - Service, finance, recalls, trade-in flow.
  - Warranty questions using **hard-coded Patty Peck warranty knowledge**.
  - General dealership questions.
- Persona:
  - “Madison” – multilingual, friendly but not over-the-top.
  - 1 emoji per response, plain-text only (no markdown formatting).
- Tools:
  - `show_directions` – returns address, Google Maps link, phone.
  - `send_sms` – placeholder for future SMS integration.
  - `notify_team` – placeholder for future internal alerting.

### `product_agent`

- Handles:
  - Natural language vehicle search and recommendations.
  - “Show me red trucks”, “Civic under $25k”, etc.
- Tool:
  - `product_search(search_query, limit)`:
    - Calls an **n8n webhook**:
      
    - Expects JSON with a `products` list containing:
      - `product_name`, `product_price`, `product_description`, `product_URL`, `product_image_URL`
    - Returns:
      - `result`: text summary
      - `products`: normalized array for carousel-style rendering
- The agent instructions tell it how to:
  - Present up to 4–8 results at a time.
  - Use names/prices/descriptions/links/images to answer clearly.

### `appointment_support_agent`

- Handles:
  - Booking, canceling, rescheduling, and searching appointments.
  - Creating support tickets and escalation.
- Tools:
  - `create_appointment(...)` – placeholder; currently points at a generic `https://XXXX/api/calendar/appointments` endpoint to be replaced with a real calendar service.
  - `create_ticket(...)` – placeholder ticket creation; to be wired to your real ticketing system.
  - `notify_team(...)` – placeholder for alerts.

---

## Webhook / Integration Points

The agent is designed to be extended via **webhooks** (n8n or any backend):

- **Product search** (already wired):
  - `product_search` → n8n webhook at  

- **To implement later (recommended)**:
  - `send_sms` → n8n workflow that calls your SMS provider.
  - `notify_team` → n8n workflow that sends email / Slack / SMS alerts to the Patty Peck team.
  - `create_ticket` → n8n or backend ticket system (e.g., Helpdesk/CRM).
  - `create_appointment` → calendar / appointment API.

When you are ready to wire these, move the URLs and secrets into a `.env` file and load them using `os.getenv` in `agent.py`.

---

## Development Notes

- This project assumes you are running under Windows with `myenv` as a local virtual environment.
- To modify behavior:
  - Update agent instructions in `multi_tool_agent/agent.py`.
  - Adjust tool implementations in the same file.

If you add new agents or tools, remember to:

- Export them from `multi_tool_agent/__init__.py` if you want external access.
- Keep the root orchestrator strictly routing-only so that specialists own all user-facing replies.
