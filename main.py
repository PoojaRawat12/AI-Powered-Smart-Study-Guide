import streamlit as st
import datetime
import random
import re
import pandas as pd
from PyPDF2 import PdfReader
from fpdf import FPDF
import io
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def clean_question_text(text):
    if not text:
        return ""
    
    # Remove unwanted phrases
    text = re.sub(r'(?i)q[:\-]?\s*', '', text)
    text = re.sub(r'(?i)define briefly[:\-]?', 'Define', text)
    text = re.sub(r'(?i)explain shortly[:\-]?', 'Explain', text)
    text = re.sub(r'(?i)write a detailed note on[:\-]?', 'Write a note on', text)
    text = re.sub(r'(?i)what is related to[:\-]?', 'Explain', text)
    
    # Remove diagram or extra content
    text = re.sub(r'\(.diagram.\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'page\s*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'||', '', text)

    # Remove multiple spaces and trim
    text = re.sub(r'\s+', ' ', text).strip()

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    return text


# ---------------------------
# Set A: Original AI Study Assistant 
# ---------------------------

# ✅ Allowed subjects list
VALID_SUBJECTS = [
    "maths", "mathematics", "physics", "chemistry", "biology",
    "english", "hindi", "sociology", "history", "geography",
    "computer", "science", "accountancy", "economics", "business studies",
    "python","computer science","c","c++","operating system","dbms"
]

def format_time(hours_float):
    """Format study time into hours/mins cleanly."""
    hours = int(hours_float)
    minutes = int(round((hours_float - hours) * 60))

    if hours > 0 and minutes > 0:
        return f"{hours} hrs {minutes} mins"
    elif hours > 0:
        return f"{hours} hrs"
    else:
        return f"{minutes} mins"

def generate_study_plan(subjects, exam_date, daily_hours):
    today = datetime.date.today()
    days_left = (exam_date - today).days
    if days_left <= 0:
        return ["⚠ Exam date must be in the future!"]

    # Assign weights based on difficulty
    weights = {"Easy": 1, "Medium": 2, "Hard": 3}
    total_weight = sum(weights[d] for _, d in subjects)

    plan = []
    for day in range(1, days_left + 1):
        daily_plan = {"Day": (today + datetime.timedelta(days=day)).strftime("%d-%b-%Y (%A)")}
        for subject, difficulty in subjects:
            allocated_time = (daily_hours * weights[difficulty]) / total_weight
            daily_plan[subject] = format_time(allocated_time)
        plan.append(daily_plan)

    return plan


def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    except:
        text = "⚠ Could not extract text from PDF"
    return text


def generate_questions_from_text(text, num_questions=5):
    sentences = re.split(r'[.!?]', text)
    keywords = [s.strip() for s in sentences if len(s.split()) > 3]

    questions = {"MCQ": [], "Very Short": [], "Short": [], "Long": []}

    for i in range(min(num_questions, len(keywords))):
        topic = keywords[i]

        mcq_q = f"Which of the following relates to: {topic}?"
        options = ["Option A", "Option B", "Option C", topic]
        random.shuffle(options)
        questions["MCQ"].append((mcq_q, options, topic))

        questions["Very Short"].append(f"Define: {topic}")
        questions["Short"].append(f"Explain briefly: {topic}")
        questions["Long"].append(f"Write a detailed note on: {topic}")

    return questions


# Export Study Plan to PDF
def export_plan_to_pdf(plan):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "Study Plan", ln=True, align="C")
    pdf.ln(10)

    for day_plan in plan:
        pdf.cell(200, 8, f"Day: {day_plan['Day']}", ln=True)
        for subj, time in day_plan.items():
            if subj != "Day":
                pdf.cell(200, 8, f" {subj}: {time}", ln=True)
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin-1")


# Export Questions to PDF
def export_questions_to_pdf(questions):
    """
    Safe exporter: replaces characters not supported by latin-1
    to avoid UnicodeEncodeError from fpdf while keeping behavior same.
    """
    def safe_latin(s: str) -> str:
        if s is None:
            return ""
        # replace unsupported chars with '?'
        return s.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "Generated Questions", ln=True, align="C")
    pdf.ln(10)

    for qtype, qlist in questions.items():
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(200, 8, safe_latin(f"{qtype} Questions"), ln=True)
        pdf.set_font("Arial", size=12)

        for q in qlist:
            if isinstance(q, tuple):  # MCQ: (question, options, ans)
                question, options, ans = q
                pdf.multi_cell(0, 8, safe_latin(f"- {question}"))
                for opt in options:
                    # Use a plain bullet char; safe_latin will replace if unsupported
                    pdf.multi_cell(0, 8, safe_latin(f" - {opt}"))
                pdf.multi_cell(0, 8, safe_latin(f"Answer: {ans}"))
            else:
                pdf.multi_cell(0, 8, safe_latin(f"- {q}"))
            pdf.ln(2)

        pdf.ln(4)

    # Return bytes (same api you already use)
    return pdf.output(dest="S").encode("utf-8")



# ---------------------------
# Set B-ish 
# ---------------------------

# We'll provide a solid sample QUESTION_BANK for many subjects.
QUESTION_BANK = {
    "mathematics": {
        "Easy": [
            {"q":"What is 7 + 5?","options":["11","12","13","10"],"ans":"12"},
            {"q":"What is the square root of 64?","options":["6","8","7","9"],"ans":"8"},
            {"q":"What is 5 * 4?","options":["20","15","25","10"],"ans":"20"},
            {"q":"What is 10 - 3?","options":["8","6","7","3"],"ans":"7"},
            {"q":"What is 9 + 1?","options":["9","10","11","8"],"ans":"10"},
            {"q":"What is 2 + 2?","options":["3","4","2","5"],"ans":"4"},
        ],
        "Medium": [
            {"q":"If 3x + 6 = 15, what is x?","options":["2","3","4","1"],"ans":"3"},
            {"q":"What is the formula for area of a triangle?","options":["(base*height)/2","base*height","2*(base+height)","base+height"],"ans":"(base*height)/2"},
            {"q":"What is the solution to x^2 = 16?","options":["±4","4 only","-4 only","0"],"ans":"±4"},
            {"q":"What is 12/3?","options":["4","3","6","2"],"ans":"4"},
            {"q":"What is the next prime after 7?","options":["11","9","13","10"],"ans":"11"},
            {"q":"If f(x)=x^2, what is f(3)?","options":["9","6","3","12"],"ans":"9"},
        ],
        "Hard": [
            {"q":"Derivative of x^3 is:","options":["3x^2","x^2","x^3","3x"],"ans":"3x^2"},
            {"q":"Integral of 2x dx is:","options":["x^2 + C","2x + C","x + C","x^3/3 + C"],"ans":"x^2 + C"},
            {"q":"If matrix A is [[1,0],[0,1]] what is determinant?","options":["1","0","2","-1"],"ans":"1"},
            {"q":"What is the quadratic formula root expression?","options":["(-b ± √(b^2-4ac))/(2a)","(b ± √(...))/2a","-b/(2a)","..."],"ans":"(-b ± √(b^2-4ac))/(2a)"},
            {"q":"What is limit of (1+1/n)^n as n→∞?","options":["e","1","0","∞"],"ans":"e"},
            {"q":"Which theorem relates to right-angled triangles?","options":["Pythagorean Theorem","Fermat's Last Theorem","Mean Value Theorem","Bayes Theorem"],"ans":"Pythagorean Theorem"},
        ],
    },

    "physics": {
        "Easy":[
            {"q":"Which force pulls objects toward Earth?","options":["Gravity","Friction","Magnetism","Electricity"],"ans":"Gravity"},
            {"q":"Unit of force is:","options":["Newton","Joule","Watt","Pascal"],"ans":"Newton"},
            {"q":"Light travels fastest in:","options":["Vacuum","Water","Glass","Air"],"ans":"Vacuum"},
            {"q":"Which instrument measures temperature?","options":["Thermometer","Barometer","Ammeter","Voltmeter"],"ans":"Thermometer"},
        ],
        "Medium":[
            {"q":"Who formulated laws of motion?","options":["Newton","Einstein","Galileo","Tesla"],"ans":"Newton"},
            {"q":"SI unit of energy is:","options":["Joule","Watt","Newton","Pascal"],"ans":"Joule"},
            {"q":"Ohm's law relates voltage, current and:","options":["Resistance","Power","Energy","Charge"],"ans":"Resistance"},
            {"q":"What is speed = distance/time measured in?","options":["m/s","m^2","N","s"],"ans":"m/s"},
        ],
        "Hard":[
            {"q":"Einstein is famous for which relation?","options":["E = mc^2","F = ma","V = IR","pV = nRT"],"ans":"E = mc^2"},
            {"q":"What is the phenomenon of bending of light?","options":["Refraction","Reflection","Diffraction","Interference"],"ans":"Refraction"},
            {"q":"What is work if force and displacement are perpendicular?","options":["0","Positive","Negative","Undefined"],"ans":"0"},
            {"q":"What is the SI unit of pressure?","options":["Pascal","Bar","atm","mmHg"],"ans":"Pascal"},
        ],
    },

    "chemistry": {
        "Easy":[
            {"q":"Water's chemical formula is:","options":["H2O","CO2","O2","H2"],"ans":"H2O"},
            {"q":"pH of neutral water approx is:","options":["7","0","14","1"],"ans":"7"},
            {"q":"What is table salt chemically?","options":["Sodium Chloride","Potassium Chloride","Sodium Hydroxide","Hydrochloric Acid"],"ans":"Sodium Chloride"},
            {"q":"Which gas is produced in photosynthesis?","options":["Oxygen","Carbon Dioxide","Nitrogen","Hydrogen"],"ans":"Oxygen"},
        ],
        "Medium":[
            {"q":"Atomic number represents:","options":["Number of protons","Number of neutrons","Mass number","Valence electrons"],"ans":"Number of protons"},
            {"q":"pH less than 7 indicates:","options":["Acidic","Basic","Neutral","Salt"],"ans":"Acidic"},
            {"q":"Which bond shares electrons?","options":["Covalent","Ionic","Hydrogen","Metallic"],"ans":"Covalent"},
            {"q":"Period in periodic table is:","options":["Row","Column","Group","Block"],"ans":"Row"},
        ],
        "Hard":[
            {"q":"What is Avogadro's number approx?","options":["6.022e23","3.14","9.81","1.6e-19"],"ans":"6.022e23"},
            {"q":"What type of reaction is combustion?","options":["Redox","Acid-base","Precipitation","Photochemical"],"ans":"Redox"},
            {"q":"What is the molar mass of CO2 (approx)?","options":["44 g/mol","12 g/mol","28 g/mol","32 g/mol"],"ans":"44 g/mol"},
            {"q":"Which is a noble gas?","options":["Argon","Oxygen","Nitrogen","Chlorine"],"ans":"Argon"},
        ],
    },

    "biology": {
        "Easy":[
            {"q":"The basic unit of life is:","options":["Cell","Tissue","Organ","Organism"],"ans":"Cell"},
            {"q":"Photosynthesis occurs in:","options":["Chloroplast","Mitochondria","Nucleus","Ribosome"],"ans":"Chloroplast"},
            {"q":"Human blood type that is universal donor:","options":["O-","A+","B+","AB+"],"ans":"O-"},
            {"q":"Which organ pumps blood?","options":["Heart","Lung","Kidney","Liver"],"ans":"Heart"},
        ],
        "Medium":[
            {"q":"Which macromolecule is enzyme?","options":["Protein","Carbohydrate","Lipid","Nucleic acid"],"ans":"Protein"},
            {"q":"Where does digestion begin?","options":["Mouth","Stomach","Small Intestine","Esophagus"],"ans":"Mouth"},
            {"q":"DNA stands for:","options":["Deoxyribonucleic Acid","Ribonucleic Acid","Protein","Carbohydrate"],"ans":"Deoxyribonucleic Acid"},
            {"q":"Which cell organelle makes ATP?","options":["Mitochondria","Ribosome","Golgi","Nucleus"],"ans":"Mitochondria"},
        ],
        "Hard":[
            {"q":"What is Mendel known for?","options":["Genetics","Evolution","Cell theory","Germ theory"],"ans":"Genetics"},
            {"q":"What carries genetic info?","options":["DNA","RNA","Protein","Lipid"],"ans":"DNA"},
            {"q":"What is homeostasis?","options":["Maintaining internal balance","Cell division","Protein synthesis","Digestion"],"ans":"Maintaining internal balance"},
            {"q":"Which system controls hormones?","options":["Endocrine","Nervous","Digestive","Respiratory"],"ans":"Endocrine"},
        ],
    },

    "english": {
        "Easy":[
            {"q":"A synonym of 'big' is:","options":["Large","Tiny","Short","Narrow"],"ans":"Large"},
            {"q":"Antonym of 'happy' is:","options":["Sad","Glad","Joyful","Cheerful"],"ans":"Sad"},
            {"q":"Which is a noun? 'Cat' is:","options":["Noun","Verb","Adjective","Adverb"],"ans":"Noun"},
            {"q":"Choose the article: '___ apple'","options":["An","A","The","No article"],"ans":"An"},
        ],
        "Medium":[
            {"q":"Which is past tense of 'go'?","options":["Went","Go","Gone","Going"],"ans":"Went"},
            {"q":"Identify adjective: 'beautiful'","options":["Adjective","Noun","Verb","Adverb"],"ans":"Adjective"},
            {"q":"Plural of 'child' is:","options":["Children","Childs","Childes","Child"],"ans":"Children"},
            {"q":"Which is correct sentence? 'She ___ a book'","options":["reads","readed","reading","rreads"],"ans":"reads"},
        ],
        "Hard":[
            {"q":"Choose correct preposition: 'good ___ mathematics'","options":["at","in","on","for"],"ans":"at"},
            {"q":"What is a conjunction?","options":["And","Run","Blue","Quickly"],"ans":"And"},
            {"q":"Which is a homophone pair?","options":["to / two","cat / car","red / bed","sun / moon"],"ans":"to / two"},
            {"q":"What is passive voice of 'She wrote a letter'?","options":["A letter was written by her","She was written a letter","She wrote a letter","She had written a letter"],"ans":"A letter was written by her"},
        ],
    },

    "hindi": {
        "Easy":[
            {"q":"भारत की राष्ट्रीय भाषा क्या है?","options":["हिंदी","अंग्रेजी","तमिल","उर्दू"],"ans":"हिंदी"},
            {"q":"'पानी' का पर्यायवाची क्या है?","options":["जल","आग","हवा","पेड़"],"ans":"जल"},
            {"q":"संज्ञा क्या दर्शाती है?","options":["नाम","क्रिया","विशेषण","क्रिया विशेषण"],"ans":"नाम"},
            {"q":"'लाल' किस प्रकार का शब्द है?","options":["विशेषण","संज्ञा","क्रिया","सर्वनाम"],"ans":"विशेषण"},
        ],
        "Medium":[
            {"q":"कबीर किसके लिए प्रसिद्ध हैं?","options":["दोहे","नाटक","उपन्यास","कहानी"],"ans":"दोहे"},
            {"q":"संज्ञा के कितने भेद हैं?","options":["5","3","2","4"],"ans":"5"},
            {"q":"किसे विलोम कहा जाता है? 'अच्छा' का विलोम है:","options":["बुरा","अच्छा","छोटा","बड़ा"],"ans":"बुरा"},
            {"q":"कबीर के दोहे में मुख्य विषय क्या है?","options":["भक्ति और समाज सुधार","युद्ध","प्रेम","प्रकृति"],"ans":"भक्ति और समाज सुधार"},
        ],
        "Hard":[
            {"q":"रस सिद्धांत के प्रणेता माने जाते हैं:","options":["भरत मुनि","रामानंद","कालिदास","हरिवंश राय"],"ans":"भरत मुनि"},
            {"q":"'अंधेर नगरी' के लेखक कौन?","options":["भारतेन्दु हरिश्चंद्र","मुंशी प्रेमचंद","हंस","जयशंकर प्रसाद"],"ans":"भारतेन्दु हरिश्चंद्र"},
            {"q":"किसे 'अलंकरण' कहते हैं?","options":["काव्य श्रृंगारिकता संवर्धन","वाक्य रचना","पाठ विभाजन","लेखन कौशल"],"ans":"काव्य श्रृंगारिकता संवर्धन"},
            {"q":"'संज्ञा' किसे कहते हैं?","options":["नाम","क्रिया","विशेषण","क्रिया विशेषण"],"ans":"नाम"},
        ],
    },

    "computer science": {
        "Easy":[
            {"q":"What is CPU?","options":["Central Processing Unit","Computer Processing Unit","Control Processing Unit","Central Program Unit"],"ans":"Central Processing Unit"},
            {"q":"What does RAM stand for?","options":["Random Access Memory","Read Access Memory","Run Access Memory","Readily Available Memory"],"ans":"Random Access Memory"},
            {"q":"Which device stores data permanently?","options":["Hard Disk","RAM","Cache","Register"],"ans":"Hard Disk"},
            {"q":"Which is an input device?","options":["Keyboard","Monitor","Printer","Speaker"],"ans":"Keyboard"},
        ],
        "Medium":[
            {"q":"Which data structure uses LIFO?","options":["Stack","Queue","Array","Tree"],"ans":"Stack"},
            {"q":"What does SQL relate to?","options":["Databases","Networks","Hardware","Operating Systems"],"ans":"Databases"},
            {"q":"Firewall protects from?","options":["Network threats","Friction","Heat","Power"],"ans":"Network threats"},
            {"q":"What is an algorithm?","options":["Step-by-step procedure","A language","A storage device","A type of hardware"],"ans":"Step-by-step procedure"},
        ],
        "Hard":[
            {"q":"Which sorting algorithm has O(n log n) average?","options":["Merge Sort","Bubble Sort","Selection Sort","Insertion Sort"],"ans":"Merge Sort"},
            {"q":"Which is not a programming paradigm?","options":["Hardware","Object-oriented","Functional","Procedural"],"ans":"Hardware"},
            {"q":"What is recursion?","options":["Function calling itself","Loop","Array operation","Sorting method"],"ans":"Function calling itself"},
            {"q":"What does 'HTTP' stand for?","options":["HyperText Transfer Protocol","High Transfer Text Protocol","Hyperlink Transfer Tool Protocol","HyperText Translate Protocol"],"ans":"HyperText Transfer Protocol"},
        ],
    },

    "python": {
        "Easy":[
            {"q":"Which symbol starts a comment in Python?","options":["#","//","/*","--"],"ans":"#"},
            {"q":"How to print in Python 3?","options":["print('hello')","echo 'hello'","printf('hello')","cout << 'hello'"],"ans":"print('hello')"},
            {"q":"Which is a Python data type?","options":["List","Table","Record","Struct"],"ans":"List"},
            {"q":"How to create a list?","options":["[1,2,3]","(1,2,3)","{1,2,3}","<1,2,3>"],"ans":"[1,2,3]"},
        ],
        "Medium":[
            {"q":"What does 'len' do?","options":["Returns length","Deletes element","Prints value","Sorts list"],"ans":"Returns length"},
            {"q":"How to define a function?","options":["def func():","function func()","func def:","create func()"],"ans":"def func():"},
            {"q":"Which loop iterates until condition false?","options":["while","for","repeat","do-while"],"ans":"while"},
            {"q":"How to import module math?","options":["import math","include math","using math","require math"],"ans":"import math"},
        ],
        "Hard":[
            {"q":"What does list comprehension produce?","options":["New list","Dictionary","Set","Tuple"],"ans":"New list"},
            {"q":"Which is mutable?","options":["List","Tuple","String","Int"],"ans":"List"},
            {"q":"What does 'init' define?","options":["Constructor","Destructor","Method call","Static block"],"ans":"Constructor"},
            {"q":"What is GIL in Python?","options":["Global Interpreter Lock","General Input Loop","Global Input Limit","Graphical Interface Layer"],"ans":"Global Interpreter Lock"},
        ],
    },

    "operating system": {
        "Easy": [
            {"question": "Which of the following is a type of OS?", 
             "options": ["Batch", "Compiler", "Linker", "Loader"], 
             "answer": "Batch"},
            {"question": "Which is the core part of an operating system?", 
             "options": ["Shell", "Kernel", "Command", "Script"], 
             "answer": "Kernel"}
        ],
        "Medium": [
            {"question": "Which scheduling algorithm gives the minimum average waiting time?", 
             "options": ["FCFS", "SJF", "RR", "Priority"], 
             "answer": "SJF"}
        ],
        "Hard": [
            {"question": "Which of the following is not a type of fragmentation?", 
             "options": ["Internal", "External", "File", "None"], 
             "answer": "File"}
        ],
    },

    "java": {
        "Easy": [
            {"question": "Which keyword is used to create a class in Java?", 
             "options": ["class", "Class", "define", "object"], 
             "answer": "class"},
            {"question": "Which method is the entry point of a Java program?", 
             "options": ["main()", "start()", "init()", "run()"], 
             "answer": "main()"}
        ],
        "Medium": [
            {"question": "Which of the following is not a Java primitive type?", 
             "options": ["int", "float", "boolean", "string"], 
             "answer": "string"}
        ],
        "Hard": [
            {"question": "Which concept allows multiple methods with the same name?", 
             "options": ["Overloading", "Overriding", "Encapsulation", "Abstraction"], 
             "answer": "Overloading"}
        ],
    },

    "c": {
        "Easy": [
            {"question": "Which of the following is used to print output in C?", 
             "options": ["print()", "printf()", "cout", "cin"], 
             "answer": "printf()"},
            {"question": "Which header file is required for printf()?", 
             "options": ["<stdio.h>", "<stdlib.h>", "<conio.h>", "<math.h>"], 
             "answer": "<stdio.h>"}
        ],
        "Medium": [
            {"question": "Which operator is used to get the address of a variable?", 
             "options": ["&", "*", "%", "#"], 
             "answer": "&"}
        ],
        "Hard": [
            {"question": "Which of the following is not a storage class in C?", 
             "options": ["auto", "static", "register", "define"], 
             "answer": "define"}
        ],
    },

    "c++": {
        "Easy": [
            {"question": "Which of the following is used to print output in C++?", 
             "options": ["print()", "printf()", "cout", "echo"], 
             "answer": "cout"},
            {"question": "Which operator is used for scope resolution in C++?", 
             "options": ["::", "->", ".", ":"], 
             "answer": "::"}
        ],
        "Medium": [
            {"question": "Which feature of OOP allows reusing code?", 
             "options": ["Encapsulation", "Polymorphism", "Inheritance", "Abstraction"], 
             "answer": "Inheritance"}
        ],
        "Hard": [
            {"question": "Which of the following is not a valid access specifier in C++?", 
             "options": ["public", "private", "protected", "secured"], 
             "answer": "secured"}
        ],
    },

    # Add more subjects as needed: economics, accountancy, business studies, history, geography, sociology...
    "economics": {
        "Easy":[
            {"q":"What does GDP stand for?","options":["Gross Domestic Product","Global Domestic Product","Government Debt Product","Gross Domestic Price"],"ans":"Gross Domestic Product"},
            {"q":"What is scarce resource?","options":["Limited resource","Unlimited resource","Free resource","Abundant resource"],"ans":"Limited resource"},
            {"q":"What is interest?","options":["Cost of borrowing money","Rent","Wage","Profit"],"ans":"Cost of borrowing money"},
            {"q":"Who introduced invisible hand?","options":["Adam Smith","Keynes","Marx","Ricardo"],"ans":"Adam Smith"},
        ],
        "Medium":[
            {"q":"Demand curve slopes:","options":["Downward","Upward","Vertical","Horizontal"],"ans":"Downward"},
            {"q":"What is inflation?","options":["Rise in general price level","Fall in prices","Stable prices","No change"],"ans":"Rise in general price level"},
            {"q":"What is scarcity?","options":["Limited resources","Enough resources","Free goods","Unlimited goods"],"ans":"Limited resources"},
            {"q":"What is barter?","options":["Direct exchange of goods","Use of money","Banking service","Taxation"],"ans":"Direct exchange of goods"},
        ],
        "Hard":[
            {"q":"What is opportunity cost?","options":["Next best alternative foregone","Actual cost","Sunk cost","Accounting cost"],"ans":"Next best alternative foregone"},
            {"q":"Which curve shows production possibilities?","options":["PPC","AD-AS","Supply","Demand"],"ans":"PPC"},
            {"q":"What is monetary policy?","options":["Control by central bank","Fiscal action","Tax policy","Trade policy"],"ans":"Control by central bank"},
            {"q":"What is Gini coefficient used for?","options":["Income inequality","Inflation measurement","Output measure","Trade balance"],"ans":"Income inequality"},
        ],
    },

    # Minimal placeholder for other subjects so selection recognizes them.
    "history": {"Easy":[{"q":"Who was first Mughal emperor?","options":["Babur","Akbar","Shah Jahan","Humayun"],"ans":"Babur"}], "Medium":[], "Hard":[]},
    "geography": {"Easy":[{"q":"Largest continent is?","options":["Asia","Africa","Europe","Antarctica"],"ans":"Asia"}], "Medium":[], "Hard":[]},
    "accountancy": {"Easy":[{"q":"Basic accounting eqn is:","options":["Assets = Liabilities + Equity","Assets + Liabilities = Equity","Assets = Revenue - Expenses","Assets = Capital - Liabilities"],"ans":"Assets = Liabilities + Equity"}], "Medium":[], "Hard":[]},
    "business studies": {"Easy":[{"q":"Primary motive of business is?","options":["Profit Earning","Charity","Service","Employment"],"ans":"Profit Earning"}], "Medium":[], "Hard":[]},
    "sociology": {"Easy":[{"q":"Study of society is called?","options":["Sociology","Psychology","Anthropology","Economics"],"ans":"Sociology"}], "Medium":[], "Hard":[]},
}

# Helper to list valid subjects based on our bank keys
BANK_SUBJECTS = sorted(list(QUESTION_BANK.keys()))

# ---- Quiz Generator utilities ----

def get_available_questions(subject, difficulty):
    """Return list of question dicts for subject & difficulty (subject already normalized)."""
    subj_lower = subject.lower()
    bank = QUESTION_BANK.get(subj_lower, {})
    return bank.get(difficulty, [])

def sample_questions(subject, difficulty, num_questions):
    """Return up to num_questions unique questions (no repeats)."""
    pool = get_available_questions(subject, difficulty)
    if not pool:
        return []
    # ensure we don't mutate original
    pool_copy = pool[:]
    random.shuffle(pool_copy)
    if num_questions >= len(pool_copy):
        return pool_copy
    return pool_copy[:num_questions]

# ---------------------------
# UI: Combined App
# ---------------------------

st.set_page_config(page_title="AI Study Assistant + Quiz Generator", layout="wide")
st.title("📚 AI-Powered Smart Study Assistant")

# Tabs:
tab1, tab2, tab3 = st.tabs(["📅 Study Planner", "❓ Question Generator", "📝 Quiz Generator"])

# ---------------------------
# Tab 1 - Study Planner 
# ---------------------------
with tab1:
    st.header("📅 Create Your Study Planner")

    exam_date = st.date_input("Select Exam Date", min_value=datetime.date.today())
    daily_hours = st.number_input("Enter study hours per day", min_value=1, max_value=12, value=4)

    st.subheader("Add Subjects")
    subjects = []
    num_subjects = st.number_input("Number of subjects", min_value=1, max_value=10, value=3)

    for i in range(num_subjects):
        col1, col2 = st.columns(2)
        with col1:
            subject_name = st.text_input(f"Subject {i+1} Name", key=f"subject_{i}").strip().lower()
        with col2:
            difficulty = st.selectbox(f"Difficulty for {i+1}", ["Easy", "Medium", "Hard"], key=f"diff_{i}")
        if subject_name:
            if subject_name not in VALID_SUBJECTS:
                st.error(f"⚠ '{subject_name}' is not a valid subject name. Please enter a real subject.")
            else:
                subjects.append((subject_name.capitalize(), difficulty))

    if st.button("Generate Study Plan"):
        if subjects:
            plan = generate_study_plan(subjects, exam_date, daily_hours)

            if isinstance(plan[0], dict):
                st.success("✅ Study Plan Generated!")

                df = pd.DataFrame(plan)
                st.dataframe(df)

                # Download as Excel
                excel_file = io.BytesIO()
                df.to_excel(excel_file, index=False, engine="openpyxl")
                excel_file.seek(0)
                st.download_button("⬇ Download as Excel", data=excel_file, file_name="study_plan.xlsx")

                # Download as PDF
                pdf_bytes = export_plan_to_pdf(plan)
                st.download_button("⬇ Download as PDF", data=pdf_bytes, file_name="study_plan.pdf", mime="application/pdf")
            else:
                st.error(plan[0])
        else:
            st.warning("⚠ Please enter at least one valid subject.")

# ---------------------------
# Tab 2 - Question Generator 
# --------------------------
with tab2:
    st.header("❓ AI Question Generator")

    uploaded_file = st.file_uploader("📂 Upload syllabus (PDF or TXT)", type=["pdf", "txt"])

    def clean_text(text):
        text = re.sub(r'(?i)(lecture\s*notes?|prepared\s*by.|page\s\d+|contents?|index|chapter\s*\d+)', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # Short 4–5 word question maker
    def shorten(q):
        words = q.split()
        return " ".join(words[:5]).capitalize()

    def generate_questions_from_text(text):
        # Extract keywords/concepts from text
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 30]
        random.shuffle(sentences)

        mcqs, very_short, short_qs, long_qs = [], [], [], []

        # Predefined question patterns
        patterns = [
            "Write a detailed note on {}",
            "Explain the difference between {} and {}",
            "Explain the types of {}",
            "Describe the architecture of {}",
            "Explain the concept of {}"
        ]

        for i, s in enumerate(sentences[:20]):
            concept = s.split()[0:5]  # take first few words as concept
            concept_text = " ".join(concept)

            # MCQs
            if i < 5:
                mcq_question = f"{patterns[i % len(patterns)].format(concept_text, concept_text)}"
                options = [f"{concept_text} Option {x}" for x in "ABCD"]
                answer = options[0]
                mcqs.append((mcq_question, options, answer))

            # Very Short
            elif i < 10:
                very_short.append(f"Define briefly: {concept_text}")

            # Short
            elif i < 15:
                short_qs.append(f"Explain shortly: {patterns[i % len(patterns)].format(concept_text, concept_text)}")

            # Long
            else:
                long_qs.append(f"{patterns[i % len(patterns)].format(concept_text, concept_text)}")

        return {"MCQ": mcqs, "Very Short": very_short, "Short": short_qs, "Long": long_qs}


    def export_questions_to_pdf(questions_dict):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        y = height - 50
        c.setFont("Helvetica", 12)

        for q_type, q_list in questions_dict.items():
            c.drawString(50, y, f"{q_type} Questions:")
            y -= 25
            for i, q in enumerate(q_list, 1):
                if y < 80:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 50
                c.drawString(50, y, f"{i}. {q}")
                y -= 25
            y -= 20

        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    if uploaded_file is not None:
        file_name = uploaded_file.name

        if file_name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            text = uploaded_file.read().decode("utf-8", errors="ignore")

        text = clean_text(text)
        questions = generate_questions_from_text(text)

        st.subheader("📘 Choose question type to view:")

        col1, col2, col3 = st.columns(3)
        selected_type = None

        with col1:
            if st.button("🔵 Very Short"):
                selected_type = "Very Short"
        with col2:
            if st.button("🟣 Short"):
                selected_type = "Short"
        with col3:
            if st.button("🟠 Long"):
                selected_type = "Long"

        if selected_type:
            st.success(f"✅ {selected_type} Questions Generated!")

            for q in questions[selected_type]:
                st.markdown(f"Q: {q}")
                st.markdown("---")

            pdf_bytes = export_questions_to_pdf({selected_type: questions[selected_type]})
            st.download_button(
                label="⬇ Download as PDF",
                data=pdf_bytes,
                file_name=f"{selected_type}_questions.pdf",
                mime="application/pdf"
            )

# ---------------------------
# Tab 3 - Quiz Generator 
# ---------------------------
with tab3:
    st.header("📝 Quiz Generator (Pre-set MCQs)")

    st.markdown("Select Subject and Difficulty. Default is **None — choose both to load questions.")
    col_subj, col_diff, col_num = st.columns([2,2,2])

    # Subject selector with "None" default
    subject_choice = col_subj.selectbox("Choose Subject", options=["None"] + BANK_SUBJECTS, index=0, key="quiz_subject_choice")

    # Difficulty selector with "None" default
    difficulty_choice = col_diff.selectbox("Choose Difficulty", options=["None", "Easy", "Medium", "Hard"], index=0, key="quiz_difficulty_choice")

    # Number of questions
    num_questions_requested = col_num.number_input("Number of Questions", min_value=1, max_value=50, value=5, key="quiz_num_questions")

    st.markdown("---")

    # Validate subject
    if subject_choice == "None" or difficulty_choice == "None":
        st.info("Please select both Subject and Difficulty to load questions.")
        # ensure quiz state cleared
        if 'quiz3' in st.session_state:
            st.session_state.pop('quiz3', None)
        if 'answers3' in st.session_state:
            st.session_state.pop('answers3', None)
        if 'submitted3' in st.session_state:
            st.session_state.pop('submitted3', None)
    else:
        # handle invalid subject (shouldn't happen since choices from bank) but check
        if subject_choice.lower() not in QUESTION_BANK:
            st.error(f'⚠ "{subject_choice}" is not a valid subject. Please select a valid subject.')
        else:
            # fetch available pool size
            pool = get_available_questions(subject_choice, difficulty_choice)
            available = len(pool)

            if available == 0:
                st.warning(f"Available questions: only 0 for {subject_choice} ({difficulty_choice}). Please choose another subject/difficulty.")
                # clear session quiz
                st.session_state.quiz3 = []
            else:
                if num_questions_requested > available:
                    st.warning(f"Available questions: only {available}. Showing all available questions.")
                    num_to_use = available
                else:
                    num_to_use = num_questions_requested

                # Build quiz if not already or if parameters changed
                rebuild = False
                if 'quiz_params' not in st.session_state:
                    rebuild = True
                else:
                    prev = st.session_state.quiz_params
                    if prev.get('subject') != subject_choice or prev.get('difficulty') != difficulty_choice or prev.get('num') != num_to_use:
                        rebuild = True

                if rebuild:
                    st.session_state.quiz_params = {'subject': subject_choice, 'difficulty': difficulty_choice, 'num': num_to_use}
                    st.session_state.quiz3 = sample_questions(subject_choice, difficulty_choice, num_to_use)
                    # initialize answers dict with None to ensure no pre-selection
                    st.session_state.answers3 = {i: None for i in range(len(st.session_state.quiz3))}
                    st.session_state.submitted3 = False

                st.info(f"Quiz loaded: {len(st.session_state.quiz3)} question(s) — {subject_choice} ({difficulty_choice})")

                # Display quiz questions
                for idx, q in enumerate(st.session_state.quiz3):
                    st.markdown(f"Q{idx+1}. {q.get('q', q.get('question', ''))}")
                    # ensure options listed but no option pre-selected
                    # Streamlit radio requires an index, so we implement with radio + a placeholder default that doesn't match any option (None)
                    # To avoid preselection, we will render as radio with options and set index to 0 only if user had previously selected.
                    prev_choice = st.session_state.answers3.get(idx, None)
                    options = q['options'][:]
                    # Show radio - to avoid auto-selection we supply index only when prev_choice is not None
                    try:
                        if prev_choice in options:
                            default_index = options.index(prev_choice)
                        else:
                            default_index = None
                        choice = st.radio("Select your answer:", options, index=None, key=f"quiz3_q{idx}", disabled=st.session_state.submitted3)
                        # BUT to simulate "no pre-selection", if previously None and we set index=0, it will select 1st option — so we handle by:
                        # If there was no prev_choice and not submitted, we treat the selection as None until user actively changes it.
                        # We detect whether the widget changed from default by storing a hidden marker per question.
                        marker_key = f"marker_q{idx}"
                        if marker_key not in st.session_state:
                            # first render; record the initial selection as sentinel
                            st.session_state[marker_key] = choice
                            # do not record into answers yet (leave None)
                            if st.session_state[marker_key] == choice and st.session_state.answers3[idx] is None:
                                # keep None
                                pass
                        # If user interacts (choice different from initial marker), set answer
                        if st.session_state[marker_key] != choice:
                            st.session_state.answers3[idx] = choice
                            st.session_state[marker_key] = choice
                    except Exception as e:
                        # fallback simple radio (shouldn't happen)
                        default_index=None
                        if idx in st.session_state.answer3 and st.session_state.answer3[idx] in options:
                            default_index= options.index(st.session_state.answer3[idx])

                        choice = st.radio(
                            "Select your answer:", 
                            options,
                            index=None,
                            key=f"quiz3_q{idx}"
                        )
                        if not st.session_state.submitted3:
                            st.session_state.answers3[idx] = choice

                    st.markdown("---")

                # Attempt count and submission logic
                total_q = len(st.session_state.quiz3)
                attempted_count = sum(1 for v in st.session_state.answers3.values() if v is not None)

                if not st.session_state.submitted3:
                    if attempted_count < total_q:
                        st.warning(f"Please attempt all {total_q} questions. Currently attempted: {attempted_count}")
                    submit_disabled = (attempted_count != total_q) or (total_q == 0)

                    if st.button("Submit Answers and Check Score", disabled=submit_disabled, key="submit_quiz3"):
                        st.session_state.submitted3 = True
                        # compute results
                        correct = 0
                        results = []
                        for i, q in enumerate(st.session_state.quiz3):
                            chosen = st.session_state.answers3.get(i)
                            correct_ans = q.get('ans') or q.get('answer')

                            is_correct = (chosen == correct_ans)
                            question_text = q.get('q') or q.get('question')
                            results.append((i, chosen, correct_ans, is_correct, question_text))

                            if is_correct:
                                correct += 1
                        st.session_state.quiz3_results = results
                        st.session_state.quiz3_score = (correct, total_q)
                        # rerun to show results
                        import streamlit as st; st.session_state["rerun"] = True

                else:
                    # Show per-question feedback & final score
                    results = st.session_state.get('quiz3_results', [])
                    correct, total_q = st.session_state.get('quiz3_score', (0, total_q))
                    score_percent = (correct / total_q) * 100 if total_q > 0 else 0

                    wrong_topics = []
                    for i, chosen, correct_ans, is_correct, qtext in results:
                        st.markdown(f"Q{i+1}. {qtext}")
                        if chosen is None:
                            st.warning(f"⚠ Not Attempted. The correct answer was {correct_ans}.")
                        elif is_correct:
                            st.success(f"✅ Correct! Your answer: {chosen}. (Correct: **{correct_ans})")
                        else:
                            st.error(f"❌ Incorrect. Your answer: {chosen}. Correct answer: **{correct_ans}.")
                            # Extract topic keywords (you can refine this)
                            topic_guess = qtext.split()[1:4]  # first few words after 'Q'
                            wrong_topics.append(" ".join(topic_guess))
                        st.markdown("---")

                    # final score and balloons for good performance
                    if score_percent >= 70:
                        st.balloons()
                        st.success(f"🎉 Excellent! You scored {correct} out of {total_q} ({score_percent:.1f}%).Try revising the topics you missed to strengthen your concepts.")
                    elif 50 <= score_percent < 70:
                        st.warning(f"👍 Good effort! You scored {correct} out of {total_q} ({score_percent:.1f}%). Try revising the topics you missed to strengthen your concepts.")
                    else:
                        st.error(f"⚠ You scored {correct} out of {total_q} ({score_percent:.1f}%). Your performance is below average — focus on understanding key topics again.")
                        
                    if wrong_topics:
                        st.markdown("### 🔍 Suggested Revision Topics:")
                        unique_topics = list(set(wrong_topics))
                        for t in unique_topics:
                            st.write(f"• Go through {t} again — you answered a related question incorrectly.")

                    if st.button("Start Another Quiz", key="restart_quiz3"):
                        # reset quiz state
                        st.session_state.pop('quiz3', None)
                        st.session_state.pop('answers3', None)
                        st.session_state.pop('submitted3', None)
                        st.session_state.pop('quiz3_results', None)
                        st.session_state.pop('quiz3_score', None)
                        st.session_state.pop('quiz_params', None)
                        # also remove markers
                        keys_to_remove = [k for k in list(st.session_state.keys()) if k.startswith("marker_q")]
                        for k in keys_to_remove:
                            st.session_state.pop(k, None)
                        st.experimental_rerun()
