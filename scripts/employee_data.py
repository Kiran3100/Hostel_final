"""
Employee data from Employee_Register.xlsx (Levitica Technologies).
63 employees — used as student seed data in seed_data.py.
"""

# (employee_code, full_name, team_lead)
EMPLOYEE_DATA = [
    ("LEV029", "Abhilash Gurrampally",                       "Mani Kiran Kopanathi"),
    ("LEV039", "Anusha Enigalla",                             "Durgaprasad Medipudi"),
    ("LEV122", "Aravelly Tharun",                             "Anusha Enigalla"),
    ("LEV047", "Ashok Kota",                                  "Sameer Shaik"),
    ("LEV121", "Baluguri Ashritha Rao",                       "Durgaprasad Medipudi"),
    ("LEV116", "Bhargava Sai Kolli",                          "Kallamadi Kranti Kumar Reddy"),
    ("LEV027", "Bogala Chandramouli",                         "Durgaprasad Medipudi"),
    ("LEV023", "Burri Gowtham",                               "Mani Kiran Kopanathi"),
    ("LEV001", "Chandu Thota",                                "Durgaprasad Medipudi"),
    ("LEV038", "Cheekati Abhinaya",                           "Durgaprasad Medipudi"),
    ("LEV014", "Chodisetti Sri Rama Sai",                     "Mani Kiran Kopanathi"),
    ("LEV123", "Dhanikela Brahmam",                           "Anusha Enigalla"),
    ("LEV012", "Dheeraj Krishna Jakkula",                     "Mani Kiran Kopanathi"),
    ("LEV028", "Dorasala Nagendra Reddy",                     "Mani Kiran Kopanathi"),
    ("LEV017", "Dubbaka Bharath",                             "Sameer Shaik"),
    ("LEV026", "Durga Sai Vara Prasad Chandragiri",           "Durgaprasad Medipudi"),
    ("LEV031", "Gorle Leela Sai Kumar",                       "Durgaprasad Medipudi"),
    ("LEV127", "Gubba Vasini",                                "Anusha Enigalla"),
    ("LEV005", "Gurajapu Pavani",                             "Nagendra Uggirala"),
    ("LEV118", "Hari Charan Teja Gudapati",                   "Anusha Enigalla"),
    ("LEV050", "Harsha Vardhan Naidu Dasireddy",              "Kallamadi Kranti Kumar Reddy"),
    ("LEV044", "Hemant Tukaram Pawade",                       "Mani Kiran Kopanathi"),
    ("LEV008", "Hruthik Venkata Sai Ganesh Jamanu",           "Chandu Thota"),
    ("LEV033", "Jagadeesh Bedolla",                           "Sameer Shaik"),
    ("LEV128", "Jothi Lakshmi A",                             "Anusha Enigalla"),
    ("LEV013", "Kallamadi Kowsik Reddy",                      "Durgaprasad Medipudi"),
    ("LEV011", "Kallamadi Kranti Kumar Reddy",                "Durgaprasad Medipudi"),
    ("LEV004", "Kallamadi Keerthi",                           "Nagendra Uggirala"),
    ("LEV003", "Kandepuneni Swetha Naga Durga",               "Chandu Thota"),
    ("LEV036", "Kasarapu Rajeswar Reddy",                     "Sameer Shaik"),
    ("LEV019", "Keerthi Ranjani Maddala",                     "Sameer Shaik"),
    ("LEV032", "Khuswanth Rao Jadav",                         "Sameer Shaik"),
    ("LEV034", "Kishore Tiruveedhula",                        "Mani Kiran Kopanathi"),
    ("LEV046", "Kondareddy Revathi",                          "Sameer Shaik"),
    ("LEV126", "Korada Kavya",                                "Anusha Enigalla"),
    ("LEV035", "Kothapalli Sai Avinash Varma",                "Mani Kiran Kopanathi"),
    ("LEV048", "Lokeshwar Reddy Kondappagari",                "Kallamadi Kranti Kumar Reddy"),
    ("LEV010", "Mani Kiran Kopanathi",                        "Durgaprasad Medipudi"),
    ("LEV039M", "Manikanta Nedunuri",                         "Mani Kiran Kopanathi"),
    ("LEV120", "Medipudi Durgaprasad",                        None),
    ("LEV002", "Minal Devidas Mahajan",                       "Durgaprasad Medipudi"),
    ("LEV041", "Mohammad Aslam Yakub Khan",                   "Durgaprasad Medipudi"),
    ("LEV042", "Muniganti Sai Sumiran",                       "Sameer Shaik"),
    ("LEV117", "N Sairam Srinivasa Chakravarthi Pothureddy",  "Kallamadi Kranti Kumar Reddy"),
    ("LEV040", "Nagadurga Sarnala",                           "Mani Kiran Kopanathi"),
    ("LEV024", "Nagendra Uggirala",                           "Durgaprasad Medipudi"),
    ("LEV015", "Nani Venkata Ravi Teja Maddala",              "Sameer Shaik"),
    ("LEV022", "Naveen Sai Koppereddy",                       "Nagendra Uggirala"),
    ("LEV025", "Nollu Lalith Kumar",                          "Sameer Shaik"),
    ("LEV021", "Pagadala Anitha",                             "Sameer Shaik"),
    ("LEV018", "Peddireddy Sai Kumar Reddy",                  "Sameer Shaik"),
    ("LEV037", "Pesaru Kireeti",                              "Sameer Shaik"),
    ("LEV049", "Pillala Sukanya",                             "Kallamadi Kranti Kumar Reddy"),
    ("LEV006", "Potnuri Naveen Bhargav",                      "Chandu Thota"),
    ("LEV051", "Pradeep Bantapalli",                          "Kallamadi Kranti Kumar Reddy"),
    ("LEV016", "Pramod Kumar Sindhe",                         "Sameer Shaik"),
    ("LEV009", "Sameer Shaik",                                "Durgaprasad Medipudi"),
    ("LEV030", "Sasi Kumar Reddy Chintala",                   "Mani Kiran Kopanathi"),
    ("LEV043", "Satya Kiran Chelluboina",                     "Mani Kiran Kopanathi"),
    ("LEV124", "Sumathi Mittapalli",                          "Anusha Enigalla"),
    ("LEV007", "Syed Afran Ali",                              "Chandu Thota"),
    ("LEV119", "Vamshi Hasanabada",                           "Kallamadi Kranti Kumar Reddy"),
    ("LEV125", "Vijay Ram Maddukuri",                         "Anusha Enigalla"),
]


def emp_email_prefix(name: str, code: str) -> str:
    """firstname.lastname.LEVXXX"""
    parts = name.lower().split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}.{code.lower().replace('b','')}"
    return f"{parts[0]}.{code.lower().replace('b','')}"


def emp_phone(code: str) -> str:
    """Deterministic phone in +91-8xxxxxxxxx range (avoids system account conflicts)."""
    digits = ''.join(c for c in code if c.isdigit())
    num = int(digits) if digits else 0
    return f"+91-8{num:09d}"


# Ready-to-use tuples for STUDENT_NAMES
STUDENT_NAMES = [
    (emp[1], emp_email_prefix(emp[1], emp[0]))
    for emp in EMPLOYEE_DATA
]

# Lookup maps
EMPLOYEE_CODE_MAP = {emp[1]: emp[0] for emp in EMPLOYEE_DATA}
EMPLOYEE_LEAD_MAP = {emp[1]: emp[2] for emp in EMPLOYEE_DATA}
