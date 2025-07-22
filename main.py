#!/usr/bin/env python3
"""
Smart Dating App - Main Entry Point
Personality-based dating app that matches users based on Big Five personality traits
"""

import logging
import sys
from user_interface import UserInterface

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dating_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        # Initialize and run the application
        app = UserInterface()
        app.run_app()
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye! Thanks for using Smart Dating App!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An unexpected error occurred. Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()