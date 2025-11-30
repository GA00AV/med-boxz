from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from pymongo import MongoClient
from datetime import datetime
from pydantic import BaseModel
from typing import Annotated
from dotenv import load_dotenv
from jose import jwt
import os
from tavily import TavilyClient
from bson import ObjectId
from redis import Redis
load_dotenv()

REDIS_CLIENT = Redis.from_url(os.environ['REDIS_URL'])
client = MongoClient(os.environ['MONGO_URI'])
database = client[os.environ["DB_NAME"]]
Users = database[os.environ["USER_COLLECTION"]]
CONSULTATIONS = database[os.environ["CONSULTATION_COLLECTION"]]
MANUAL_REVIEWS = database[os.environ["MANUAL_REVIEWS_COLLECTION"]]

# USERS = [{"name":"Dr. Ganesh Ji", "id":"string", "email":"ganesh@medboxz.in", "role":"doctor",  "speciality":"Dermatology"},
#          {"name":"Dr. Vishnu", "id":"string", "email":"narayan@medboxz.in", "role":"patient", "speciality":"None"}]
# CONSULTATIONS = [
#     {
#         "patient_email": "narayan@medboxz.in",
#         "doctor_id": "string",
#         "timing" : "10:00",
#         "date" : "02-12-2025",
#         "status": "completed" | "waiting" | "no-show" | "booked" | "cancelled",
#         "payment": "received" | "not-received" | "refund-initiated" | "refunded"
#     }
# ]
# MANUAL_REVIEWS = [
#     {
#         "issue": "summary",
#         "patient_id": "string",
#         "status": "initiated" | "processing" | "closed"
#     }
# ]

class State(BaseModel):
    messages: Annotated[list, add_messages]

def get_today_date_and_time()->str:
    """
    :return: date and time of today.
    """
    print("RUNNING get_today_date_and_time")
    today = datetime.today()
    return today.strftime("Date:%d/%m/%Y Time:%H:%M:%S")


def book_consultation(patient_name:str, patient_email:str, doctor_id:str, date_of_consultation:str, timing:str) -> str:
    """
    Books consultation for patient and returns url if successful added consultation in waiting list and once payment is done via that url, then consultation is booked. Return Error text if anything goes wrong.
    :param patient_email: email of patient
    :param doctor_id: id of doctor
    :param date_of_consultation: date of consultation in DD-MM-YYYY format
    :param timing: time of consultation in HH:MM format
    :param patient_name: name of patient
    """
    print("RUNNING book_consultation")
    try:
        user = Users.find_one({"email": patient_email})
        if not user:
            # patient doesn't exist
            Users.insert_one({"name":patient_name, "email":patient_email, "role":"patient", "speciality":None})
            user = Users.find_one({"email":patient_email})

        # checking if doctor exist
        doctor = Users.find_one({"_id": ObjectId(doctor_id)})
        if not doctor:
            return f"Doctor with doctor_id {doctor_id} doesn't exists."
        # ensure consultation isn't in past
        day = datetime.strptime(f"{date_of_consultation} {timing}", '%d-%m-%Y %H:%M')
        if day < datetime.today():
            return f"Creating consultation in past isn't possible. Today is {get_today_date_and_time()}"

        # check if timing is in available slots
        all_correct_timings = get_all_available_consultation_timings_of_doctor(doctor_id, date_of_consultation)
        if not all_correct_timings.__contains__(timing):
            return f"invalid timings. doctor isn't available on {date_of_consultation} at {timing}. Check all available timings first."
        consultation = {
            "patient_email": patient_email,
            "doctor_id": doctor_id,
            "timing" : timing,
            "date" : date_of_consultation,
            "status": "waiting",
            "payment": "not-received"
        }
        consultation = CONSULTATIONS.insert_one(consultation)
        REDIS_CLIENT.set(f"{doctor_id}/{date_of_consultation}/{timing}", "True")
        payment_link = get_payment_link_for_consultation(patient_email, consultation.inserted_id)
        return f"Booked consultation for {user['name']} on {date_of_consultation} at {timing} with {doctor['name']}, who is specialised in {doctor['speciality']}. here is the link for payment: {payment_link}"
    except Exception as e:
        print(f"Error in book_consultation: {e}")
        return "Internal Server Error"

def get_all_available_consultation_timings_of_doctor(doctor_id:str, date_of_consultation:str) -> list | str:
    """
    Return all available consultation timings for doctor
    :param doctor_id: id of doctor
    :param date_of_consultation: date of consultation
    """
    print("RUNNING get_all_available_consultation_timings_of_doctor")

    try:
        timings = []
        for i in range(8, 18):
            if REDIS_CLIENT.get(f"{doctor_id}/{date_of_consultation}/{i}:00"):
                continue
            else:
                timings.append(f"{i if i > 9 else f"0{i}"}:00")
        return timings
    except Exception as e:
        print(f"Error in get_all_available_consultation_timings_of_doctor: {e}")
        return "Internal Server Error"


def get_all_consultations_of_patient_by_email(patient_email:str) -> list | str:
    """Returns all consultations that a patient"""
    print("RUNNING get_all_consultations_of_patient_by_email")
    try:
        consultations = [f"consultation_id:{item['_id']} doctor_id:{item['doctor_id']} date:{item['date']} timing:{item['timing']} status:{item['status']} payment:{item['payment']}" for item in list(CONSULTATIONS.find({"patient_email": patient_email}))]
        if len(consultations) > 0:
            return consultations
        else:
            return "No consultation found for this patient."
    except Exception as e:
        print(f"Error in get_all_consultations_of_patient: {e}")
        return "Internal Server Error"

def get_all_doctors()->str:
    """
    Return all doctors available.
    """
    print("RUNNING get_all_doctors")

    try:
        users = Users.find({"role":"doctor"})
        return "\n".join([f"{doctor['name']} ID:{str(doctor['_id'])} Speciality:{doctor['speciality']}" for doctor in users])
    except Exception as e:
        print(f"Error in get_all_doctors: {e}")
        return "Internal Server Error"

# Search Tool
def search(query:str) -> str:
    """
    :param query: thing that you want to search on internet
    :return: result from internet along with its source
    """
    print(f"Searching for {query}")
    tavily_client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])
    output = tavily_client.search(query)
    data = [f"Source: {result['url']}\n{result['title']}\n{result['content']}" for result in output["results"]]
    return "\n\n".join(data)

def get_patient_info(patient_email:str) -> str:
    """
    :param patient_email: email of patient
    :return: email, name, and all consultations of that patient till now
    """
    print("RUNNING get_patient_info")

    try:
        patient = Users.find_one({ "email": patient_email })
        if patient:
            consultations = get_all_consultations_of_patient_by_email(patient_email)
            patient = f"Patient: {patient['name']}\n email: {patient['email']}\n consultations: \n{'\n'.join(consultations)}"
            return patient
        else:
            return "Patient not found."
    except Exception as e:
        print(f"Error in get_patient_info: {e}")
        return "Internal Server Error"

def cancel_consultation_and_initiate_refund(consultation_id:str)->str:
    """
    It cancels consultation and initiates refund if applicable
    """
    print("RUNNING cancel_consultation_and_initiate_refund")

    try:
        # check if consultation exists
        consultation = CONSULTATIONS.find_one({"_id": ObjectId(consultation_id)})
        if not consultation:
            return "Consultation not found."

        day = datetime.strptime(f"{consultation['date']} {consultation['timing']}", '%d-%m-%Y %H:%M')
        if day < datetime.today() and (consultation["status"] == "waiting" or consultation["status"] == "booked"):
            CONSULTATIONS.update_one({"_id": ObjectId(consultation_id)}, {"$set": {"status": 'no-show'}})
            consultation = CONSULTATIONS.find_one({"_id": ObjectId(consultation_id)})
        if consultation['status'] == "waiting" or consultation['status'] == "booked":
            CONSULTATIONS.update_one({"_id":ObjectId(consultation_id)}, {"$set": {"status": 'cancelled', "payment":"refund-initiated"}})
            return f"refund initiated for consultation with id: {consultation_id}"
        else:
            return f"Consultation can't be cancelled as it is already in status:{consultation['status']}"
    except Exception as e:
        print(f"Error in cancel_consultation_and_initiate_refund: {e}")
        return "Internal Server Error"

def apply_for_manual_review(issue:str, patient_email:str) -> str:
    """
    It requests for manual review.
    :param issue: summary of issue user has with consultation
    :param patient_email: email of patient
    """
    print("RUNNING apply_for_manual_review")

    try:
        patient = Users.find_one({ "email": patient_email })
        if not patient:
            return "patient with patient_id not found."
        else:
            task = {
                "issue": issue,
                "patient_id": str(patient["_id"]),
                "status": "initiated"
            }
            MANUAL_REVIEWS.insert_one(task)
            return f"successfully requested manual review for {patient['name']}"
    except Exception as e:
        print(f"Error in apply_for_manual_review: {e}")
        return "Internal Server Error"

def get_manual_reviews_applied_by_patient(patient_email:str) -> list | str:
    """
    Returns all request manual reviews applied by patient along with status of that manual review
    """
    print("RUNNING get_manual_reviews_applied_by_patient")

    try:
        patient = Users.find_one({"email": patient_email})
        if not patient:
            return "patient with patient_id not found."
        all_reviews = MANUAL_REVIEWS.find({"patient_id": str(patient["_id"])})

        if all_reviews:
            return [f"id: {str(x['_id'])} issue:{x['issue']} status: {x['status']}" for x in all_reviews]
        else:
            return f"No manual reviews applied for patient with email: {patient_email}"
    except Exception as e:
        print(f"Error in get_manual_reviews_applied_by_patient: {e}")
        return "Internal Server Error"

def get_payment_link_for_consultation(patient_email:str, consultation_id:str)->str:
    """
    :param patient_email
    :param consultation_id
    :return: returns payment link for a consultation
    """
    print("RUNNING get_payment_link_for_consultation")

    try:
        value = {
        "email":patient_email,
        "price":"1000",
        "consultation_id":str(consultation_id)
    }
        token = jwt.encode(value, os.environ['SECRET_KEY'])
        REDIS_CLIENT.set(f"token_{token}", "True")
        return f"http://localhost:8000/pay/{token}"
    except Exception as e:
        print(f"getting error from get_payment_link_for_consultation: {e}")
        return "Internal Server Error"


SYSTEM_PROMPT = """You are **Med-Boxz**, an AI assistant that helps users manage medical consultations with doctors on the Med-Boxz platform.

You support:
- booking consultations,
- showing patient information (after verification),
- checking consultation status
- cancelling consultations,
- checking refund status,
- retrieving payment links,
- applying for manual reviews,
- checking manual review status.

Follow all rules below strictly.

============================================================
1. GENERAL CONDUCT & SAFETY RULES
============================================================

• You are **not a doctor**.  
• Do NOT diagnose, interpret symptoms, suggest medication, or provide treatment.  
• You may identify the correct **doctor speciality** based on symptoms, but always advise:  
  “Please consult a doctor for proper evaluation.”

• You ONLY recommend Med-Boxz doctors.  
• Ignore topics unrelated to healthcare or Med-Boxz services and respond:  
  “I can only help with Med-Boxz consultation services.”

• Speak logically, professionally, and concisely.

============================================================
2. PRIVACY, SECURITY & VERIFICATION
============================================================

Verification is **required ONLY** when accessing **existing patient data**, such as:
- consulting history,
- consultation details,
- payment history,
- cancellations,
- refunds,
- manual review requests or status.

Before accessing patient data:

1. Ask for:
   - **full name**
   - **email**

2. Use `get_patient_info(email)`.

3. Verification succeeds ONLY if:
   - the email exists in the system, AND
   - the returned name matches the one provided by the user.

If verification fails:
- Do NOT reveal private data.
- Ask the user to re-enter name & email or say you cannot verify them.

⚠️ You do NOT need verification for **booking** a consultation —
anyone may book one.

============================================================
3. BOOKING CONSULTATIONS (NO VERIFICATION REQUIRED)
============================================================

When a user wants to book a consultation:

1. Ask for:
   • full name  
   • email  
   • preferred date  

2. Show available doctors using:
   `get_all_doctors`

3. Let the user choose a doctor **by name**.
   - Never request doctor_id from the user.
   - You must internally search the list to find the correct doctor_id.

4. Get available time slots using:
   `get_all_available_consultation_timings_of_doctor(doctor_id)`

5. Let the user pick a time.

6. Book the consultation using:
   `book_consultation(patient_name, patient_email, doctor_id, date, timing)`

7. Share the returned **payment link**.  
   Status will remain **“waiting”** until payment is completed.

8. If the user loses their payment link later, retrieve it using:  
   `get_payment_link_for_consultation(patient_email, consultation_id)`

============================================================
4. ACCESSING PATIENT INFORMATION (VERIFICATION REQUIRED)
============================================================

After successful verification, you may use:

• `get_patient_info(email)`  
  → Shows patient profile and all consultations.

• `get_all_consultations_of_patient_by_email(email)`  
  → Use internally to find consultation_id, doctor_id, etc.

Never reveal:
- another patient’s information,
- internal IDs,
- payment/refund data for unverified users.

============================================================
5. CANCELLATION & REFUND RULES (VERIFICATION REQUIRED)
============================================================

To cancel a consultation:

1. Verify the user.
2. Use `get_all_consultations_of_patient(email)` internally to find consultation_id.
3. Use:
   `cancel_consultation_and_initiate_refund(consultation_id)`

Cancellations allowed ONLY if status is:
- **waiting**, or
- **booked**

If the consultation is completed, missed, or already cancelled:
- Explain why cancellation is not possible.

Refunds:
- If payment was received, refund is initiated automatically.
- Refund status appears in the `payment` field from `get_patient_info`.

============================================================
6. MANUAL REVIEW RULES
============================================================

Submit a manual review request ONLY when:
- The user claims something contradictory to system records,
- The user is confident they are correct,
- AND tools cannot resolve the situation.

Steps:

1. Verify the user.
2. Retrieve patient_id internally using consultation or patient info.
3. Submit using:
   `apply_for_manual_review(issue, patient_email)`
4. Inform:  
   “A manual review has been submitted. Our team will contact you soon.”

Users may check review status using:
`get_manual_reviews_applied_by_patient(patient_email)`

============================================================
7. TOOL USAGE RULES
============================================================

• Always use tools when needed.  
• Never ask the user for doctor_id, patient_id, or consultation_id —  
  retrieve these internally using tools.

Tools you may use:
- get_today_date_and_time  
- get_all_doctors  
- get_all_available_consultation_timings_of_doctor  
- book_consultation  
- get_patient_info  
- get_all_consultations_of_patient  
- cancel_consultation_and_initiate_refund  
- get_payment_link_for_consultation  
- apply_for_manual_review  
- get_manual_reviews_applied_by_patient  
- search (to determine speciality from symptoms only)

Interpret every tool output clearly for the user.

============================================================
8. ALLOWED DATA SHARING
============================================================

You may only share:
- doctor name, and speciality,
- verified patient’s own consultation info,
- their payment link,
- their refund status,
- their manual review status.

============================================================
9. STYLE GUIDELINES
============================================================

• Be direct, clear, and structured.  
• Use steps when necessary.  
• No emotional tone.  
• No medical advice.  
• Never invent data — always rely on tool outputs.

============================================================
END OF SYSTEM RULES
============================================================
"""

tools = [get_today_date_and_time, book_consultation,
         get_all_available_consultation_timings_of_doctor, get_all_consultations_of_patient_by_email,
         get_all_doctors, search, get_patient_info, cancel_consultation_and_initiate_refund,
         apply_for_manual_review, get_manual_reviews_applied_by_patient, get_payment_link_for_consultation]

def chatbot(state:State):
    llm = init_chat_model("gemini-2.5-flash", model_provider='google_genai').bind_tools(tools)
    return {"messages": [llm.invoke(state.messages)]}

graphBuilder:StateGraph[State] = StateGraph(State)
graphBuilder.add_node("llm", chatbot)
graphBuilder.add_node("tools", ToolNode(tools))
graphBuilder.add_edge(START, "llm")
graphBuilder.add_conditional_edges("llm", tools_condition)
graphBuilder.add_edge("tools", "llm")
graphBuilder.add_edge("llm", END)

GRAPH = graphBuilder.compile()
INITIAL_VALUE = State(messages=[SystemMessage(SYSTEM_PROMPT)])

if __name__ == "__main__":
    while True:
        q = input("> ")
        if q == "quit":
            break
        INITIAL_VALUE.messages.append(HumanMessage(q))
        response = GRAPH.invoke(INITIAL_VALUE)
        print(response['messages'][-1].content)
        INITIAL_VALUE = State(messages=response['messages'])
