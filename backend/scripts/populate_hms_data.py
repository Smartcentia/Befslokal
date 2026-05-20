#!/usr/bin/env python3
"""
Populate HMS tables with realistic internal control data
Based on: Leietakers internkontroll veileder
"""
import asyncio
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta
import random
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

# Norwegian assessors/inspectors
ASSESSORS = [
    "Kari Nordmann",
    "Ola Hansen",
    "Ingrid Berg",
    "Lars Johansen",
    "Maria Olsen",
    "Erik Kristiansen",
    "Anne Larsen"
]

# Risk categories from documentation
RISK_CATEGORIES = {
    "fire_evacuation": {
        "name": "Brann og Rømning",
        "consequence": "Høy",
        "likelihood": ["Lav", "Middels", "Høy"],
        "findings": [
            "Rømningsveier blokkert av lagring",
            "Branndører kilet fast i åpen stilling",
            "Manglende brannøvelser siste 12 måneder",
            "Håndslukkere mangler eller utløpt",
            "Brannalarmsystem med feil"
        ]
    },
    "personnel_safety": {
        "name": "Personellsikkerhet",
        "consequence": "Høy",
        "likelihood": ["Lav", "Middels"],
        "findings": [
            "Adgangskontroll fungerer ikke tilfredsstillende",
            "Manglende voldsalarm i utsatte områder",
            "Dårlig belysning i parkeringsområder",
            "Låsesystem ikke testet ved brannalarm"
        ]
    },
    "indoor_climate": {
        "name": "Inneklima og Helse",
        "consequence": "Middels",
        "likelihood": ["Middels", "Høy"],
        "findings": [
            "Ventilasjon leverer for lite luft",
            "Temperatur utenfor anbefalt område",
            "Støv på ventilasjonsventiler",
            "Klager på tung luft fra ansatte",
            "Muggsopp oppdaget i våtrom"
        ]
    },
    "operational": {
        "name": "Driftsavbrudd",
        "consequence": "Lav",
        "likelihood": ["Lav", "Middels"],
        "findings": [
            "Ingen backup ved strømbrudd",
            "Manglende rutiner for vannlekkasje",
            "Nødbelysning ikke testet"
        ]
    }
}

# Internal control case categories
IC_CATEGORIES = [
    "Brannsikkerhet",
    "Inneklima",
    "Sikkerhet",
    "Vedlikehold",
    "Tilgjengelighet (UU)"
]

# Deviation types
DEVIATION_TYPES = {
    "fire": [
        "Rømningsvei blokkert",
        "Brannslukker mangler",
        "Branndør defekt",
        "Brannalarm feilmelding"
    ],
    "technical": [
        "Ventilasjon støyer",
        "Varme/kjøling fungerer ikke",
        "Nødlys lyser ikke",
        "Elektrisk anlegg defekt"
    ],
    "security": [
        "Lås defekt",
        "Adgangskort fungerer ikke",
        "Vindu knust",
        "Dør går ikke i lås"
    ],
    "structural": [
        "Vannlekkasje",
        "Sprekk i vegg",
        "Løs flise",
        "Muggsopp"
    ]
}

async def get_sample_properties(db, limit=20):
    """Get sample properties for HMS data"""
    result = await db.execute(text("""
        SELECT 
            property_id,
            name,
            address,
            municipality,
            region,
            total_area,
            approved_places
        FROM properties
        ORDER BY RANDOM()
        LIMIT :limit
    """), {"limit": limit})
    
    return result.fetchall()

async def create_risk_assessments(db, properties):
    """Create risk assessments"""
    print("\n📋 Creating Risk Assessments...")
    
    assessments = []
    
    for prop in properties[:15]:  # 15 assessments
        prop_id, name, address, municipality, region, area, places = prop
        
        # Determine if institution (Risk Class 6)
        is_institution = places and places > 5
        
        # Select risk categories
        categories = random.sample(list(RISK_CATEGORIES.keys()), k=random.randint(2, 4))
        
        findings = {}
        action_plan = {}
        overall_risk = "Lav"
        
        for cat_key in categories:
            cat = RISK_CATEGORIES[cat_key]
            likelihood = random.choice(cat["likelihood"])
            selected_findings = random.sample(cat["findings"], k=random.randint(1, 3))
            
            findings[cat["name"]] = {
                "consequence": cat["consequence"],
                "likelihood": likelihood,
                "findings": selected_findings
            }
            
            # Determine overall risk
            if cat["consequence"] == "Høy" and likelihood in ["Middels", "Høy"]:
                overall_risk = "Høy"
            elif overall_risk != "Høy" and likelihood == "Middels":
                overall_risk = "Middels"
            
            # Create action plan
            for finding in selected_findings:
                action_plan[finding] = {
                    "tiltak": f"Utbedre {finding.lower()}",
                    "ansvarlig": random.choice(ASSESSORS),
                    "frist": (datetime.now() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d")
                }
        
        # Add institution-specific checks
        if is_institution:
            findings["Institusjonssikkerhet"] = {
                "consequence": "Høy",
                "likelihood": "Middels",
                "findings": [
                    "Vindussikring kontrollert",
                    "Nødåpning testet",
                    "Bemanning vurdert"
                ]
            }
        
        assessment_date = datetime.now() - timedelta(days=random.randint(30, 365))
        
        # Map to actual schema columns
        assessments.append({
            "assessment_id": str(uuid4()),
            "property_id": str(prop_id),
            "assessment_date": assessment_date,
            "methodology": "Internkontroll ROS-analyse",
            "overall_risk_score": {"Lav": 1, "Middels": 2, "Høy": 3}[overall_risk],
            "risk_category": categories[0],  # Use first category (varchar(20) limit)
            "assessed_by": random.choice(ASSESSORS),
            "notes": json.dumps({"findings": findings, "action_plan": action_plan}, ensure_ascii=False)
        })
    
    # Insert assessments
    for assessment in assessments:
        await db.execute(text("""
            INSERT INTO risk_assessments 
            (assessment_id, property_id, assessment_date, methodology, overall_risk_score, risk_category, assessed_by, notes)
            VALUES 
            (:assessment_id, :property_id, :assessment_date, :methodology, :overall_risk_score, :risk_category, :assessed_by, :notes)
        """), assessment)
    
    print(f"✅ Created {len(assessments)} risk assessments")
    return assessments

async def create_internal_control_cases(db, properties, assessments):
    """Create internal control cases"""
    print("\n📋 Creating Internal Control Cases...")
    
    cases = []
    
    for i in range(35):  # 35 cases
        prop = random.choice(properties)
        prop_id = prop[0]
        
        category = random.choice(IC_CATEGORIES)
        severity = random.choices(
            ["Kritisk", "Høy", "Middels", "Lav"],
            weights=[0.1, 0.25, 0.4, 0.25]
        )[0]
        
        status = random.choices(
            ["Lukket", "Under arbeid", "Åpen"],
            weights=[0.6, 0.25, 0.15]
        )[0]
        
        # Generate realistic titles based on category
        titles = {
            "Brannsikkerhet": [
                "Rømningsvei blokkert av lagring",
                "Brannslukker mangler i 2. etasje",
                "Branndør holder ikke automatisk lukking"
            ],
            "Inneklima": [
                "Ventilasjon støyer i møterom",
                "For høy temperatur i kontorlandskap",
                "Klager på dårlig luftkvalitet"
            ],
            "Sikkerhet": [
                "Adgangskort fungerer ikke konsekvent",
                "Ytterdør smekker ikke i lås",
                "Manglende belysning i parkeringsområde"
            ],
            "Vedlikehold": [
                "Vannlekkasje fra tak",
                "Sprekk i yttervegg",
                "Defekt vindu"
            ],
            "Tilgjengelighet (UU)": [
                "Rampe for bratt",
                "Manglende håndlist",
                "Dør for tung å åpne"
            ]
        }
        
        title = random.choice(titles.get(category, ["Generell sak"]))
        
        created = datetime.now() - timedelta(days=random.randint(7, 365))
        due_date = created + timedelta(days=random.randint(14, 90))
        
        resolution = None
        if status == "Lukket":
            resolution = f"Utbedret av utleier. Verifisert {(created + timedelta(days=random.randint(7, 60))).strftime('%Y-%m-%d')}"
        
        # Map to actual schema
        cases.append({
            "case_id": str(uuid4()),
            "property_id": str(prop_id),
            "title": title,
            "description": f"Internkontroll avdekket: {title}. Krever oppfølging.",
            "case_type": category,
            "status": {"Lukket": "closed", "Under arbeid": "in_progress", "Åpen": "open"}[status],
            "priority": {"Kritisk": "critical", "Høy": "high", "Middels": "medium", "Lav": "low"}[severity],
            "due_date": due_date if status != "Lukket" else None,
            "completed_at": created + timedelta(days=random.randint(7, 60)) if status == "Lukket" else None,
            "notes": resolution
        })
    
    # Insert cases
    for case in cases:
        await db.execute(text("""
            INSERT INTO internal_control_cases 
            (case_id, property_id, title, description, case_type, status, priority, due_date, completed_at, notes)
            VALUES 
            (:case_id, :property_id, :title, :description, :case_type, :status, :priority, :due_date, :completed_at, :notes)
        """), case)
    
    print(f"✅ Created {len(cases)} internal control cases")
    return cases

async def create_deviations(db, properties):
    """Create deviation reports"""
    print("\n📋 Creating Deviations...")
    
    deviations = []
    
    for i in range(55):  # 55 deviations
        prop = random.choice(properties)
        prop_id = prop[0]
        
        dev_type = random.choice(list(DEVIATION_TYPES.keys()))
        title = random.choice(DEVIATION_TYPES[dev_type])
        
        severity = random.choices(
            ["Kritisk", "Høy", "Middels", "Lav"],
            weights=[0.05, 0.2, 0.45, 0.3]
        )[0]
        
        status = random.choices(
            ["Utbedret", "Under utbedring", "Meldt utleier"],
            weights=[0.7, 0.2, 0.1]
        )[0]
        
        reported_date = datetime.now() - timedelta(days=random.randint(1, 180))
        
        deviations.append({
            "deviation_id": str(uuid4()),
            "property_id": str(prop_id),
            "title": title,
            "description": f"Avvik oppdaget under internkontroll: {title}",
            "severity": severity,
            "status": status,
            "reported_by": random.choice(ASSESSORS),
            "assigned_to": random.choice(ASSESSORS) if status != "Meldt utleier" else "Utleier",
            "created_at": reported_date
        })
    
    # Insert deviations
    for deviation in deviations:
        await db.execute(text("""
            INSERT INTO deviations 
            (deviation_id, property_id, title, description, severity, status, reported_by, assigned_to, created_at)
            VALUES 
            (:deviation_id, :property_id, :title, :description, :severity, :status, :reported_by, :assigned_to, :created_at)
        """), deviation)
    
    print(f"✅ Created {len(deviations)} deviations")
    return deviations

async def create_checklists(db, properties):
    """Create inspection checklists"""
    print("\n📋 Creating Checklists...")
    
    checklists = []
    
    # Monthly fire safety checklist
    fire_items = [
        {"item": "Rømningsveier", "requirement": "Frie for hindringer", "status": "OK"},
        {"item": "Håndslukkere", "requirement": "Splint på plass, pil på grønt", "status": "OK"},
        {"item": "Brannsentralen", "requirement": "Ingen feilmeldinger", "status": "OK"},
        {"item": "Branndører", "requirement": "Lukker automatisk", "status": "OK"}
    ]
    
    # Quarterly ventilation check
    vent_items = [
        {"item": "Ventiler", "requirement": "Ingen synlig støv", "status": "Avvik"},
        {"item": "Støynivå", "requirement": "Akseptabelt", "status": "OK"},
        {"item": "Temperatur", "requirement": "19-26 grader", "status": "OK"}
    ]
    
    # Annual fire drill
    drill_items = [
        {"item": "Deltakelse", "requirement": "Alle ansatte", "status": "OK"},
        {"item": "Evakueringstid", "requirement": "Under 5 minutter", "status": "OK"},
        {"item": "Samlingsplass", "requirement": "Alle funnet", "status": "OK"}
    ]
    
    # Institution-specific (Risk Class 6)
    inst_items = [
        {"item": "Vindussikring", "requirement": "Ingen skader", "status": "OK"},
        {"item": "Nødåpning", "requirement": "Testet ved alarm", "status": "OK"},
        {"item": "Bemanning", "requirement": "I henhold til ROS", "status": "OK"}
    ]
    
    checklist_templates = [
        {
            "title": "Månedlig Brannsikkerhetskontroll",
            "description": "Rutinekontroll av brannsikkerhet",
            "items": fire_items,
            "frequency": "monthly"
        },
        {
            "title": "Kvartalsvis Ventilasjonskontroll",
            "description": "Kontroll av ventilasjon og inneklima",
            "items": vent_items,
            "frequency": "quarterly"
        },
        {
            "title": "Årlig Brannøvelse",
            "description": "Gjennomføring av brannøvelse",
            "items": drill_items,
            "frequency": "yearly"
        },
        {
            "title": "Institusjonssikkerhet (Risikoklasse 6)",
            "description": "Spesialkontroll for barnevernsinstitusjoner",
            "items": inst_items,
            "frequency": "monthly"
        }
    ]
    
    for prop in properties[:12]:  # 12 properties with checklists
        prop_id = prop[0]
        is_institution = prop[6] and prop[6] > 5  # approved_places > 5
        
        templates_to_use = checklist_templates[:3]
        if is_institution:
            templates_to_use = checklist_templates  # Include institution checklist
        
        for template in templates_to_use:
            last_completed = datetime.now() - timedelta(days=random.randint(1, 30))
            
            checklists.append({
                "checklist_id": str(uuid4()),
                "property_id": str(prop_id),
                "title": template["title"],
                "description": template["description"],
                "items": json.dumps(template["items"], ensure_ascii=False),
                "frequency": template["frequency"],
                "last_completed": last_completed
            })
    
    # Insert checklists
    for checklist in checklists:
        await db.execute(text("""
            INSERT INTO checklists 
            (checklist_id, property_id, title, description, items, frequency, last_completed)
            VALUES 
            (:checklist_id, :property_id, :title, :description, :items, :frequency, :last_completed)
        """), checklist)
    
    print(f"✅ Created {len(checklists)} checklists")
    return checklists

async def main():
    print("=" * 70)
    print("🏗️  POPULATING HMS TABLES WITH INTERNAL CONTROL DATA")
    print("=" * 70)
    
    async with SessionLocal() as db:
        # Get sample properties
        print("\n📊 Fetching properties...")
        properties = await get_sample_properties(db, limit=20)
        print(f"✅ Found {len(properties)} properties")
        
        # Create data (only tables that exist)
        assessments = await create_risk_assessments(db, properties)
        cases = await create_internal_control_cases(db, properties, assessments)
        
        # Note: deviations and checklists tables don't exist yet
        print("\n⚠️  Skipping deviations and checklists (tables not found in schema)")
        
        # Commit transaction
        await db.commit()
        
        print("\n" + "=" * 70)
        print("✅ HMS DATA POPULATION COMPLETE")
        print("=" * 70)
        print(f"\nCreated:")
        print(f"  - {len(assessments)} Risk Assessments")
        print(f"  - {len(cases)} Internal Control Cases")
        print(f"\nTotal: {len(assessments) + len(cases)} HMS records")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
