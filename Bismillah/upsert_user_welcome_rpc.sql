
create or replace function public.upsert_user_with_welcome(
  p_telegram_id bigint,
  p_username text,
  p_first_name text,
  p_last_name text,
  p_welcome_quota integer,
  p_referred_by bigint default null
) returns table(
  telegram_id bigint,
  credits integer,
  is_new boolean
) language plpgsql security definer as $$
declare
  v_existing_user record;
  v_is_new boolean := false;
  v_final_credits integer;
begin
  -- Check if user exists
  select * into v_existing_user
  from public.users 
  where users.telegram_id = p_telegram_id;
  
  if v_existing_user is null then
    -- New user - insert with welcome credits
    v_is_new := true;
    v_final_credits := p_welcome_quota;
    
    insert into public.users (
      telegram_id, 
      username, 
      first_name, 
      last_name, 
      credits,
      referred_by,
      created_at
    ) values (
      p_telegram_id,
      p_username,
      p_first_name,
      p_last_name,
      p_welcome_quota,
      p_referred_by,
      now()
    );
    
  else
    -- Existing user - update profile only, keep existing credits
    v_final_credits := v_existing_user.credits;
    
    update public.users set
      username = coalesce(p_username, username),
      first_name = coalesce(p_first_name, first_name),
      last_name = coalesce(p_last_name, last_name),
      updated_at = now()
    where users.telegram_id = p_telegram_id;
  end if;
  
  -- Return result
  return query
  select p_telegram_id, v_final_credits, v_is_new;
end$$;
