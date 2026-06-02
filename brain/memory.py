import sqlite3
import os
import sys
# Add parent directory to path to allow importing config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class JarvisMemory:
    """Manages long-term SQLite-based memory for the JARVIS assistant."""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DATABASE_PATH
        self._init_db()

    def _init_db(self):
        """Initializes the database and ensures the memories table exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Memory Error] Could not initialize database: {e}")

    def store(self, key: str, value: str) -> str:
        """Stores or updates a memory key-value pair."""
        key = key.strip().lower()
        value = value.strip()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memories (key, value, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value=excluded.value,
                    timestamp=CURRENT_TIMESTAMP
            ''', (key, value))
            conn.commit()
            conn.close()
            return f"Successfully stored memory for '{key}': '{value}'"
        except Exception as e:
            return f"Failed to store memory: {e}"

    def recall(self, query: str) -> str:
        """Recalls a memory by searching keys or values matching the query string."""
        query = query.strip().lower()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Perform a wildcard match against both key and value
            cursor.execute('''
                SELECT key, value, timestamp FROM memories 
                WHERE key LIKE ? OR value LIKE ?
            ''', (f"%{query}%", f"%{query}%"))
            results = cursor.fetchall()
            conn.close()

            if not results:
                return f"No memories found matching '{query}'."

            memory_strings = []
            for r_key, r_value, r_time in results:
                memory_strings.append(f"- '{r_key}': '{r_value}' (stored on {r_time})")
            
            return "Here are the memories I found:\n" + "\n".join(memory_strings)
        except Exception as e:
            return f"Failed to retrieve memory: {e}"

    def delete(self, key: str) -> str:
        """Deletes a memory key-value pair."""
        key = key.strip().lower()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memories WHERE key = ?', (key,))
            changes = conn.total_changes
            conn.commit()
            conn.close()
            if changes > 0:
                return f"Successfully deleted memory for key '{key}'."
            else:
                return f"No memory key matching '{key}' was found to delete."
        except Exception as e:
            return f"Failed to delete memory: {e}"

    def list_all(self) -> str:
        """Returns all stored memories."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM memories')
            results = cursor.fetchall()
            conn.close()

            if not results:
                return "My memory is currently empty, sir."

            memory_strings = []
            for r_key, r_value in results:
                memory_strings.append(f"- '{r_key}': '{r_value}'")
            return "All stored memories:\n" + "\n".join(memory_strings)
        except Exception as e:
            return f"Failed to list memories: {e}"

# Simple self-test if run directly
if __name__ == "__main__":
    memory = JarvisMemory("test_memory.db")
    print(memory.store("server ip", "192.168.1.50"))
    print(memory.store("wifi password", "admin123"))
    print(memory.recall("server"))
    print(memory.list_all())
    print(memory.delete("wifi password"))
    print(memory.list_all())
    # Clean up test database
    if os.path.exists("test_memory.db"):
        os.remove("test_memory.db")
        print("Cleaned up test db.")
