# #uvicorn a2a_app.district_court_service.agent:a2a_app --host localhost --port 8003

# from dotenv import load_dotenv
# load_dotenv()

# import asyncio
# from google.adk.agents import Agent
# from google.adk.models.lite_llm import LiteLlm
# from google.adk.a2a.utils.agent_to_a2a import to_a2a

# # Import the District Court client from bharat-courts
# from bharat_courts import DistrictCourtClient

# async def check_district_court(state: str, district: str, case_type: str, case_number: str, year: str) -> str:
#     """
#     Checks the status of a District Court case using the official eCourts portal.
#     Requires state, district, case_type, case_number, and year.
#     """
#     client = DistrictCourtClient()
#     try:
#         async with client:
#             cases = await client.case_status(
#                 state=state, 
#                 district=district, 
#                 case_type=case_type, 
#                 case_number=case_number, 
#                 year=year
#             )
            
#             if not cases:
#                 return "No cases found with the provided details."
            
#             # Format the first matching case found
#             case = cases[0]
#             return f"Case Found: {case.petitioner} vs {case.respondent} | Status: {case.status} | Next Hearing: {case.next_hearing_date}"
            
#     except Exception as e:
#         return f"Error connecting to District Court portal: {str(e)}"

# district_court_service = Agent(
#     name="district_court_service",
#     model=LiteLlm(model="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"),
#     description="Handles inquiries and case lookups for the District Court.",
#     instruction="""You are the District Court Agent. 
#     Your job is to look up district court cases using your tool.
#     CRITICAL: If the user does not provide the state, district, case_type, case_number, AND year, you MUST politely ask them for the missing information before executing the tool.""",
#     tools=[check_district_court],
# )

# # Expose as an A2A-compliant ASGI app
# a2a_app = to_a2a(district_court_service, port=8003)


import asyncio
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from bharat_courts import DistrictCourtClient

async def get_states_dropdown() -> str:
    """Gets the list of available States and their specific state codes."""
    async with DistrictCourtClient() as client:
        states = await client.list_states()
        return f"Available States and Codes: {states}"

async def get_districts_dropdown(state_code: str) -> str:
    """Gets the list of Districts and their district codes for a specific state_code."""
    async with DistrictCourtClient() as client:
        districts = await client.list_districts(state_code)
        return f"Available Districts for state_code {state_code}: {districts}"

async def get_court_complexes_dropdown(state_code: str, district_code: str) -> str:
    """Gets the list of Court Complexes and their complex codes for a specific district."""
    async with DistrictCourtClient() as client:
        complexes = await client.list_complexes(state_code, district_code)
        return f"Available Court Complexes: {complexes}"

async def get_case_types_dropdown(state_code: str, district_code: str, complex_code: str) -> str:
    """Gets the list of valid Case Types for a specific court complex."""
    async with DistrictCourtClient() as client:
        case_types = await client.list_case_types(state_code, district_code, complex_code)
        return f"Available Case Types: {case_types}"



# async def check_district_court(state_code: str, district_code: str, complex_code: str, case_type: str, case_number: str, year: str) -> str:
#     """
#     Checks the status of a District Court case on the eCourts portal.
#     Requires the exact state_code, district_code, and complex_code gathered from the dropdown tools, 
#     along with case_type, case_number, and year.
#     """
#     try:
#         async with DistrictCourtClient() as client:
#             cases = await client.case_status(
#                 state=state_code, 
#                 district=district_code, 
#                 court_complex=complex_code,
#                 case_type=case_type, 
#                 case_number=case_number, 
#                 year=year
#             )
            
#             if not cases:
#                 return "No cases found with the provided details."
            
#             # Format the first matching case found
#             case = cases[0]
#             return f"Case Found: {case.petitioner} vs {case.respondent} | Status: {case.status} | Next Hearing: {case.next_hearing_date}"
            
#     except Exception as e:
#         return f"Error connecting to District Court portal: {str(e)}"


async def check_district_court(state_code: str, district_code: str, complex_code: str, case_type: str, case_number: str, year: str) -> str:
    """
    Checks the status of a District Court case on the eCourts portal.
    Requires the exact state_code, district_code, and complex_code.
    """
    try:
        async with DistrictCourtClient() as client:
            # FIX: We changed state= to state_code= and district= to dist_code=
            cases = await client.case_status(
                state_code=state_code, 
                dist_code=district_code, 
                court_complex_code=complex_code,
                est_code="",  # Include an empty est_code if required
                case_type=case_type, 
                case_number=case_number, 
                year=year
            )
            
            if not cases:
                return "No cases found with the provided details."
            
            # Format the first matching case found
            case = cases[0]
            return f"Case Found: {case.petitioner} vs {case.respondent} | Status: {case.status} | Next Hearing: {case.next_hearing_date}"
            
    except Exception as e:
        return f"Error connecting to District Court portal: {str(e)}"


district_court_service = Agent(
    name="district_court_service",
    model=LiteLlm(model="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"),
    description="Handles inquiries and case lookups for the District Court.",
    instruction="""You are the District Court Agent. Your goal is to fetch case status for the user.
    Because District Courts require strict internal codes rather than plain text names, you MUST follow this sequence if the user doesn't provide the exact codes:
    
    1. Check state: If you don't know the exact state_code, use get_states_dropdown(). Show the options to the user and ask them to choose.
    2. Check district: Once you have the state_code, use get_districts_dropdown(state_code). Ask the user to choose their district.
    3. Check complex: Use get_court_complexes_dropdown() and ask the user to pick their exact court complex.
    4. Check case type: Use get_case_types_dropdown() to ensure they are using a valid case type abbreviation.
    5. Final Lookup: Once you have all 6 parameters (state_code, district_code, complex_code, case_type, case_number, year), use the check_district_court tool to get the status.
    
    Do NOT guess the codes. Always look them up using your tools and verify with the user if ambiguous.""",
    tools=[
        get_states_dropdown,
        get_districts_dropdown,
        get_court_complexes_dropdown,
        get_case_types_dropdown,
        check_district_court
    ],
)


a2a_app = to_a2a(district_court_service, port=8003)
