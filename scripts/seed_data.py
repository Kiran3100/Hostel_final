"""
StayEase - Complete Seed Data Script
Run: python -m scripts.seed_data  (from hostel-management-api/)
Populates: users, hostels, rooms, beds, bookings, students, payments,
           mess menus (full 7-day × 4-meal), notices, complaints,
           attendance, maintenance, reviews, subscriptions, images.
"""
import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta, time

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.database import Base
from app.core.security import hash_password
from app.models.booking import (
    BedStay, BedStayStatus, Booking, BookingMode,
    BookingStatus, BookingStatusHistory, Inquiry,
)
from app.models.hostel import (
    AdminHostelMapping, Hostel, HostelAmenity,
    HostelImage, HostelStatus, SupervisorHostelMapping,
)
from app.models.operations import (
    AttendanceRecord, Complaint, ComplaintComment,
    MaintenanceRequest, MessMenu, MessMenuItem,
    Notice, Review, Subscription,
)

# Import employee data from separate file (63 Levitica employees)
from scripts.employee_data import (
    EMPLOYEE_DATA, STUDENT_NAMES, EMPLOYEE_CODE_MAP,
    emp_phone as _emp_phone,
)
from app.models.payment import Payment
from app.models.room import Bed, BedStatus, Room, RoomType
from app.models.student import Student, StudentStatus
from app.models.user import User, UserRole

settings = get_settings()

# ---------------------------------------------------------------------------
# Realistic Unsplash image URLs (free, no auth needed)
# ---------------------------------------------------------------------------
HOSTEL_IMAGES = {
    "Green Valley Boys Hostel": [
        "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=800",
        "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800",
    ],
    "Pearl Girls Hostel": [
        "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800",
        "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=800",
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800",
    ],
    "Sunrise Co-ed Hostel": [
        "https://images.unsplash.com/photo-1564078516393-cf04bd966897?w=800",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
    ],
    "Metro Stay Hostel": [
        "https://images.unsplash.com/photo-1571508601891-ca5e7a713859?w=800",
        "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=800",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800",
    ],
}

# ---------------------------------------------------------------------------
# Full 7-day × 4-meal mess menu data (realistic Indian hostel food)
# ---------------------------------------------------------------------------
MESS_MENU = [
    # (day, meal_type, item_name, is_veg, special_note)
    # Monday
    ("Monday", "breakfast", "Idli Sambar with Coconut Chutney", True, None),
    ("Monday", "lunch", "Steamed Rice, Dal Tadka, Aloo Gobi, Papad", True, None),
    ("Monday", "snacks", "Bread Pakora with Mint Chutney", True, None),
    ("Monday", "dinner", "Chapati, Paneer Butter Masala, Jeera Rice, Salad", True, None),
    # Tuesday
    ("Tuesday", "breakfast", "Poha with Sev and Lemon", True, None),
    ("Tuesday", "lunch", "Chicken Biryani, Raita, Boiled Egg", False, "Non-veg day"),
    ("Tuesday", "snacks", "Samosa with Tamarind Chutney", True, None),
    ("Tuesday", "dinner", "Roti, Dal Makhani, Bhindi Fry, Rice", True, None),
    # Wednesday
    ("Wednesday", "breakfast", "Upma with Coconut Chutney", True, None),
    ("Wednesday", "lunch", "Rice, Rajma Masala, Cucumber Raita, Pickle", True, None),
    ("Wednesday", "snacks", "Veg Cutlet with Ketchup", True, None),
    ("Wednesday", "dinner", "Chapati, Egg Curry, Steamed Rice, Salad", False, "Egg available"),
    # Thursday
    ("Thursday", "breakfast", "Dosa with Sambar and Chutney", True, None),
    ("Thursday", "lunch", "Mutton Curry, Rice, Dal, Papad", False, "Non-veg day"),
    ("Thursday", "snacks", "Pav Bhaji", True, None),
    ("Thursday", "dinner", "Roti, Chana Masala, Jeera Rice, Curd", True, None),
    # Friday
    ("Friday", "breakfast", "Aloo Paratha with Curd and Pickle", True, None),
    ("Friday", "lunch", "Veg Pulao, Raita, Mixed Veg Curry, Papad", True, None),
    ("Friday", "snacks", "Maggi Noodles", True, "Special Friday snack"),
    ("Friday", "dinner", "Chapati, Fish Curry, Rice, Salad", False, "Fish Friday"),
    # Saturday
    ("Saturday", "breakfast", "Chole Bhature", True, "Weekend special"),
    ("Saturday", "lunch", "Chicken Fried Rice, Manchurian, Soup", False, "Weekend special"),
    ("Saturday", "snacks", "Fruit Chaat", True, None),
    ("Saturday", "dinner", "Biryani, Raita, Mirchi Ka Salan, Dessert", False, "Weekend feast"),
    # Sunday
    ("Sunday", "breakfast", "Puri Sabzi with Halwa", True, "Sunday special"),
    ("Sunday", "lunch", "Dal Baati Churma", True, "Rajasthani special"),
    ("Sunday", "snacks", "Ice Cream / Kulfi", True, "Sunday treat"),
    ("Sunday", "dinner", "Paneer Tikka Masala, Naan, Rice, Kheer", True, "Sunday feast"),
]

# ---------------------------------------------------------------------------
# Hostel configurations
# ---------------------------------------------------------------------------
HOSTELS_CONFIG = [
    {
        "name": "Green Valley Boys Hostel",
        "slug": "green-valley-boys-hostel",
        "city": "Hyderabad",
        "state": "Telangana",
        "hostel_type": "boys",
        "description": (
            "Green Valley Boys Hostel is a premium accommodation for male students and "
            "working professionals in the heart of Hyderabad. Surrounded by lush greenery, "
            "we offer a peaceful environment with all modern amenities. Our 24/7 security, "
            "high-speed WiFi, and nutritious mess food make us the top choice for students "
            "from JNTU, Osmania University, and nearby IT companies."
        ),
        "address_line1": "Plot 45, Green Valley Road, Madhapur",
        "address_line2": "Near Hitech City Metro Station",
        "pincode": "500081",
        "latitude": 17.4474,
        "longitude": 78.3762,
        "phone": "+91-9876543210",
        "email": "greenvalley@stayease.in",
        "website": "https://greenvalley.stayease.in",
        "rules": (
            "1. Visitors allowed only in common areas between 9 AM - 8 PM.\n"
            "2. No smoking or alcohol on premises.\n"
            "3. Lights out by 11 PM on weekdays.\n"
            "4. Mess timings: Breakfast 7-9 AM, Lunch 12-2 PM, Snacks 5-6 PM, Dinner 8-10 PM.\n"
            "5. Laundry service available on Sundays.\n"
            "6. ID proof mandatory at entry for all visitors."
        ),
        "is_featured": True,
        "amenities": [
            ("WiFi", "connectivity"), ("Study Room", "facilities"),
            ("Laundry", "facilities"), ("Gym", "facilities"),
            ("CCTV", "safety"), ("Security Guard", "safety"),
            ("Parking", "facilities"), ("Power Backup", "utilities"),
            ("RO Water", "utilities"), ("Housekeeping", "services"),
        ],
        "rooms": [
            {"number": "101", "floor": 1, "type": "single", "beds": 1, "daily": 900, "monthly": 8500, "deposit": 8500, "dim": "12x10 ft"},
            {"number": "102", "floor": 1, "type": "double", "beds": 2, "daily": 700, "monthly": 6500, "deposit": 6500, "dim": "14x12 ft"},
            {"number": "103", "floor": 1, "type": "double", "beds": 2, "daily": 700, "monthly": 6500, "deposit": 6500, "dim": "14x12 ft"},
            {"number": "201", "floor": 2, "type": "triple", "beds": 3, "daily": 600, "monthly": 5500, "deposit": 5500, "dim": "16x14 ft"},
            {"number": "202", "floor": 2, "type": "triple", "beds": 3, "daily": 600, "monthly": 5500, "deposit": 5500, "dim": "16x14 ft"},
            {"number": "203", "floor": 2, "type": "dormitory", "beds": 6, "daily": 400, "monthly": 3500, "deposit": 3500, "dim": "20x18 ft"},
            {"number": "301", "floor": 3, "type": "single", "beds": 1, "daily": 950, "monthly": 9000, "deposit": 9000, "dim": "12x10 ft"},
            {"number": "302", "floor": 3, "type": "double", "beds": 2, "daily": 750, "monthly": 7000, "deposit": 7000, "dim": "14x12 ft"},
        ],
    },
    {
        "name": "Pearl Girls Hostel",
        "slug": "pearl-girls-hostel",
        "city": "Bangalore",
        "state": "Karnataka",
        "hostel_type": "girls",
        "description": (
            "Pearl Girls Hostel is a safe, comfortable, and well-managed accommodation "
            "exclusively for women in Bangalore. Located in Koramangala, we are minutes "
            "away from major IT parks, colleges, and shopping centers. Our all-female staff, "
            "biometric entry, and CCTV surveillance ensure maximum safety. We offer "
            "home-cooked meals, a reading room, and a rooftop garden."
        ),
        "address_line1": "12/3, 5th Block, Koramangala",
        "address_line2": "Near Forum Mall, Bangalore",
        "pincode": "560095",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "phone": "+91-9876543211",
        "email": "pearl@stayease.in",
        "website": "https://pearl.stayease.in",
        "rules": (
            "1. Male visitors strictly not allowed beyond reception.\n"
            "2. Gate closes at 10 PM. Late entry requires prior permission.\n"
            "3. No cooking in rooms. Use common kitchen only.\n"
            "4. Mess timings: Breakfast 7-9 AM, Lunch 12-2 PM, Snacks 5-6 PM, Dinner 8-10 PM.\n"
            "5. Maintain cleanliness in common areas.\n"
            "6. Report any issues to warden immediately."
        ),
        "is_featured": True,
        "amenities": [
            ("WiFi", "connectivity"), ("Reading Room", "facilities"),
            ("Laundry", "facilities"), ("Rooftop Garden", "recreation"),
            ("CCTV", "safety"), ("Biometric Entry", "safety"),
            ("Power Backup", "utilities"), ("RO Water", "utilities"),
            ("Housekeeping", "services"), ("Wardrobe", "furniture"),
        ],
        "rooms": [
            {"number": "A101", "floor": 1, "type": "single", "beds": 1, "daily": 1000, "monthly": 9500, "deposit": 9500, "dim": "12x10 ft"},
            {"number": "A102", "floor": 1, "type": "double", "beds": 2, "daily": 800, "monthly": 7500, "deposit": 7500, "dim": "14x12 ft"},
            {"number": "A103", "floor": 1, "type": "double", "beds": 2, "daily": 800, "monthly": 7500, "deposit": 7500, "dim": "14x12 ft"},
            {"number": "B201", "floor": 2, "type": "triple", "beds": 3, "daily": 650, "monthly": 6000, "deposit": 6000, "dim": "16x14 ft"},
            {"number": "B202", "floor": 2, "type": "triple", "beds": 3, "daily": 650, "monthly": 6000, "deposit": 6000, "dim": "16x14 ft"},
            {"number": "C301", "floor": 3, "type": "single", "beds": 1, "daily": 1050, "monthly": 10000, "deposit": 10000, "dim": "12x10 ft"},
            {"number": "C302", "floor": 3, "type": "dormitory", "beds": 4, "daily": 450, "monthly": 4000, "deposit": 4000, "dim": "18x16 ft"},
        ],
    },
    {
        "name": "Sunrise Co-ed Hostel",
        "slug": "sunrise-co-ed-hostel",
        "city": "Pune",
        "state": "Maharashtra",
        "hostel_type": "coed",
        "description": (
            "Sunrise Co-ed Hostel is a modern, vibrant accommodation for students and "
            "young professionals in Pune. Located in Kothrud, we offer separate floors "
            "for male and female residents with shared common areas. Our hostel features "
            "a fully equipped gym, indoor games room, and a rooftop terrace. Perfect for "
            "students from Pune University, COEP, and nearby IT companies."
        ),
        "address_line1": "Survey No. 78, Kothrud",
        "address_line2": "Near Kothrud Bus Stand, Pune",
        "pincode": "411038",
        "latitude": 18.5074,
        "longitude": 73.8077,
        "phone": "+91-9876543212",
        "email": "sunrise@stayease.in",
        "website": "https://sunrise.stayease.in",
        "rules": (
            "1. Separate floors for male and female residents.\n"
            "2. Common areas accessible to all residents.\n"
            "3. No alcohol or drugs on premises.\n"
            "4. Mess timings: Breakfast 7-9 AM, Lunch 12-2 PM, Snacks 5-6 PM, Dinner 8-10 PM.\n"
            "5. Gym available 6 AM - 10 PM.\n"
            "6. Guests must register at reception."
        ),
        "is_featured": True,
        "amenities": [
            ("WiFi", "connectivity"), ("Gym", "recreation"),
            ("Indoor Games", "recreation"), ("Rooftop Terrace", "recreation"),
            ("Laundry", "facilities"), ("CCTV", "safety"),
            ("Power Backup", "utilities"), ("RO Water", "utilities"),
            ("Cafeteria", "food"), ("Study Hall", "facilities"),
        ],
        "rooms": [
            {"number": "M101", "floor": 1, "type": "single", "beds": 1, "daily": 850, "monthly": 8000, "deposit": 8000, "dim": "12x10 ft"},
            {"number": "M102", "floor": 1, "type": "double", "beds": 2, "daily": 650, "monthly": 6000, "deposit": 6000, "dim": "14x12 ft"},
            {"number": "M201", "floor": 2, "type": "triple", "beds": 3, "daily": 550, "monthly": 5000, "deposit": 5000, "dim": "16x14 ft"},
            {"number": "M202", "floor": 2, "type": "dormitory", "beds": 6, "daily": 380, "monthly": 3200, "deposit": 3200, "dim": "20x18 ft"},
            {"number": "F301", "floor": 3, "type": "single", "beds": 1, "daily": 900, "monthly": 8500, "deposit": 8500, "dim": "12x10 ft"},
            {"number": "F302", "floor": 3, "type": "double", "beds": 2, "daily": 700, "monthly": 6500, "deposit": 6500, "dim": "14x12 ft"},
            {"number": "F303", "floor": 3, "type": "triple", "beds": 3, "daily": 580, "monthly": 5200, "deposit": 5200, "dim": "16x14 ft"},
        ],
    },
    {
        "name": "Metro Stay Hostel",
        "slug": "metro-stay-hostel",
        "city": "Mumbai",
        "state": "Maharashtra",
        "hostel_type": "coed",
        "description": (
            "Metro Stay Hostel is a premium co-ed hostel in the heart of Mumbai, "
            "offering unmatched connectivity and comfort. Located in Andheri West, "
            "we are a 5-minute walk from the metro station and close to BKC, "
            "Bandra, and major corporate offices. Our hostel offers AC rooms, "
            "a fully equipped kitchen, and a vibrant community of young professionals."
        ),
        "address_line1": "14, Versova Road, Andheri West",
        "address_line2": "Near Andheri Metro Station, Mumbai",
        "pincode": "400058",
        "latitude": 19.1136,
        "longitude": 72.8697,
        "phone": "+91-9876543213",
        "email": "metro@stayease.in",
        "website": "https://metro.stayease.in",
        "rules": (
            "1. AC rooms — do not tamper with AC settings.\n"
            "2. Gate closes at 11 PM. Late entry via security intercom.\n"
            "3. No cooking in rooms. Use common kitchen.\n"
            "4. Mess timings: Breakfast 7-9 AM, Lunch 12-2 PM, Snacks 5-6 PM, Dinner 8-10 PM.\n"
            "5. Maintain silence after 11 PM.\n"
            "6. Parking available for 2-wheelers only."
        ),
        "is_featured": False,
        "amenities": [
            ("WiFi", "connectivity"), ("AC Rooms", "comfort"),
            ("Common Kitchen", "facilities"), ("Laundry", "facilities"),
            ("CCTV", "safety"), ("Security Guard", "safety"),
            ("Power Backup", "utilities"), ("RO Water", "utilities"),
            ("Elevator", "facilities"), ("Parking", "facilities"),
        ],
        "rooms": [
            {"number": "101", "floor": 1, "type": "single", "beds": 1, "daily": 1200, "monthly": 12000, "deposit": 12000, "dim": "12x10 ft"},
            {"number": "102", "floor": 1, "type": "double", "beds": 2, "daily": 950, "monthly": 9000, "deposit": 9000, "dim": "14x12 ft"},
            {"number": "201", "floor": 2, "type": "single", "beds": 1, "daily": 1300, "monthly": 13000, "deposit": 13000, "dim": "12x10 ft"},
            {"number": "202", "floor": 2, "type": "double", "beds": 2, "daily": 1000, "monthly": 9500, "deposit": 9500, "dim": "14x12 ft"},
            {"number": "203", "floor": 2, "type": "triple", "beds": 3, "daily": 800, "monthly": 7500, "deposit": 7500, "dim": "16x14 ft"},
            {"number": "301", "floor": 3, "type": "dormitory", "beds": 5, "daily": 550, "monthly": 5000, "deposit": 5000, "dim": "20x18 ft"},
        ],
    },
]

# ---------------------------------------------------------------------------
# Student / visitor names
# ---------------------------------------------------------------------------
# ── Generated from Employee_Register.xlsx (Levitica Technologies) ──────────
# Format: (full_name, email_prefix)
# Employee codes LEV001–LEV128 mapped to student numbers STU-LEV001 etc.
# Team leads become supervisors; remaining employees become students.
EMPLOYEE_DATA = [
    # (employee_code, full_name, team_lead)
    ("LEV029", "Abhilash Gurrampally",                  "Mani Kiran Kopanathi"),
    ("LEV039", "Anusha Enigalla",                        "Durgaprasad Medipudi"),
    ("LEV122", "Aravelly Tharun",                        "Anusha Enigalla"),
    ("LEV047", "Ashok Kota",                             "Sameer Shaik"),
    ("LEV121", "Baluguri Ashritha Rao",                  "Durgaprasad Medipudi"),
    ("LEV116", "Bhargava Sai Kolli",                     "Kallamadi Kranti Kumar Reddy"),
    ("LEV027", "Bogala Chandramouli",                    "Durgaprasad Medipudi"),
    ("LEV023", "Burri Gowtham",                          "Mani Kiran Kopanathi"),
    ("LEV001", "Chandu Thota",                           "Durgaprasad Medipudi"),
    ("LEV038", "Cheekati Abhinaya",                      "Durgaprasad Medipudi"),
    ("LEV014", "Chodisetti Sri Rama Sai",                "Mani Kiran Kopanathi"),
    ("LEV123", "Dhanikela Brahmam",                      "Anusha Enigalla"),
    ("LEV012", "Dheeraj Krishna Jakkula",                "Mani Kiran Kopanathi"),
    ("LEV028", "Dorasala Nagendra Reddy",                "Mani Kiran Kopanathi"),
    ("LEV017", "Dubbaka Bharath",                        "Sameer Shaik"),
    ("LEV026", "Durga Sai Vara Prasad Chandragiri",      "Durgaprasad Medipudi"),
    ("LEV031", "Gorle Leela Sai Kumar",                  "Durgaprasad Medipudi"),
    ("LEV127", "Gubba Vasini",                           "Anusha Enigalla"),
    ("LEV005", "Gurajapu Pavani",                        "Nagendra Uggirala"),
    ("LEV118", "Hari Charan Teja Gudapati",              "Anusha Enigalla"),
    ("LEV050", "Harsha Vardhan Naidu Dasireddy",         "Kallamadi Kranti Kumar Reddy"),
    ("LEV044", "Hemant Tukaram Pawade",                  "Mani Kiran Kopanathi"),
    ("LEV008", "Hruthik Venkata Sai Ganesh Jamanu",      "Chandu Thota"),
    ("LEV033", "Jagadeesh Bedolla",                      "Sameer Shaik"),
    ("LEV128", "Jothi Lakshmi A",                        "Anusha Enigalla"),
    ("LEV013", "Kallamadi Kowsik Reddy",                 "Durgaprasad Medipudi"),
    ("LEV011", "Kallamadi Kranti Kumar Reddy",           "Durgaprasad Medipudi"),
    ("LEV004", "Kallamadi Keerthi",                      "Nagendra Uggirala"),
    ("LEV003", "Kandepuneni Swetha Naga Durga",          "Chandu Thota"),
    ("LEV036", "Kasarapu Rajeswar Reddy",                "Sameer Shaik"),
    ("LEV019", "Keerthi Ranjani Maddala",                "Sameer Shaik"),
    ("LEV032", "Khuswanth Rao Jadav",                    "Sameer Shaik"),
    ("LEV034", "Kishore Tiruveedhula",                   "Mani Kiran Kopanathi"),
    ("LEV046", "Kondareddy Revathi",                     "Sameer Shaik"),
    ("LEV126", "Korada Kavya",                           "Anusha Enigalla"),
    ("LEV035", "Kothapalli Sai Avinash Varma",           "Mani Kiran Kopanathi"),
    ("LEV048", "Lokeshwar Reddy Kondappagari",           "Kallamadi Kranti Kumar Reddy"),
    ("LEV010", "Mani Kiran Kopanathi",                   "Durgaprasad Medipudi"),
    ("LEV041", "Manikanta Nedunuri",                     "Mani Kiran Kopanathi"),
    ("LEV120", "Medipudi Durgaprasad",                   None),
    ("LEV002", "Minal Devidas Mahajan",                  "Durgaprasad Medipudi"),
    ("LEV041", "Mohammad Aslam Yakub Khan",              "Durgaprasad Medipudi"),
    ("LEV042", "Muniganti Sai Sumiran",                  "Sameer Shaik"),
    ("LEV117", "N Sairam Srinivasa Chakravarthi Pothureddy", "Kallamadi Kranti Kumar Reddy"),
    ("LEV040", "Nagadurga Sarnala",                      "Mani Kiran Kopanathi"),
    ("LEV024", "Nagendra Uggirala",                      "Durgaprasad Medipudi"),
    ("LEV015", "Nani Venkata Ravi Teja Maddala",         "Sameer Shaik"),
    ("LEV022", "Naveen Sai Koppereddy",                  "Nagendra Uggirala"),
    ("LEV025", "Nollu Lalith Kumar",                     "Sameer Shaik"),
    ("LEV021", "Pagadala Anitha",                        "Sameer Shaik"),
    ("LEV018", "Peddireddy Sai Kumar Reddy",             "Sameer Shaik"),
    ("LEV037", "Pesaru Kireeti",                         "Sameer Shaik"),
    ("LEV049", "Pillala Sukanya",                        "Kallamadi Kranti Kumar Reddy"),
    ("LEV006", "Potnuri Naveen Bhargav",                 "Chandu Thota"),
    ("LEV051", "Pradeep Bantapalli",                     "Kallamadi Kranti Kumar Reddy"),
    ("LEV016", "Pramod Kumar Sindhe",                    "Sameer Shaik"),
    ("LEV009", "Sameer Shaik",                           "Durgaprasad Medipudi"),
    ("LEV030", "Sasi Kumar Reddy Chintala",              "Mani Kiran Kopanathi"),
    ("LEV043", "Satya Kiran Chelluboina",                "Mani Kiran Kopanathi"),
    ("LEV124", "Sumathi Mittapalli",                     "Anusha Enigalla"),
    ("LEV007", "Syed Afran Ali",                         "Chandu Thota"),
    ("LEV119", "Vamshi Hasanabada",                      "Kallamadi Kranti Kumar Reddy"),
    ("LEV125", "Vijay Ram Maddukuri",                    "Anusha Enigalla"),
]


def _emp_email_prefix(name: str, code: str) -> str:
    """Generate email prefix from name + employee code."""
    parts = name.lower().split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}.{code.lower()}"
    return f"{parts[0]}.{code.lower()}"


def _emp_phone(code: str) -> str:
    """Generate a deterministic phone from employee code number — offset by 8000000000 to avoid conflicts."""
    num = int(code[3:]) if code[3:].isdigit() else 0
    # Use 8xxxxxxxxx range (distinct from 9xxxxxxxxx used by system accounts)
    return f"+91-8{num:09d}"


# Build STUDENT_NAMES from employee data (all 63 employees as students)
STUDENT_NAMES = [
    (emp[1], _emp_email_prefix(emp[1], emp[0]))
    for emp in EMPLOYEE_DATA
]

# Keep original visitor names for booking demo data
VISITOR_NAMES = [
    ("Arun Kapoor", "arun.kapoor"), ("Sunita Bose", "sunita.bose"),
    ("Manoj Yadav", "manoj.yadav"), ("Rekha Mishra", "rekha.mishra"),
    ("Tarun Saxena", "tarun.saxena"), ("Geeta Pandey", "geeta.pandey"),
    ("Harish Nambiar", "harish.nambiar"), ("Swati Kulkarni", "swati.kulkarni"),
    ("Rajesh Dubey", "rajesh.dubey"), ("Anjali Sinha", "anjali.sinha"),
]

# Employee code → student number mapping (for student_number field)
EMPLOYEE_CODE_MAP = {emp[1]: emp[0] for emp in EMPLOYEE_DATA}
EMPLOYEE_LEAD_MAP = {emp[1]: emp[2] for emp in EMPLOYEE_DATA}

COMPLAINT_DATA = [
    ("maintenance", "Water leakage in bathroom", "There is a continuous water leakage from the bathroom tap. It has been going on for 3 days and wasting a lot of water.", "high"),
    ("food", "Mess food quality declined", "The quality of food in the mess has significantly declined over the past week. The dal is undercooked and vegetables are not fresh.", "medium"),
    ("electricity", "Power socket not working", "The power socket near my bed (Bed 2, Room 201) is not working. I cannot charge my laptop.", "medium"),
    ("cleanliness", "Common bathroom not cleaned", "The common bathroom on floor 2 has not been cleaned for 2 days. It is unhygienic.", "high"),
    ("wifi", "WiFi speed very slow", "The WiFi speed has been extremely slow for the past week. I cannot attend online classes properly.", "low"),
    ("security", "Main gate left open at night", "The main gate was found open at 2 AM last night. This is a serious security concern.", "high"),
    ("noise", "Loud music from room 302", "Residents in room 302 play loud music after 11 PM regularly, disturbing others.", "medium"),
    ("maintenance", "Ceiling fan making noise", "The ceiling fan in room 103 makes a loud rattling noise. Please fix it.", "low"),
]

NOTICE_DATA = [
    ("Mess Menu Update - Week of March 27", "Dear residents, please note the updated mess menu for this week. Special Sunday feast includes Biryani and Kheer. Mess timings remain unchanged.", "general", "medium"),
    ("Water Supply Interruption - Sunday 6 AM to 10 AM", "Due to maintenance work, water supply will be interrupted on Sunday from 6 AM to 10 AM. Please store water accordingly.", "maintenance", "high"),
    ("Hostel Day Celebration - April 5th", "We are celebrating Hostel Day on April 5th! Events include cultural programs, sports, and a special dinner. All residents are invited.", "event", "medium"),
    ("Visitor Policy Reminder", "Reminder: Visitors are allowed only in common areas between 9 AM and 8 PM. All visitors must register at the reception desk.", "policy", "medium"),
    ("Laundry Service Schedule Change", "Starting next week, laundry service will be available on both Saturday and Sunday (previously only Sunday). Charges remain the same.", "general", "low"),
    ("Fire Safety Drill - April 10th", "A mandatory fire safety drill will be conducted on April 10th at 10 AM. All residents must participate. Assembly point: Main gate.", "safety", "high"),
    ("Internet Upgrade Complete", "We have upgraded our internet connection to 200 Mbps fiber. You should experience significantly faster speeds now.", "general", "low"),
    ("Rent Due Reminder - April 1st", "Monthly rent for April is due on April 1st. Please pay at the reception or via online transfer. Late payment attracts a penalty of Rs. 100/day.", "payment", "high"),
]

MAINTENANCE_DATA = [
    ("plumbing", "Bathroom pipe burst in Room 201", "The main water pipe in the bathroom of Room 201 has burst. Water is leaking onto the floor.", "emergency", True),
    ("electrical", "Short circuit in corridor lights", "The corridor lights on floor 2 have a short circuit. They flicker and sometimes go off completely.", "high", True),
    ("carpentry", "Broken door hinge in Room 103", "The door hinge in Room 103 is broken. The door does not close properly.", "medium", False),
    ("painting", "Wall paint peeling in Room 302", "The wall paint in Room 302 is peeling off. It looks unhygienic and needs repainting.", "low", False),
    ("plumbing", "Clogged drain in common bathroom", "The drain in the common bathroom on floor 1 is clogged. Water is not draining properly.", "high", False),
    ("electrical", "AC not cooling in Room 201", "The AC in Room 201 is not cooling properly. Temperature stays at 28°C even at lowest setting.", "medium", True),
]

# Visitor names for booking demo data
VISITOR_NAMES = [
    ("Arun Kapoor", "arun.kapoor"), ("Sunita Bose", "sunita.bose"),
    ("Manoj Yadav", "manoj.yadav"), ("Rekha Mishra", "rekha.mishra"),
    ("Tarun Saxena", "tarun.saxena"), ("Geeta Pandey", "geeta.pandey"),
    ("Harish Nambiar", "harish.nambiar"), ("Swati Kulkarni", "swati.kulkarni"),
    ("Rajesh Dubey", "rajesh.dubey"), ("Anjali Sinha", "anjali.sinha"),
]

# ---------------------------------------------------------------------------
# Seeder class
# ---------------------------------------------------------------------------
class StayEaseSeeder:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users: dict[str, str] = {}       # email -> id
        self.hostels: dict[str, str] = {}     # name -> id
        self.rooms: dict[str, dict] = {}      # room_id -> {hostel_id, room_id}
        self.beds: dict[str, dict] = {}       # bed_id -> {hostel_id, room_id, bed_id}
        self.students: dict[str, str] = {}    # user_id -> student_id
        self.bookings: list[Booking] = []

    # ------------------------------------------------------------------
    def _uid(self) -> uuid.UUID:
        return uuid.uuid4()

    async def _flush(self):
        await self.session.flush()

    # ------------------------------------------------------------------
    async def create_user(self, email: str, phone: str, full_name: str,
                          role: UserRole, password: str = "Test@1234") -> str:
        user = User(
            id=self._uid(), email=email, phone=phone, full_name=full_name,
            password_hash=hash_password(password), role=role,
            is_active=True, is_email_verified=True, is_phone_verified=True,
        )
        self.session.add(user)
        await self._flush()
        self.users[email] = user.id
        print(f"  ✓ {role.value:15s} {full_name} ({email})")
        return user.id

    # ------------------------------------------------------------------
    async def create_hostel(self, cfg: dict, admin_id: str,
                            supervisor_id: str) -> str:
        hostel = Hostel(
            id=self._uid(),
            name=cfg["name"], slug=cfg["slug"],
            description=cfg["description"],
            hostel_type=cfg["hostel_type"],
            status=HostelStatus.ACTIVE,
            address_line1=cfg["address_line1"],
            address_line2=cfg["address_line2"],
            city=cfg["city"], state=cfg["state"],
            country="India", pincode=cfg["pincode"],
            latitude=cfg["latitude"], longitude=cfg["longitude"],
            phone=cfg["phone"], email=cfg["email"],
            website=cfg.get("website"),
            is_featured=cfg.get("is_featured", False),
            is_public=True,
            rules_and_regulations=cfg["rules"],
        )
        self.session.add(hostel)
        await self._flush()
        self.hostels[cfg["name"]] = hostel.id

        # Admin mapping
        self.session.add(AdminHostelMapping(
            id=self._uid(), admin_id=admin_id, hostel_id=hostel.id,
            is_primary=True, assigned_by=admin_id,
        ))
        # Supervisor mapping
        self.session.add(SupervisorHostelMapping(
            id=self._uid(), supervisor_id=supervisor_id,
            hostel_id=hostel.id, assigned_by=admin_id,
        ))

        # Amenities
        for name, category in cfg["amenities"]:
            self.session.add(HostelAmenity(
                id=self._uid(), hostel_id=hostel.id,
                name=name, category=category,
            ))

        # Images
        images = HOSTEL_IMAGES.get(cfg["name"], [])
        for i, url in enumerate(images):
            self.session.add(HostelImage(
                id=self._uid(), hostel_id=hostel.id,
                url=url,
                thumbnail_url=url.replace("w=800", "w=400"),
                caption=f"{cfg['name']} - Photo {i+1}",
                image_type="gallery",
                sort_order=i,
                is_primary=(i == 0),
            ))

        await self._flush()
        print(f"  ✓ Hostel: {cfg['name']} ({cfg['city']})")
        return hostel.id

    # ------------------------------------------------------------------
    async def create_rooms_and_beds(self, hostel_id: str,
                                    rooms_cfg: list) -> None:
        for r in rooms_cfg:
            room = Room(
                id=self._uid(), hostel_id=hostel_id,
                room_number=r["number"], floor=r["floor"],
                room_type=r["type"],
                total_beds=r["beds"],
                daily_rent=r["daily"], monthly_rent=r["monthly"],
                security_deposit=r["deposit"],
                dimensions=r.get("dim"), is_active=True,
            )
            self.session.add(room)
            await self._flush()
            self.rooms[room.id] = {"hostel_id": hostel_id, "room_id": room.id}

            for b in range(1, r["beds"] + 1):
                bed = Bed(
                    id=self._uid(), hostel_id=hostel_id,
                    room_id=room.id,
                    bed_number=f"B{b}",
                    status=BedStatus.AVAILABLE,
                )
                self.session.add(bed)
                await self._flush()
                self.beds[bed.id] = {
                    "hostel_id": hostel_id,
                    "room_id": room.id,
                    "bed_id": bed.id,
                }

    # ------------------------------------------------------------------
    async def create_booking(self, visitor_id: str, hostel_id: str,
                             room_id: str, bed_id: str | None,
                             status: BookingStatus,
                             mode: BookingMode = BookingMode.MONTHLY,
                             days: int = 30,
                             full_name: str = "Test Visitor",
                             approved_by: str | None = None) -> Booking:
        check_in = date.today() - timedelta(days=5)
        check_out = check_in + timedelta(days=days)
        room = next((r for r in self.rooms.values() if r["room_id"] == room_id), None)
        monthly_rent = 6000.0
        booking_advance = monthly_rent * 0.25

        booking = Booking(
            id=self._uid(),
            booking_number=f"SE-{uuid.uuid4().hex[:8].upper()}",
            visitor_id=visitor_id,
            hostel_id=hostel_id,
            room_id=room_id,
            bed_id=bed_id,
            booking_mode=mode,
            status=status,
            check_in_date=check_in,
            check_out_date=check_out,
            total_nights=days if mode == BookingMode.DAILY else None,
            total_months=1 if mode == BookingMode.MONTHLY else None,
            base_rent_amount=monthly_rent,
            security_deposit=6000.0,
            booking_advance=booking_advance,
            grand_total=monthly_rent + 6000.0,
            full_name=full_name,
            date_of_birth=date(2000, 6, 15),
            gender="M",
            occupation="Student",
            institution="Osmania University",
            current_address="123 Main Street, Hyderabad",
            id_type="aadhar",
            emergency_contact_name="Parent",
            emergency_contact_phone="+91-9000000099",
            emergency_contact_relationship="Parent",
            approved_by=approved_by,
        )
        self.session.add(booking)
        await self._flush()

        self.session.add(BookingStatusHistory(
            id=self._uid(), booking_id=booking.id,
            old_status=None, new_status=status,
            changed_by=visitor_id,
            note=f"Booking created with status {status.value}",
        ))

        if status in (BookingStatus.APPROVED, BookingStatus.CHECKED_IN) and bed_id:
            self.session.add(BedStay(
                id=self._uid(), hostel_id=hostel_id,
                bed_id=bed_id, booking_id=booking.id,
                student_id=None,
                start_date=check_in, end_date=check_out,
                status=BedStayStatus.ACTIVE if status == BookingStatus.CHECKED_IN else BedStayStatus.RESERVED,
            ))

        await self._flush()
        self.bookings.append(booking)
        return booking

    # ------------------------------------------------------------------
    async def create_student(self, user_id: str, hostel_id: str,
                             room_id: str, bed_id: str,
                             booking_id: str, idx: int,
                             employee_code: str | None = None) -> str:
        # Use employee code + index suffix to guarantee uniqueness
        # e.g. LEV044-22 for Hemant Pawade (index 22)
        if employee_code:
            student_number = f"{employee_code}-{idx:02d}"
        else:
            student_number = f"SE{2026}{idx:04d}"
        student = Student(
            id=self._uid(), user_id=user_id,
            hostel_id=hostel_id, room_id=room_id,
            bed_id=bed_id, booking_id=booking_id,
            student_number=student_number,
            check_in_date=date.today() - timedelta(days=30),
            check_out_date=None,
            status=StudentStatus.ACTIVE,
        )
        self.session.add(student)
        await self._flush()
        self.students[user_id] = student.id
        return student.id

    # ------------------------------------------------------------------
    async def create_payment(self, hostel_id: str, booking_id: str | None,
                             student_id: str | None, amount: float,
                             ptype: str = "booking_advance",
                             status: str = "captured") -> None:
        self.session.add(Payment(
            id=self._uid(), hostel_id=hostel_id,
            booking_id=booking_id, student_id=student_id,
            amount=amount, payment_type=ptype,
            payment_method="razorpay",
            gateway_order_id=f"order_{uuid.uuid4().hex[:12]}",
            gateway_payment_id=f"pay_{uuid.uuid4().hex[:12]}" if status == "captured" else None,
            gateway_signature=f"sig_{uuid.uuid4().hex[:24]}" if status == "captured" else None,
            status=status,
            receipt_url=f"https://stayease.in/receipts/{uuid.uuid4().hex[:8]}.pdf" if status == "captured" else None,
            due_date=date.today(),
            paid_at=datetime.now(UTC) if status == "captured" else None,
        ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_mess_menu(self, hostel_id: str, created_by: str) -> None:
        # Current week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        menu = MessMenu(
            id=self._uid(), hostel_id=hostel_id,
            week_start_date=week_start,
            is_active=True, created_by=created_by,
        )
        self.session.add(menu)
        await self._flush()
        for day, meal, item, is_veg, note in MESS_MENU:
            self.session.add(MessMenuItem(
                id=self._uid(), menu_id=menu.id,
                day_of_week=day, meal_type=meal,
                item_name=item, is_veg=is_veg,
                special_note=note,
            ))
        # Next week (preview)
        next_week_start = week_start + timedelta(weeks=1)
        menu2 = MessMenu(
            id=self._uid(), hostel_id=hostel_id,
            week_start_date=next_week_start,
            is_active=False, created_by=created_by,
        )
        self.session.add(menu2)
        await self._flush()
        for day, meal, item, is_veg, note in MESS_MENU:
            self.session.add(MessMenuItem(
                id=self._uid(), menu_id=menu2.id,
                day_of_week=day, meal_type=meal,
                item_name=item, is_veg=is_veg,
                special_note=note,
            ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_notices(self, hostel_id: str, created_by: str) -> None:
        for title, content, ntype, priority in NOTICE_DATA:
            self.session.add(Notice(
                id=self._uid(), hostel_id=hostel_id,
                title=title, content=content,
                notice_type=ntype, priority=priority,
                is_published=True, created_by=created_by,
            ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_complaints(self, hostel_id: str,
                                student_ids: list[str],
                                supervisor_id: str) -> None:
        for i, (cat, title, desc, priority) in enumerate(COMPLAINT_DATA):
            student_id = student_ids[i % len(student_ids)]
            complaint = Complaint(
                id=self._uid(),
                complaint_number=f"CMP-{uuid.uuid4().hex[:6].upper()}",
                student_id=student_id, hostel_id=hostel_id,
                category=cat, title=title, description=desc,
                priority=priority,
                status="resolved" if i % 3 == 0 else ("in_progress" if i % 3 == 1 else "open"),
                assigned_to=supervisor_id if i % 2 == 0 else None,
                resolution_notes="Issue has been resolved by maintenance team." if i % 3 == 0 else None,
            )
            self.session.add(complaint)
            await self._flush()
            # Add a comment
            self.session.add(ComplaintComment(
                id=self._uid(), complaint_id=complaint.id,
                author_id=supervisor_id,
                content="We have received your complaint and are looking into it.",
            ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_attendance(self, hostel_id: str,
                                student_ids: list[str],
                                supervisor_id: str) -> None:
        statuses = ["present", "present", "present", "late", "absent"]
        seen: set[tuple] = set()
        for student_id in student_ids:
            for days_ago in range(14):
                d = date.today() - timedelta(days=days_ago)
                key = (student_id, d)
                if key in seen:
                    continue
                seen.add(key)
                st = statuses[days_ago % len(statuses)]
                self.session.add(AttendanceRecord(
                    id=self._uid(), student_id=student_id,
                    hostel_id=hostel_id, date=d,
                    check_in_time=time(9, 0) if st != "absent" else None,
                    check_out_time=time(22, 0) if st == "present" else None,
                    status=st, marked_by=supervisor_id,
                    method="manual",
                    remarks="Late arrival" if st == "late" else None,
                ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_maintenance(self, hostel_id: str,
                                 room_ids: list[str],
                                 supervisor_id: str,
                                 admin_id: str) -> None:
        for i, (cat, title, desc, priority, needs_approval) in enumerate(MAINTENANCE_DATA):
            room_id = room_ids[i % len(room_ids)] if room_ids else None
            self.session.add(MaintenanceRequest(
                id=self._uid(), hostel_id=hostel_id,
                room_id=room_id, reported_by=supervisor_id,
                category=cat, title=title, description=desc,
                priority=priority,
                status="completed" if i % 3 == 0 else ("in_progress" if i % 3 == 1 else "open"),
                estimated_cost=500.0 + (i * 200),
                actual_cost=450.0 + (i * 180) if i % 3 == 0 else None,
                requires_admin_approval=needs_approval,
                approved_by=admin_id if needs_approval and i % 2 == 0 else None,
            ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_reviews(self, hostel_id: str,
                             visitor_ids: list[str]) -> None:
        reviews = [
            (4.8, "Excellent hostel!", "Best hostel I've stayed in. Clean rooms, great food, and friendly staff. The WiFi is fast and the study room is very helpful for exam prep."),
            (4.5, "Very good experience", "Good facilities and nice location. The mess food is tasty and the staff is responsive. Minor issue with hot water sometimes."),
            (4.2, "Comfortable stay", "Decent hostel with good amenities. The gym is well-equipped. Would recommend to students looking for budget accommodation."),
            (3.8, "Good but can improve", "Overall good experience. The food quality could be better on weekdays. Security is excellent and the location is convenient."),
            (5.0, "Perfect for students!", "Absolutely love this hostel. The community is great, food is delicious, and the management is very professional. Highly recommended!"),
        ]
        for i, (rating, title, content) in enumerate(reviews):
            visitor_id = visitor_ids[i % len(visitor_ids)]
            self.session.add(Review(
                id=self._uid(), visitor_id=visitor_id,
                hostel_id=hostel_id, booking_id=None,
                overall_rating=rating,
                cleanliness_rating=min(5.0, rating + 0.1),
                food_rating=max(3.0, rating - 0.3),
                security_rating=min(5.0, rating + 0.2),
                value_rating=max(3.5, rating - 0.1),
                title=title, content=content,
                is_verified=True, is_published=True,
                admin_reply="Thank you for your feedback! We're glad you enjoyed your stay." if i % 2 == 0 else None,
            ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_subscription(self, hostel_id: str) -> None:
        self.session.add(Subscription(
            id=self._uid(), hostel_id=hostel_id,
            tier="professional",
            price_monthly=2999.0,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=305),
            status="active", auto_renew=True,
        ))
        await self._flush()

    # ------------------------------------------------------------------
    async def create_inquiry(self, hostel_id: str) -> None:
        inquiries = [
            ("Ravi Kumar", "ravi.kumar@gmail.com", "+91-9111111111", "Is there availability for a single room from April 1st?"),
            ("Preethi S", "preethi.s@gmail.com", "+91-9222222222", "What are the monthly charges including food?"),
            ("Aditya M", "aditya.m@gmail.com", "+91-9333333333", "Do you allow short-term stays of 2 weeks?"),
        ]
        for name, email, phone, msg in inquiries:
            self.session.add(Inquiry(
                id=self._uid(), hostel_id=hostel_id,
                name=name, email=email, phone=phone, message=msg,
            ))
        await self._flush()

    # ------------------------------------------------------------------
    async def run(self) -> None:
        print("\n" + "="*60)
        print("  🌱  StayEase — Full Seed Data Population")
        print("="*60 + "\n")

        # ── Users ──────────────────────────────────────────────────────
        print("👤 Creating users...\n")

        super_admin_id = await self.create_user(
            "superadmin@stayease.com", "+91-9000000001",
            "Super Admin", UserRole.SUPER_ADMIN,
        )

        admin_ids = []
        for i in range(2):
            aid = await self.create_user(
                f"admin{i+1}@stayease.com", f"+91-900000010{i}",
                f"Hostel Admin {i+1}", UserRole.HOSTEL_ADMIN,
            )
            admin_ids.append(aid)

        supervisor_ids = []
        for i in range(4):
            sid = await self.create_user(
                f"supervisor{i+1}@stayease.com", f"+91-900000020{i}",
                f"Supervisor {i+1}", UserRole.SUPERVISOR,
            )
            supervisor_ids.append(sid)

        visitor_ids = []
        for name, prefix in VISITOR_NAMES:
            vid = await self.create_user(
                f"{prefix}@gmail.com", f"+91-91{len(visitor_ids):08d}",
                name, UserRole.VISITOR,
            )
            visitor_ids.append(vid)

        student_user_ids = []
        for i, (name, prefix) in enumerate(STUDENT_NAMES):
            emp_code = EMPLOYEE_DATA[i][0] if i < len(EMPLOYEE_DATA) else f"LEV{i+1:03d}"
            # Use row index (i+1) for phone to guarantee uniqueness across all 63 employees
            emp_phone = f"+91-8{(i + 1):09d}"
            sid = await self.create_user(
                f"{prefix}@levitica.in", emp_phone,
                name, UserRole.STUDENT,
            )
            student_user_ids.append(sid)

        # ── Hostels ────────────────────────────────────────────────────
        print("\n🏠 Creating hostels, rooms, beds...\n")

        hostel_ids = []
        for i, cfg in enumerate(HOSTELS_CONFIG):
            admin_id = admin_ids[i % len(admin_ids)]
            supervisor_id = supervisor_ids[i % len(supervisor_ids)]
            hid = await self.create_hostel(cfg, admin_id, supervisor_id)
            hostel_ids.append(hid)
            await self.create_rooms_and_beds(hid, cfg["rooms"])
            print(f"    → {len(cfg['rooms'])} rooms created")

        # ── Bookings & Students ────────────────────────────────────────
        print("\n📅 Creating bookings and students...\n")

        # Group beds by hostel
        beds_by_hostel: dict[str, list[str]] = {}
        for bid, bdata in self.beds.items():
            hid = bdata["hostel_id"]
            beds_by_hostel.setdefault(hid, []).append(bid)

        rooms_by_hostel: dict[str, list[str]] = {}
        for rid, rdata in self.rooms.items():
            hid = rdata["hostel_id"]
            rooms_by_hostel.setdefault(hid, []).append(rid)

        student_idx = 0
        booking_statuses = [
            BookingStatus.CHECKED_IN,
            BookingStatus.CHECKED_IN,
            BookingStatus.APPROVED,
            BookingStatus.PENDING_APPROVAL,
            BookingStatus.PAYMENT_PENDING,
            BookingStatus.REJECTED,
            BookingStatus.CANCELLED,
        ]

        # Create bookings for visitors (various statuses)
        for i, visitor_id in enumerate(visitor_ids):
            hid = hostel_ids[i % len(hostel_ids)]
            hostel_beds = beds_by_hostel.get(hid, [])
            hostel_rooms = rooms_by_hostel.get(hid, [])
            if not hostel_beds or not hostel_rooms:
                continue
            bed_id = hostel_beds[i % len(hostel_beds)]
            room_id = self.beds[bed_id]["room_id"]
            status = booking_statuses[i % len(booking_statuses)]
            admin_id = admin_ids[i % len(admin_ids)]
            name = VISITOR_NAMES[i][0]

            booking = await self.create_booking(
                visitor_id=visitor_id, hostel_id=hid,
                room_id=room_id,
                bed_id=bed_id if status not in (BookingStatus.PAYMENT_PENDING, BookingStatus.PENDING_APPROVAL, BookingStatus.REJECTED, BookingStatus.CANCELLED) else None,
                status=status,
                mode=BookingMode.MONTHLY if i % 2 == 0 else BookingMode.DAILY,
                days=30 if i % 2 == 0 else 14,
                full_name=name,
                approved_by=admin_id if status in (BookingStatus.APPROVED, BookingStatus.CHECKED_IN) else None,
            )
            print(f"  ✓ Booking {booking.booking_number} [{status.value}] — {name}")

            # Create payment for paid bookings
            if status in (BookingStatus.APPROVED, BookingStatus.CHECKED_IN):
                await self.create_payment(
                    hostel_id=hid, booking_id=booking.id,
                    student_id=None, amount=booking.booking_advance,
                    status="captured",
                )

            # Create checked-in students from student users
        print("\n🎓 Creating student records...\n")
        for i, student_user_id in enumerate(student_user_ids):
            hid = hostel_ids[i % len(hostel_ids)]
            hostel_beds = beds_by_hostel.get(hid, [])
            hostel_rooms = rooms_by_hostel.get(hid, [])
            if not hostel_beds or not hostel_rooms:
                continue

            # Use a different bed for each student
            bed_idx = (i + len(visitor_ids)) % len(hostel_beds)
            bed_id = hostel_beds[bed_idx]
            room_id = self.beds[bed_id]["room_id"]
            admin_id = admin_ids[i % len(admin_ids)]
            name = STUDENT_NAMES[i][0]
            emp_code = EMPLOYEE_DATA[i][0] if i < len(EMPLOYEE_DATA) else None

            booking = await self.create_booking(
                visitor_id=student_user_id, hostel_id=hid,
                room_id=room_id, bed_id=bed_id,
                status=BookingStatus.CHECKED_IN,
                mode=BookingMode.MONTHLY, days=30,
                full_name=name, approved_by=admin_id,
            )

            student_id = await self.create_student(
                user_id=student_user_id, hostel_id=hid,
                room_id=room_id, bed_id=bed_id,
                booking_id=booking.id, idx=student_idx + 1,
                employee_code=emp_code,
            )
            student_idx += 1

            # Monthly rent payment
            await self.create_payment(
                hostel_id=hid, booking_id=booking.id,
                student_id=student_id, amount=6000.0,
                ptype="monthly_rent", status="captured",
            )
            print(f"  ✓ Student {emp_code or 'SE'+str(student_idx).zfill(4)} — {name}")

        # ── Mess Menus ─────────────────────────────────────────────────
        print("\n🍽️  Creating mess menus (full 7-day × 4-meal)...\n")
        for i, hid in enumerate(hostel_ids):
            await self.create_mess_menu(hid, admin_ids[i % len(admin_ids)])
            print(f"  ✓ Mess menu for hostel {i+1} (28 items × 2 weeks)")

        # ── Notices ────────────────────────────────────────────────────
        print("\n📢 Creating notices...\n")
        for i, hid in enumerate(hostel_ids):
            await self.create_notices(hid, supervisor_ids[i % len(supervisor_ids)])
        print(f"  ✓ {len(NOTICE_DATA)} notices per hostel")

        # ── Complaints ─────────────────────────────────────────────────
        print("\n💬 Creating complaints...\n")
        student_ids_list = list(self.students.values())
        if student_ids_list:
            for i, hid in enumerate(hostel_ids):
                sup_id = supervisor_ids[i % len(supervisor_ids)]
                await self.create_complaints(hid, student_ids_list, sup_id)
            print(f"  ✓ {len(COMPLAINT_DATA)} complaints per hostel")

        # ── Attendance ─────────────────────────────────────────────────
        print("\n📋 Creating attendance records (14 days)...\n")
        if student_ids_list:
            for i, hid in enumerate(hostel_ids):
                sup_id = supervisor_ids[i % len(supervisor_ids)]
                # Only students belonging to this hostel
                hostel_student_ids = [
                    sid for uid, sid in self.students.items()
                    if any(
                        b.hostel_id == hid and str(b.visitor_id) == str(uid)
                        for b in self.bookings
                    )
                ]
                # Fallback: take first 5 from all students if none found
                if not hostel_student_ids:
                    hostel_student_ids = student_ids_list[:5]
                await self.create_attendance(hid, hostel_student_ids[:5], sup_id)
            print(f"  ✓ 14 days × up to 5 students per hostel")

        # ── Maintenance ────────────────────────────────────────────────
        print("\n🔧 Creating maintenance requests...\n")
        for i, hid in enumerate(hostel_ids):
            room_ids = rooms_by_hostel.get(hid, [])
            sup_id = supervisor_ids[i % len(supervisor_ids)]
            adm_id = admin_ids[i % len(admin_ids)]
            await self.create_maintenance(hid, room_ids, sup_id, adm_id)
        print(f"  ✓ {len(MAINTENANCE_DATA)} maintenance requests per hostel")

        # ── Reviews ────────────────────────────────────────────────────
        print("\n⭐ Creating reviews...\n")
        for i, hid in enumerate(hostel_ids):
            await self.create_reviews(hid, visitor_ids)
        print(f"  ✓ 5 reviews per hostel")

        # ── Subscriptions ──────────────────────────────────────────────
        print("\n💳 Creating subscriptions...\n")
        for hid in hostel_ids:
            await self.create_subscription(hid)
        print(f"  ✓ 1 active subscription per hostel")

        # ── Inquiries ──────────────────────────────────────────────────
        print("\n📩 Creating inquiries...\n")
        for hid in hostel_ids:
            await self.create_inquiry(hid)
        print(f"  ✓ 3 inquiries per hostel")

        # ── Commit ─────────────────────────────────────────────────────
        print("\n💾 Committing to database...\n")
        await self.session.commit()

        print("="*60)
        print("  ✅  Seed complete!")
        print("="*60)
        print(f"""
  📊 Summary
  ──────────────────────────────────────
  Users          : {len(self.users)}
    Super Admin  : 1
    Hostel Admin : 2
    Supervisors  : 4
    Visitors     : {len(VISITOR_NAMES)}
    Students     : {len(STUDENT_NAMES)}
  Hostels        : {len(hostel_ids)}
  Rooms          : {len(self.rooms)}
  Beds           : {len(self.beds)}
  Bookings       : {len(self.bookings)}
  Students       : {len(self.students)}
  Mess menus     : {len(hostel_ids) * 2} (current + next week)
  Menu items     : {len(hostel_ids) * 2 * len(MESS_MENU)} total
  Notices        : {len(hostel_ids) * len(NOTICE_DATA)}
  Complaints     : {len(hostel_ids) * len(COMPLAINT_DATA)}
  Maintenance    : {len(hostel_ids) * len(MAINTENANCE_DATA)}
  Reviews        : {len(hostel_ids) * 5}
  Subscriptions  : {len(hostel_ids)}
  Inquiries      : {len(hostel_ids) * 3}
  ──────────────────────────────────────

  🔑 Login credentials (all use password: Test@1234)
  ──────────────────────────────────────
  Super Admin  : superadmin@stayease.com
  Admin 1      : admin1@stayease.com
  Admin 2      : admin2@stayease.com
  Supervisor 1 : supervisor1@stayease.com
  Visitor 1    : arun.kapoor@gmail.com
  Student 1    : abhilash.gurrampally.lev029@levitica.in  (LEV029)
  Student 22   : hemant.pawade.lev044@levitica.in         (LEV044 — Hemant Pawade)
  ──────────────────────────────────────
""")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def _run():
    import sys
    clean = "--clean" in sys.argv or "--reset" in sys.argv

    engine = create_async_engine(settings.database_url, echo=False)

    if clean:
        print("\n🗑️  Cleaning existing data (--clean flag)...\n")
        async with engine.begin() as conn:
            # Disable FK checks temporarily and delete all data
            await conn.execute(__import__("sqlalchemy").text("SET session_replication_role = replica"))
            tables = [
                "complaint_comments", "notice_reads", "attendance_records",
                "maintenance_requests", "complaints", "notices",
                "mess_menu_items", "mess_menus",
                "reviews", "inquiries", "subscriptions",
                "bed_stays", "booking_status_history", "payments",
                "payment_webhook_events", "students",
                "bookings", "beds", "rooms",
                "hostel_amenities", "hostel_images",
                "admin_hostel_mappings", "supervisor_hostel_mappings",
                "visitor_favorites", "waitlist_entries",
                "hostels", "otp_verifications", "refresh_tokens", "users",
            ]
            for table in tables:
                try:
                    await conn.execute(__import__("sqlalchemy").text(f'DELETE FROM "{table}"'))
                    print(f"  ✓ Cleared {table}")
                except Exception as e:
                    print(f"  ⚠ Skip {table}: {e}")
            await conn.execute(__import__("sqlalchemy").text("SET session_replication_role = DEFAULT"))
        print("\n  ✓ All tables cleared\n")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        seeder = StayEaseSeeder(session)
        await seeder.run()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_run())
