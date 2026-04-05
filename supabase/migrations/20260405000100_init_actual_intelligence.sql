-- Initial schema for GPTless "Actual Intelligence" app.
-- Covers auth-linked profiles, chats, requests, messages, fulfillments, and token accounting.

create extension if not exists pgcrypto;

-- ----------
-- Enum types
-- ----------
do $$
begin
  if not exists (select 1 from pg_type where typname = 'app_role') then
    create type public.app_role as enum ('requester', 'responder', 'developer', 'admin');
  end if;

  if not exists (select 1 from pg_type where typname = 'chat_status') then
    create type public.chat_status as enum ('open', 'closed');
  end if;

  if not exists (select 1 from pg_type where typname = 'claim_status') then
    create type public.claim_status as enum ('unclaimed', 'claimed');
  end if;

  if not exists (select 1 from pg_type where typname = 'sender_type') then
    create type public.sender_type as enum ('requester', 'responder', 'system');
  end if;

  if not exists (select 1 from pg_type where typname = 'request_status') then
    create type public.request_status as enum ('pending', 'in_progress', 'fulfilled', 'cancelled');
  end if;

  if not exists (select 1 from pg_type where typname = 'token_txn_type') then
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
begin
  insert into public.profiles (user_id, username, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'username', split_part(new.email, '@', 1)),
    coalesce(new.raw_user_meta_data ->> 'name', split_part(new.email, '@', 1))
  )
  on conflict (user_id) do nothing;

  insert into public.user_roles (user_id, role)
  values (new.id, 'requester')
  on conflict do nothing;

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
  created_at timestamptz not null default now()
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

create table if not exists public.account_members (
  account_id uuid not null references public.accounts(account_id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  is_owner boolean not null default false,
  joined_at timestamptz not null default now(),
  primary key (account_id, user_id)
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
create index if not exists idx_account_members_user_id on public.account_members(user_id);
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

create or replace function public.is_account_member(p_account_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.account_members am
    where am.account_id = p_account_id
      and am.user_id = auth.uid()
  );
$$;

create or replace function public.is_account_owner(p_account_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.account_members am
    where am.account_id = p_account_id
      and am.user_id = auth.uid()
      and am.is_owner = true
  );
$$;

-- ----------
-- Enable RLS
-- ----------
alter table public.profiles enable row level security;
alter table public.user_roles enable row level security;
alter table public.accounts enable row level security;
alter table public.account_members enable row level security;
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

create policy "user_roles_select_own"
on public.user_roles
for select
to authenticated
using (user_id = auth.uid());

-- ----------
-- Account/token policies
-- ----------
create policy "accounts_select_member"
on public.accounts
for select
to authenticated
using (public.is_account_member(account_id));

create policy "account_members_select_member"
on public.account_members
for select
to authenticated
using (public.is_account_member(account_id));

create policy "token_balances_select_member"
on public.token_balances
for select
to authenticated
using (public.is_account_member(account_id));

create policy "token_txn_select_member"
on public.token_transactions
for select
to authenticated
using (public.is_account_member(account_id));

-- Developer/admin style write access for token management endpoints.
create policy "accounts_write_developer"
on public.accounts
for all
to authenticated
using (public.has_role('developer') or public.has_role('admin'))
with check (public.has_role('developer') or public.has_role('admin'));

create policy "account_members_write_developer"
on public.account_members
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
