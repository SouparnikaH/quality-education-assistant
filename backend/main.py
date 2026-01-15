from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
import uuid
import time
import os
from dotenv import load_dotenv
from app.database import Database

# Load environment variables
load_dotenv()

app = FastAPI(title="Quality Education Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development URLs
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
        "http://127.0.0.1:5180",
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

# Initialize Gemini API with fallback models
llm = None
try:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key and not api_key.startswith("your_") and not api_key.startswith("AIzaSyAlUIt0b7ew08vscFLB7F6nYREOHkEiH4A"):
        genai.configure(api_key=api_key)

        # Try different models in order of preference
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-2.0-flash']

        for model_name in models_to_try:
            try:
                llm = genai.GenerativeModel(model_name)
                # Test the model with a simple request
                test_response = llm.generate_content("Test")
                if test_response and test_response.text:
                    print(f"SUCCESS: Gemini API initialized successfully with model: {model_name}")
                    break
            except Exception as e:
                print(f"WARNING: Model {model_name} failed: {str(e)[:100]}...")
                llm = None
                continue

        if llm is None:
            print("ERROR: All Gemini models failed - using static responses only")
            print("HINT: To enable AI responses, get a new API key from: https://aistudio.google.com/")
    else:
        print("WARNING: Gemini API key not configured or using leaked key - using static responses")
        print("HINT: To enable AI responses, get a new API key from: https://aistudio.google.com/")
        llm = None

except Exception as e:
    print(f"ERROR: Gemini API initialization failed: {str(e)[:100]}...")
    print("INFO: Using static responses - chatbot will still work without AI")
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
    """Generate intelligent education guidance using Gemini AI with context awareness"""

    print(f"Generating response for query: '{query}', category: '{category}', LLM available: {llm is not None}")

    # Build personalized context
    student_name = context.get('name', '') if context else ''
    student_age = context.get('age', 0) if context else 0
    student_interest = context.get('interest', '') if context else ''

    # Try to use Gemini AI for dynamic, intelligent responses
    if llm:
        try:
            print("Attempting to use Gemini AI for response generation...")

            # Create intelligent prompt for Gemini with personalized context
            personalized_intro = ""
            if student_name:
                personalized_intro = f"Hello {student_name}! "

            if student_age and student_age > 0:
                if student_age < 18:
                    tone_instruction = "Use an encouraging, supportive tone suitable for a younger student. Focus on building confidence and long-term planning."
                elif student_age < 25:
                    tone_instruction = "Use an energetic, practical tone suitable for a young adult exploring career options. Focus on immediate next steps and skill-building."
                else:
                    tone_instruction = "Use a professional, insightful tone suitable for someone considering career transitions or advancement."

            response_prompt = f"""You are an expert AI education counselor with extensive knowledge about careers, courses, and educational guidance.

{student_name and f'Student Name: {student_name}' or ''}
{student_age and f'Student Age: {student_age}' or ''}
{student_interest and f'Field of Interest: {student_interest}' or ''}

Student Query: "{query}"
Category: {category}
{tone_instruction if 'tone_instruction' in locals() else ''}

Please provide a comprehensive, helpful, and highly personalized response to this student's educational query. Make it conversational and engaging while being informative.

Format your response using:
- Clear sections with descriptive headers
- Bullet points for lists and key information
- Numbered steps where appropriate
- Bold text for important terms or emphasis

Include:
- Direct, actionable advice
- Specific examples relevant to their situation
- Realistic expectations and timelines
- Encouragement and motivation
- Follow-up questions or next steps

Adapt your response based on their age, interests, and the specific nature of their question."""

            response = llm.generate_content(response_prompt)
            ai_response = response.text.strip()

            # Ensure response is properly formatted
            if ai_response and len(ai_response) > 50:  # Ensure meaningful response
                print("Gemini AI response generated successfully")
                return f"{personalized_intro}{ai_response}"

        except Exception as e:
            print(f"Error: Gemini response generation failed: {e}")
            print("Falling back to enhanced static responses...")

    # Fallback to static responses if Gemini is not available or fails

    # Fallback to static responses if Gemini is not available
    # Determine field context for fallback responses
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

    # Create personalized introduction
    personalized_intro = ""
    if context and context.get('name'):
        personalized_intro = f"Hello {context['name']}! "

    if context and context.get('age') and context.get('age') > 0:
        if context['age'] < 18:
            age_context = "as a young person exploring your future"
        elif context['age'] < 25:
            age_context = "as someone starting your educational journey"
        else:
            age_context = "with your experience and perspective"
    else:
        age_context = "on your educational path"

    # Provide field-specific responses based on context
    if field_context == "engineering":
        if "skill" in query.lower() or "need" in query.lower():
            age_specific_advice = ""
            if context and context.get('age'):
                if context['age'] < 18:
                    age_specific_advice = """
**For Your Age Group:**
• Focus on high school STEM courses (Physics, Calculus, Computer Science)
• Participate in science fairs and robotics clubs
• Consider summer engineering camps or online courses
• Build a strong foundation in mathematics and physics"""
                elif context['age'] < 22:
                    age_specific_advice = """
**For College Students:**
• Take introductory engineering courses to explore specializations
• Join engineering student organizations on campus
• Seek undergraduate research opportunities
• Consider co-op or internship programs"""
                else:
                    age_specific_advice = """
**For Career Changers:**
• Assess your transferable skills from previous experience
• Consider bridge programs or certifications
• Network with engineering professionals
• Start with entry-level positions or apprenticeships"""

            return f"""{personalized_intro}Based on your interest in engineering {age_context}, here are the essential skills and requirements you'll need:

**Core Technical Skills**
• **Mathematics**: Calculus, Differential Equations, Linear Algebra, Statistics
• **Physics**: Mechanics, Thermodynamics, Electricity & Magnetism, Materials Science
• **Computer Programming**: Python, C/C++, MATLAB, Java (varies by specialization)
• **Engineering Fundamentals**: Statics, Dynamics, Fluid Mechanics, Heat Transfer

**Essential Soft Skills**
• **Problem-Solving**: Analytical thinking, creative solutions, systems thinking
• **Communication**: Technical writing, presentations, teamwork
• **Project Management**: Time management, organization, leadership
• **Critical Thinking**: Data analysis, decision-making, ethical reasoning

**Specialized Tools & Software**
• **CAD Software**: AutoCAD, SolidWorks, CATIA, Inventor
• **Analysis Tools**: MATLAB, ANSYS, COMSOL, LabVIEW
• **Programming**: Python, MATLAB, C++, JavaScript
• **Industry-Specific**: PLC programming, robotics software, simulation tools

**Education Pathways**
• **Bachelor's Degree**: 4-year program in your chosen engineering field
• **Master's Degree**: Often preferred for advanced positions (2 years)
• **Professional Licenses**: PE (Professional Engineer) license for many roles
• **Certifications**: Industry-specific credentials (AWS, PMP, etc.)

**Key Competencies for Success**
• Attention to detail and precision in work
• Ability to work under pressure and meet deadlines
• Adaptability to rapidly changing technologies
• Strong work ethic and commitment to excellence
• Continuous learning mindset{age_specific_advice}

**Recommended Next Steps**
• Research different engineering specializations to find your passion
• Build a strong foundation in mathematics and physics
• Gain practical experience through internships or projects
• Connect with engineering professionals for mentorship
• Consider joining engineering societies for networking and resources

What specific engineering field interests you most, or would you like more details about any of these areas?"""

        elif "job" in query.lower() or "career" in query.lower():
            career_focus = ""
            if context and context.get('age'):
                if context['age'] < 18:
                    career_focus = """
**Focus for High School Students:**
• Research engineering fields through online resources and career days
• Shadow engineers or participate in engineering internships
• Build a strong academic foundation for college admissions
• Consider engineering-focused summer programs"""
                elif context['age'] < 22:
                    career_focus = """
**Focus for College Students:**
• Explore different engineering specializations through coursework
• Gain practical experience through internships and co-ops
• Join professional engineering societies as a student member
• Develop both technical and soft skills for career readiness"""
                else:
                    career_focus = """
**Focus for Career Changers:**
• Assess transferable skills from your previous career
• Consider accelerated engineering programs or certifications
• Leverage your professional network for engineering opportunities
• Start with entry-level positions to gain engineering experience"""

            return f"""{personalized_intro}Engineering offers diverse and rewarding career opportunities {age_context}. Here are the main engineering career paths and their characteristics:

**Major Engineering Disciplines**

**🏗️ Civil Engineering** - Infrastructure & Construction
• Design and oversee construction of buildings, bridges, roads, and water systems
• Specializations: Structural, Environmental, Transportation, Geotechnical
• Salary Range: $75K-$120K+ annually
• Work Settings: Construction sites, offices, government agencies

**⚙️ Mechanical Engineering** - Machines & Systems
• Design, develop, and test mechanical systems and machines
• Specializations: Automotive, HVAC, Robotics, Manufacturing
• Salary Range: $75K-$115K+ annually
• Work Settings: Manufacturing plants, R&D labs, automotive companies

**⚡ Electrical Engineering** - Power & Electronics
• Design electrical systems, power generation, and electronic devices
• Specializations: Power Systems, Controls, Communications, Microelectronics
• Salary Range: $80K-$120K+ annually
• Work Settings: Utilities, electronics companies, tech firms

**💻 Computer Engineering** - Hardware/Software Integration
• Develop computer hardware and software systems
• Specializations: Embedded Systems, Cybersecurity, AI/ML Hardware
• Salary Range: $85K-$140K+ annually
• Work Settings: Tech companies, semiconductor firms, research labs

**🧪 Chemical Engineering** - Process & Materials
• Design processes for chemical manufacturing and materials development
• Specializations: Pharmaceuticals, Petrochemicals, Biotechnology, Nanotechnology
• Salary Range: $80K-$125K+ annually
• Work Settings: Chemical plants, pharmaceutical companies, research facilities

**🚀 Aerospace Engineering** - Aircraft & Spacecraft
• Design aircraft, spacecraft, and propulsion systems
• Specializations: Aerodynamics, Propulsion, Avionics, Space Systems
• Salary Range: $85K-$130K+ annually
• Work Settings: Aerospace companies, defense contractors, NASA

**🏥 Biomedical Engineering** - Medical Technology
• Develop medical devices, diagnostic equipment, and healthcare solutions
• Specializations: Medical Imaging, Prosthetics, Drug Delivery Systems
• Salary Range: $75K-$115K+ annually
• Work Settings: Medical device companies, hospitals, research institutions

**📊 Industrial Engineering** - Process Optimization
• Optimize manufacturing processes and systems for efficiency
• Specializations: Quality Control, Supply Chain, Operations Research
• Salary Range: $75K-$110K+ annually
• Work Settings: Manufacturing firms, consulting companies, logistics

**High-Growth Engineering Sectors**
• **Renewable Energy**: Solar, wind, battery technology
• **Artificial Intelligence**: Machine learning hardware, autonomous systems
• **Biotechnology**: Medical devices, genetic engineering
• **Space Exploration**: Commercial spaceflight, satellite technology
• **Cybersecurity**: Secure system design and implementation

**Career Progression Path**
• **Entry Level (0-3 years)**: Junior Engineer, Design Engineer
• **Mid Level (3-7 years)**: Senior Engineer, Project Engineer, Technical Lead
• **Senior Level (7-15 years)**: Engineering Manager, Principal Engineer
• **Executive Level (15+ years)**: Director, VP of Engineering, CTO

**Work Environment Characteristics**
• Collaborative team-based projects
• Mix of office work, lab testing, and field work
• Research and development opportunities
• Global project teams and travel potential
• Continuous learning and skill development{career_focus}

**Choosing Your Engineering Path**
Consider your interests, strengths, and market demand when selecting a specialization. Many engineers work in interdisciplinary teams, so you'll have opportunities to collaborate across fields. The key is finding an area that excites you while offering good career prospects.

Which engineering field interests you most, or would you like more details about any of these career paths?"""

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

    else:  # general_education or fallback
        if "skill" in query.lower() or "need" in query.lower():
            return """**Essential Study Skills & Requirements**
• **Time Management**: Create schedules, prioritize tasks, avoid procrastination
• **Note-Taking**: Use effective methods (Cornell, mind mapping, digital tools)
• **Reading Techniques**: Active reading, SQ3R method, speed reading
• **Memory Techniques**: Spaced repetition, mnemonic devices, visualization
• **Critical Thinking**: Question assumptions, evaluate evidence, draw conclusions

**Academic Success Strategies**
• Set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
• Create a dedicated study space free from distractions
• Use active recall and practice testing
• Join study groups and peer learning communities
• Maintain a healthy sleep schedule (7-9 hours per night)

**Digital Learning Tools**
• **Organization**: Notion, Evernote, OneNote for notes and planning
• **Flashcards**: Anki, Quizlet for memorization
• **Time Tracking**: Forest app, Focus@Will for concentration
• **Research**: Google Scholar, JSTOR, academic databases
• **Collaboration**: Microsoft Teams, Slack for group work

**Next Steps**
• Assess your current study habits and identify areas for improvement
• Start with one or two new techniques at a time
• Track your progress and adjust as needed
• Seek feedback from teachers or tutors"""

        elif "career" in query.lower() or "job" in query.lower():
            return """**Career Exploration & Planning**
• **Self-Assessment**: Identify your interests, skills, and values using career assessment tools
• **Research**: Explore different career paths, job descriptions, and industry trends
• **Networking**: Connect with professionals through LinkedIn, career fairs, and informational interviews
• **Experience**: Gain relevant experience through internships, volunteer work, or part-time jobs
• **Education**: Research degree requirements and program options

**Popular Career Fields**
• **Technology**: Software development, data science, cybersecurity
• **Healthcare**: Nursing, physical therapy, medical research
• **Business**: Marketing, finance, management, entrepreneurship
• **Education**: Teaching, counseling, educational administration
• **Creative**: Graphic design, writing, digital media, performing arts

**Career Development Steps**
• Update your resume and LinkedIn profile
• Build a professional network of contacts
• Develop both hard and soft skills
• Seek mentorship from experienced professionals
• Set career goals and create an action plan

**Resources for Career Planning**
• Career counseling services at your school/university
• Online platforms: LinkedIn, Indeed, Glassdoor
• Career assessment tools: Myers-Briggs, StrengthsFinder
• Professional organizations in your field of interest
• Local workforce development centers

What specific career questions do you have?"""

        else:
            return """**Education & Career Guidance**
• **Academic Success**: Study skills, time management, learning strategies
• **Career Exploration**: Self-assessment, research, networking, gaining experience
• **Personal Development**: Goal setting, motivation, work-life balance
• **Resource Access**: Tutoring, counseling, online learning platforms

**I'm here to help with:**
- Study techniques and academic challenges
- Career exploration and planning
- Course selection and degree programs
- Test preparation and exam strategies
- Motivation and goal setting

**Popular Topics:**
• How to improve study habits
• Career options in different fields
• Time management techniques
• Dealing with academic stress
• Finding the right college or program

What specific question can I help you with today?"""

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Quality Education Chatbot API", "status": "running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle education chat messages with field context awareness"""
    try:
        print(f"Chat request received: message='{request.message}', session_id='{request.session_id}'")

        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        print(f"Using session_id: {session_id}")

        # Debug: Print current sessions
        print(f"Current sessions in memory: {list(sessions.keys())}")

        # Initialize or retrieve session data
        if session_id not in sessions:
            print(f"Creating new session: {session_id}")
            sessions[session_id] = {
                "student_info": {"name": "", "age": 0, "interest": "", "query": ""},
                "conversation_stage": "greeting",  # greeting -> name -> age -> interest -> query -> recommendation
                "messages": []
            }
        else:
            print(f"Retrieving existing session: {session_id}")

        session_data = sessions[session_id]
        print(f"Current session stage: {session_data['conversation_stage']}")
        print(f"Current student info: {session_data['student_info']}")

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

                # Save name to database immediately
                db.save_conversation_state(session_id, {
                    "student_name": session_data["student_info"]["name"]
                })
            else:
                response_text = "I didn't catch your name. Could you please tell me your name?"

        elif session_data["conversation_stage"] == "age":
            # Extract and validate age
            extracted_info = extract_student_info(user_message, session_data["student_info"])
            if extracted_info["age"] > 0:
                session_data["student_info"]["age"] = extracted_info["age"]
                response_text = f"Great! At {session_data['student_info']['age']} years old, you have so many exciting educational opportunities ahead. What area interests you most? (e.g., Engineering, Medicine, Arts, Business, Science, Law, Education)"
                session_data["conversation_stage"] = "interest"

                # Save age to database immediately
                db.save_conversation_state(session_id, {
                    "student_name": session_data["student_info"]["name"],
                    "student_age": session_data["student_info"]["age"]
                })
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

                        # Save age to database immediately
                        db.save_conversation_state(session_id, {
                            "student_name": session_data["student_info"]["name"],
                            "student_age": age
                        })
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

                # Save interest to database immediately
                db.save_conversation_state(session_id, {
                    "student_name": session_data["student_info"]["name"],
                    "student_age": session_data["student_info"]["age"],
                    "area_of_interest": session_data["student_info"]["interest"]
                })
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

                    # Save interest to database immediately
                    db.save_conversation_state(session_id, {
                        "student_name": session_data["student_info"]["name"],
                        "student_age": session_data["student_info"]["age"],
                        "area_of_interest": found_interest
                    })
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
            # Allow ongoing conversations after initial setup
            context = session_data["student_info"]
            category = classify_education_query(user_message, context)
            response_text = generate_education_response(user_message, category, context)

            # Keep the conversation going - don't change stage

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
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

# Render deployment configuration
# This ensures the app binds to Render's assigned PORT and listens on 0.0.0.0
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Render provides PORT env var
    uvicorn.run(
        app,  # Use the app instance directly
        host="0.0.0.0",  # Bind to all interfaces for Render
        port=port,  # Use Render's assigned port
        reload=False  # Disable reload in production
    )
