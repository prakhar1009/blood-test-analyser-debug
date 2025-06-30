#!/usr/bin/env python3
"""
Enhanced Blood Test Report Analyzer - Fixed Version
Processes PDF blood test reports and generates real, actionable analysis
"""

import os
import time
import sys
from datetime import datetime
import warnings
import re
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables
load_dotenv()

# Import our enhanced tools
try:
    from tools import read_blood_test_report, analyze_nutrition, create_exercise_plan, extract_blood_markers
except ImportError as e:
    print(f"Error importing tools: {e}")
    print("Make sure tools.py is in the same directory")
    sys.exit(1)

# Initialize the OpenAI LLM
llm = LLM(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.1,
    max_retries=3,
    timeout=60
)

# Define specialized agents for blood test analysis
medical_doctor = Agent(
    role="Senior Medical Doctor and Laboratory Specialist",
    goal="Provide real, specific medical analysis based on actual blood test values found in the report",
    backstory="""You are a board-certified physician with 20+ years of experience in internal medicine 
    and laboratory diagnostics. You NEVER use placeholder text or templates. You ALWAYS work with the 
    actual blood test data provided to you. You extract real values from the report and provide specific 
    medical interpretations based on those exact numbers. If you cannot find specific values, you clearly 
    state what you did find and provide general guidance based on the available information.""",
    llm=llm,
    verbose=True,
    memory=False,
    allow_delegation=False,
    max_iter=3
)

clinical_nutritionist = Agent(
    role="Registered Dietitian and Clinical Nutritionist",
    goal="Analyze real blood markers and provide specific, actionable nutrition recommendations",
    backstory="""You are a registered dietitian with extensive experience in medical nutrition therapy. 
    You work with ACTUAL blood test values to provide specific dietary recommendations. You never use 
    placeholder text. When given blood test data, you extract the real numbers and provide targeted 
    nutrition advice based on those specific values. Your recommendations include exact food portions, 
    specific nutrients, and practical meal planning based on the actual test results.""",
    llm=llm,
    verbose=True,
    memory=False,
    allow_delegation=False,
    max_iter=3
)

exercise_physiologist = Agent(
    role="Certified Exercise Physiologist",
    goal="Create specific exercise plans based on actual health markers from blood tests",
    backstory="""You are a certified exercise physiologist who designs real, practical exercise programs 
    based on actual blood test results. You never use template responses. You analyze the specific health 
    markers found in the blood test and create detailed, personalized exercise prescriptions with exact 
    parameters (duration, intensity, frequency) based on those real values.""",
    llm=llm,
    verbose=True,
    memory=False,
    allow_delegation=False,
    max_iter=3
)

# Enhanced task creation with actual data processing
def create_medical_analysis_task(file_content: str, query: str) -> Task:
    return Task(
        description=f"""
        Analyze the ACTUAL blood test report content and provide REAL medical interpretation.
        
        User Query: "{query}"
        
        Blood Test Report Content:
        {file_content[:3000]}...
        
        CRITICAL INSTRUCTIONS:
        1. Extract REAL blood marker values from the actual report content above
        2. Do NOT use placeholder text like [Value] or template responses
        3. Work ONLY with the actual numbers and data found in the report
        4. If specific values are not clearly visible, state what you can see and provide general guidance
        5. Provide specific medical interpretation based on the REAL values found
        6. Compare actual values against standard reference ranges
        7. Give specific recommendations based on the actual findings
        
        Example of GOOD response:
        "Your hemoglobin level is 11.5 g/dL, which is below the normal range of 12.1-15.1 g/dL for women..."
        
        Example of BAD response (DO NOT DO THIS):
        "Hemoglobin: [Value] g/dL (Normal/Abnormal)"
        
        Focus on what you can actually see in the report and provide real, actionable medical insights.
        """,
        expected_output="""
        A comprehensive medical analysis that includes:
        - Specific blood marker values found in the actual report
        - Real interpretation of abnormal values with exact numbers
        - Clinical significance of the actual findings
        - Specific recommendations based on real results
        - Clear statement of what markers were analyzed
        - If values are unclear, honest statement about limitations
        """,
        agent=medical_doctor
    )

def create_nutrition_analysis_task(file_content: str) -> Task:
    return Task(
        description=f"""
        Provide REAL nutrition recommendations based on the ACTUAL blood test values.
        
        Blood Test Report Content:
        {file_content[:3000]}...
        
        CRITICAL INSTRUCTIONS:
        1. Extract ACTUAL blood marker values from the report content above
        2. Use the analyze_nutrition function with the real extracted data
        3. Do NOT provide template responses with placeholder values
        4. Base ALL recommendations on the specific values found
        5. If you cannot extract specific values, work with what's available and state limitations
        6. Provide exact food recommendations with real portions based on actual findings
        
        Focus on giving practical, specific nutrition advice based on what you can actually see in the blood test.
        """,
        expected_output="""
        Specific nutrition recommendations including:
        - Analysis of actual blood markers found
        - Targeted food recommendations based on real values
        - Specific portion sizes and meal planning
        - Exact supplement recommendations if needed
        - Clear explanation of why recommendations are made
        """,
        agent=clinical_nutritionist
    )

def create_exercise_planning_task(file_content: str) -> Task:
    return Task(
        description=f"""
        Create a REAL exercise plan based on ACTUAL blood test markers.
        
        Blood Test Report Content:
        {file_content[:3000]}...
        
        CRITICAL INSTRUCTIONS:
        1. Extract ACTUAL health markers from the report content above
        2. Use the create_exercise_plan function with real extracted data
        3. Do NOT provide template responses
        4. Base exercise recommendations on specific health markers found
        5. Provide exact exercise parameters (duration, intensity, frequency)
        6. If specific markers are unclear, work with available information
        
        Create a real, practical exercise program based on actual findings.
        """,
        expected_output="""
        A specific exercise plan including:
        - Assessment based on actual blood markers
        - Exact exercise prescriptions with real parameters
        - Specific safety considerations based on findings
        - Real progression timeline
        - Practical implementation guidance
        """,
        agent=exercise_physiologist
    )

def format_analysis_output(crew_result) -> dict:
    """Format the analysis output for better readability"""
    try:
        tasks_output = crew_result.tasks_output if hasattr(crew_result, 'tasks_output') else []
        
        formatted_result = {
            'medical_analysis': '',
            'nutrition_analysis': '',
            'exercise_plan': '',
            'full_analysis': str(crew_result)
        }
        
        # Map each task output to the correct section
        task_keys = ['medical_analysis', 'nutrition_analysis', 'exercise_plan']
        
        for i, task_output in enumerate(tasks_output):
            if i < len(task_keys):
                formatted_result[task_keys[i]] = str(task_output.raw) if hasattr(task_output, 'raw') else str(task_output)
        
        return formatted_result
    except Exception as e:
        print(f"Error formatting results: {e}")
        return {
            'medical_analysis': str(crew_result),
            'nutrition_analysis': '',
            'exercise_plan': '',
            'full_analysis': str(crew_result)
        }

def print_colored_text(text: str, color: str = 'white'):
    """Print colored text to terminal"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def create_markdown_report(formatted_result: dict, file_path: str, query: str, processing_time: float, 
                          markers_found: dict, file_content: str) -> str:
    """Create a comprehensive markdown report with actual data"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract a meaningful sample of the actual report content
    content_preview = file_content[:1000].replace('\n', ' ').strip()
    if len(file_content) > 1000:
        content_preview += "..."
    
    markdown_content = f"""# 🩺 Blood Test Analysis Report

**Generated:** {timestamp}  
**Processing Time:** {processing_time//60:.0f}m {processing_time%60:.0f}s  
**Source File:** {os.path.basename(file_path)}  
**Query:** {query}  
**Blood Markers Detected:** {len(markers_found)}

---

## 📋 Original Report Content Preview

```
{content_preview}
```

---

## 📊 Blood Markers Summary

"""
    
    if markers_found:
        markdown_content += "| Marker | Value | Unit | Status |\n|--------|-------|------|--------|\n"
        
        # Define reference ranges for status indication
        ref_ranges = {
            'hemoglobin': (12.0, 16.0, 'g/dL'),
            'cholesterol': (0, 200, 'mg/dL'),
            'glucose': (70, 99, 'mg/dL'),
            'protein': (6.0, 8.3, 'g/dL'),
            'albumin': (3.5, 5.0, 'g/dL'),
            'creatinine': (0.6, 1.3, 'mg/dL')
        }
        
        for marker, value in markers_found.items():
            if marker in ref_ranges:
                min_val, max_val, unit = ref_ranges[marker]
                if marker == 'cholesterol':  # Lower is better for cholesterol
                    status = "✅ Normal" if value <= max_val else "⚠️ Elevated"
                else:
                    status = "✅ Normal" if min_val <= value <= max_val else "⚠️ Abnormal"
                
                markdown_content += f"| {marker.title()} | {value} | {unit} | {status} |\n"
            else:
                markdown_content += f"| {marker.title()} | {value} | - | 📋 See Analysis |\n"
    else:
        markdown_content += "*Blood markers were not automatically detected. See detailed analysis below for manual interpretation.*\n"
    
    markdown_content += "\n---\n\n"
    
    # Medical Analysis Section
    if formatted_result['medical_analysis']:
        markdown_content += "## 🏥 Medical Analysis\n\n"
        markdown_content += formatted_result['medical_analysis'] + "\n\n---\n\n"
    
    # Nutrition Analysis Section
    if formatted_result['nutrition_analysis']:
        markdown_content += "## 🥗 Nutrition Recommendations\n\n"
        markdown_content += formatted_result['nutrition_analysis'] + "\n\n---\n\n"
    
    # Exercise Plan Section
    if formatted_result['exercise_plan']:
        markdown_content += "## 💪 Exercise Plan\n\n"
        markdown_content += formatted_result['exercise_plan'] + "\n\n---\n\n"
    
    # Add important disclaimers
    markdown_content += """## ⚠️ Important Disclaimers

- This analysis is for **informational purposes only** and should not replace professional medical advice
- **Always consult with your healthcare provider** before making any medical, nutritional, or exercise changes
- Blood test interpretation requires clinical context and professional medical judgment
- This AI analysis is meant to **supplement**, not replace, professional healthcare guidance
- For urgent health concerns, seek immediate medical attention

## 📞 Next Steps

1. **Schedule an appointment** with your healthcare provider to discuss these results
2. **Share this analysis** with your doctor for professional interpretation
3. **Ask specific questions** about any concerning findings
4. **Request follow-up testing** if recommended
5. **Implement lifestyle changes gradually** under medical supervision

---

*Report generated by AI Blood Test Analysis System v2.0*  
*Analysis Date: {timestamp}*
"""
    
    return markdown_content

def get_file_input() -> str:
    """Get file path from user with multiple options"""
    print_colored_text("📁 FILE INPUT OPTIONS:", 'bold')
    print_colored_text("  1️⃣  Use sample.pdf from data folder", 'white')
    print_colored_text("  2️⃣  Use blood_test_report.pdf from data folder", 'white')
    print_colored_text("  3️⃣  Enter custom file path", 'white')
    
    choice = input("\n🔽 Choose option (1, 2, or 3): ").strip()
    
    if choice == "1":
        return "data/sample.pdf"
    elif choice == "2":
        return "data/blood_test_report.pdf"
    elif choice == "3":
        custom_path = input("\n📂 Enter full path to your PDF file: ").strip()
        return custom_path
    else:
        print_colored_text("❌ Invalid choice. Using default sample.pdf", 'yellow')
        return "data/sample.pdf"

def main():
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print_colored_text("❌ ERROR: OPENAI_API_KEY not found!", 'red')
        print_colored_text("\nPlease create a .env file with:", 'yellow')
        print_colored_text("OPENAI_API_KEY=your_api_key_here", 'cyan')
        sys.exit(1)
    
    # Create reports directory
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # Enhanced header
    print_colored_text("\n" + "="*70, 'cyan')
    print_colored_text("🩺 AI Blood Test Analysis System v2.0 (Fixed)", 'bold')
    print_colored_text("="*70, 'cyan')
    print_colored_text("✅ Real analysis based on actual blood test values", 'green')
    print_colored_text("⏱️  Processing takes 2-4 minutes for complete analysis", 'blue')
    print_colored_text("📁 Results saved in markdown format\n", 'purple')
    
    # Get file input
    file_path = get_file_input()
    
    # Verify file exists
    if not os.path.exists(file_path):
        print_colored_text(f"\n❌ File not found: {file_path}", 'red')
        print_colored_text("Please check the file path and try again.", 'yellow')
        sys.exit(1)
    
    # Get user query
    print_colored_text("\n📝 ANALYSIS QUERY:", 'bold')
    print_colored_text("What specific aspect would you like analyzed?", 'white')
    print_colored_text("Examples:", 'cyan')
    print_colored_text("  • 'Focus on my cholesterol and heart health'", 'white')
    print_colored_text("  • 'Analyze my blood sugar and diabetes risk'", 'white')
    print_colored_text("  • 'Check my iron levels and energy'", 'white')
    
    query = input("\n🔽 Enter your query (or press Enter for comprehensive analysis): ").strip()
    if not query:
        query = "Provide a comprehensive analysis of my blood test results with specific recommendations"
    
    # Read and analyze the file content first
    try:
        print_colored_text("\n🔍 READING BLOOD TEST REPORT...", 'blue')
        file_content = read_blood_test_report(file_path)
        
        if file_content.startswith("Error:"):
            print_colored_text(f"\n❌ {file_content}", 'red')
            sys.exit(1)
        
        # Extract markers for preview
        markers = extract_blood_markers(file_content)
        
        print_colored_text(f"✅ Successfully read {len(file_content)} characters from PDF", 'green')
        print_colored_text(f"🔬 Detected {len(markers)} blood markers: {', '.join(markers.keys()) if markers else 'Manual analysis required'}", 'cyan')
        
        # Show a preview of what was extracted
        preview = file_content[:300].replace('\n', ' ').strip()
        if len(file_content) > 300:
            preview += "..."
        print_colored_text(f"📋 Content preview: {preview}", 'white')
        
    except Exception as e:
        print_colored_text(f"\n❌ Error reading file: {e}", 'red')
        sys.exit(1)
    
    # Create analysis tasks with actual content
    try:
        print_colored_text("\n" + "="*70, 'cyan')
        print_colored_text("🔄 STARTING REAL ANALYSIS WITH ACTUAL DATA", 'bold')
        print_colored_text("="*70, 'cyan')
        
        # Progress indicators
        steps = [
            "🩺 Medical Analysis - Interpreting actual blood values",
            "🥗 Nutrition Analysis - Creating targeted dietary plan", 
            "💪 Exercise Planning - Designing personalized program"
        ]
        
        for step in steps:
            print_colored_text(f"⏳ {step}", 'blue')
        
        print_colored_text("\n⏱️  Estimated time: 2-4 minutes", 'yellow')
        print()
        
        start_time = time.time()
        
        # Create all analysis tasks with actual file content
        medical_task = create_medical_analysis_task(file_content, query)
        nutrition_task = create_nutrition_analysis_task(file_content)
        exercise_task = create_exercise_planning_task(file_content)
        
        # Create crew with real data processing
        analysis_crew = Crew(
            agents=[medical_doctor, clinical_nutritionist, exercise_physiologist],
            tasks=[medical_task, nutrition_task, exercise_task],
            process=Process.sequential,
            verbose=False,  # Reduce verbose output for cleaner display
            memory=False
        )
        
        # Run analysis with actual content
        result = analysis_crew.kickoff(inputs={
            "query": query,
            "file_content": file_content
        })
        
        elapsed = time.time() - start_time
        
        # Format results
        formatted_result = format_analysis_output(result)
        
        # Display results with enhanced formatting
        print_colored_text("\n" + "="*70, 'green')
        print_colored_text("✅ REAL ANALYSIS COMPLETE", 'bold')
        print_colored_text("="*70, 'green')
        print_colored_text(f"⏱️  Processing time: {elapsed//60:.0f}m {elapsed%60:.0f}s", 'cyan')
        print_colored_text(f"🔬 Blood markers analyzed: {len(markers)}", 'white')
        print()
        
        # Display each section with colors
        sections = [
            ("🩺 MEDICAL ANALYSIS", 'medical_analysis', 'blue'),
            ("🥗 NUTRITION RECOMMENDATIONS", 'nutrition_analysis', 'green'), 
            ("💪 EXERCISE PLAN", 'exercise_plan', 'yellow')
        ]
        
        for title, key, color in sections:
            if formatted_result[key]:
                print_colored_text(f"\n{title}", color)
                print_colored_text("-" * 60, color)
                # Display first 400 characters of each section
                section_text = formatted_result[key]
                preview = section_text[:400] + "..." if len(section_text) > 400 else section_text
                print(preview)
                print_colored_text("(Full details in saved report)", 'cyan')
        
        print_colored_text("\n" + "="*70, 'green')
        
        # Save comprehensive report as markdown
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blood_analysis_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)
        
        markdown_content = create_markdown_report(
            formatted_result, 
            file_path,
            query,
            elapsed,
            markers,
            file_content
        )
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print_colored_text(f"💾 Real analysis report saved: {filepath}", 'green')
        print_colored_text("📋 Report includes: Actual blood values, real interpretations, and specific recommendations", 'cyan')
        print_colored_text("✨ Analysis completed successfully!", 'bold')
        
        # Summary of key findings
        if markers:
            print_colored_text(f"\n📊 ACTUAL FINDINGS SUMMARY:", 'bold')
            for marker, value in list(markers.items())[:3]:  # Show first 3 markers
                print_colored_text(f"   • {marker.title()}: {value}", 'white')
            if len(markers) > 3:
                print_colored_text(f"   • And {len(markers)-3} more markers analyzed", 'cyan')
        else:
            print_colored_text(f"\n📊 ANALYSIS SUMMARY:", 'bold')
            print_colored_text(f"   • Manual analysis completed on {len(file_content)} characters of report data", 'white')
            print_colored_text(f"   • Specific recommendations provided based on available content", 'cyan')
        
        print_colored_text(f"\n📁 Open the report file to view complete analysis: {filepath}", 'yellow')
        
    except KeyboardInterrupt:
        print_colored_text("\n\n⚠️  Analysis interrupted by user", 'yellow')
        sys.exit(0)
    except Exception as e:
        error_msg = str(e)
        print_colored_text(f"\n❌ Error: {error_msg}", 'red')
        
        if "API key" in error_msg:
            print_colored_text("\n🔑 API KEY ERROR", 'red')
            print_colored_text("1. Verify your key in .env file", 'cyan')
            print_colored_text("2. Check if the key is valid and active", 'white')
            print_colored_text("3. Ensure you have API credits available", 'white')
        else:
            print_colored_text("\n💡 Troubleshooting tips:", 'yellow')
            print_colored_text("1. Check your internet connection", 'white')
            print_colored_text("2. Verify the PDF file is readable", 'white')
            print_colored_text("3. Try with a different PDF file", 'white')
            print_colored_text("4. Check API status and rate limits", 'white')

if __name__ == "__main__":
    main()