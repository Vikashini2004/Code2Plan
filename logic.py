import json
from config import ai_client, MODEL_NAME

def generate_project_plan(idea, stack, duration_days, team_breakdown):
    """Generates a Forward Engineering timeline in JSON format with specific team constraints.
For each task, provide a JSON object with: 'phase', 'task_name', and 'difficulty' (an integer from 1 to 5, where 1 is a quick setup and 5 is heavy coding/research)."""
    
    system_prompt = (
        "You are an expert Senior Project Manager and Software Architect. "
        "Your goal is to generate a realistic, high-efficiency engineering roadmap. "
        "Output ONLY raw JSON. No conversational text."
    )
    
    # We update the prompt to explicitly mention 'Days' and the 'Role Breakdown'
    user_prompt = f"""
        Project Idea: {idea}
        Tech Stack: {stack}
        Strict Deadline: {duration_days} Days
        Team Resources: {team_breakdown}

        Task: Create a 5-step Forward Engineering roadmap. 
        1. Distribute the {duration_days} days across the 5 phases based on technical complexity.
        2. The SUM of 'days_allocated' must equal exactly {duration_days}.
        3. Ensure tasks are specific to the {stack}.

        Return a JSON array exactly in this format:
        [
          {{"phase": "Requirements", "task": "...", "days_allocated": 2}},
          {{"phase": "Design", "task": "...", "days_allocated": 2}},
          {{"phase": "Implementation", "task": "...", "days_allocated": 6}},
          {{"phase": "Testing", "task": "...", "days_allocated": 2}},
          {{"phase": "Deployment", "task": "...", "days_allocated": 2}}
        ]
        """
    try:
        response = ai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3 
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # Clean up potential Markdown formatting
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("```").replace("json", "", 1).strip()
            
        return json.loads(raw_output)
    except Exception as e:
        print(f"AI Error: {e}")
        return None
