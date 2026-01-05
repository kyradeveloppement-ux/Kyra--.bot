"""
Centralized Database Manager for Kyra Discord Bot
Provides a unified interface for all database operations.
"""
import aiosqlite
from typing import Optional, List, Tuple, Any
from contextlib import asynccontextmanager
import os


class DatabaseManager:
    """Manages all database connections and operations"""
    
    # Database paths
    DB_DIR = "db"
    NP_DB = os.path.join(DB_DIR, "np.db")
    
    @staticmethod
    @asynccontextmanager
    async def get_connection(db_path: str):
        """
        Context manager for database connections.
        Automatically handles connection opening and closing.
        
        Usage:
            async with DatabaseManager.get_connection('db/np.db') as db:
                cursor = await db.execute("SELECT * FROM table")
                result = await cursor.fetchone()
        """
        conn = await aiosqlite.connect(db_path)
        try:
            yield conn
        finally:
            await conn.close()
    
    @staticmethod
    async def execute_query(
        db_path: str,
        query: str,
        params: Tuple = (),
        fetch: str = None
    ) -> Optional[Any]:
        """
        Execute a database query with automatic connection management.
        
        Args:
            db_path: Path to the database file
            query: SQL query to execute
            params: Query parameters (tuple)
            fetch: How to fetch results - 'one', 'all', or None (for INSERT/UPDATE/DELETE)
        
        Returns:
            Query results based on fetch parameter, or None
        """
        async with DatabaseManager.get_connection(db_path) as db:
            cursor = await db.execute(query, params)
            
            if fetch == 'one':
                result = await cursor.fetchone()
            elif fetch == 'all':
                result = await cursor.fetchall()
            else:
                await db.commit()
                result = None
            
            await cursor.close()
            return result
    
    @staticmethod
    async def initialize_databases():
        """Initialize all required databases on bot startup"""
        # Ensure database directory exists
        os.makedirs(DatabaseManager.DB_DIR, exist_ok=True)
        
        # Initialize NP (No Prefix) database
        await DatabaseManager.init_np_db()
        
        print("✅ All databases initialized successfully")
    
    @staticmethod
    async def init_np_db():
        """Initialize the No Prefix database"""
        query = """
        CREATE TABLE IF NOT EXISTS np (
            id INTEGER PRIMARY KEY
        )
        """
        await DatabaseManager.execute_query(DatabaseManager.NP_DB, query)
    
    # ============================================
    # NO PREFIX DATABASE HELPERS
    # ============================================
    
    @staticmethod
    async def is_np_user(user_id: int) -> bool:
        """Check if a user has no-prefix privileges"""
        result = await DatabaseManager.execute_query(
            DatabaseManager.NP_DB,
            "SELECT id FROM np WHERE id = ?",
            (user_id,),
            fetch='one'
        )
        return result is not None
    
    @staticmethod
    async def add_np_user(user_id: int):
        """Add a user to no-prefix list"""
        await DatabaseManager.execute_query(
            DatabaseManager.NP_DB,
            "INSERT OR IGNORE INTO np (id) VALUES (?)",
            (user_id,)
        )
    
    @staticmethod
    async def remove_np_user(user_id: int):
        """Remove a user from no-prefix list"""
        await DatabaseManager.execute_query(
            DatabaseManager.NP_DB,
            "DELETE FROM np WHERE id = ?",
            (user_id,)
        )
    
    @staticmethod
    async def get_all_np_users() -> List[int]:
        """Get all no-prefix users"""
        results = await DatabaseManager.execute_query(
            DatabaseManager.NP_DB,
            "SELECT id FROM np",
            fetch='all'
        )
        return [row[0] for row in results] if results else []


# Singleton instance for easy access
db = DatabaseManager()
