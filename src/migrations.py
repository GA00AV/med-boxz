from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

doctors = [
  {
    "name": "Dr. Arjun Mehta",
    "email": "arjun.mehta@medboxz.in",
    "role": "doctor",
    "speciality": "Cardiologist"
  },
  {
    "name": "Dr. Kavya Iyer",
    "email": "kavya.iyer@medboxz.in",
    "role": "doctor",
    "speciality": "Dermatologist"
  },
  {
    "name": "Dr. Rohan Sharma",
    "email": "rohan.sharma@medboxz.in",
    "role": "doctor",
    "speciality": "Orthopedic Surgeon"
  },
  {
    "name": "Dr. Priya Narang",
    "email": "priya.narang@medboxz.in",
    "role": "doctor",
    "speciality": "Pediatrician"
  },
  {
    "name": "Dr. Aditya Verma",
    "email": "aditya.verma@medboxz.in",
    "role": "doctor",
    "speciality": "ENT Specialist"
  },
  {
    "name": "Dr. Sneha Kulkarni",
    "email": "sneha.kulkarni@medboxz.in",
    "role": "doctor",
    "speciality": "Gynecologist"
  },
  {
    "name": "Dr. Manish Patil",
    "email": "manish.patil@medboxz.in",
    "role": "doctor",
    "speciality": "Neurologist"
  },
  {
    "name": "Dr. Ritu Sinha",
    "email": "ritu.sinha@medboxz.in",
    "role": "doctor",
    "speciality": "Psychiatrist"
  },
  {
    "name": "Dr. Devansh Rao",
    "email": "devansh.rao@medboxz.in",
    "role": "doctor",
    "speciality": "General Physician"
  },
  {
    "name": "Dr. Aishwarya Nair",
    "email": "aishwarya.nair@medboxz.in",
    "role": "doctor",
    "speciality": "Ophthalmologist"
  },
  {
    "name": "Dr. Nikhil Reddy",
    "email": "nikhil.reddy@medboxz.in",
    "role": "doctor",
    "speciality": "Urologist"
  },
  {
    "name": "Dr. Meera Krishnan",
    "email": "meera.krishnan@medboxz.in",
    "role": "doctor",
    "speciality": "Endocrinologist"
  },
  {
    "name": "Dr. Sanjay Gupta",
    "email": "sanjay.gupta@medboxz.in",
    "role": "doctor",
    "speciality": "Oncologist"
  },
  {
    "name": "Dr. Ishita Deshpande",
    "email": "ishita.deshpande@medboxz.in",
    "role": "doctor",
    "speciality": "Physiotherapist"
  },
  {
    "name": "Dr. Varun Chatterjee",
    "email": "varun.chatterjee@medboxz.in",
    "role": "doctor",
    "speciality": "Gastroenterologist"
  },
  {
    "name": "Dr. Deepika Banerjee",
    "email": "deepika.banerjee@medboxz.in",
    "role": "doctor",
    "speciality": "Radiologist"
  },
  {
    "name": "Dr. Karan Singh",
    "email": "karan.singh@medboxz.in",
    "role": "doctor",
    "speciality": "Pulmonologist"
  },
  {
    "name": "Dr. Neha Bhat",
    "email": "neha.bhat@medboxz.in",
    "role": "doctor",
    "speciality": "Nutritionist"
  },
  {
    "name": "Dr. Abhay Kulshreshtha",
    "email": "abhay.kulshreshtha@medboxz.in",
    "role": "doctor",
    "speciality": "Nephrologist"
  },
  {
    "name": "Dr. Shalini Menon",
    "email": "shalini.menon@medboxz.in",
    "role": "doctor",
    "speciality": "Rheumatologist"
  }
]


client = MongoClient(os.environ['MONGO_URI'])
database = client[os.environ["DB_NAME"]]
Users = database[os.environ["USER_COLLECTION"]]
Users.insert_many(doctors)
print("MIGRATIONS SUCCESSFUL")