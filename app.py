import streamlit as st
import json
import sqlite3
import pandas as pd
from datetime import datetime
import sys
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="ChemCode - Chemistry Coding Challenges", 
    page_icon="⚗️",
    layout="wide"
)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('chemcode.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  problem_id TEXT,
                  user_code TEXT,
                  result TEXT,
                  timestamp DATETIME)""")
    conn.commit()
    conn.close()

# Load problems from JSON
@st.cache_data
def load_problems():
    try:
        with open('problems.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("problems.json file not found!")
        return {}

# Execute user code safely
def execute_code(code, test_cases):
    results = []
    for test_case in test_cases:
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Create namespace for execution
            namespace = {}
            exec(code, namespace)
            
            # Find the function
            func_name = None
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_'):
                    func_name = name
                    break
            
            if func_name:
                result = namespace[func_name](*test_case['input'])
                expected = test_case['expected']
                sys.stdout = old_stdout
                
                if result == expected:
                    results.append({"status": "PASS", "input": test_case['input'], 
                                  "expected": expected, "got": result})
                else:
                    results.append({"status": "FAIL", "input": test_case['input'], 
                                  "expected": expected, "got": result})
            else:
                sys.stdout = old_stdout
                results.append({"status": "ERROR", "message": "No function found"})
                
        except Exception as e:
            sys.stdout = old_stdout
            results.append({"status": "ERROR", "message": str(e)})
    
    return results

# Main application
def main():
    # Initialize database
    init_db()
    
    st.title("⚗️ ChemCode - Chemistry Coding Challenges")
    st.markdown("*Practice chemistry problems with Python - 15 minutes a day!*")
    
    # Load problems
    problems = load_problems()
    if not problems:
        return
    
    # Sidebar navigation
    st.sidebar.title("📚 Problems")
    selected_problem = st.sidebar.selectbox("Select Problem", list(problems.keys()))
    
    if selected_problem:
        problem = problems[selected_problem]
        
        # Create two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Problem description
            st.header(f"Problem: {problem['title']}")
            st.write(f"**Difficulty:** {problem['difficulty']}")
            st.write(f"**Time:** {problem['time_estimate']}")
            
            st.markdown("### Description")
            st.markdown(problem['description'])
            
            st.markdown("### Examples")
            for example in problem['examples']:
                st.code(f"Input: {example['input']}\nOutput: {example['output']}")
            
            if 'constraints' in problem:
                st.markdown("### Constraints")
                st.markdown(problem['constraints'])
        
        with col2:
            # Code editor
            st.markdown("### Solution")
            
            default_code = problem.get('starter_code', '# Write your solution here\ndef solve():\n    pass')
            user_code = st.text_area("Enter your Python code:", 
                                   value=default_code, 
                                   height=300)
            
            # Run button
            if st.button("🚀 Run Code", type="primary"):
                if user_code.strip():
                    # Execute code
                    results = execute_code(user_code, problem['test_cases'])
                    
                    # Display results
                    st.markdown("### Results")
                    
                    passed = sum(1 for r in results if r.get('status') == 'PASS')
                    total = len(results)
                    
                    if passed == total:
                        st.success(f"✅ All tests passed! ({passed}/{total})")
                    else:
                        st.error(f"❌ {passed}/{total} tests passed")
                    
                    # Show detailed results
                    for i, result in enumerate(results, 1):
                        with st.expander(f"Test Case {i} - {result['status']}"):
                            if result['status'] in ['PASS', 'FAIL']:
                                st.write(f"**Input:** {result['input']}")
                                st.write(f"**Expected:** {result['expected']}")
                                st.write(f"**Got:** {result['got']}")
                            else:
                                st.write(f"**Error:** {result['message']}")
                    
                    # Save submission to database
                    conn = sqlite3.connect('chemcode.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO submissions VALUES (NULL, ?, ?, ?, ?)",
                             (selected_problem, user_code, f"{passed}/{total}", datetime.now()))
                    conn.commit()
                    conn.close()
                else:
                    st.warning("Please enter some code!")
    
    # Progress tracking in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Your Progress")
    
    conn = sqlite3.connect('chemcode.db')
    try:
        submissions_df = pd.read_sql_query("SELECT * FROM submissions", conn)
        
        if not submissions_df.empty:
            total_attempts = len(submissions_df)
            problems_attempted = submissions_df['problem_id'].nunique()
            successful_submissions = len(submissions_df[submissions_df['result'].str.contains('3/3')])
            
            st.sidebar.write(f"📝 Total attempts: {total_attempts}")
            st.sidebar.write(f"🎯 Problems tried: {problems_attempted}")
            st.sidebar.write(f"✅ Successful solutions: {successful_submissions}")
            
            # Recent submissions
            st.sidebar.markdown("**Recent submissions:**")
            for _, row in submissions_df.tail(3).iterrows():
                st.sidebar.write(f"- {row['problem_id']}: {row['result']}")
        else:
            st.sidebar.write("No submissions yet. Start coding!")
            
    except Exception as e:
        st.sidebar.write("No submissions yet.")
    
    conn.close()

if __name__ == "__main__":
    main()

