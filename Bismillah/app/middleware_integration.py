
# app/middleware_integration.py
"""
Integration helper for telebot middleware
"""
from .middlewares.ensure_weekly_sb import touch_user_sync

def setup_user_middleware(bot_instance):
    """
    Setup middleware for telebot - call this from your bot initialization
    """
    # Store original message handler
    original_process_new_messages = bot_instance.process_new_messages
    original_process_new_callback_query = bot_instance.process_new_callback_query
    
    def enhanced_process_new_messages(messages):
        # Touch users before processing messages
        for message in messages:
            try:
                touch_user_sync(message)
            except Exception as e:
                print(f"Middleware error for message: {e}")
        
        return original_process_new_messages(messages)
    
    def enhanced_process_new_callback_query(callback_queries):
        # Touch users before processing callbacks
        for callback in callback_queries:
            try:
                touch_user_sync(callback)
            except Exception as e:
                print(f"Middleware error for callback: {e}")
        
        return original_process_new_callback_query(callback_queries)
    
    # Replace handlers
    bot_instance.process_new_messages = enhanced_process_new_messages
    bot_instance.process_new_callback_query = enhanced_process_new_callback_query
    
    print("✅ User middleware integration enabled")
