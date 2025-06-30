## Enhanced tools for real blood test analysis
import os
import re
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
load_dotenv()

# PDF processing
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not found. Installing...")
    os.system("pip install PyPDF2")
    import PyPDF2

try:
    import pandas as pd
except ImportError:
    print("pandas not found. Installing...")
    os.system("pip install pandas")
    import pandas as pd

# Try to get search tool - optional
search_tool = None
try:
    from crewai_tools import SerperDevTool
    search_tool = SerperDevTool()
except ImportError:
    print("SerperDevTool not available. Continuing without search functionality.")

## Enhanced function to read PDF files with better text extraction
def read_blood_test_report(path: str = 'data/sample.pdf') -> str:
    """Read and extract text from a PDF blood test report with enhanced processing
    
    Args:
        path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content from the PDF with enhanced formatting
    """
    try:
        # Handle different possible file paths
        possible_paths = [
            path,
            f"data/{os.path.basename(path)}",
            f"data/sample.pdf",
            f"data/blood_test_report.pdf"
        ]
        
        actual_path = None
        for test_path in possible_paths:
            if os.path.exists(test_path):
                actual_path = test_path
                break
        
        if not actual_path:
            return f"Error: File not found. Tried paths: {', '.join(possible_paths)}"
        
        # Check file size
        file_size = os.path.getsize(actual_path)
        if file_size == 0:
            return "Error: File is empty"
        
        print(f"📄 Reading PDF from: {actual_path} (Size: {file_size} bytes)")
        
        with open(actual_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF has pages
                if len(pdf_reader.pages) == 0:
                    return "Error: PDF has no pages"
                
                full_report = ""
                page_count = len(pdf_reader.pages)
                
                for page_num in range(page_count):
                    try:
                        page = pdf_reader.pages[page_num]
                        content = page.extract_text()
                        
                        if content.strip():  # Only add non-empty content
                            # Enhanced cleaning for medical reports
                            content = re.sub(r'\n+', '\n', content)  # Remove multiple newlines
                            content = re.sub(r'\s+', ' ', content)   # Remove multiple spaces
                            
                            # Preserve important medical formatting and values
                            content = re.sub(r'(\d+\.?\d*)\s*(mg/dL|g/dL|mmol/L|µg/dL|ng/mL|mL/min|%)', r'\1 \2', content)
                            
                            full_report += content + "\n"
                            
                    except Exception as page_error:
                        print(f"⚠️ Error reading page {page_num + 1}: {str(page_error)}")
                        continue
                
                if not full_report.strip():
                    return "Error: Could not extract text from PDF. The PDF might be image-based, password-protected, or corrupted."
                
                # Add extraction metadata
                print(f"✅ Successfully extracted {len(full_report)} characters from {page_count} pages")
                
                return full_report.strip()
                
            except PyPDF2.errors.PdfReadError as pdf_error:
                return f"Error: Invalid or corrupted PDF file - {str(pdf_error)}"
            except Exception as pdf_error:
                return f"Error reading PDF structure: {str(pdf_error)}"
            
    except PermissionError:
        return f"Error: Permission denied accessing file: {actual_path}"
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

## Enhanced blood marker extraction with comprehensive patterns
def extract_blood_markers(report_data: str) -> Dict[str, float]:
    """Extract blood marker values from report text with comprehensive pattern matching"""
    markers = {}
    
    if not report_data:
        return markers
    
    # Comprehensive regex patterns for common markers with multiple variations
    patterns = {
        'hemoglobin': [
            r'hemoglobin[:\s]*(\d+\.?\d*)\s*g/dl',
            r'hgb[:\s]*(\d+\.?\d*)\s*g/dl',
            r'hb[:\s]*(\d+\.?\d*)\s*g/dl',
            r'hemoglobin[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)hb\s*:?\s*(\d+\.?\d*)',
            r'hemoglobin\s*(?:level)?[:\s]*(\d+\.?\d*)',
        ],
        'cholesterol': [
            r'total\s*cholesterol[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'cholesterol\s*(?:total)?[:\s]*(\d+\.?\d*)\s*mg/dl',
            r't\.?\s*chol[:\s]*(\d+\.?\d*)',
            r'cholesterol[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)chol\s*:?\s*(\d+\.?\d*)',
        ],
        'glucose': [
            r'glucose[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'blood\s*glucose[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'fasting\s*glucose[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'glucose[:\s]*(\d+\.?\d*)',
            r'blood\s*sugar[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)glu\s*:?\s*(\d+\.?\d*)',
        ],
        'protein': [
            r'total\s*protein[:\s]*(\d+\.?\d*)\s*g/dl',
            r'protein\s*(?:total)?[:\s]*(\d+\.?\d*)\s*g/dl',
            r't\.?\s*protein[:\s]*(\d+\.?\d*)',
            r'protein[:\s]*(\d+\.?\d*)',
        ],
        'albumin': [
            r'albumin[:\s]*(\d+\.?\d*)\s*g/dl',
            r'albumin[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)alb\s*:?\s*(\d+\.?\d*)',
        ],
        'creatinine': [
            r'creatinine[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'creatinine[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)creat\s*:?\s*(\d+\.?\d*)',
        ],
        'hdl': [
            r'hdl[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'hdl\s*cholesterol[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)hdl\s*:?\s*(\d+\.?\d*)',
        ],
        'ldl': [
            r'ldl[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'ldl\s*cholesterol[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)ldl\s*:?\s*(\d+\.?\d*)',
        ],
        'triglycerides': [
            r'triglycerides[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'triglycerides[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)trig\s*:?\s*(\d+\.?\d*)',
            r'(?:^|\s)tg\s*:?\s*(\d+\.?\d*)',
        ],
        'bun': [
            r'bun[:\s]*(\d+\.?\d*)\s*mg/dl',
            r'blood\s*urea\s*nitrogen[:\s]*(\d+\.?\d*)',
            r'(?:^|\s)bun\s*:?\s*(\d+\.?\d*)',
        ],
        'sodium': [
            r'sodium[:\s]*(\d+\.?\d*)\s*(?:meq/l|mmol/l)?',
            r'(?:^|\s)na\s*:?\s*(\d+\.?\d*)',
        ],
        'potassium': [
            r'potassium[:\s]*(\d+\.?\d*)\s*(?:meq/l|mmol/l)?',
            r'(?:^|\s)k\s*:?\s*(\d+\.?\d*)',
        ]
    }
    
    report_lower = report_data.lower()
    
    # Extract markers with validation
    for marker, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, report_lower, re.MULTILINE)
            for match in matches:
                try:
                    value = float(match.group(1))
                    # Validate reasonable ranges for markers
                    if marker == 'hemoglobin' and 5 <= value <= 25:
                        markers[marker] = value
                        break
                    elif marker == 'cholesterol' and 50 <= value <= 500:
                        markers[marker] = value
                        break
                    elif marker == 'glucose' and 30 <= value <= 600:
                        markers[marker] = value
                        break
                    elif marker in ['protein', 'albumin'] and 2 <= value <= 15:
                        markers[marker] = value
                        break
                    elif marker == 'creatinine' and 0.1 <= value <= 15:
                        markers[marker] = value
                        break
                    elif marker in ['hdl', 'ldl'] and 10 <= value <= 300:
                        markers[marker] = value
                        break
                    elif marker == 'triglycerides' and 20 <= value <= 1000:
                        markers[marker] = value
                        break
                    elif marker == 'bun' and 5 <= value <= 100:
                        markers[marker] = value
                        break
                    elif marker in ['sodium', 'potassium'] and 100 <= value <= 200:
                        markers[marker] = value
                        break
                except ValueError:
                    continue
        if marker in markers:  # Break outer loop if marker found
            break
    
    return markers

## Enhanced nutrition analysis with real interpretations
def analyze_nutrition(blood_report_data: str) -> str:
    """Analyze blood test results and provide real nutrition recommendations"""
    try:
        if not blood_report_data or blood_report_data.strip() == "":
            return "Error: No blood report data provided for nutrition analysis."
        
        # Extract actual blood markers
        markers = extract_blood_markers(blood_report_data)
        recommendations = []
        
        recommendations.append("🥗 NUTRITION ANALYSIS BASED ON YOUR BLOOD TEST RESULTS")
        recommendations.append("=" * 65)
        recommendations.append(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        recommendations.append(f"Blood Markers Found: {len(markers)}")
        
        if markers:
            recommendations.append("Detected Values:")
            for marker, value in markers.items():
                recommendations.append(f"  • {marker.title()}: {value}")
        
        recommendations.append("")
        
        # Analyze each detected marker with real values
        analysis_provided = False
        
        if 'hemoglobin' in markers:
            analysis_provided = True
            hb_value = markers['hemoglobin']
            recommendations.append("🩸 IRON STATUS ANALYSIS")
            recommendations.append("-" * 40)
            recommendations.append(f"Your Hemoglobin Level: {hb_value} g/dL")
            
            if hb_value < 12:
                recommendations.append(f"⚠️  LOW HEMOGLOBIN DETECTED ({hb_value} g/dL)")
                recommendations.append("Your hemoglobin is below normal range (12.1-15.1 g/dL for women, 13.8-17.2 g/dL for men)")
                recommendations.append("")
                recommendations.append("🥩 IRON-RICH FOODS TO INCLUDE DAILY:")
                recommendations.append("• Red meat: 3-4 oz serving (provides ~2.5mg iron)")
                recommendations.append("• Chicken/Turkey: 4 oz serving (provides ~1.1mg iron)")
                recommendations.append("• Spinach: 1 cup cooked (provides ~6.4mg iron)")
                recommendations.append("• Lentils: 1 cup cooked (provides ~6.6mg iron)")
                recommendations.append("• Fortified cereals: 1 cup (provides ~4-18mg iron)")
                
                recommendations.append("\n🍊 ENHANCE IRON ABSORPTION WITH VITAMIN C:")
                recommendations.append("• Drink orange juice with iron-rich meals")
                recommendations.append("• Add bell peppers, strawberries, or tomatoes")
                recommendations.append("• Take iron supplements with vitamin C (consult doctor first)")
                
                recommendations.append("\n🚫 AVOID WITH IRON-RICH MEALS:")
                recommendations.append("• Coffee and tea (wait 1-2 hours after eating)")
                recommendations.append("• Calcium supplements")
                recommendations.append("• Dairy products during iron-rich meals")
                
            elif hb_value > 16:
                recommendations.append(f"⚠️  ELEVATED HEMOGLOBIN ({hb_value} g/dL)")
                recommendations.append("Your hemoglobin is above normal range")
                recommendations.append("• Increase daily water intake to 10-12 glasses")
                recommendations.append("• Avoid iron supplements unless prescribed")
                recommendations.append("• Focus on hydrating foods: watermelon, cucumber, soups")
                recommendations.append("• Consult your doctor about this elevated level")
            else:
                recommendations.append(f"✅ NORMAL HEMOGLOBIN LEVEL ({hb_value} g/dL)")
                recommendations.append("Your iron status appears healthy")
                recommendations.append("• Continue current iron intake from balanced diet")
                recommendations.append("• Include variety of protein sources")
            
            recommendations.append("")
        
        if 'cholesterol' in markers:
            analysis_provided = True
            chol_value = markers['cholesterol']
            recommendations.append("❤️  CHOLESTEROL MANAGEMENT")
            recommendations.append("-" * 35)
            recommendations.append(f"Your Total Cholesterol: {chol_value} mg/dL")
            
            if chol_value > 200:
                recommendations.append(f"⚠️  ELEVATED CHOLESTEROL ({chol_value} mg/dL)")
                recommendations.append("Your cholesterol is above desirable level (<200 mg/dL)")
                recommendations.append("")
                recommendations.append("🐟 HEART-HEALTHY FOODS TO EAT DAILY:")
                recommendations.append("• Fatty fish: Salmon, mackerel, sardines (2-3x/week, 4oz servings)")
                recommendations.append("• Oats: 1 cup cooked daily (provides 3g soluble fiber)")
                recommendations.append("• Beans: 1/2 cup daily (lentils, black beans, chickpeas)")
                recommendations.append("• Nuts: 1 oz almonds or walnuts daily")
                recommendations.append("• Olive oil: 2-3 tablespoons for cooking")
                
                recommendations.append("\n🚫 FOODS TO LIMIT OR AVOID:")
                recommendations.append("• Red meat: Limit to 2x/week, lean cuts only")
                recommendations.append("• Full-fat dairy: Switch to low-fat versions")
                recommendations.append("• Fried foods: Bake, grill, or steam instead")
                recommendations.append("• Processed foods: Avoid packaged snacks and fast food")
                
                recommendations.append(f"\n📉 TARGET: Reduce cholesterol by 10-15% in 3 months")
                recommendations.append("This could bring your level to approximately {:.0f}-{:.0f} mg/dL".format(chol_value * 0.85, chol_value * 0.9))
                
            else:
                recommendations.append(f"✅ GOOD CHOLESTEROL LEVEL ({chol_value} mg/dL)")
                recommendations.append("Your cholesterol is in the desirable range (<200 mg/dL)")
                recommendations.append("• Continue heart-healthy Mediterranean-style diet")
                recommendations.append("• Maintain current healthy fat intake")
            
            recommendations.append("")
        
        if 'glucose' in markers:
            analysis_provided = True
            glucose_value = markers['glucose']
            recommendations.append("🍯 BLOOD SUGAR MANAGEMENT")
            recommendations.append("-" * 30)
            recommendations.append(f"Your Glucose Level: {glucose_value} mg/dL")
            
            if glucose_value > 100:
                recommendations.append(f"⚠️  ELEVATED GLUCOSE ({glucose_value} mg/dL)")
                if glucose_value >= 126:
                    recommendations.append("This indicates diabetes range (≥126 mg/dL)")
                elif glucose_value >= 100:
                    recommendations.append("This indicates prediabetes range (100-125 mg/dL)")
                
                recommendations.append("")
                recommendations.append("🌾 BLOOD SUGAR FRIENDLY FOODS:")
                recommendations.append("• Whole grains: Brown rice, quinoa, steel-cut oats")
                recommendations.append("• Legumes: Beans, lentils, chickpeas (1/2 cup per meal)")
                recommendations.append("• Non-starchy vegetables: Broccoli, spinach, peppers (unlimited)")
                recommendations.append("• Lean proteins: Chicken, fish, tofu (4-6 oz per meal)")
                
                recommendations.append("\n⏰ MEAL TIMING STRATEGY:")
                recommendations.append("• Eat every 3-4 hours to prevent blood sugar spikes")
                recommendations.append("• Include protein with every meal and snack")
                recommendations.append("• Avoid large portions of carbohydrates")
                recommendations.append("• Test blood sugar before and after meals if possible")
                
                recommendations.append("\n🚫 FOODS TO AVOID:")
                recommendations.append("• White bread, white rice, pastries")
                recommendations.append("• Sugary drinks: Soda, fruit juice, sports drinks")
                recommendations.append("• Candy, cookies, ice cream")
                recommendations.append("• Large portions of any carbohydrate")
                
            else:
                recommendations.append(f"✅ NORMAL GLUCOSE LEVEL ({glucose_value} mg/dL)")
                recommendations.append("Your blood sugar is in the healthy range (70-99 mg/dL)")
                recommendations.append("• Continue balanced carbohydrate intake")
                recommendations.append("• Maintain regular meal timing")
            
            recommendations.append("")
        
        # If no specific markers found, provide general guidance
        if not analysis_provided:
            recommendations.append("📋 GENERAL NUTRITION GUIDANCE")
            recommendations.append("-" * 35)
            recommendations.append("Specific blood markers were not detected in the automated analysis.")
            recommendations.append("However, here are evidence-based nutrition recommendations:")
            recommendations.append("")
            recommendations.append("🥗 DAILY NUTRITION TARGETS:")
            recommendations.append("• Vegetables: 5-9 servings (1 serving = 1 cup raw or 1/2 cup cooked)")
            recommendations.append("• Fruits: 2-4 servings (1 serving = 1 medium fruit)")
            recommendations.append("• Whole grains: 6-8 servings (1 serving = 1 slice bread or 1/2 cup rice)")
            recommendations.append("• Lean protein: 5-6 oz total daily")
            recommendations.append("• Healthy fats: 2-3 tablespoons daily (olive oil, nuts)")
            recommendations.append("")
            recommendations.append("💧 HYDRATION:")
            recommendations.append("• Water: 8-10 glasses daily")
            recommendations.append("• Limit sugary beverages and alcohol")
            
        # Implementation timeline
        recommendations.append("")
        recommendations.append("📅 IMPLEMENTATION TIMELINE")
        recommendations.append("-" * 30)
        recommendations.append("Week 1: Focus on increasing vegetables and water intake")
        recommendations.append("Week 2: Add heart-healthy fats and reduce processed foods")
        recommendations.append("Week 3-4: Establish consistent meal timing")
        recommendations.append("Month 2-3: Monitor progress with follow-up blood tests")
        
        recommendations.append("")
        recommendations.append("📊 MONITORING PROGRESS:")
        recommendations.append("• Keep a 3-day food diary")
        recommendations.append("• Track energy levels and symptoms")
        recommendations.append("• Schedule blood work in 3 months to reassess")
        recommendations.append("• Work with a registered dietitian for personalized guidance")
        
        recommendations.append("")
        recommendations.append("⚠️  IMPORTANT: Consult with your healthcare provider before making")
        recommendations.append("    significant dietary changes, especially if you have medical conditions.")
        
        return "\n".join(recommendations)
        
    except Exception as e:
        return f"Error in nutrition analysis: {str(e)}"

## Enhanced exercise planning with real assessments
def create_exercise_plan(blood_report_data: str) -> str:
    """Create real exercise plan based on actual blood test results"""
    try:
        if not blood_report_data or blood_report_data.strip() == "":
            return "Error: No blood report data provided for exercise planning."
        
        # Extract relevant markers for exercise planning
        markers = extract_blood_markers(blood_report_data)
        exercise_plan = []
        
        # Header with actual analysis info
        exercise_plan.append("💪 PERSONALIZED EXERCISE PLAN BASED ON YOUR BLOOD RESULTS")
        exercise_plan.append("=" * 60)
        exercise_plan.append(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        exercise_plan.append(f"Blood Markers Evaluated: {len(markers)}")
        
        if markers:
            exercise_plan.append("Your Blood Values:")
            for marker, value in markers.items():
                exercise_plan.append(f"  • {marker.title()}: {value}")
        
        exercise_plan.append("")
        
        # Safety assessment based on actual values
        exercise_plan.append("⚠️  MEDICAL CLEARANCE REQUIRED")
        exercise_plan.append("Obtain physician approval before starting any new exercise program")
        exercise_plan.append("")
        
        # Risk assessment based on actual markers
        risk_factors = []
        special_considerations = []
        
        if 'cholesterol' in markers and markers['cholesterol'] > 240:
            risk_factors.append(f"High cholesterol ({markers['cholesterol']} mg/dL)")
            special_considerations.append("Emphasize aerobic exercise for cholesterol management")
        
        if 'glucose' in markers and markers['glucose'] > 126:
            risk_factors.append(f"Elevated glucose ({markers['glucose']} mg/dL)")
            special_considerations.append("Monitor blood sugar before and after exercise")
        
        if 'hemoglobin' in markers and markers['hemoglobin'] < 12:
            risk_factors.append(f"Low hemoglobin ({markers['hemoglobin']} g/dL)")
            special_considerations.append("Start with low-intensity exercise due to potential anemia")
        
        if risk_factors:
            exercise_plan.append("🎯 HEALTH CONSIDERATIONS BASED ON YOUR RESULTS:")
            for factor in risk_factors:
                exercise_plan.append(f"  ⚠️  {factor}")
            exercise_plan.append("")
        
        # Exercise prescription based on findings
        exercise_plan.append("🏃 CARDIOVASCULAR EXERCISE PROGRAM")
        exercise_plan.append("-" * 45)
        
        # Adjust intensity based on actual health markers
        if any('hemoglobin' in markers and markers['hemoglobin'] < 12, 
               'glucose' in markers and markers['glucose'] > 200):
            intensity = "Low to moderate intensity"
            duration = "20-30 minutes"
            frequency = "3-4 times per week"
            exercise_plan.append("⚠️  Modified program due to your blood test results")
        else:
            intensity = "Moderate intensity"
            duration = "30-45 minutes"
            frequency = "4-5 times per week"
        
        exercise_plan.append(f"• Intensity: {intensity}")
        exercise_plan.append(f"• Duration: {duration}")
        exercise_plan.append(f"• Frequency: {frequency}")
        exercise_plan.append("• Target heart rate: 50-70% of maximum")
        exercise_plan.append("")
        
        exercise_plan.append("🏃‍♀️ RECOMMENDED ACTIVITIES:")
        exercise_plan.append("• Walking: Start with 20 minutes, gradually increase")
        exercise_plan.append("• Swimming: Excellent low-impact option")
        exercise_plan.append("• Cycling: Stationary or outdoor on flat terrain")
        exercise_plan.append("• Elliptical machine: Joint-friendly cardio")
        exercise_plan.append("• Water aerobics: Great for joint protection")
        
        # Strength training recommendations
        exercise_plan.append("\n💪 STRENGTH TRAINING PROGRAM")
        exercise_plan.append("-" * 40)
        exercise_plan.append("• Frequency: 2-3 times per week")
        exercise_plan.append("• Focus: Full-body functional movements")
        exercise_plan.append("• Rest: 48 hours between strength sessions")
        exercise_plan.append("")
        
        exercise_plan.append("🏋️ BEGINNER STRENGTH ROUTINE:")
        exercise_plan.append("• Bodyweight squats: 2 sets x 8-12 reps")
        exercise_plan.append("• Wall or knee push-ups: 2 sets x 5-10 reps")
        exercise_plan.append("• Seated rows (resistance band): 2 sets x 8-12 reps")
        exercise_plan.append("• Plank hold: 2 sets x 15-30 seconds")
        exercise_plan.append("• Glute bridges: 2 sets x 10-15 reps")
        
        # Special considerations based on specific blood values
        if special_considerations:
            exercise_plan.append("\n🩺 SPECIAL CONSIDERATIONS FOR YOUR BLOOD RESULTS:")
            exercise_plan.append("-" * 55)
            for consideration in special_considerations:
                exercise_plan.append(f"• {consideration}")
        
        # Specific recommendations based on blood markers
        if 'glucose' in markers and markers['glucose'] > 100:
            exercise_plan.append(f"\n🍯 BLOOD SUGAR MANAGEMENT (Your glucose: {markers['glucose']} mg/dL):")
            exercise_plan.append("• Check blood sugar before exercising")
            exercise_plan.append("• Exercise 1-2 hours after meals when possible")
            exercise_plan.append("• Keep glucose tablets available during exercise")
            exercise_plan.append("• Stop exercising if you feel dizzy or weak")
        
        if 'cholesterol' in markers and markers['cholesterol'] > 200:
            exercise_plan.append(f"\n❤️  HEART HEALTH FOCUS (Your cholesterol: {markers['cholesterol']} mg/dL):")
            exercise_plan.append("• Prioritize aerobic exercise for cholesterol reduction")
            exercise_plan.append("• Monitor heart rate during exercise")
            exercise_plan.append("• Aim for 150+ minutes of cardio per week")
            exercise_plan.append("• Consider joining cardiac rehabilitation if available")
        
        # Progress timeline
        exercise_plan.append("\n📈 12-WEEK PROGRESSION PLAN:")
        exercise_plan.append("-" * 35)
        exercise_plan.append("Weeks 1-2: Establish routine, focus on consistency")
        exercise_plan.append("Weeks 3-4: Gradually increase duration by 5 minutes")
        exercise_plan.append("Weeks 5-8: Add second strength training day")
        exercise_plan.append("Weeks 9-12: Increase intensity or add new activities")
        
        # Warning signs
        exercise_plan.append("\n🚨 STOP EXERCISE IMMEDIATELY IF YOU EXPERIENCE:")
        exercise_plan.append("-" * 50)
        exercise_plan.append("• Chest pain or pressure")
        exercise_plan.append("• Unusual shortness of breath")
        exercise_plan.append("• Dizziness or lightheadedness")
        exercise_plan.append("• Irregular heartbeat")
        exercise_plan.append("• Nausea or excessive fatigue")
        
        exercise_plan.append("\n📞 SEEK IMMEDIATE MEDICAL ATTENTION FOR ANY OF THESE SYMPTOMS")
        
        exercise_plan.append(f"\n📋 SUMMARY: Exercise plan customized for your {len(markers)} blood markers")
        exercise_plan.append("⚠️  DISCLAIMER: This plan is based on your blood test results but")
        exercise_plan.append("    requires medical clearance before implementation.")
        
        return "\n".join(exercise_plan)
        
    except Exception as e:
        return f"Error creating exercise plan: {str(e)}"

# For backward compatibility, create simple wrapper classes
class BloodTestReportTool:
    """Enhanced wrapper for blood test report reading"""
    def __init__(self):
        self.name = "Blood Test Report Reader"
        self.description = "Tool to read and parse blood test reports from PDF files with enhanced analysis"
    
    def run(self, path: str = 'data/sample.pdf') -> str:
        return read_blood_test_report(path)

class NutritionTool:
    """Enhanced wrapper for nutrition analysis"""
    def __init__(self):
        self.name = "Nutrition Analyzer"
        self.description = "Real nutrition analysis tool based on actual blood test markers"
    
    def run(self, blood_report_data: str = "") -> str:
        return analyze_nutrition(blood_report_data)

class ExerciseTool:
    """Enhanced wrapper for exercise planning"""
    def __init__(self):
        self.name = "Exercise Planner"
        self.description = "Real exercise planning tool based on actual health markers"
    
    def run(self, blood_report_data: str = "") -> str:
        return create_exercise_plan(blood_report_data)