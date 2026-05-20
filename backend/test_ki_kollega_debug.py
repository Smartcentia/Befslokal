#!/usr/bin/env python3
"""
KI Kollega Debug Test Suite
Tester hver komponent separat for å finne hvor problemet oppstår.
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env')

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_pass(msg: str):
    print(f"{GREEN}✅ PASS: {msg}{RESET}")

def print_fail(msg: str):
    print(f"{RED}❌ FAIL: {msg}{RESET}")

def print_warn(msg: str):
    print(f"{YELLOW}⚠️  WARN: {msg}{RESET}")

def print_info(msg: str):
    print(f"   ℹ️  {msg}")

async def test_1_environment_variables():
    """Test 1: Sjekk at alle nødvendige miljøvariabler er satt."""
    print_test("1. Miljøvariabler")
    
    from app.core.config import settings
    # Force import of all models for mappers
    import app.db.base
    
    errors = []
    
    # OPENAI_API_KEY
    if settings.OPENAI_API_KEY:
        if settings.OPENAI_API_KEY.startswith("sk-"):
            print_pass(f"OPENAI_API_KEY er satt (starter med 'sk-...')")
            print_info(f"Lengde: {len(settings.OPENAI_API_KEY)} tegn")
        else:
            print_fail(f"OPENAI_API_KEY har ugyldig format: {settings.OPENAI_API_KEY[:20]}...")
            errors.append("OPENAI_API_KEY ugyldig format")
    else:
        print_fail("OPENAI_API_KEY er IKKE satt!")
        errors.append("OPENAI_API_KEY mangler")
    
    # OPENAI_MODEL
    print_info(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")
    
    # DATABASE_URL
    if settings.DATABASE_URL:
        print_pass(f"DATABASE_URL er satt")
        print_info(f"Host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'ukjent'}")
    else:
        print_fail("DATABASE_URL er IKKE satt!")
        errors.append("DATABASE_URL mangler")
    
    return len(errors) == 0, errors


async def test_2_openai_connection():
    """Test 2: Test direkte OpenAI API-tilkobling."""
    print_test("2. OpenAI API-tilkobling")
    
    from app.core.config import settings
    
    if not settings.OPENAI_API_KEY:
        print_fail("Kan ikke teste - OPENAI_API_KEY mangler")
        return False, ["OPENAI_API_KEY mangler"]
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        
        print_info(f"Tester med modell: {settings.OPENAI_MODEL}")
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Du er en hjelpsom assistent. Svar kort."},
                {"role": "user", "content": "Si 'Hei, jeg fungerer!' på norsk."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        answer = response.choices[0].message.content
        print_pass(f"OpenAI svarte: '{answer}'")
        print_info(f"Tokens brukt: {response.usage.total_tokens}")
        
        # Sjekk at svaret gir mening
        if "hei" in answer.lower() or "fungerer" in answer.lower():
            print_pass("Svaret ser fornuftig ut")
            return True, []
        else:
            print_warn(f"Svaret kan være merkelig: {answer}")
            return True, ["Svaret kan være merkelig"]
        
    except Exception as e:
        print_fail(f"OpenAI API feilet: {e}")
        return False, [str(e)]


async def test_3_langchain_openai():
    """Test 3: Test LangChain OpenAI wrapper (brukes av Writer)."""
    print_test("3. LangChain ChatOpenAI")
    
    from app.core.config import settings
    
    if not settings.OPENAI_API_KEY:
        print_fail("Kan ikke teste - OPENAI_API_KEY mangler")
        return False, ["OPENAI_API_KEY mangler"]
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        
        print_info(f"Tester LangChain med modell: {settings.OPENAI_MODEL}")
        
        messages = [
            SystemMessage(content="Du er en hjelpsom assistent. Svar kort på norsk."),
            HumanMessage(content="Hva er 2+2?")
        ]
        
        response = await llm.ainvoke(messages)
        
        print_pass(f"LangChain svarte: '{response.content}'")
        
        # Sjekk at svaret inneholder 4
        if "4" in response.content or "fire" in response.content.lower():
            print_pass("Svaret er korrekt!")
            return True, []
        else:
            print_warn(f"Svaret kan være feil - forventet '4'")
            return True, ["Svaret kan være feil"]
        
    except Exception as e:
        print_fail(f"LangChain feilet: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def test_4_database_connection():
    """Test 4: Test database-tilkobling."""
    print_test("4. Database-tilkobling")
    
    try:
        from app.db.session import SessionLocal
        from sqlalchemy import text
        
        async with SessionLocal() as db:
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print_pass("Database-tilkobling OK")
            else:
                print_fail("Uventet resultat fra database")
                return False, ["Database-feil"]
            
            # Tell eiendommer
            result = await db.execute(text("SELECT COUNT(*) FROM properties"))
            count = result.scalar()
            print_info(f"Antall eiendommer i database: {count}")
            
            return True, []
            
    except Exception as e:
        print_fail(f"Database-tilkobling feilet: {e}")
        return False, [str(e)]


async def test_5_ki_kollega_service_init():
    """Test 5: Test KI Kollega service initialisering."""
    print_test("5. KI Kollega Service Init")
    
    try:
        from app.services.intelligence.ki_kollega.service import KIKollegaService
        
        service = KIKollegaService()
        
        if service.client:
            print_pass("KI Kollega service initialisert med client")
            print_info(f"Modell: {service.model}")
            return True, []
        else:
            print_fail("KI Kollega service har INGEN client!")
            return False, ["Client ikke initialisert"]
            
    except Exception as e:
        print_fail(f"KI Kollega init feilet: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def test_6_supervisor_node():
    """Test 6: Test Supervisor routing."""
    print_test("6. Supervisor Node")
    
    try:
        from app.services.intelligence.agents.nodes.supervisor import supervisor_node
        from langchain_core.messages import HumanMessage
        
        # Test case 1: Hilsen
        state = {
            "messages": [HumanMessage(content="Hei!")],
            "discovered_tools": [],
            "persona": None
        }
        
        result = await supervisor_node(state)
        print_info(f"'Hei!' -> rutes til: {result.get('next_step')}")
        
        if result.get("next_step") == "writer":
            print_pass("Hilsen rutes korrekt til writer")
        else:
            print_warn(f"Hilsen rutes til {result.get('next_step')} (forventet: writer)")
        
        # Test case 2: Database-spørsmål
        state2 = {
            "messages": [HumanMessage(content="Hva er den største eiendommen?")],
            "discovered_tools": [],
            "persona": None
        }
        
        result2 = await supervisor_node(state2)
        print_info(f"'Hva er den største eiendommen?' -> rutes til: {result2.get('next_step')}")
        
        return True, []
        
    except Exception as e:
        print_fail(f"Supervisor feilet: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def test_7_writer_node_direct():
    """Test 7: Test Writer node direkte."""
    print_test("7. Writer Node Direkte")
    
    try:
        from app.services.intelligence.agents.nodes.writer import writer_node
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Simuler en enkel state med bruker-spørsmål
        state = {
            "messages": [
                HumanMessage(content="Hei, hva kan du hjelpe meg med?")
            ],
            "persona": "Du er KI Kollega, en hjelpsom assistent.",
            "discovered_tools": [],
            "research_data": {}
        }
        
        print_info("Sender til Writer: 'Hei, hva kan du hjelpe meg med?'")
        
        result = await writer_node(state)
        
        if "messages" in result and len(result["messages"]) > 0:
            answer = result["messages"][0].content
            print_pass(f"Writer svarte!")
            print_info(f"Svar (første 200 tegn): {answer[:200]}...")
            
            # Sjekk om svaret gir mening
            if len(answer) > 10 and any(word in answer.lower() for word in ["hjelpe", "kan", "spørsmål", "eiendom", "hei"]):
                print_pass("Svaret ser fornuftig ut på norsk")
                return True, []
            else:
                print_warn("Svaret kan være uforståelig")
                print_info(f"Fullt svar: {answer}")
                return True, ["Svaret kan være uforståelig"]
        else:
            print_fail("Writer returnerte ingen melding!")
            return False, ["Ingen melding fra Writer"]
        
    except Exception as e:
        print_fail(f"Writer feilet: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def test_8_full_langgraph_flow():
    """Test 8: Test full LangGraph flyt."""
    print_test("8. Full LangGraph Flyt")
    
    try:
        from langchain_core.messages import HumanMessage
        from app.services.intelligence.agents.graph import app
        
        inputs = {
            "messages": [HumanMessage(content="Hei!")],
            "discovered_tools": [],
            "persona": "Du er KI Kollega."
        }
        
        print_info("Kjører full graf med 'Hei!'...")
        
        # Kjør med timeout
        final_state = await asyncio.wait_for(
            app.ainvoke(inputs),
            timeout=30.0
        )
        
        if "messages" in final_state:
            last_msg = final_state["messages"][-1]
            print_pass(f"Graf fullført!")
            print_info(f"Antall meldinger: {len(final_state['messages'])}")
            print_info(f"Siste melding (første 200 tegn): {last_msg.content[:200]}...")
            
            # Sjekk kvalitet
            if len(last_msg.content) > 5:
                if any(word in last_msg.content.lower() for word in ["hei", "hjelpe", "kan", "spørsmål"]):
                    print_pass("Svaret ser fornuftig ut!")
                    return True, []
                else:
                    print_warn("Svaret kan være merkelig")
                    print_info(f"Fullt svar: {last_msg.content}")
                    return True, ["Svaret kan være merkelig"]
            else:
                print_fail("Svaret er for kort/tomt")
                return False, ["Svaret er for kort"]
        else:
            print_fail("Ingen meldinger i final state")
            return False, ["Ingen meldinger"]
        
    except asyncio.TimeoutError:
        print_fail("Graf timed out etter 30 sekunder!")
        return False, ["Timeout"]
    except Exception as e:
        print_fail(f"Graf feilet: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def test_9_ki_kollega_chat():
    """Test 9: Test full KI Kollega chat metode."""
    print_test("9. KI Kollega chat() metode")
    
    try:
        from app.services.intelligence.ki_kollega.service import ki_kollega_service
        from app.db.session import SessionLocal
        
        async with SessionLocal() as db:
            print_info("Kaller ki_kollega_service.chat()...")
            
            result = await asyncio.wait_for(
                ki_kollega_service.chat(
                    message="Hei, fortell meg kort hva du kan hjelpe meg med.",
                    db=db
                ),
                timeout=45.0
            )
            
            if "answer" in result:
                answer = result["answer"]
                print_pass(f"Chat returnerte svar!")
                print_info(f"Svar (første 300 tegn): {answer[:300]}...")
                
                if result.get("error"):
                    print_warn(f"Error i resultat: {result['error']}")
                
                # Sjekk kvalitet
                if len(answer) > 10:
                    # Sjekk for nonsens (repeterende tegn, uforståelig tekst)
                    words = answer.split()
                    unique_words = set(words)
                    
                    if len(unique_words) < len(words) * 0.3:
                        print_warn("Mulig repeterende/nonsens tekst")
                        print_info(f"Unike ord: {len(unique_words)} av {len(words)}")
                    
                    if any(word in answer.lower() for word in ["hjelpe", "eiendom", "kan", "spørsmål", "hei"]):
                        print_pass("Svaret inneholder forventede ord!")
                        return True, []
                    else:
                        print_warn("Svaret mangler forventede norske ord")
                        return True, ["Kan mangle forventede ord"]
                else:
                    print_warn("Svaret er veldig kort")
                    return True, ["Kort svar"]
            else:
                print_fail("Ingen 'answer' i resultat")
                print_info(f"Resultat: {result}")
                return False, ["Ingen answer"]
                
    except asyncio.TimeoutError:
        print_fail("Chat timed out etter 45 sekunder!")
        return False, ["Timeout"]
    except Exception as e:
        print_fail(f"Chat feilet: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


async def test_10_dspy_sql_generator():
    """Test 10: Test DSPy SQL Generator."""
    print_test("10. DSPy SQL Generator")
    
    try:
        from app.services.dspy.sql_generator import dspy_generator
        from app.db.session import SessionLocal
        
        print_info("Tester DSPy SQL-generering...")
        
        async with SessionLocal() as db:
            result = await dspy_generator.execute_query(
                db, 
                "Hvor mange eiendommer har vi?"
            )
            
            if result.get("error"):
                print_warn(f"DSPy feil: {result['error']}")
                print_info(f"SQL forsøkt: {result.get('sql', 'N/A')}")
                return True, [result['error']]  # Ikke kritisk feil
            
            print_pass(f"DSPy genererte SQL: {result.get('sql', 'N/A')[:100]}...")
            print_info(f"Antall resultater: {result.get('count', 0)}")
            
            return True, []
            
    except Exception as e:
        print_warn(f"DSPy test feilet (ikke kritisk): {e}")
        return True, [str(e)]  # DSPy-feil er ikke kritisk for enkel chat


async def main():
    """Kjør alle tester."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}   KI KOLLEGA DEBUG TEST SUITE{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    tests = [
        ("1. Miljøvariabler", test_1_environment_variables),
        ("2. OpenAI API", test_2_openai_connection),
        ("3. LangChain OpenAI", test_3_langchain_openai),
        ("4. Database", test_4_database_connection),
        ("5. KI Kollega Init", test_5_ki_kollega_service_init),
        ("6. Supervisor Node", test_6_supervisor_node),
        ("7. Writer Node", test_7_writer_node_direct),
        ("8. Full LangGraph", test_8_full_langgraph_flow),
        ("9. KI Kollega Chat", test_9_ki_kollega_chat),
        ("10. DSPy SQL", test_10_dspy_sql_generator),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed, errors = await test_func()
            results.append((name, passed, errors))
        except Exception as e:
            results.append((name, False, [str(e)]))
    
    # Oppsummering
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}   OPPSUMMERING{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    passed_count = 0
    failed_count = 0
    
    for name, passed, errors in results:
        if passed:
            print(f"{GREEN}✅ {name}{RESET}")
            passed_count += 1
        else:
            print(f"{RED}❌ {name}: {', '.join(errors)}{RESET}")
            failed_count += 1
    
    print(f"\n{BLUE}Totalt: {passed_count} passert, {failed_count} feilet{RESET}")
    
    if failed_count > 0:
        print(f"\n{RED}⚠️  Det er feil som må fikses!{RESET}")
    else:
        print(f"\n{GREEN}🎉 Alle tester passerte!{RESET}")
    
    return failed_count == 0


if __name__ == "__main__":
    asyncio.run(main())
