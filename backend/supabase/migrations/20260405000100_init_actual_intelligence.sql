-- Initial schema for GPTless "Actual Intelligence" app.
-- Covers auth-linked profiles, chats, requests, messages, fulfillments, token accounting,
-- API RPC helpers (create chat + fulfill request), and responder/unclaimed-chat RLS.

create extension if not exists pgcrypto;

-- ----------
-- Enum types
-- ----------
do $$
begin
  if to_regtype('public.app_role') is null then
    create type public.app_role as enum ('requester', 'responder', 'developer', 'admin');
  end if;

  if to_regtype('public.chat_status') is null then
    create type public.chat_status as enum ('open', 'closed');
  end if;

  if to_regtype('public.claim_status') is null then
    create type public.claim_status as enum ('unclaimed', 'claimed');
  end if;

  if to_regtype('public.sender_type') is null then
    create type public.sender_type as enum ('requester', 'responder', 'system');
  end if;

  if to_regtype('public.request_status') is null then
    create type public.request_status as enum ('pending', 'in_progress', 'fulfilled', 'cancelled');
  end if;

  if to_regtype('public.token_txn_type') is null then
    create type public.token_txn_type as enum ('buy', 'redeem', 'spend', 'refund', 'adjustment');
  end if;
end
$$;

-- ----------
-- Auth bootstrap
-- ----------
-- Bootstrap profile + default role on new Supabase auth user creation.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_username text;
  v_account_id uuid;
begin
  v_username := coalesce(
    new.raw_user_meta_data ->> 'username',
    split_part(new.email, '@', 1),
    'user_' || substr(new.id::text, 1, 8)
  );

  insert into public.profiles (user_id, username, display_name)
  values (
    new.id,
    v_username,
    coalesce(new.raw_user_meta_data ->> 'name', split_part(new.email, '@', 1))
  )
  on conflict (user_id) do nothing;

  insert into public.user_roles (user_id, role)
  values (new.id, 'requester')
  on conflict do nothing;

  insert into public.accounts (account_name, created_by)
  values (v_username, new.id)
  on conflict (account_name) do nothing
  returning account_id into v_account_id;

  if v_account_id is null then
    select a.account_id
      into v_account_id
      from public.accounts a
     where a.created_by = new.id
     order by a.created_at asc
     limit 1;
  end if;

  if v_account_id is not null then
    insert into public.token_balances (account_id, balance)
    values (v_account_id, 0)
    on conflict (account_id) do nothing;
  end if;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();

-- ----------
-- Auth profile + roles
-- ----------
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  username text not null unique,
  display_name text not null,
  created_at timestamptz not null default now(),
  last_online_at timestamptz
);

create table if not exists public.user_roles (
  user_id uuid not null references auth.users(id) on delete cascade,
  role public.app_role not null,
  created_at timestamptz not null default now(),
  primary key (user_id, role)
);

-- ----------
-- Accounts and token ledger
-- ----------
create table if not exists public.accounts (
  account_id uuid primary key default gen_random_uuid(),
  account_name text not null unique,
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table if not exists public.token_balances (
  account_id uuid primary key references public.accounts(account_id) on delete cascade,
  balance bigint not null default 0 check (balance >= 0),
  updated_at timestamptz not null default now()
);

create table if not exists public.token_transactions (
  token_txn_id text primary key default ('tok_' || replace(gen_random_uuid()::text, '-', '')),
  account_id uuid not null references public.accounts(account_id) on delete restrict,
  txn_type public.token_txn_type not null,
  amount bigint not null check (amount <> 0),
  chat_id text,
  request_id text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

-- Backfill default accounts for existing users missing one.
insert into public.accounts (account_name, created_by)
select p.username, p.user_id
from public.profiles p
where not exists (
  select 1
  from public.accounts a
  where a.created_by = p.user_id
)
on conflict (account_name) do nothing;

-- Ensure every account has a token balance row.
insert into public.token_balances (account_id, balance)
select a.account_id, 0
from public.accounts a
where not exists (
  select 1
  from public.token_balances tb
  where tb.account_id = a.account_id
);

-- ----------
-- Chat workflow
-- ----------
create table if not exists public.chats (
  chat_id text primary key default ('chat_' || replace(gen_random_uuid()::text, '-', '')),
  requester_id uuid not null references auth.users(id) on delete restrict,
  responder_id uuid references auth.users(id) on delete set null,
  status public.chat_status not null default 'open',
  claim_state public.claim_status not null default 'unclaimed',
  title text,
  category text,
  created_at timestamptz not null default now(),
  closed_at timestamptz
);

create table if not exists public.requests (
  request_id text primary key default ('req_' || replace(gen_random_uuid()::text, '-', '')),
  chat_id text not null references public.chats(chat_id) on delete cascade,
  requester_id uuid not null references auth.users(id) on delete restrict,
  request_text text not null,
  tokens_to_spend bigint not null check (tokens_to_spend > 0),
  status public.request_status not null default 'pending',
  created_at timestamptz not null default now()
);

create table if not exists public.messages (
  message_id text primary key default ('msg_' || replace(gen_random_uuid()::text, '-', '')),
  chat_id text not null references public.chats(chat_id) on delete cascade,
  sender_id uuid not null references auth.users(id) on delete restrict,
  sender_type public.sender_type not null,
  message text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.fulfillments (
  fulfillment_id text primary key default ('full_' || replace(gen_random_uuid()::text, '-', '')),
  request_id text not null unique references public.requests(request_id) on delete cascade,
  chat_id text not null references public.chats(chat_id) on delete cascade,
  responder_id uuid not null references auth.users(id) on delete restrict,
  response_text text not null,
  attachments jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

-- ----------
-- Indexes
-- ----------
create index if not exists idx_user_roles_user_id on public.user_roles(user_id);
create index if not exists idx_token_transactions_account_created_at on public.token_transactions(account_id, created_at desc);
create index if not exists idx_chats_requester on public.chats(requester_id, created_at desc);
create index if not exists idx_chats_responder on public.chats(responder_id, created_at desc);
create index if not exists idx_requests_chat on public.requests(chat_id, created_at asc);
create index if not exists idx_messages_chat on public.messages(chat_id, created_at asc);
create index if not exists idx_fulfillments_chat on public.fulfillments(chat_id, created_at asc);

-- ----------
-- Helper functions for RLS
-- ----------
create or replace function public.has_role(required_role public.app_role)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.user_roles ur
    where ur.user_id = auth.uid()
      and ur.role = required_role
  );
$$;

create or replace function public.is_chat_participant(p_chat_id text)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.chats c
    where c.chat_id = p_chat_id
      and (c.requester_id = auth.uid() or c.responder_id = auth.uid())
  );
$$;

create or replace function public.is_account_owner(p_account_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.accounts a
    where a.account_id = p_account_id
      and a.created_by = auth.uid()
  );
$$;

-- ----------
-- Enable RLS
-- ----------
alter table public.profiles enable row level security;
alter table public.user_roles enable row level security;
alter table public.accounts enable row level security;
alter table public.token_balances enable row level security;
alter table public.token_transactions enable row level security;
alter table public.chats enable row level security;
alter table public.requests enable row level security;
alter table public.messages enable row level security;
alter table public.fulfillments enable row level security;

-- ----------
-- Profiles and roles policies
-- ----------
create policy "profiles_select_own"
on public.profiles
for select
to authenticated
using (user_id = auth.uid());

create policy "profiles_insert_own"
on public.profiles
for insert
to authenticated
with check (user_id = auth.uid());

create policy "profiles_update_own"
on public.profiles
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "profiles_select_for_chat_peer"
on public.profiles
for select
to authenticated
using (
  exists (
    select 1
    from public.chats c
    where (c.requester_id = profiles.user_id or c.responder_id = profiles.user_id)
      and (c.requester_id = auth.uid() or c.responder_id = auth.uid())
  )
);

create policy "profiles_select_requester_when_unclaimed_pool"
on public.profiles
for select
to authenticated
using (
  public.has_role('responder')
  and exists (
    select 1
    from public.chats c
    where c.requester_id = profiles.user_id
      and c.responder_id is null
      and c.claim_state = 'unclaimed'
      and c.status = 'open'
  )
);

create policy "user_roles_select_own"
on public.user_roles
for select
to authenticated
using (user_id = auth.uid());

-- ----------
-- Account/token policies
-- ----------
create policy "accounts_select_owner"
on public.accounts
for select
to authenticated
using (public.is_account_owner(account_id));

create policy "token_balances_select_owner"
on public.token_balances
for select
to authenticated
using (public.is_account_owner(account_id));

create policy "token_txn_select_owner"
on public.token_transactions
for select
to authenticated
using (public.is_account_owner(account_id));

-- Developer/admin style write access for token management endpoints.
create policy "accounts_write_developer"
on public.accounts
for all
to authenticated
using (public.has_role('developer') or public.has_role('admin'))
with check (public.has_role('developer') or public.has_role('admin'));

create policy "token_balances_write_developer"
on public.token_balances
for all
to authenticated
using (public.has_role('developer') or public.has_role('admin'))
with check (public.has_role('developer') or public.has_role('admin'));

create policy "token_txn_write_developer"
on public.token_transactions
for all
to authenticated
using (public.has_role('developer') or public.has_role('admin'))
with check (public.has_role('developer') or public.has_role('admin'));

-- ----------
-- Chat policies
-- ----------
create policy "chats_select_participant"
on public.chats
for select
to authenticated
using (requester_id = auth.uid() or responder_id = auth.uid());

create policy "chats_insert_requester"
on public.chats
for insert
to authenticated
with check (requester_id = auth.uid());

create policy "chats_update_requester"
on public.chats
for update
to authenticated
using (requester_id = auth.uid())
with check (requester_id = auth.uid());

create policy "chats_claim_responder"
on public.chats
for update
to authenticated
using (
  responder_id is null
  and claim_state = 'unclaimed'
  and public.has_role('responder')
)
with check (
  responder_id = auth.uid()
  and claim_state = 'claimed'
);

create policy "chats_select_unclaimed_for_responder"
on public.chats
for select
to authenticated
using (
  public.has_role('responder')
  and responder_id is null
  and claim_state = 'unclaimed'
  and status = 'open'
);

-- ----------
-- Requests policies
-- ----------
create policy "requests_select_participant"
on public.requests
for select
to authenticated
using (public.is_chat_participant(chat_id));

create policy "requests_insert_requester"
on public.requests
for insert
to authenticated
with check (
  requester_id = auth.uid()
  and exists (
    select 1
    from public.chats c
    where c.chat_id = requests.chat_id
      and c.requester_id = auth.uid()
      and c.status = 'open'
  )
);

create policy "requests_update_responder"
on public.requests
for update
to authenticated
using (
  exists (
    select 1
    from public.chats c
    where c.chat_id = requests.chat_id
      and c.responder_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from public.chats c
    where c.chat_id = requests.chat_id
      and c.responder_id = auth.uid()
  )
);

-- ----------
-- Message policies
-- ----------
create policy "messages_select_participant"
on public.messages
for select
to authenticated
using (public.is_chat_participant(chat_id));

create policy "messages_insert_participant"
on public.messages
for insert
to authenticated
with check (
  sender_id = auth.uid()
  and public.is_chat_participant(chat_id)
);

-- ----------
-- Fulfillment policies
-- ----------
create policy "fulfillments_select_participant"
on public.fulfillments
for select
to authenticated
using (public.is_chat_participant(chat_id));

create policy "fulfillments_insert_assigned_responder"
on public.fulfillments
for insert
to authenticated
with check (
  responder_id = auth.uid()
  and exists (
    select 1
    from public.chats c
    where c.chat_id = fulfillments.chat_id
      and c.responder_id = auth.uid()
  )
);

-- ----------
-- API RPCs (called from PostgREST / supabase-py as invoke)
-- ----------
create or replace function public.create_chat_with_initial_request(
  p_title text,
  p_category text,
  p_request_text text,
  p_tokens_to_spend bigint
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_chat_id text;
  v_request_id text;
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'not authenticated';
  end if;

  if p_request_text is null or length(trim(p_request_text)) = 0 then
    raise exception 'invalid_request_text';
  end if;

  if p_tokens_to_spend is null or p_tokens_to_spend <= 0 then
    raise exception 'invalid_tokens';
  end if;

  insert into public.chats (requester_id, title, category, status, claim_state)
  values (
    v_uid,
    coalesce(nullif(trim(p_title), ''), 'New Request'),
    coalesce(nullif(trim(p_category), ''), 'general'),
    'open',
    'unclaimed'
  )
  returning chat_id into v_chat_id;

  insert into public.requests (chat_id, requester_id, request_text, tokens_to_spend, status)
  values (v_chat_id, v_uid, trim(p_request_text), p_tokens_to_spend, 'pending')
  returning request_id into v_request_id;

  return jsonb_build_object(
    'ok', true,
    'chat_id', v_chat_id,
    'request_id', v_request_id
  );
end;
$$;

create or replace function public.fulfill_chat_active_request(
  p_chat_id text,
  p_response_text text,
  p_attachments jsonb default '[]'::jsonb
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_req public.requests%rowtype;
  v_fid text;
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'not authenticated';
  end if;

  if p_response_text is null or length(trim(p_response_text)) = 0 then
    raise exception 'invalid_response_text';
  end if;

  select * into v_req
  from public.requests r
  where r.chat_id = p_chat_id
    and r.status in ('pending', 'in_progress')
  order by r.created_at asc
  limit 1
  for update;

  if v_req.request_id is null then
    return jsonb_build_object('ok', false, 'error', 'no_active_request');
  end if;

  insert into public.fulfillments (request_id, chat_id, responder_id, response_text, attachments)
  values (v_req.request_id, p_chat_id, v_uid, trim(p_response_text), coalesce(p_attachments, '[]'::jsonb))
  returning fulfillment_id into v_fid;

  update public.requests
  set status = 'fulfilled'
  where request_id = v_req.request_id;

  return jsonb_build_object(
    'ok', true,
    'fulfillment_id', v_fid,
    'request_id', v_req.request_id
  );
end;
$$;

grant execute on function public.create_chat_with_initial_request(text, text, text, bigint) to authenticated;
grant execute on function public.fulfill_chat_active_request(text, text, jsonb) to authenticated;

-- ----------
-- Realtime subscriptions
-- ----------
-- Realtime requires table SELECT privilege plus RLS visibility.
grant select on table public.chats to authenticated;
grant select on table public.requests to authenticated;
grant select on table public.messages to authenticated;
grant select on table public.fulfillments to authenticated;
grant select on table public.token_balances to authenticated;

do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'chats'
  ) then
    alter publication supabase_realtime add table public.chats;
  end if;

  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'requests'
  ) then
    alter publication supabase_realtime add table public.requests;
  end if;

  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'messages'
  ) then
    alter publication supabase_realtime add table public.messages;
  end if;

  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'fulfillments'
  ) then
    alter publication supabase_realtime add table public.fulfillments;
  end if;

  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'token_balances'
  ) then
    alter publication supabase_realtime add table public.token_balances;
  end if;
end
$$;
