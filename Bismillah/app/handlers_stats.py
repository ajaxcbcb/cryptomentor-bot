# Get statistics
    try:
        from app.users_aggregate import aggregated_premium_active, aggregated_lifetime

        # Get aggregated data
        merged_active, stats_active = aggregated_premium_active()
        lif = aggregated_lifetime()

        # Calculate counts
        old_premium = stats_active["old"]  # from backup
        premium_new = stats_active["supabase"]  # from Supabase
        lifetime_total = len(lif)

        # Admin count for autosignal eligibility
        from app.lib.auth import _resolve_admin_ids
        admin_count = len(_resolve_admin_ids())
        total_eligible = len(set(list(lif.keys()) + [int(x) for x in _resolve_admin_ids() if x.isdigit()]))

        stats_message = f"""📊 **CryptoMentor AI Statistics (Hybrid)**

👥 **Users:**
• old_premium: {old_premium}
• premium: {premium_new}
• lifetime_total: {lifetime_total}
• total_eligible (for autosignal): {total_eligible}

🤖 **System Status:**
• Database: ✅ Supabase + Legacy
• Bot Status: ✅ Running  
• Auto Signals: ✅ Admin + Lifetime Only
• Admins: {admin_count}

💡 **AutoSignal Recipients:**
• Admins: {admin_count}
• Lifetime Users: {lifetime_total}
• Total Potential: {total_eligible}"""