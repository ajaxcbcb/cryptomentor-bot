
create or replace function public.debit_credits(
  p_telegram_id bigint,
  p_amount integer
) returns integer language plpgsql security definer as $$
declare v_remaining integer;
begin
  update public.users
  set credits = greatest(0, credits - p_amount)
  where telegram_id = p_telegram_id
  returning credits into v_remaining;

  insert into public.user_events (telegram_id, event_type, meta)
  values (p_telegram_id, 'DEBIT_CREDIT', jsonb_build_object('amount', p_amount, 'remaining', v_remaining));

  return coalesce(v_remaining, 0);
end$$;

create or replace function public.upsert_user_with_welcome(
  p_telegram_id bigint,
  p_username text default null,
  p_first_name text default null,
  p_last_name text default null,
  p_welcome_quota integer default 100,
  p_referred_by bigint default null
) returns table(telegram_id bigint, credits integer, is_new boolean) language plpgsql security definer as $$
declare
  v_user_exists boolean;
  v_credits integer;
begin
  -- Check if user exists
  select exists(select 1 from public.users where users.telegram_id = p_telegram_id) into v_user_exists;
  
  if not v_user_exists then
    -- Insert new user with welcome credits
    insert into public.users (telegram_id, username, first_name, last_name, credits, referred_by)
    values (p_telegram_id, p_username, p_first_name, p_last_name, p_welcome_quota, p_referred_by);
    
    return query select p_telegram_id, p_welcome_quota, true;
  else
    -- User exists, just update profile info but DON'T touch credits
    update public.users 
    set username = coalesce(p_username, username),
        first_name = coalesce(p_first_name, first_name),
        last_name = coalesce(p_last_name, last_name),
        updated_at = now()
    where users.telegram_id = p_telegram_id
    returning users.credits into v_credits;
    
    return query select p_telegram_id, v_credits, false;
  end if;
end$$;
