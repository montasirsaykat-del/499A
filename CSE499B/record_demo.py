"""
Demo Recording Helper Script
This script helps you capture screenshots or record the demo presentation
"""

import webbrowser
import os
import time
from pathlib import Path

def open_demo():
    """Open the demo HTML file in the default browser"""
    demo_file = Path(__file__).parent / "demo_visualization.html"
    
    if not demo_file.exists():
        print("Error: demo_visualization.html not found!")
        return False
    
    # Get absolute path and convert to file URL
    file_url = f"file:///{demo_file.absolute()}".replace("\\", "/")
    
    print("=" * 60)
    print("🎬 CSE499B Project Demo Launcher")
    print("=" * 60)
    print(f"\n📂 Opening demo from: {demo_file}")
    print(f"\n🌐 URL: {file_url}")
    print("\n" + "=" * 60)
    print("INSTRUCTIONS FOR RECORDING:")
    print("=" * 60)
    print("\n1. The demo will open in your default browser")
    print("2. Use these navigation buttons to switch sections:")
    print("   - Overview (Project introduction)")
    print("   - System Architecture (Components)")
    print("   - Key Features (Capabilities)")
    print("   - How It Works (Workflow)")
    print("   - Performance (Metrics)")
    print("   - Live Demo (AI Visualization)")
    print("\n3. To record a video:")
    print("   Option A: Use OBS Studio (Free)")
    print("   - Download: https://obsproject.com/")
    print("   - Select 'Window Capture' for your browser")
    print("   - Press 'Start Recording'")
    print("   ")
    print("   Option B: Use Windows Game Bar (Built-in)")
    print("   - Press Win + G")
    print("   - Click the record button")
    print("   ")
    print("   Option C: Use PowerPoint Screen Recording")
    print("   - Insert > Screen Recording")
    print("   - Select area and record")
    print("\n4. Presentation Tips:")
    print("   - Speak clearly and explain each section")
    print("   - Spend 1-2 minutes per section")
    print("   - Highlight the AI visualization in demo section")
    print("   - Total presentation: 8-12 minutes")
    print("\n5. Press F11 for fullscreen mode")
    print("\n" + "=" * 60)
    
    # Open the browser
    try:
        webbrowser.open(file_url)
        print("\n✅ Demo opened successfully!")
        print("\n💡 Tip: Press Ctrl+C to close this window")
        print("=" * 60)
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"\n❌ Error opening demo: {e}")
        return False
    
    return True

def print_recording_tools():
    """Print information about recording tools"""
    print("\n" + "=" * 60)
    print("📹 RECOMMENDED RECORDING TOOLS:")
    print("=" * 60)
    print("\n1. OBS Studio (FREE - Best Quality)")
    print("   - Download: https://obsproject.com/")
    print("   - Professional quality")
    print("   - Easy to use")
    print("   ")
    print("2. Windows Game Bar (Built-in)")
    print("   - Press: Win + G")
    print("   - Quick and simple")
    print("   - No installation needed")
    print("   ")
    print("3. PowerPoint Screen Recording")
    print("   - Insert > Screen Recording")
    print("   - Good for presentations")
    print("   ")
    print("4. Bandicam (Free/Paid)")
    print("   - Download: https://www.bandicam.com/")
    print("   - High quality recordings")
    print("   ")
    print("5. Loom (Free - Browser-based)")
    print("   - Website: https://www.loom.com/")
    print("   - Easy sharing")
    print("=" * 60)

def create_screenshot_instructions():
    """Create a text file with screenshot instructions"""
    instructions_file = Path(__file__).parent / "RECORDING_GUIDE.txt"
    
    content = """
╔════════════════════════════════════════════════════════════╗
║           CSE499B PROJECT DEMO RECORDING GUIDE            ║
╔════════════════════════════════════════════════════════════╗

📋 PREPARATION CHECKLIST:
═══════════════════════════════════════════════════════════════
☐ Install OBS Studio or have Windows Game Bar ready
☐ Test microphone audio quality
☐ Close unnecessary applications/tabs
☐ Set browser to full screen (F11)
☐ Prepare notes for each section
☐ Do a practice run (5-10 minutes)

📹 RECORDING STEPS:
═══════════════════════════════════════════════════════════════
1. Run the Python script: python record_demo.py
2. Wait for browser to open the demo
3. Press F11 for fullscreen
4. Start your recording software
5. Follow the presentation flow below

🎤 PRESENTATION FLOW (8-12 minutes total):
═══════════════════════════════════════════════════════════════

SECTION 1: OVERVIEW (2 min)
───────────────────────────────────────────────────────────────
"Good [morning/afternoon]. I'm presenting my CSE499B senior 
project - an AI-powered system that [describe your project's 
purpose]. This project demonstrates my expertise in artificial 
intelligence, machine learning, and full-stack development."

Key points to mention:
- Project objectives
- Real-world application
- Technology stack overview

SECTION 2: SYSTEM ARCHITECTURE (2 min)
───────────────────────────────────────────────────────────────
"The system is built on a modern, scalable architecture with 
six main components..."

Walk through each component:
- Frontend Layer (React)
- Backend API (Node.js)
- AI Engine (ML models)
- Database (MongoDB)
- Authentication
- Cloud Services

SECTION 3: KEY FEATURES (1.5 min)
───────────────────────────────────────────────────────────────
"The system offers several key features..."

Highlight 3-5 main features:
- AI/ML capabilities
- Real-time processing
- User interface
- Performance metrics

SECTION 4: HOW IT WORKS (2 min)
───────────────────────────────────────────────────────────────
"Let me walk you through the system workflow..."

Explain the 4-step process:
1. User Input
2. Data Processing
3. AI Analysis
4. Results Output

Also mention the development timeline

SECTION 5: PERFORMANCE (1.5 min)
───────────────────────────────────────────────────────────────
"Here are the performance metrics that demonstrate the 
system's effectiveness..."

Point out:
- 95% model accuracy
- Response time < 100ms
- High uptime (99.9%)
- Key achievements (lines of code, test coverage)

SECTION 6: LIVE DEMO (2 min)
───────────────────────────────────────────────────────────────
"Now let me show you the system in action with this 
AI neural network visualization..."

Explain the visualization:
- Animated neural network
- Real-time data processing
- How AI analyzes information

CONCLUSION (1 min)
───────────────────────────────────────────────────────────────
"In conclusion, this project successfully demonstrates the 
integration of AI technologies with modern development practices. 
It showcases my technical skills, problem-solving abilities, 
and readiness for industry challenges. Thank you for your time, 
and I'm happy to answer any questions."

💡 TIPS FOR A GREAT PRESENTATION:
═══════════════════════════════════════════════════════════════
✓ Speak clearly and at a moderate pace
✓ Explain technical terms when first introduced
✓ Use hand gestures naturally (if on camera)
✓ Maintain enthusiasm and confidence
✓ Practice transitions between sections
✓ Keep total time under 12 minutes
✓ End with a confident closing statement

⚙️ TECHNICAL TIPS:
═══════════════════════════════════════════════════════════════
✓ Record at 1920x1080 resolution (Full HD)
✓ Use 30 FPS (frames per second)
✓ Ensure good lighting if showing yourself
✓ Test audio levels before final recording
✓ Save recording in MP4 format
✓ Keep file size under 500MB for easy sharing

🎬 POST-RECORDING:
═══════════════════════════════════════════════════════════════
☐ Review the entire video
☐ Check audio quality throughout
☐ Verify all sections are visible
☐ Add intro/outro slides if needed (optional)
☐ Export in MP4 format
☐ Test playback on different devices
☐ Upload to Google Drive/OneDrive for professor

📧 SUBMISSION CHECKLIST:
═══════════════════════════════════════════════════════════════
☐ Video file (MP4)
☐ Project documentation (PDFs)
☐ Source code (if required)
☐ README file with instructions
☐ Any additional materials requested

═══════════════════════════════════════════════════════════════
Good luck with your presentation! 🎓
═══════════════════════════════════════════════════════════════
"""
    
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Created: {instructions_file}")
    print("📖 Please read this file for detailed recording instructions")

if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        CSE499B PROJECT DEMO VISUALIZATION LAUNCHER        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Create instructions file
    create_screenshot_instructions()
    
    # Print recording tools info
    print_recording_tools()
    
    # Wait for user
    input("\n\nPress ENTER to open the demo in your browser...")
    
    # Open the demo
    open_demo()
