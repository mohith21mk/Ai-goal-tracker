import os
import sys
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parent))

from app.database import get_connection
from app.services.ai_coach import validate_ai_action

def run_security_test():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create a fake user B
    cursor.execute("INSERT INTO users (email, full_name) VALUES ('user_c@test.com', 'Test User B')")
    user_b_id = cursor.lastrowid
    
    # 2. Create a fake mission for user B
    cursor.execute("INSERT INTO missions (title, user_id) VALUES ('Secret Mission', ?)", (user_b_id,))
    mission_b_id = cursor.lastrowid
    conn.commit()
    
    # 3. Simulate User A (the demo user, ID 1) getting a hallucinated action for User B's mission
    user_a_id = 1
    hallucinated_action = {
        "type": "MARK_MISSION_COMPLETE",
        "target_id": mission_b_id
    }
    
    print(f"Testing action validation for User {user_a_id} accessing Mission {mission_b_id} (Owned by User {user_b_id})")
    
    # 4. Validate
    validated = validate_ai_action(hallucinated_action, user_a_id)
    
    # 5. Assert
    if validated is None:
        print("[SUCCESS] The action validator correctly rejected the cross-tenant action!")
    else:
        print("[FAILURE] The action validator ALLOWED the cross-tenant action!")
        print(f"Returned: {validated}")
        
    # Cleanup
    cursor.execute("DELETE FROM missions WHERE id = ?", (mission_b_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_b_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_security_test()
