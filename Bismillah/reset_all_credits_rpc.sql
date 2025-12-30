
create or replace function public.reset_all_user_credits(
  p_amount integer default 100
) returns integer language plpgsql security definer as $$
declare 
  v_updated_count integer;
begin
  -- Update all non-premium users to specified credit amount
  update public.users
  set credits = p_amount
  where is_premium = false
  and telegram_id is not null;
  
  -- Get count of updated rows
  get diagnostics v_updated_count = row_count;
  
  -- Log the mass update
  insert into public.user_events (telegram_id, event_type, meta)
  values (0, 'MASS_CREDIT_RESET', jsonb_build_object('amount', p_amount, 'updated_count', v_updated_count));
  
  return v_updated_count;
end$$;
