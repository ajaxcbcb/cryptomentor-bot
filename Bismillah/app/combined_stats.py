
def get_combined_user_stats():
    """Get combined user statistics from both SQLite and Supabase"""
    stats = {
        'supabase': {'total': 0, 'premium': 0},
        'local': {'total': 0, 'premium': 0},
        'combined_estimate': {'total': 0, 'premium': 0}
    }
    
    # Get Supabase stats
    try:
        from app.stats import get_supabase_totals
        supabase_users, supabase_premium = get_supabase_totals()
        stats['supabase']['total'] = supabase_users
        stats['supabase']['premium'] = supabase_premium
    except Exception as e:
        print(f"Error getting Supabase stats: {e}")
    
    # Get Local SQLite stats
    try:
        from database import Database
        db = Database()
        
        # Count total local users
        db.cursor.execute("SELECT COUNT(*) FROM users")
        local_users = db.cursor.fetchone()[0] or 0
        
        # Count premium local users
        db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
        local_premium = db.cursor.fetchone()[0] or 0
        
        stats['local']['total'] = local_users
        stats['local']['premium'] = local_premium
        
        db.close()
    except Exception as e:
        print(f"Error getting Local SQLite stats: {e}")
    
    # Calculate combined estimates (avoiding duplicates)
    # Use max of both sources + half of min (conservative estimate for duplicates)
    total_estimate = max(stats['supabase']['total'], stats['local']['total']) + \
                    min(stats['supabase']['total'], stats['local']['total']) // 2
    
    premium_estimate = max(stats['supabase']['premium'], stats['local']['premium']) + \
                      min(stats['supabase']['premium'], stats['local']['premium']) // 2
    
    stats['combined_estimate']['total'] = total_estimate
    stats['combined_estimate']['premium'] = premium_estimate
    
    return stats

def format_user_stats_summary():
    """Get formatted summary of user statistics"""
    stats = get_combined_user_stats()
    
    return f"""📊 **User Statistics Summary:**

🎯 **Combined Estimate:**
• Total Users: ~{stats['combined_estimate']['total']}
• Premium Users: ~{stats['combined_estimate']['premium']}

📈 **Source Breakdown:**
• Supabase: {stats['supabase']['total']} total, {stats['supabase']['premium']} premium
• Local DB: {stats['local']['total']} total, {stats['local']['premium']} premium

💡 Combined estimate accounts for potential duplicates"""
