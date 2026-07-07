"""
=====================================================
Database Connection
Project : AI Powered EMI Planner
Author  : Srinivas Rao

Purpose:
Manage SQLite database connection
=====================================================
"""

import sqlite3
from pathlib import Path


# Database location

DB_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "emi_planner.db"
)



def get_connection():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )


    return connection