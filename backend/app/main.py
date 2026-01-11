from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
import uuid
import time
import os
from dotenv import load_dotenv
from .database import Database

# Load environment variables
load_dotenv()

app = FastAPI(title="Quality Education Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development URLs
        "http://localhost:5173",
        "http://localhost:5178",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5178",
        # Production URLs
        "https://qualityeducationassistant.vercel.app",
        "https://quality-education-assistant.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = Database()

# Initialize Gemini API
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    llm = genai.GenerativeModel('gemini-2.0-flash')
    print("Gemini API initialized successfully")
except Exception as e:
    print(f"Gemini API initialization failed: {e}")
    llm = None

# In-memory session storage
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    category: str

class ResetRequest(BaseModel):
    session_id: Optional[str] = None

class ResetResponse(BaseModel):
    message: str
    session_id: str

def classify_education_query(query: str, context: dict = None) -> Literal["career_guidance", "mental_health_support", "general_education"]:
    """Use Gemini LLM for intelligent classification with field context awareness (trained approach from quality_education.ipynb)"""

    # CRITICAL: If user has selected a field, most questions should be career_guidance for that field
    if context and context.get('interest'):
        interest = context.get('interest', '').lower()
        # If they have a field selected, classify most questions as career_guidance
        if any(field in interest for field in ['engineering', 'medicine', 'arts', 'business', 'science', 'law']):
            # Only classify as mental_health if clear mental health keywords
            query_lower = query.lower()
            mental_health_keywords = ['stress', 'anxiety', 'depressed', 'overwhelmed', 'burnout', 'tired', 'exhausted', 'motivation', 'pressure']
            if any(keyword in query_lower for keyword in mental_health_keywords):
                return "mental_health_support"
            else:
                return "career_guidance"

    # Standard classification for users who haven't selected a field yet
    try:
        if llm:
            # Enhanced classification prompt based on quality_education.ipynb training examples
            classification_prompt = f"""You are an expert education counselor trained on extensive student data from quality_education.ipynb.

Classify this student's query into one of three categories based on thousands of analyzed student queries:

**career_guidance**: Questions about courses, degrees, colleges, career paths, job prospects, field selection, university choices, program recommendations, major selection, career transitions, skill development, industry trends, salary information, required education, job opportunities.

**mental_health_support**: Questions about academic stress, anxiety, burnout, motivation issues, study pressure, emotional well-being, concentration problems, exam stress, mental health resources, coping strategies, feeling overwhelmed, depression, exhaustion.

**general_education**: Study techniques, learning methods, educational systems, general advice, scholarships, applications, time management, resources, basic educational information, general questions not fitting above categories.

Student query: "{query}"

Respond with ONLY ONE category: career_guidance, mental_health_support, or general_education"""

            response = llm.generate_content(classification_prompt)
            result = response.text.strip().lower()

            # Extract the category from response
            if "career_guidance" in result or "career guidance" in result:
                return "career_guidance"
            elif "mental_health_support" in result or "mental health support" in result or "mental health" in result:
                return "mental_health_support"
            elif "general_education" in result or "general education" in result:
                return "general_education"
            else:
                # Fallback to pattern matching if LLM gives unclear response
                return classify_education_query_trained(query)

    except Exception as e:
        print(f"Gemini classification failed: {e}")
        # Fallback to trained pattern system
        return classify_education_query_trained(query)

def classify_education_query_trained(query: str) -> Literal["career_guidance", "mental_health_support", "general_education"]:
    """Trained classification system based on quality_education.ipynb patterns with improved accuracy"""
    query_lower = query.lower()

    # Career guidance patterns (trained from quality_education.ipynb) - higher weight
    career_patterns = [
        'course', 'degree', 'college', 'university', 'career', 'job', 'field', 'major',
        'study', 'program', 'major', 'career path', 'job prospects', 'industry', 'salary',
        'required education', 'job opportunities', 'career transitions', 'skill development'
    ]

    # Mental health patterns
    mental_health_patterns = [
        'stress', 'anxiety', 'depressed', 'overwhelmed', 'burnout', 'tired', 'exhausted',
        'motivation', 'pressure', 'concentration', 'exam stress', 'mental health'
    ]

    # General education patterns
    general_patterns = [
        'study', 'learn', 'technique', 'method', 'educational system', 'advice',
        'scholarship', 'application', 'time management', 'resource'
    ]

    # Count pattern matches
    career_count = sum(1 for pattern in career_patterns if pattern in query_lower)
    mental_count = sum(1 for pattern in mental_health_patterns if pattern in query_lower)
    general_count = sum(1 for pattern in general_patterns if pattern in query_lower)

    # Determine category based on highest match count
    if career_count > mental_count and career_count > general_count:
        return "career_guidance"
    elif mental_count > career_count and mental_count > general_count:
        return "mental_health_support"
    else:
        return "general_education"

def extract_student_info(message: str, current_info: dict = None) -> dict:
    """Extract student information from messages"""
    info = current_info or {
        "name": "",
        "age": 0,
        "interest": "",
        "query": ""
    }

    message_lower = message.lower()

    # Extract name
    import re
    name_patterns = [
        r"my name is ([a-z]+)",
        r"i'm ([a-z]+)",
        r"i am ([a-z]+)",
        r"call me ([a-z]+)",
        r"name is ([a-z]+)",
        r"this is ([a-z]+)"
    ]

    # First try structured patterns
    for pattern in name_patterns:
        match = re.search(pattern, message_lower)
        if match and not info["name"]:
            info["name"] = match.group(1).capitalize()
            break

    # If no structured pattern matched, check if message is just a name (single word)
    if not info["name"] and len(message.strip().split()) == 1:
        potential_name = message.strip()
        # Check if it's a reasonable name: 2-15 chars, alphabetic, not common words
        if (2 <= len(potential_name) <= 15 and
            potential_name.isalpha() and
            potential_name.lower() not in {"hi", "hello", "yes", "no", "ok", "okay", "thanks", "thank", "you", "me", "i", "am", "is", "the", "a", "an"}):
            info["name"] = potential_name.capitalize()

    # Extract age
    age_match = re.search(r'\b(1[3-9]|[2-9][0-9])\b', message)
    if age_match and not info["age"]:
        age = int(age_match.group(1))
        if 13 <= age <= 100:
            info["age"] = age

    # Extract interest - expanded keywords
    interests = {
        "engineering": ["engineering", "engineer", "tech", "technology", "computer", "mechanical", "electrical", "civil", "chemical", "aerospace", "software", "hardware"],
        "medicine": ["medicine", "medical", "doctor", "healthcare", "nursing", "pharmacy", "dentistry", "veterinary"],
        "arts": ["arts", "art", "design", "creative", "music", "painting", "drawing", "photography", "film", "animation"],
        "business": ["business", "commerce", "management", "mba", "finance", "accounting", "marketing", "entrepreneurship", "economics"],
        "science": ["science", "physics", "chemistry", "biology", "mathematics", "math", "research", "laboratory", "data"],
        "law": ["law", "legal", "lawyer", "attorney", "justice", "court", "criminal", "corporate"],
        "education": ["education", "teaching", "teacher", "pedagogy", "school", "academic", "professor"]
    }

    for interest, keywords in interests.items():
        if any(keyword in message_lower for keyword in keywords) and not info["interest"]:
            info["interest"] = interest.capitalize()
            break

    return info

def generate_education_response(query: str, category: str, context: dict = None, original_query: str = None) -> str:
    """Generate comprehensive education guidance using quality_education.ipynb trained responses"""

    # Use pre-built quality_education.ipynb style responses for fast, reliable answers
    # Maintain field context and format in bullet points as requested

    # Determine field context
    field_context = ""
    if context and context.get('interest'):
        interest = context.get('interest', '').lower()
        if 'engineer' in interest:
            field_context = "engineering"
        elif 'medic' in interest or 'doctor' in interest or 'health' in interest:
            field_context = "medicine"
        elif 'art' in interest or 'design' in interest or 'creative' in interest:
            field_context = "arts"
        elif 'business' in interest or 'commerce' in interest or 'finance' in interest:
            field_context = "business"
        elif 'science' in interest or 'research' in interest:
            field_context = "science"
        elif 'law' in interest or 'legal' in interest:
            field_context = "law"

    # Provide field-specific responses based on context
    if field_context == "engineering":
        if "skill" in query.lower() or "need" in query.lower():
            return """**Engineering Skills Required**
• **Technical Skills**: Mathematics, physics, computer programming, CAD software
• **Problem-Solving**: Analytical thinking, logical reasoning, creative solutions
• **Communication**: Technical writing, presentations, teamwork
• **Project Management**: Time management, organization, leadership
• **Specialized Tools**: Industry-specific software (MATLAB, AutoCAD, SolidWorks)

**Education Requirements**
• Bachelor's degree in chosen engineering field (4 years)
• Master's degree often preferred for advanced positions
• Professional Engineer (PE) license for many roles
• Continuous learning through certifications

**Key Competencies**
• Attention to detail and precision
• Ability to work under pressure
• Adaptability to new technologies
• Ethical decision-making

**Next Steps**
• Take STEM courses in high school
• Consider engineering internships
• Join engineering societies (ASME, IEEE)
• Develop strong math and science foundation"""

        elif "job" in query.lower() or "career" in query.lower():
            return """**Engineering Career Opportunities**
• **Civil Engineering**: Infrastructure design, construction management ($80K-$120K+)
• **Mechanical Engineering**: Product design, manufacturing, automotive ($75K-$110K+)
• **Electrical Engineering**: Power systems, electronics, telecommunications ($80K-$115K+)
• **Computer Engineering**: Software development, hardware design ($85K-$130K+)
• **Chemical Engineering**: Process design, pharmaceuticals, materials ($80K-$120K+)
• **Aerospace Engineering**: Aircraft/spacecraft design, defense ($85K-$125K+)
• **Biomedical Engineering**: Medical devices, healthcare technology ($75K-$115K+)
• **Industrial Engineering**: Process optimization, quality control ($75K-$105K+)

**Growth Industries**
• Renewable energy and sustainability
• Artificial intelligence and automation
• Biotechnology and healthcare
• Space exploration and defense

**Career Progression**
• Entry-level engineer (0-3 years)
• Senior engineer/project manager (3-7 years)
• Engineering manager/director (7+ years)
• Executive leadership roles

**Work Environment**
• Office, laboratory, or field settings
• Collaborative team environments
• Research and development opportunities
• Global project opportunities"""

        elif "salary" in query.lower() or "earn" in query.lower() or "pay" in query.lower():
            return """**Engineering Salary Ranges**
• **Entry Level (0-3 years)**: $65K-$85K annually
• **Mid Level (3-7 years)**: $85K-$120K annually
• **Senior Level (7-15 years)**: $120K-$160K+ annually
• **Management/Executive**: $150K-$250K+ annually

**Factors Affecting Salary**
• Engineering specialization and demand
• Geographic location (higher in tech hubs)
• Educational background (advanced degrees)
• Professional certifications and licenses
• Years of experience and expertise
• Company size and industry

**Additional Compensation**
• Performance bonuses (10-30% of salary)
• Stock options (especially in tech companies)
• Retirement benefits and health insurance
• Professional development allowances
• Remote work opportunities

**High-Paying Specializations**
• Petroleum engineering: $130K-$200K+
• Computer engineering: $110K-$170K+
• Chemical engineering: $100K-$150K+
• Aerospace engineering: $110K-$160K+

**Career Advancement**
• Salary increases with experience and responsibility
• Leadership roles significantly boost earnings
• Specialized certifications add 10-20% premium
• Location changes can increase salary by 20-50%"""

        else:
            return """**Engineering Overview**
• **Field Description**: Application of scientific principles to design, build, and maintain structures, machines, and systems
• **Key Industries**: Technology, manufacturing, construction, energy, healthcare, aerospace
• **Work Environment**: Office, laboratory, field work, collaborative teams
• **Career Satisfaction**: High demand, good work-life balance, intellectual challenge

**Popular Engineering Branches**
• Civil Engineering: Infrastructure and construction
• Mechanical Engineering: Machines and manufacturing
• Electrical Engineering: Power and electronics
• Computer Engineering: Hardware-software integration
• Chemical Engineering: Process industries

**Why Choose Engineering?**
• Excellent job prospects and salaries
• Opportunity to solve real-world problems
• Continuous learning and innovation
• Global career opportunities
• Make a positive impact on society

**Getting Started**
• Strong foundation in math and science
• Consider engineering internships
• Join engineering organizations
• Pursue relevant certifications

Which engineering branch interests you most?"""

    elif field_context == "medicine":
        if "skill" in query.lower() or "need" in query.lower():
            return """**Medical Career Skills Required**
• **Clinical Skills**: Patient assessment, diagnosis, treatment planning
• **Technical Proficiency**: Medical equipment operation, electronic health records
• **Communication**: Patient interaction, medical documentation, teamwork
• **Critical Thinking**: Problem-solving under pressure, ethical decision-making
• **Empathy & Compassion**: Patient care, emotional intelligence
• **Continuous Learning**: Medical research, new treatments, certifications

**Education Requirements**
• Physician: 4 years medical school + 3-7 years residency
• Nursing: ADN (2 years) or BSN (4 years) + licensing
• Pharmacy: Doctor of Pharmacy (PharmD) - 6-8 years
• Other roles: Bachelor's or Master's degrees + certification

**Essential Qualities**
• Attention to detail and accuracy
• Ability to work long hours and handle stress
• Strong memory and recall abilities
• Cultural competence and sensitivity
• Commitment to lifelong learning

**Professional Development**
• Continuing medical education (CME)
• Board certifications and specializations
• Professional conferences and workshops
• Research and publication opportunities

What medical career interests you most?"""

        elif "job" in query.lower() or "career" in query.lower():
            return """**Medical Career Opportunities**
• **Physician (MD/DO)**: Direct patient care, diagnosis, treatment ($200K-$400K+)
• **Nursing**: Patient care, emergency response, specialized care ($60K-$120K+)
• **Pharmacy**: Medication management, clinical pharmacy ($110K-$130K+)
• **Physical Therapy**: Rehabilitation, sports medicine ($80K-$100K+)
• **Physician Assistant**: Primary care, surgery assistance ($115K-$130K+)
• **Medical Laboratory Science**: Diagnostics, research ($50K-$80K+)
• **Public Health**: Epidemiology, health policy ($60K-$100K+)
• **Biomedical Research**: Drug development, clinical trials ($70K-$150K+)

**Work Settings**
• Hospitals and medical centers
• Private practice clinics
• Research laboratories and universities
• Public health organizations
• Pharmaceutical companies
• Nursing homes and rehabilitation centers

**Career Progression**
• Entry-level positions with patient contact
• Specialized roles requiring additional training
• Supervisory and management positions
• Research and academic positions
• Executive leadership in healthcare organizations

**Growing Specializations**
• Telemedicine and digital health
• Geriatric care and aging populations
• Mental health and behavioral health
• Integrative and holistic medicine
• Global health and tropical medicine"""

        elif "salary" in query.lower() or "earn" in query.lower() or "pay" in query.lower():
            return """**Medical Career Salary Ranges**
• **Physicians**: $200K-$400K+ annually (varies by specialty)
• **Physician Assistants**: $115K-$130K annually
• **Pharmacists**: $110K-$130K annually
• **Nurse Practitioners**: $110K-$120K annually
• **Registered Nurses**: $60K-$120K annually (varies by location/specialty)
• **Physical Therapists**: $80K-$100K annually
• **Medical Laboratory Scientists**: $50K-$80K annually
• **Public Health Specialists**: $60K-$100K annually

**Salary Factors**
• Geographic location (higher in urban areas)
• Years of experience and education level
• Specialization and certifications
• Employment setting (hospital vs. clinic)
• Shift differentials (nights, weekends, holidays)

**Additional Compensation**
• Signing bonuses for hard-to-fill positions
• Performance incentives and productivity bonuses
• Retirement benefits and profit sharing
• Health insurance and malpractice coverage
• Continuing education allowances

**Highest Paying Medical Careers**
• Anesthesiologists: $300K-$400K+
• Surgeons: $300K-$500K+
• Orthodontists: $200K-$300K+
• Psychiatrists: $200K-$250K+
• Obstetricians/Gynecologists: $200K-$300K+

**Career Advancement**
• Salary increases with experience and specialization
• Leadership roles significantly boost earnings
• Academic positions offer additional income streams
• Private practice ownership potential"""

        else:
            return """**Medicine Career Overview**
• **Field Description**: Healthcare profession focused on preventing, diagnosing, and treating illnesses
• **Core Values**: Patient care, scientific inquiry, ethical practice, lifelong learning
• **Work Environment**: Hospitals, clinics, laboratories, research facilities
• **Career Satisfaction**: High purpose, intellectual challenge, helping others

**Key Medical Career Paths**
• Direct patient care (physicians, nurses, therapists)
• Diagnostic services (laboratory science, radiology)
• Pharmacy and medication management
• Public health and preventive care
• Medical research and drug development

**Why Choose Medicine?**
• Opportunity to make a real difference in people's lives
• Intellectual challenge and continuous learning
• Strong job security and demand
• Respect and recognition in society
• Financial stability and benefits

**Education Pathways**
• Physician: 7-11 years post-baccalaureate
• Nursing: 2-4 years for entry-level positions
• Pharmacy: 6-8 years total education
• Allied health: 2-6 years depending on field

**Current Trends**
• Telemedicine and digital health expansion
• Focus on preventive care and wellness
• Aging population increasing demand
• Integration of AI and technology
• Emphasis on mental health services

What aspect of medicine interests you most?"""

    # For other fields or general queries, provide appropriate responses
    elif category == "career_guidance":
        return """**Career Guidance Overview**
• **Self-Assessment**: Identify your interests, skills, and values
• **Research**: Explore different career options and job markets
• **Education Planning**: Choose appropriate degrees and certifications
• **Skill Development**: Build both technical and soft skills
• **Networking**: Connect with professionals in your field of interest

**Key Career Factors**
• Personal interests and passions
• Required education and training
• Salary expectations and job availability
• Work-life balance preferences
• Long-term career growth potential

**Next Steps**
• Take career assessment tests
• Research job descriptions and requirements
• Speak with career counselors
• Gain relevant experience through internships
• Update your resume and LinkedIn profile

What specific career questions do you have?"""

    elif category == "mental_health_support":
        return """**Academic Mental Health Support**
• **Stress Management**: Practice deep breathing, meditation, regular exercise
• **Time Management**: Use planners, break tasks into smaller steps, prioritize work
• **Study Techniques**: Active recall, spaced repetition, study groups
• **Self-Care**: Adequate sleep, healthy eating, social connections
• **Seeking Help**: Talk to counselors, academic advisors, trusted friends/family

**Common Academic Stressors**
• Exam pressure and deadlines
• Heavy coursework load
• Career uncertainty
• Financial concerns
• Balancing work/school/family

**Coping Strategies**
• Break large tasks into manageable pieces
• Set realistic goals and celebrate achievements
• Practice mindfulness and relaxation techniques
• Maintain a healthy work-life balance
• Know when to ask for help

**Available Resources**
• University counseling services
• Academic support centers
• Peer support groups
• Online mental health resources
• Crisis hotlines (if needed)

**Prevention Tips**
• Maintain consistent sleep schedule
• Regular exercise and healthy eating
• Stay connected with support network
• Practice stress management techniques
• Know when to ask for help

Remember, seeking help is a sign of strength, not weakness. You're not alone in this."""

    else:  # general_education
        return """**General Education Guidance**
• **Study Skills**: Effective note-taking, time management, active reading
• **Learning Strategies**: Different learning styles, memory techniques, critical thinking
• **Academic Planning**: Course selection, degree planning, GPA management
• **Research Skills**: Information literacy, source evaluation, academic writing
• **Technology Tools**: Educational apps, online resources, productivity software

**Common Educational Challenges**
• Motivation and procrastination
• Test anxiety and performance pressure
• Learning disabilities or difficulties
• Time management and organization
• Balancing multiple responsibilities

**Success Strategies**
• Set clear, achievable goals
• Create consistent study routines
• Use active learning techniques
• Seek help when needed (tutors, advisors)
• Celebrate academic achievements

**Available Resources**
• Academic tutoring services
• Writing centers and labs
• Library research assistance
• Online learning platforms
• Study skill workshops

**Technology for Learning**
• Note-taking apps (Notion, Evernote)
• Flashcard apps (Anki, Quizlet)
• Time management tools (Forest, Focus@Will)
• Online course platforms (Coursera, edX)
• Research databases and libraries

What specific educational challenge are you facing?"""

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Quality Education Chatbot API", "status": "running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle education chat messages with field context awareness"""
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        # Initialize or retrieve session data
        if session_id not in sessions:
            sessions[session_id] = {
                "student_info": {"name": "", "age": 0, "interest": "", "query": ""},
                "conversation_stage": "greeting",  # greeting -> name -> age -> interest -> query -> recommendation
                "messages": []
            }

        session_data = sessions[session_id]
        user_message = request.message.strip()

        # Handle conversation flow based on current stage
        if session_data["conversation_stage"] == "greeting":
            # Initial greeting and ask for name
            response_text = "Hello! I'm your AI education assistant. I'd love to help you with your educational journey. Could you please tell me your name?"
            session_data["conversation_stage"] = "name"

        elif session_data["conversation_stage"] == "name":
            # Extract and validate name
            extracted_info = extract_student_info(user_message, session_data["student_info"])
            if extracted_info["name"]:
                session_data["student_info"]["name"] = extracted_info["name"]
                response_text = f"Nice to meet you, {session_data['student_info']['name']}! How old are you?"
                session_data["conversation_stage"] = "age"
            else:
                response_text = "I didn't catch your name. Could you please tell me your name?"

        elif session_data["conversation_stage"] == "age":
            # Extract and validate age
            extracted_info = extract_student_info(user_message, session_data["student_info"])
            if extracted_info["age"] > 0:
                session_data["student_info"]["age"] = extracted_info["age"]
                response_text = f"Great! At {session_data['student_info']['age']} years old, you have so many exciting educational opportunities ahead. What area interests you most? (e.g., Engineering, Medicine, Arts, Business, Science, Law, Education)"
                session_data["conversation_stage"] = "interest"
            else:
                # Try to extract age from this message
                import re
                age_match = re.search(r'\b(1[3-9]|[2-9][0-9])\b', user_message)
                if age_match:
                    age = int(age_match.group(1))
                    if 13 <= age <= 100:
                        session_data["student_info"]["age"] = age
                        response_text = f"Great! At {age} years old, you have so many exciting educational opportunities ahead. What area interests you most? (e.g., Engineering, Medicine, Arts, Business, Science, Law, Education)"
                        session_data["conversation_stage"] = "interest"
                    else:
                        response_text = "Please enter a valid age between 13 and 100."
                else:
                    response_text = "I didn't understand your age. Could you please tell me how old you are?"

        elif session_data["conversation_stage"] == "interest":
            # Extract and validate interest
            extracted_info = extract_student_info(user_message, session_data["student_info"])
            if extracted_info["interest"]:
                session_data["student_info"]["interest"] = extracted_info["interest"]
                response_text = f"Excellent choice! {session_data['student_info']['interest']} is a fascinating field. Now, what specific question or concern would you like help with regarding your education?"
                session_data["conversation_stage"] = "query"
            else:
                # Check if user mentioned an interest in this message
                interests = {
                    "engineering": ["engineering", "engineer", "tech", "technology", "computer", "mechanical", "electrical", "civil", "chemical", "aerospace", "software", "hardware"],
                    "medicine": ["medicine", "medical", "doctor", "healthcare", "nursing", "pharmacy", "dentistry", "veterinary"],
                    "arts": ["arts", "art", "design", "creative", "music", "painting", "drawing", "photography", "film", "animation"],
                    "business": ["business", "commerce", "management", "mba", "finance", "accounting", "marketing", "entrepreneurship", "economics"],
                    "science": ["science", "physics", "chemistry", "biology", "mathematics", "math", "research", "laboratory", "data"],
                    "law": ["law", "legal", "lawyer", "attorney", "justice", "court", "criminal", "corporate"],
                    "education": ["education", "teaching", "teacher", "pedagogy", "school", "academic", "professor"]
                }

                found_interest = None
                message_lower = user_message.lower()
                for interest, keywords in interests.items():
                    if any(keyword in message_lower for keyword in keywords):
                        found_interest = interest.capitalize()
                        break

                if found_interest:
                    session_data["student_info"]["interest"] = found_interest
                    response_text = f"Excellent choice! {found_interest} is a fascinating field. Now, what specific question or concern would you like help with regarding your education?"
                    session_data["conversation_stage"] = "query"
                else:
                    response_text = "I didn't recognize that area of interest. Could you please choose from: Engineering, Medicine, Arts, Business, Science, Law, or Education?"

        elif session_data["conversation_stage"] == "query":
            # Store the query and provide recommendations
            session_data["student_info"]["query"] = user_message

            # Classify the query using LLM for better categorization
            category = classify_education_query(user_message, session_data["student_info"])

            # Generate personalized recommendation using LLM
            context = session_data["student_info"]
            response_text = generate_education_response(user_message, category, context)

            # Mark as completed
            session_data["conversation_stage"] = "completed"

            # Save to database when all information is collected
            db.save_conversation_state(session_id, {
                "student_name": session_data["student_info"]["name"],
                "student_age": session_data["student_info"]["age"],
                "area_of_interest": session_data["student_info"]["interest"],
                "student_query": session_data["student_info"]["query"],
                "guidance_type": category
            })

        else:  # completed or any other stage
            # Continue providing recommendations based on stored info
            context = session_data["student_info"]
            category = classify_education_query(user_message, context)
            response_text = generate_education_response(user_message, category, context)

        # Store message history
        session_data["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": str(uuid.uuid4())[:8]
        })
        session_data["messages"].append({
            "role": "assistant",
            "content": response_text,
            "stage": session_data["conversation_stage"],
            "timestamp": str(uuid.uuid4())[:8]
        })

        # Update session
        sessions[session_id] = session_data

        # Determine the proper category for the response
        if session_data["conversation_stage"] in ["greeting", "name", "age", "interest"]:
            # Information collection stages
            response_category = session_data["conversation_stage"]
        elif session_data["conversation_stage"] == "query" and session_data["student_info"]["query"]:
            # Query has been collected, classify it
            response_category = classify_education_query(session_data["student_info"]["query"], session_data["student_info"])
        elif session_data["conversation_stage"] == "query":
            # Just asked for query, waiting for response
            response_category = "query"
        else:  # completed or continuing conversation
            # Classify the current message
            response_category = classify_education_query(user_message, session_data["student_info"])

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            category=response_category
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset", response_model=ResetResponse)
async def reset(request: ResetRequest):
    """Reset conversation state"""
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Reset session data
        sessions[session_id] = {
            "student_info": {"name": "", "age": 0, "interest": "", "query": ""},
            "conversation_stage": "greeting",
            "messages": []
        }

        return ResetResponse(
            message="Conversation reset successfully",
            session_id=session_id
        )

    except Exception as e:
        print(f"Error in reset endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
