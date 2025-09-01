
create or replace function public.add_credits(
  p_telegram_id bigint,
  p_amount integer
) returns integer language plpgsql security definer as $$
declare 
  v_new_balance integer;
begin
  update public.users
  set credits = credits + p_amount
  where telegram_id = p_telegram_id
  returning credits into v_new_balance;
  
  if not found then
    return 0;
  end if;
  
  return v_new_balance;
end$$;
