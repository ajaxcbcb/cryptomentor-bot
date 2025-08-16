
create or replace function public.stats_totals()
returns table(total_users bigint, premium_users bigint)
language sql stable as $$
  select
    count(*)::bigint as total_users,
    count(*) filter (
      where
        coalesce(is_lifetime, false)
        or (coalesce(is_premium, false) and premium_until is not null and premium_until > now())
    )::bigint as premium_users
  from public.users;
$$;

NOTIFY pgrst, 'reload schema';
