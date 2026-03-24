from jinja2 import Environment, BaseLoader

env = Environment(
    loader=BaseLoader(),
    autoescape=False
)

def render_template(content: str, lead: dict):
    if not content:
        return content

    safe_lead = {k: (v or "") for k, v in lead.items()}

    template = env.from_string(content)
    return template.render(**safe_lead)

def build_lead_context(lead):
    return {
        "name": lead.get("name"),
        "email": lead.get("email"),
        "company_name": lead.get("company_name"),
        "industry": lead.get("industry"),
        "title": lead.get("title"),
        "location": lead.get("location")
    }