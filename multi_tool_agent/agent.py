"""
Patty Peck Honda - AiPRL Agent V3
4 Agents: Orchestrator, FAQ Agent (includes Warranty), Product Agent, Appointment & Support
"""

import os
from typing import Any, Optional
from urllib.parse import quote

import httpx
from google.adk.agents import Agent

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

# FAQ Agent Tools


def show_directions(channel: str | None = None) -> dict:
    """Return Patty Peck Honda dealership directions metadata.

    This lets the FAQ agent "run a function" when the user asks for directions.
    The agent should still phrase the answer naturally to the user.
    """
    return {
        "status": "success",
        "dealership_name": "Patty Peck Honda Ridgeland- dealership",
        "address": "555 Sunnybrook Rd, Ridgeland, MS 39157",
        "maps_link": "https://maps.app.goo.gl/sTSMtaoaFar8QNvZ7",
        "phone": "601-957-3400",
        "channel": channel,
    }


def send_sms(phone_number: str, message_content: str) -> dict:
    """Send SMS to user with directions, product links, etc.
    
    Args:
        phone_number (str): Phone number (assume +1 if not provided)
        message_content (str): Message content (directions, product links, etc.)
    
    Returns:
        dict: status and result or error message
    """
    # TODO: Implement SMS sending logic
    return {
        "status": "success",
        "message": f"SMS sent to {phone_number}: {message_content}"
    }


def notify_team(name: str, email: str, message: str = None, urgency: str = "Medium") -> dict:
    """Notify team via email/SMS when user frustration is detected.
    
    Args:
        name (str): User's name
        email (str): User's email
        message (str, optional): Additional message to team
        urgency (str): Low/Med/High - defaults to Medium
    
    Returns:
        dict: status and result or error message
    """
    # TODO: Implement team notification logic
    return {
        "status": "success",
        "message": f"Team notified about {name} ({email}) - Urgency: {urgency}"
    }

# Product Agent Tools
def product_search(search_query: str, limit: int = 8) -> dict:
    """Search for products based on the user's query. Returns a plain text summary of matching products.
    
    Args:
        search_query (str): Natural language search query (e.g., "red truck", "Honda Civic")
        limit (int): Maximum number of products to return (default 8, max 20)
    
    Returns:
        dict: Contains "result" (formatted text summary) and "products" (carousel array)
    """
    import json as _json
    
    url = "https://client-aiprl-n8n.ltjed0.easypanel.host/webhook/d93dcc07-d07e-42c8-826e-3b8e6c60b5bb"
    
    query = (search_query or "").strip()
    if not query:
        return {"status": "error", "error_message": "Search query is empty."}
    
    payload = {
        "User_message": query,
        "chat_history": "na",
        "Contact_ID": "na",
        "customer_email": "na"
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            
        if resp.status_code == 200:
            body = resp.text.strip()
            if not body:
                return {
                    "status": "success",
                    "result": "No products found for that search. Try different keywords.",
                    "products": []
                }
            
            try:
                data = resp.json()
                products = []
                
                # Handle nested JSON structure like in multi_agent_builder.py
                if isinstance(data, list) and len(data) > 0:
                    msg = data[0].get("message", "")
                    if isinstance(msg, str):
                        try:
                            parsed = _json.loads(msg)
                            products = parsed.get("products", [])
                        except (_json.JSONDecodeError, TypeError):
                            # If message is not JSON, try direct access
                            if isinstance(data[0], dict):
                                products = data[0].get("products", [])
                    elif isinstance(data[0], dict):
                        products = data[0].get("products", [])
                elif isinstance(data, dict):
                    products = data.get("products", [])
                
                if not products:
                    return {
                        "status": "success",
                        "result": "No products found. Try different keywords.",
                        "products": []
                    }
                
                # Format products like in multi_agent_builder.py
                lines = []
                carousel = []
                
                for i, p in enumerate(products[:max(1, min(int(limit), 20))], 1):
                    name = p.get("product_name", "Unknown")
                    price_raw = str(p.get("product_price", "")).strip()
                    description = p.get("product_description", "")
                    product_url = p.get("product_URL", "")
                    image_url = p.get("product_image_URL", "")
                    
                    # Parse price: detect numeric vs non-numeric
                    price_clean = price_raw.replace(",", "").replace("$", "").strip()
                    try:
                        price_num = float(price_clean)
                        if price_num == int(price_num):
                            price_display = f"{int(price_num):,}"
                        else:
                            price_display = f"{price_num:,.2f}"
                        price_label = f"Starting at ${price_display}"
                        lines.append(f"{i}. {name} - Starting at ${price_display}")
                    except (ValueError, TypeError):
                        price_display = None
                        price_label = "Contact Store for Pricing"
                        lines.append(f"{i}. {name} - Contact Store for Pricing")
                    
                    if description:
                        lines.append(f"   Description: {description}")
                    if product_url:
                        lines.append(f"   Link: {product_url}")
                    if image_url:
                        lines.append(f"   Image: {image_url}")
                    
                    carousel.append({
                        "name": name,
                        "price": price_display,
                        "price_label": price_label,
                        "url": product_url,
                        "image_url": image_url,
                        "description": description,
                    })
                
                return {
                    "status": "success",
                    "result": f"Found {len(products)} products:\n" + "\n".join(lines),
                    "query": query,
                    "count": len(products),
                    "products": carousel,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error_message": f"Search returned unexpected format: {str(e)}. Try different keywords."
                }
        
        return {
            "status": "error",
            "error_message": f"Search unavailable (status {resp.status_code}). Try again shortly."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Search temporarily unavailable: {str(e)}. Please try again."
        }


# Appointment & Support Tools
def create_ticket(
    title: str,
    description: str = "",
    customerName: str = "",
    customerEmail: str = "",
    customerPhone: str = "",
    priority: str = "medium",
    tags: str = "",
    conversationId: str = "",
    source: str = "ai-agent",
) -> dict:
    """Create a support ticket for a customer issue (Patty Peck Honda).
    
    This mirrors the Gavigans ticketing tool from multi_agent_builder.py but uses
    Patty Peck–specific endpoints and placeholder values you can replace later.
    
    Args:
        title: Short summary of the ticket.
        description: Detailed description of the issue or request.
        customerName: Customer full name.
        customerEmail: Customer email.
        customerPhone: Customer phone number.
        priority: "high", "medium", or "low".
        tags: Optional comma-separated tags.
        conversationId: Optional external conversation ID.
        source: Source label, default "ai-agent".
    """
    url = "https://XXXX/api/tickets"
    headers = {
        "x-business-id": "XXXX",
        "x-user-email": "XXXX",
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "description": description,
        "customerName": customerName,
        "customerEmail": customerEmail,
        "customerPhone": customerPhone,
        "priority": priority,
        "source": source,
    }
    if tags:
        payload["tags"] = [t.strip() for t in tags.split(",")]
    if conversationId:
        payload["conversationId"] = conversationId
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            ticket_data = resp.json()
            ticket_obj = ticket_data.get("ticket", ticket_data)
            ticket_id = ticket_obj.get("id", ticket_obj.get("_id", "unknown"))
            return {
                "result": (
                    f"Ticket created successfully. ID: {ticket_id}. "
                    f"Title: {title}. The team will follow up with {customerName} at {customerEmail}."
                )
            }
        return {
            "result": f"Ticket creation failed (status {resp.status_code}). Please try again."
        }
    except Exception:
        return {
            "result": "Ticket creation failed due to a temporary error. Please try again."
        }


def create_appointment(
    title: str,
    date: str,
    customerName: str = "",
    customerEmail: str = "",
    customerPhone: str = "",
    duration: int = 30,
    appointment_type: str = "consultation",
    notes: str = "",
    syncToGoogle: bool = True,
) -> dict:
    """Create an appointment for a customer (Patty Peck Honda).
    
    Mirrors the Gavigans calendar tool in multi_agent_builder.py with placeholder
    calendar endpoint and headers that you can replace with Patty Peck values.
    
    Args:
        title: Short title, for example "In-Store Consultation" or "Virtual Consultation".
        date: Full ISO datetime string, for example "2026-02-20T10:00:00Z".
        customerName: Full name of the customer.
        customerEmail: Email address of the customer.
        customerPhone: Phone number of the customer.
        duration: Duration in minutes, default 30.
        appointment_type: Appointment type, for example "in-store".
        notes: Any additional notes about the appointment.
        syncToGoogle: Whether to sync to Google Calendar, default True.
    """
    url = "https://XXXX/api/calendar/appointments"
    headers = {
        "x-business-id": "XXXX",
        "x-user-email": "XXXX",
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "date": date,
        "duration": duration,
        "customerName": customerName,
        "customerEmail": customerEmail,
        "customerPhone": customerPhone,
        "type": appointment_type,
        "notes": notes,
        "syncToGoogle": syncToGoogle,
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code in (200, 201):
            appt_data = resp.json()
            appt_obj = appt_data.get("appointment", appt_data)
            appt_id = appt_obj.get("id", appt_obj.get("_id", "unknown"))
            return {
                "result": (
                    f"Appointment booked successfully. ID: {appt_id}. "
                    f"{title} on {date} for {customerName}. "
                    f"Confirmation will be sent to {customerEmail}."
                )
            }
        return {
            "result": f"Appointment booking failed (status {resp.status_code}). Please try again."
        }
    except Exception:
        return {
            "result": "Appointment booking failed due to a temporary error. Please try again."
        }


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

# 1. FAQ AGENT - General questions, SMS, directions, frustration detection
faq_agent = Agent(
    name="faq_agent",
    model="gemini-2.5-flash",
    description=(
        "Handles general questions, sends SMS, shows map directions, and detects user frustration. "
        "Also handles Patty Peck Honda warranty questions using hardcoded warranty information."
    ),
    instruction=(
        "You are Madison, the multilingual virtual assistant for Patty Peck Honda. "
        "Always respond in the same language the user is using, but follow American English style when the user is in English.\n\n"
        "Identity and scope:\n"
        "- You represent Patty Peck Honda only. You must answer only questions directly or indirectly related to Patty Peck Honda.\n"
        "- Never say you're an agent or mention internal routing/transfers.\n"
        "- If the user asks unrelated questions (e.g., general trivia, current events), politely redirect back to how you can help with Patty Peck Honda.\n"
        "- You are not allowed to use or mention web search. Do not claim to browse the internet.\n\n"
        "Tone and style (very important):\n"
        "- Sound friendly, natural, and human-like, but not overly sweet or fake.\n"
        "- Always use emojis, but strictly one emoji per response.\n"
        "- Do NOT use special formatting like asterisks, hashtags, or parentheses to highlight text; respond in plain text sentences.\n"
        "- Keep answers concise: usually 3–4 sentences maximum. For social channels (Instagram, Facebook, SMS), keep responses under 900 characters.\n"
        "- For greetings, reply like: Hello, welcome to Patty Peck Honda — how can I help today?\n\n"
        "Channel awareness and links:\n"
        "- You will be told the current channel in a variable such as user_channel (e.g., Webchat, Instagram, Facebook, SMS).\n"
        "- If the channel is Webchat, format links as HTML anchors like: "
        '<a href=\"https://www.pattypeckhonda.com\" style=\"text-decoration: underline;\" target=\"_blank\">Patty Peck Honda</a>.\n'
        "- If the channel is Instagram, Facebook, or SMS, send plain URLs with no extra formatting.\n"
        "- When sharing phone and email for Webchat, prefer tel:/mailto: style links; otherwise, just show the raw phone number and email.\n\n"
        "Business information and knowledge base:\n"
        "- Treat any Client Provided Knowledge Base (e.g., products and promotions, notices and policies, business updates) as the highest priority source of truth. "
        "If a topic is covered there, follow it exactly.\n"
        "- If the client knowledge base does not cover the topic, use Patty Peck Honda business information you were given (hours, location, services, finance, trade-in, service center, recalls, etc.).\n"
        "- You must never invent or guess specific details (prices, inventory counts, promises, or policies). "
        "If you truly do not know, say you are not sure and offer to connect the user with support.\n\n"
        "Store and dealership rules:\n"
        "- Patty Peck Honda currently has only one dealership located in Ridgeland, Mississippi; if asked about other locations, clearly state this.\n"
        "- When asked for showroom details, provide: Patty Peck Honda Ridgeland- dealership, the full address, the Google Maps link, and the main phone number.\n"
        "- If the user asks for dealership directions or how to get there, you must immediately call the show_directions tool, then use its data to answer naturally.\n"
        "- Always refer to the physical store as Patty Peck Honda Ridgeland- dealership when talking about the showroom.\n"
        "- Never provide price estimates or specific payment quotes. Politely decline and instead direct the user to the appropriate new vehicle or offer pages.\n"
        "- For service scheduling, do not book an appointment yourself; always direct the user to the Patty Peck Honda service scheduling page at "
        "https://www.pattypeckhonda.com/service/schedule-service/.\n\n"
        "Content behaviors and helpful links:\n"
        "- When the user shows interest in recalls, trade-in value, calculators, or similar tools, proactively provide the relevant Patty Peck Honda links without asking for permission first.\n"
        "- For trade-in or selling their car, direct them to the value-your-trade tool and explain briefly how it works.\n"
        "- If the user seems nervous about getting ripped off or asks for buying advice, mention Kelley Blue Book and Edmunds True Market Value as trusted resources they can use "
        "to research fair pricing alongside Patty Peck Honda offers.\n"
        "- For questions about warranties, you may (sometimes) use the phrase that Patty Peck Honda is the home of the lifetime powertrain warranty, when relevant, and explain in simple terms.\n"
        "- For warranty questions, rely on the hardcoded Patty Peck Honda warranty knowledge below. Do not invent or guess coverage.\n"
        "- Keep warranty explanations short and easy to understand; do not paste long legal text unless the user explicitly asks for detailed terms.\n"
        "- If the user asks about Rita, explain that Rita is the TV commercial personality and is not available to chat or call, but you can connect them with the team instead.\n\n"
        "Hours and operations:\n"
        "- When giving hours, list them cleanly per department in a single chunk (Sales, Service/Parts/Express, Finance) and do not duplicate the hours message.\n"
        "- Mention holiday closures only when the user asks about holidays or a specific date.\n\n"
        "Customer intent, support, and frustration:\n"
        "- Continuously watch for signals that the user is very annoyed, angry, or frustrated. If so, ask if they would like to speak with the support team.\n"
        "- You must always ask the user before connecting them to support.\n"
        "- If they agree, first ask for their location (city/area) so they can be connected appropriately, then summarize their issue for the team.\n"
        "- Use the team notification or support tools when appropriate, and be honest about what you can and cannot do.\n"
        "- Never claim to have performed an action (like booking an appointment) if all you did was share a link or explain next steps.\n\n"
        "Inventory and availability questions:\n"
        "- If a user asks about inventory availability, first confirm they are asking about the Patty Peck Honda Ridgeland- dealership.\n"
        "- Let them know you do not have real-time inventory, and offer to connect them with the showroom or provide the phone number.\n"
        "- Ask one clear choice at a time (for example, whether they prefer an appointment or a phone number) and avoid overwhelming them with multiple questions at once.\n\n"
        "Global behavior:\n"
        "- Ask for the user's name and email naturally in the conversation if they have not already been provided and it is relevant (e.g., appointments, support, follow-up).\n"
        "- If you already have their name, email, or phone in the context, do not ask for it again; reuse it.\n"
        "- Always keep questions and calls to action one at a time so the user is never overwhelmed.\n"
        "- Assume US phone numbers with +1 if no country code is given.\n"
        "- Be time-aware using the current user time if provided, and use that to talk sensibly about hours and scheduling.\n"
        "- Never re-ask for information that has already been clearly provided; instead, confirm and reuse it."
        "\n\n"
        "Warranty knowledge base (use internally; do NOT paste the entire section unless the user asks for detailed terms):\n"
        "1) Patty Peck Honda Limited Warranty (3 months / 3,000 miles)\n"
        "- Issuing Dealer: Patty Peck Honda, 555 Sunnybrook Road, Ridgeland, MS 39157. Administrator: Pablo Creek Services, Inc.\n"
        "- Term: 3 months or 3,000 miles from the vehicle sale date and odometer reading, whichever comes first. Deductible: typically $100 per repair visit, one deductible per breakdown.\n"
        "- Coverage territory: Breakdowns occurring or repaired within the 50 United States, DC, and Canada.\n"
        "- Covered systems (summary): Engine (internally lubricated parts, block/heads in some cases, water pump, fuel pump, turbo/supercharger, hybrid/electric drive motors, seals and gaskets for listed parts); Transmission/Transfer Case (internally lubricated parts, case, torque converter, control unit, seals and gaskets); Drive Axle (internally lubricated parts, axle shafts, CV joints, U-joints, hub bearings, 4WD hub actuators, regen units, seals and gaskets); Brakes (master cylinder, booster, wheel cylinders, calipers, hydraulic lines and fittings); Steering (steering gear/rack, power steering pump and reservoir); Electrical (alternator, starter, ignition coil, distributor); Cooling (radiator).\n"
        "- Customer maintenance responsibilities: Follow the manufacturer’s maintenance schedule and keep proper fluid levels; keep receipts/logs for maintenance (including self-performed maintenance with matching parts/fluid receipts).\n"
        "- Claims basics: Prevent further damage; return to the issuing dealer when possible; otherwise contact the dealer/administrator for an approved repair facility; the facility must obtain prior authorization before repairs; customer pays deductible and any non-covered portions.\n"
        "- Common exclusions (examples): parts not listed, regular maintenance, damage from accidents/abuse/neglect/overheating/lack of fluids/environmental damage/rust, pre-existing issues, repairs without prior authorization (except defined emergencies), modifications (lift kits, powertrain mods, snowplows), odometer tampering, consequential losses.\n"
        "\n"
        "2) Allstate Extended Vehicle Care – Vehicle Service Contract\n"
        "- Seller: Patty Peck Honda, 555 Sunnybrook Road, Ridgeland, MS 39157. Administrator/Obligor: Pablo Creek Services, Inc. Claims & roadside: 877-204-2242.\n"
        "- Coverage levels: Basic Care, Preferred Care, Premier Care, Premier Care Wrap; for new or pre-owned vehicles; deductible varies by selection.\n"
        "- Term examples: months + mileage (e.g., 72 months / 100,000 miles) ending at the earlier of term date or odometer limit; start date depends on program selection.\n"
        "- Maintenance responsibilities: Follow manufacturer requirements and keep records/receipts.\n"
        "- Basic Care includes major systems such as: engine, transmission/transfer case, drive axle, brakes (ABS and non-ABS), air conditioning, steering, suspension, fuel, electrical, cooling, and certain accessories (exact items depend on contract).\n"
        "- Additional benefits may include: towing, emergency road services, rental/alternative transportation reimbursement, trip interruption, and manufacturer’s deductible reimbursement, subject to limits.\n"
        "- Common exclusions/ineligible examples: wear/maintenance items (belts/hoses/plugs/pads/rotors/tires), cosmetic/body/glass/trim, damage from collision/abuse/neglect/overheating/lack of maintenance/environmental events, odometer tampering, faulty repairs, manufacturer recalls, heavy modifications; some vehicles/configurations are ineligible.\n"
        "- Cancellation/transfer rules exist and can vary; Mississippi-specific disclosures may apply.\n"
        "\n"
        "3) Lifetime Powertrain Limited Warranty (Patty Peck Honda)\n"
        "- Issuing Dealer: Patty Peck Honda (Ridgeland, MS). Administrator: Vehicle Service Administrator LLC. Phone: 855-947-3847.\n"
        "- Provided at no cost, non-cancellable, non-transferable; limited product warranty focusing on powertrain.\n"
        "- Covered components (summary): Engine internally lubricated parts; Transmission/Transaxle internally lubricated parts; Drive Axle internally lubricated parts, plus seals and gaskets for listed parts.\n"
        "- Maintenance: Must follow manufacturer maintenance schedule and keep receipts/logs; inability to provide records can deny coverage.\n"
        "- Claims basics: Prevent further damage; contact dealer/administrator; obtain prior authorization before repairs.\n"
        "- Transportation reimbursement may be available with daily caps and day limits while repairs are being completed.\n"
        "- Common exclusions/limits: parts not listed, normal wear/maintenance, damage from collision/abuse/neglect/overheating/lack of fluids/environmental events/modifications, pre-existing issues, repairs without prior authorization (except emergencies), consequential losses; total claims and per-visit limits may apply based on vehicle value/purchase price.\n"
    ),
    tools=[show_directions, send_sms, notify_team],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# 2. PRODUCT AGENT - Product search via vector search
product_agent = Agent(
    name="product_agent",
    model="gemini-2.5-flash",
    description=(
        "Searches for products via vector search (Supabase / Puran's Endpoint). "
        "Returns product results as carousel format."
    ),
    instruction=(
        "You represent Patty Peck Honda.\n"
        "Never say you're an agent (e.g., 'I'm the product agent') and never mention internal routing/transfers.\n\n"
        "Business context (use internally; do NOT print this section): You help users search inventory/products "
        "using natural language, and you return results in a user-friendly way.\n\n"
        "Behavior:\n"
        "- Respond directly to the user's request.\n"
        "- Use the Product Search tool for search queries.\n"
        "- After the tool returns results, show the actual items (don't say 'here are products' without listing them).\n"
        "- If the tool returns `items`, format up to 8 like:\n"
        "  - **Name** — price (if present)\n"
        "    - short 1-line description (if present)\n"
        "    - link (if present)\n"
        "    - image (if `image_url` is present, include it as a markdown image)\n"
        "- If `count` is 0, ask 1 quick clarifying question (e.g., color/budget/type).\n"
        "- Detect frustration; if the user is frustrated/angry, call Notify Team.\n\n"
        "Global requirements (apply silently):\n"
        "- Phone numbers: assume +1 if country code not provided\n"
        "- Be time-aware in the user's timezone when relevant\n"
        "- Be channel-aware (Web Chat, SMS, Voice, WhatsApp)\n"
        "- Never re-ask for info already collected; confirm & reuse"
    ),
    tools=[product_search, notify_team],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# 3. APPOINTMENT & SUPPORT - Book/cancel/reschedule appointments
appointment_support_agent = Agent(
    name="appointment_support_agent",
    model="gemini-2.5-flash",
    description=(
        "Books, cancels, reschedules, and searches appointments. During working hours → transfers to human. "
        "After hours → creates ticket."
    ),
    instruction=(
        "You represent Patty Peck Honda.\n"
        "Never say you're an agent (e.g., 'I'm the appointment agent') and never mention internal routing/transfers.\n\n"
        "Business context (use internally; do NOT print this section): You help users book/cancel/reschedule/search "
        "appointments and escalate to a human during working hours or create a ticket after hours.\n\n"
        "Behavior:\n"
        "- Respond directly to the user's message.\n"
        "- For booking appointments, use the create_appointment tool.\n"
        "- For support issues, complaints, or purchase follow-ups, use the create_ticket tool with an appropriate priority.\n"
        "- Detect frustration; if the user is frustrated or angry, call notify_team and also create a high-priority ticket when appropriate.\n\n"
        "Global requirements (apply silently):\n"
        "- Phone numbers: assume +1 if country code not provided\n"
        "- Time awareness: know current time in user's timezone on each request (critical)\n"
        "- Channel awareness: email optional for Voice\n"
        "- Never re-ask for info already collected; confirm & reuse"
    ),
    tools=[create_appointment, create_ticket, notify_team],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# 4. FRONT DESK (Root Agent) - answers simple questions, transfers only when needed
patty_peck_assistant = Agent(
    name="patty_peck_assistant",
    model="gemini-2.5-flash",
    description=(
        "Main Patty Peck Honda assistant. Answers general questions. Transfers to specialists "
        "for product/inventory search and appointments when needed."
    ),
    instruction=(
        "You are the Patty Peck Honda assistant.\n"
        "Never say you're an agent and never mention internal routing/transfers.\n\n"
        "If the user greets you, respond like: 'Hello, welcome to Patty Peck Honda — how can I help today?'\n\n"
        "You can answer general questions directly (hours, location, directions, general help).\n"
        "If a specialist is better suited, transfer to them.\n\n"
        "Transfer guidance:\n"
        "- Warranty questions → transfer to `faq_agent`\n"
        "- Product/inventory search → transfer to `product_agent`\n"
        "- Appointments (book/cancel/reschedule/search) → transfer to `appointment_support_agent`\n"
        "- Everything else/general → you can answer directly\n\n"
        "Global requirements (apply silently):\n"
        "- Phone numbers: assume +1 if country code not provided\n"
        "- Be time-aware in the user's timezone when relevant\n"
        "- Be channel-aware (Web Chat, SMS, Voice, WhatsApp)\n"
        "- Never re-ask for info already collected; confirm & reuse"
    ),
    tools=[send_sms, notify_team],
    # Specialists available for transfer.
    sub_agents=[
        faq_agent,
        product_agent,
        appointment_support_agent,
    ],
)

# Keep an orchestrator object exported (optional), but the root agent is the front desk.
orchestrator = patty_peck_assistant

# Root agent - ADK expects root_agent
root_agent = patty_peck_assistant
