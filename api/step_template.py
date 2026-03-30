from database import database
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from services.template_renderer import render_template, build_lead_context
step_template_router = APIRouter(prefix="/step_templates", tags=["step-templates"])

async def seed_templates():
   
    existing = await database.sequence_templates.find_one({
        "name": "Cold Outreach 3-Step"
    })

    if existing:
        return
    templates = [
    {
        "name": "Cold Outreach 3-Step",
        "description": "Basic outbound cold email sequence",
        "is_predefined": True,
        "category": "cold_email",
        "tags": ["sales", "b2b"],
        "steps": [
            {
                "step_order": 1,
                "step_type": "email",
                "delay_in_minutes": 5,
                "subject": "Quick question about cold outreach",
                "body": "Hi {{name}}, I came across {{company_name}}..."
            },
            {
                "step_order": 2,
                "step_type": "email",
                "delay_in_minutes": 5,
                "subject": "Following up",
                "body": "Just checking in..."
            },
            {
                "step_order": 3,
                "step_type": "email",
                "delay_in_minutes": 5,
                "subject": "Demo Booking",
                "body": "Just checking in..."
            }
        ]
    },
    {
        "name": "Follow Up Sequence",
        "description": "Simple follow-up flow",
        "is_predefined": True,
        "category": "follow_up",
        "tags": ["followup"],
        "steps": [
            {
                "step_order": 1,
                "step_type": "email",
                "delay_in_minutes": 0,
                "subject": "Just checking in",
                "body": "Hi {{name}}, following up..."
            }
        ]
    },
    {
        "name": "Product Demo Follow-up Sequence",
        "description": "A 4-step follow-up sequence after demo booking",
        "is_predefined": True,
        "category": "demo_followup",
        "tags": ["sales", "demo", "b2b"],

        "steps": [
            {
                "step_order": 1,
                "step_type": "email",
                "delay_in_minutes": 0,
                "subject": "Great connecting today!",
                "body": "Hi {{name}}, thanks for attending the demo..."
            },
            {
                "step_order": 2,
                "step_type": "email",
                "delay_in_minutes": 2,
                "subject": "Any questions?",
                "body": "Hi {{name}} ,Hope you are Doing well ....Just wanted to check if you had any questions..."
            },
            {
                "step_order": 3,
                "step_type": "email",
                "delay_in_minutes": 2,
                "subject": "Resources for {{company_name}}",
                "body": "Sharing some useful resources..."
            },
            {
                "step_order": 4,
                "step_type": "email",
                "delay_in_minutes": 2,
                "subject": "Final follow-up",
                "body": "Just closing the loop..."
            }
        ]
    }
]

    await database.sequence_templates.insert_many(templates)


@step_template_router.post("/apply")
async def apply_template(template_id: str, 
                         sequence_id: str):
    if not ObjectId.is_valid(template_id):
        raise HTTPException(400, "Invalid template id")

    if not ObjectId.is_valid(sequence_id):
        raise HTTPException(400, "Invalid sequence id")

    template = await database.sequence_templates.find_one({
        "_id": ObjectId(template_id)
    })

    if not template:
        raise HTTPException(404, "Template not found")

    sequence_obj_id = ObjectId(sequence_id)
    existing = await database.sequence_steps.count_documents({
        "sequence_id": sequence_obj_id
    })

    if existing > 0:
        raise HTTPException(400, "Sequence already has steps")

    steps_to_insert = []

    for step in template.get("steps", []):
       
        steps_to_insert.append({
            "sequence_id": sequence_obj_id,
            "step_order": step["step_order"],
            "step_type": step["step_type"],
            "delay_in_minutes": step["delay_in_minutes"],
            "subject": step.get("subject"),
            "body": step.get("body")
        })

    await database.sequence_steps.insert_many(steps_to_insert)

    return {
        "message": "Template applied successfully",
        "steps_created": len(steps_to_insert)
    }

@step_template_router.get("/view")
async def get_templates():

    templates = await database.sequence_templates.find({
        "is_predefined": True
    }).to_list(length=100)

    for t in templates:
        t["id"] = str(t["_id"])
        t.pop("_id")

    return templates