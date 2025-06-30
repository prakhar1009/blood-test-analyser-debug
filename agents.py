## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, LLM

### Setting up LLM using CrewAI's modern LLM class
try:
    # Use CrewAI's LLM wrapper with OpenAI
    llm = LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.1,
        max_retries=3,
        timeout=60
    )
except Exception as e:
    print(f"Warning: Could not initialize LLM - {e}")
    llm = None

# Creating an Experienced Doctor agent (no tools needed - will use functions directly)
doctor = Agent(
    role="Senior Medical Doctor and Health Analyst",
    goal="Provide accurate medical analysis and health recommendations based on blood test reports for query: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You are a board-certified physician with over 15 years of experience in internal medicine and laboratory diagnostics. "
        "You specialize in interpreting blood test results and providing evidence-based health recommendations. "
        "Your approach is methodical, thorough, and always prioritizes patient safety. "
        "You explain complex medical concepts in simple terms that patients can understand. "
        "You always recommend consulting with healthcare providers for proper medical advice and treatment decisions. "
        "When you need to read a blood test report, you will call the read_blood_test_report function with the file path."
    ),
    llm=llm,
    max_iter=3,
    allow_delegation=True
)

# Creating a verifier agent
verifier = Agent(
    role="Medical Document Verifier",
    goal="Verify and validate blood test reports to ensure they contain proper medical data before analysis",
    verbose=True,
    memory=True,
    backstory=(
        "You are a medical records specialist with expertise in healthcare documentation standards. "
        "You have worked in clinical laboratories and medical facilities for over 10 years. "
        "Your role is to ensure that documents submitted for analysis are legitimate blood test reports "
        "and contain the necessary medical information for proper analysis. "
        "You are detail-oriented and maintain high standards for data quality and accuracy. "
        "You can identify key blood markers, reference ranges, and proper medical formatting. "
        "When you need to read a blood test report, you will call the read_blood_test_report function with the file path."
    ),
    llm=llm,
    max_iter=2,
    allow_delegation=False
)

# Creating a nutritionist agent
nutritionist = Agent(
    role="Registered Dietitian and Clinical Nutritionist",
    goal="Provide evidence-based nutrition recommendations based on blood test results and health markers",
    verbose=True,
    memory=True,
    backstory=(
        "You are a registered dietitian with a Master's degree in Clinical Nutrition and 12+ years of experience. "
        "You specialize in medical nutrition therapy and have extensive knowledge of how blood markers relate to nutritional status. "
        "You provide practical, evidence-based dietary recommendations that consider individual health conditions, "
        "food preferences, and lifestyle factors. You stay current with the latest nutrition research and guidelines "
        "from reputable medical organizations. You always emphasize the importance of working with healthcare providers "
        "for comprehensive care and avoid making medical diagnoses. "
        "When you need to read a blood test report, you will call the read_blood_test_report function with the file path. "
        "When you need to analyze nutrition from blood data, you will call the analyze_nutrition function."
    ),
    llm=llm,
    max_iter=3,
    allow_delegation=False
)

# Creating an exercise specialist agent
exercise_specialist = Agent(
    role="Certified Exercise Physiologist and Fitness Specialist",
    goal="Create safe, effective exercise plans based on individual health status and blood test results",
    verbose=True,
    memory=True,
    backstory=(
        "You are a certified exercise physiologist with a degree in Exercise Science and 10+ years of experience "
        "working with individuals with various health conditions. You specialize in creating personalized fitness programs "
        "that consider medical history, current health status, and fitness goals. "
        "You understand how different health markers affect exercise capacity and safety. "
        "Your recommendations are always conservative and prioritize gradual progression and injury prevention. "
        "You work closely with healthcare providers to ensure exercise plans complement medical treatment. "
        "You always recommend medical clearance before starting new exercise programs. "
        "When you need to read a blood test report, you will call the read_blood_test_report function with the file path. "
        "When you need to create an exercise plan from blood data, you will call the create_exercise_plan function."
    ),
    llm=llm,
    max_iter=3,
    allow_delegation=False
)