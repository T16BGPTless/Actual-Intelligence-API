


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;




ALTER SCHEMA "public" OWNER TO "postgres";


CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "public"."app_role" AS ENUM (
    'requester',
    'responder',
    'developer',
    'admin'
);


ALTER TYPE "public"."app_role" OWNER TO "postgres";


CREATE TYPE "public"."chat_status" AS ENUM (
    'open',
    'closed'
);


ALTER TYPE "public"."chat_status" OWNER TO "postgres";


CREATE TYPE "public"."claim_status" AS ENUM (
    'unclaimed',
    'claimed'
);


ALTER TYPE "public"."claim_status" OWNER TO "postgres";


CREATE TYPE "public"."request_status" AS ENUM (
    'pending',
    'in_progress',
    'fulfilled',
    'cancelled'
);


ALTER TYPE "public"."request_status" OWNER TO "postgres";


CREATE TYPE "public"."sender_type" AS ENUM (
    'requester',
    'responder',
    'system'
);


ALTER TYPE "public"."sender_type" OWNER TO "postgres";


CREATE TYPE "public"."token_txn_type" AS ENUM (
    'buy',
    'redeem',
    'spend',
    'refund',
    'adjustment'
);


ALTER TYPE "public"."token_txn_type" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."create_chat_with_initial_request"("p_title" "text", "p_category" "text", "p_request_text" "text", "p_tokens_to_spend" bigint) RETURNS "jsonb"
    LANGUAGE "plpgsql"
    SET "search_path" TO 'public'
    AS $$
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


ALTER FUNCTION "public"."create_chat_with_initial_request"("p_title" "text", "p_category" "text", "p_request_text" "text", "p_tokens_to_spend" bigint) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."fulfill_chat_active_request"("p_chat_id" "text", "p_response_text" "text", "p_attachments" "jsonb" DEFAULT '[]'::"jsonb") RETURNS "jsonb"
    LANGUAGE "plpgsql"
    SET "search_path" TO 'public'
    AS $$
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


ALTER FUNCTION "public"."fulfill_chat_active_request"("p_chat_id" "text", "p_response_text" "text", "p_attachments" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
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


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."has_role"("required_role" "public"."app_role") RETURNS boolean
    LANGUAGE "sql" STABLE
    SET "search_path" TO ''
    AS $$
  select exists (
    select 1
    from public.user_roles ur
    where ur.user_id = auth.uid()
      and ur.role = required_role
  );
$$;


ALTER FUNCTION "public"."has_role"("required_role" "public"."app_role") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."is_account_owner"("p_account_id" "uuid") RETURNS boolean
    LANGUAGE "sql" STABLE
    SET "search_path" TO ''
    AS $$
  select exists (
    select 1
    from public.accounts a
    where a.account_id = p_account_id
      and a.created_by = auth.uid()
  );
$$;


ALTER FUNCTION "public"."is_account_owner"("p_account_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."is_chat_participant"("p_chat_id" "text") RETURNS boolean
    LANGUAGE "sql" STABLE
    SET "search_path" TO ''
    AS $$
  select exists (
    select 1
    from public.chats c
    where c.chat_id = p_chat_id
      and (c.requester_id = auth.uid() or c.responder_id = auth.uid())
  );
$$;


ALTER FUNCTION "public"."is_chat_participant"("p_chat_id" "text") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."accounts" (
    "account_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "account_name" "text" NOT NULL,
    "created_by" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."accounts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."chats" (
    "chat_id" "text" DEFAULT ('chat_'::"text" || "replace"(("gen_random_uuid"())::"text", '-'::"text", ''::"text")) NOT NULL,
    "requester_id" "uuid" NOT NULL,
    "responder_id" "uuid",
    "status" "public"."chat_status" DEFAULT 'open'::"public"."chat_status" NOT NULL,
    "claim_state" "public"."claim_status" DEFAULT 'unclaimed'::"public"."claim_status" NOT NULL,
    "title" "text",
    "category" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "closed_at" timestamp with time zone
);


ALTER TABLE "public"."chats" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."fulfillments" (
    "fulfillment_id" "text" DEFAULT ('full_'::"text" || "replace"(("gen_random_uuid"())::"text", '-'::"text", ''::"text")) NOT NULL,
    "request_id" "text" NOT NULL,
    "chat_id" "text" NOT NULL,
    "responder_id" "uuid" NOT NULL,
    "response_text" "text" NOT NULL,
    "attachments" "jsonb" DEFAULT '[]'::"jsonb" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."fulfillments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."messages" (
    "message_id" "text" DEFAULT ('msg_'::"text" || "replace"(("gen_random_uuid"())::"text", '-'::"text", ''::"text")) NOT NULL,
    "chat_id" "text" NOT NULL,
    "sender_id" "uuid" NOT NULL,
    "sender_type" "public"."sender_type" NOT NULL,
    "message" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."messages" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "user_id" "uuid" NOT NULL,
    "username" "text" NOT NULL,
    "display_name" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "last_online_at" timestamp with time zone
);


ALTER TABLE "public"."profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."requests" (
    "request_id" "text" DEFAULT ('req_'::"text" || "replace"(("gen_random_uuid"())::"text", '-'::"text", ''::"text")) NOT NULL,
    "chat_id" "text" NOT NULL,
    "requester_id" "uuid" NOT NULL,
    "request_text" "text" NOT NULL,
    "tokens_to_spend" bigint NOT NULL,
    "status" "public"."request_status" DEFAULT 'pending'::"public"."request_status" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "requests_tokens_to_spend_check" CHECK (("tokens_to_spend" > 0))
);


ALTER TABLE "public"."requests" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."token_balances" (
    "account_id" "uuid" NOT NULL,
    "balance" bigint DEFAULT 0 NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "token_balances_balance_check" CHECK (("balance" >= 0))
);


ALTER TABLE "public"."token_balances" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."token_transactions" (
    "token_txn_id" "text" DEFAULT ('tok_'::"text" || "replace"(("gen_random_uuid"())::"text", '-'::"text", ''::"text")) NOT NULL,
    "account_id" "uuid" NOT NULL,
    "txn_type" "public"."token_txn_type" NOT NULL,
    "amount" bigint NOT NULL,
    "chat_id" "text",
    "request_id" "text",
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "token_transactions_amount_check" CHECK (("amount" <> 0))
);


ALTER TABLE "public"."token_transactions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_roles" (
    "user_id" "uuid" NOT NULL,
    "role" "public"."app_role" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."user_roles" OWNER TO "postgres";


ALTER TABLE ONLY "public"."accounts"
    ADD CONSTRAINT "accounts_account_name_key" UNIQUE ("account_name");



ALTER TABLE ONLY "public"."accounts"
    ADD CONSTRAINT "accounts_pkey" PRIMARY KEY ("account_id");



ALTER TABLE ONLY "public"."chats"
    ADD CONSTRAINT "chats_pkey" PRIMARY KEY ("chat_id");



ALTER TABLE ONLY "public"."fulfillments"
    ADD CONSTRAINT "fulfillments_pkey" PRIMARY KEY ("fulfillment_id");



ALTER TABLE ONLY "public"."fulfillments"
    ADD CONSTRAINT "fulfillments_request_id_key" UNIQUE ("request_id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("message_id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("user_id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_username_key" UNIQUE ("username");



ALTER TABLE ONLY "public"."requests"
    ADD CONSTRAINT "requests_pkey" PRIMARY KEY ("request_id");



ALTER TABLE ONLY "public"."token_balances"
    ADD CONSTRAINT "token_balances_pkey" PRIMARY KEY ("account_id");



ALTER TABLE ONLY "public"."token_transactions"
    ADD CONSTRAINT "token_transactions_pkey" PRIMARY KEY ("token_txn_id");



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_pkey" PRIMARY KEY ("user_id", "role");



CREATE INDEX "idx_chats_requester" ON "public"."chats" USING "btree" ("requester_id", "created_at" DESC);



CREATE INDEX "idx_chats_responder" ON "public"."chats" USING "btree" ("responder_id", "created_at" DESC);



CREATE INDEX "idx_fulfillments_chat" ON "public"."fulfillments" USING "btree" ("chat_id", "created_at");



CREATE INDEX "idx_messages_chat" ON "public"."messages" USING "btree" ("chat_id", "created_at");



CREATE INDEX "idx_requests_chat" ON "public"."requests" USING "btree" ("chat_id", "created_at");



CREATE INDEX "idx_token_transactions_account_created_at" ON "public"."token_transactions" USING "btree" ("account_id", "created_at" DESC);



CREATE INDEX "idx_user_roles_user_id" ON "public"."user_roles" USING "btree" ("user_id");



ALTER TABLE ONLY "public"."accounts"
    ADD CONSTRAINT "accounts_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."chats"
    ADD CONSTRAINT "chats_requester_id_fkey" FOREIGN KEY ("requester_id") REFERENCES "auth"."users"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."chats"
    ADD CONSTRAINT "chats_responder_id_fkey" FOREIGN KEY ("responder_id") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."fulfillments"
    ADD CONSTRAINT "fulfillments_chat_id_fkey" FOREIGN KEY ("chat_id") REFERENCES "public"."chats"("chat_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."fulfillments"
    ADD CONSTRAINT "fulfillments_request_id_fkey" FOREIGN KEY ("request_id") REFERENCES "public"."requests"("request_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."fulfillments"
    ADD CONSTRAINT "fulfillments_responder_id_fkey" FOREIGN KEY ("responder_id") REFERENCES "auth"."users"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_chat_id_fkey" FOREIGN KEY ("chat_id") REFERENCES "public"."chats"("chat_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "auth"."users"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."requests"
    ADD CONSTRAINT "requests_chat_id_fkey" FOREIGN KEY ("chat_id") REFERENCES "public"."chats"("chat_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."requests"
    ADD CONSTRAINT "requests_requester_id_fkey" FOREIGN KEY ("requester_id") REFERENCES "auth"."users"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."token_balances"
    ADD CONSTRAINT "token_balances_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("account_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."token_transactions"
    ADD CONSTRAINT "token_transactions_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("account_id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."token_transactions"
    ADD CONSTRAINT "token_transactions_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."user_roles"
    ADD CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE "public"."accounts" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "accounts_select_owner" ON "public"."accounts" FOR SELECT TO "authenticated" USING ("public"."is_account_owner"("account_id"));



CREATE POLICY "accounts_write_developer" ON "public"."accounts" TO "authenticated" USING (("public"."has_role"('developer'::"public"."app_role") OR "public"."has_role"('admin'::"public"."app_role"))) WITH CHECK (("public"."has_role"('developer'::"public"."app_role") OR "public"."has_role"('admin'::"public"."app_role")));



ALTER TABLE "public"."chats" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "chats_claim_responder" ON "public"."chats" FOR UPDATE TO "authenticated" USING ((("responder_id" IS NULL) AND ("claim_state" = 'unclaimed'::"public"."claim_status") AND "public"."has_role"('responder'::"public"."app_role"))) WITH CHECK ((("responder_id" = "auth"."uid"()) AND ("claim_state" = 'claimed'::"public"."claim_status")));



CREATE POLICY "chats_insert_requester" ON "public"."chats" FOR INSERT TO "authenticated" WITH CHECK (("requester_id" = "auth"."uid"()));



CREATE POLICY "chats_select_participant" ON "public"."chats" FOR SELECT TO "authenticated" USING ((("requester_id" = "auth"."uid"()) OR ("responder_id" = "auth"."uid"())));



CREATE POLICY "chats_select_unclaimed_for_responder" ON "public"."chats" FOR SELECT TO "authenticated" USING (("public"."has_role"('responder'::"public"."app_role") AND ("responder_id" IS NULL) AND ("claim_state" = 'unclaimed'::"public"."claim_status") AND ("status" = 'open'::"public"."chat_status")));



CREATE POLICY "chats_update_requester" ON "public"."chats" FOR UPDATE TO "authenticated" USING (("requester_id" = "auth"."uid"())) WITH CHECK (("requester_id" = "auth"."uid"()));



ALTER TABLE "public"."fulfillments" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "fulfillments_insert_assigned_responder" ON "public"."fulfillments" FOR INSERT TO "authenticated" WITH CHECK ((("responder_id" = "auth"."uid"()) AND (EXISTS ( SELECT 1
   FROM "public"."chats" "c"
  WHERE (("c"."chat_id" = "fulfillments"."chat_id") AND ("c"."responder_id" = "auth"."uid"()))))));



CREATE POLICY "fulfillments_select_participant" ON "public"."fulfillments" FOR SELECT TO "authenticated" USING ("public"."is_chat_participant"("chat_id"));



ALTER TABLE "public"."messages" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "messages_insert_participant" ON "public"."messages" FOR INSERT TO "authenticated" WITH CHECK ((("sender_id" = "auth"."uid"()) AND "public"."is_chat_participant"("chat_id")));



CREATE POLICY "messages_select_participant" ON "public"."messages" FOR SELECT TO "authenticated" USING ("public"."is_chat_participant"("chat_id"));



ALTER TABLE "public"."profiles" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "profiles_insert_own" ON "public"."profiles" FOR INSERT TO "authenticated" WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "profiles_select_for_chat_peer" ON "public"."profiles" FOR SELECT TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."chats" "c"
  WHERE ((("c"."requester_id" = "profiles"."user_id") OR ("c"."responder_id" = "profiles"."user_id")) AND (("c"."requester_id" = "auth"."uid"()) OR ("c"."responder_id" = "auth"."uid"()))))));



CREATE POLICY "profiles_select_own" ON "public"."profiles" FOR SELECT TO "authenticated" USING (("user_id" = "auth"."uid"()));



CREATE POLICY "profiles_select_requester_when_unclaimed_pool" ON "public"."profiles" FOR SELECT TO "authenticated" USING (("public"."has_role"('responder'::"public"."app_role") AND (EXISTS ( SELECT 1
   FROM "public"."chats" "c"
  WHERE (("c"."requester_id" = "profiles"."user_id") AND ("c"."responder_id" IS NULL) AND ("c"."claim_state" = 'unclaimed'::"public"."claim_status") AND ("c"."status" = 'open'::"public"."chat_status"))))));



CREATE POLICY "profiles_update_own" ON "public"."profiles" FOR UPDATE TO "authenticated" USING (("user_id" = "auth"."uid"())) WITH CHECK (("user_id" = "auth"."uid"()));



ALTER TABLE "public"."requests" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "requests_insert_requester" ON "public"."requests" FOR INSERT TO "authenticated" WITH CHECK ((("requester_id" = "auth"."uid"()) AND (EXISTS ( SELECT 1
   FROM "public"."chats" "c"
  WHERE (("c"."chat_id" = "requests"."chat_id") AND ("c"."requester_id" = "auth"."uid"()) AND ("c"."status" = 'open'::"public"."chat_status"))))));



CREATE POLICY "requests_select_participant" ON "public"."requests" FOR SELECT TO "authenticated" USING ("public"."is_chat_participant"("chat_id"));



CREATE POLICY "requests_update_responder" ON "public"."requests" FOR UPDATE TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."chats" "c"
  WHERE (("c"."chat_id" = "requests"."chat_id") AND ("c"."responder_id" = "auth"."uid"()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."chats" "c"
  WHERE (("c"."chat_id" = "requests"."chat_id") AND ("c"."responder_id" = "auth"."uid"())))));



ALTER TABLE "public"."token_balances" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "token_balances_select_owner" ON "public"."token_balances" FOR SELECT TO "authenticated" USING ("public"."is_account_owner"("account_id"));



CREATE POLICY "token_balances_write_developer" ON "public"."token_balances" TO "authenticated" USING (("public"."has_role"('developer'::"public"."app_role") OR "public"."has_role"('admin'::"public"."app_role"))) WITH CHECK (("public"."has_role"('developer'::"public"."app_role") OR "public"."has_role"('admin'::"public"."app_role")));



ALTER TABLE "public"."token_transactions" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "token_txn_select_owner" ON "public"."token_transactions" FOR SELECT TO "authenticated" USING ("public"."is_account_owner"("account_id"));



CREATE POLICY "token_txn_write_developer" ON "public"."token_transactions" TO "authenticated" USING (("public"."has_role"('developer'::"public"."app_role") OR "public"."has_role"('admin'::"public"."app_role"))) WITH CHECK (("public"."has_role"('developer'::"public"."app_role") OR "public"."has_role"('admin'::"public"."app_role")));



ALTER TABLE "public"."user_roles" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "user_roles_select_own" ON "public"."user_roles" FOR SELECT TO "authenticated" USING (("user_id" = "auth"."uid"()));





ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."chats";



ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."fulfillments";



ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."messages";



ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."requests";



ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."token_balances";



REVOKE USAGE ON SCHEMA "public" FROM PUBLIC;

























































































































































GRANT ALL ON FUNCTION "public"."create_chat_with_initial_request"("p_title" "text", "p_category" "text", "p_request_text" "text", "p_tokens_to_spend" bigint) TO "authenticated";



GRANT ALL ON FUNCTION "public"."fulfill_chat_active_request"("p_chat_id" "text", "p_response_text" "text", "p_attachments" "jsonb") TO "authenticated";


















GRANT SELECT ON TABLE "public"."chats" TO "authenticated";



GRANT SELECT ON TABLE "public"."fulfillments" TO "authenticated";



GRANT SELECT ON TABLE "public"."messages" TO "authenticated";



GRANT SELECT ON TABLE "public"."requests" TO "authenticated";



GRANT SELECT ON TABLE "public"."token_balances" TO "authenticated";


































drop extension if exists "pg_net";

revoke delete on table "public"."accounts" from "anon";

revoke insert on table "public"."accounts" from "anon";

revoke references on table "public"."accounts" from "anon";

revoke select on table "public"."accounts" from "anon";

revoke trigger on table "public"."accounts" from "anon";

revoke truncate on table "public"."accounts" from "anon";

revoke update on table "public"."accounts" from "anon";

revoke delete on table "public"."accounts" from "authenticated";

revoke insert on table "public"."accounts" from "authenticated";

revoke references on table "public"."accounts" from "authenticated";

revoke select on table "public"."accounts" from "authenticated";

revoke trigger on table "public"."accounts" from "authenticated";

revoke truncate on table "public"."accounts" from "authenticated";

revoke update on table "public"."accounts" from "authenticated";

revoke delete on table "public"."accounts" from "service_role";

revoke insert on table "public"."accounts" from "service_role";

revoke references on table "public"."accounts" from "service_role";

revoke select on table "public"."accounts" from "service_role";

revoke trigger on table "public"."accounts" from "service_role";

revoke truncate on table "public"."accounts" from "service_role";

revoke update on table "public"."accounts" from "service_role";

revoke delete on table "public"."chats" from "anon";

revoke insert on table "public"."chats" from "anon";

revoke references on table "public"."chats" from "anon";

revoke select on table "public"."chats" from "anon";

revoke trigger on table "public"."chats" from "anon";

revoke truncate on table "public"."chats" from "anon";

revoke update on table "public"."chats" from "anon";

revoke delete on table "public"."chats" from "authenticated";

revoke insert on table "public"."chats" from "authenticated";

revoke references on table "public"."chats" from "authenticated";

revoke trigger on table "public"."chats" from "authenticated";

revoke truncate on table "public"."chats" from "authenticated";

revoke update on table "public"."chats" from "authenticated";

revoke delete on table "public"."chats" from "service_role";

revoke insert on table "public"."chats" from "service_role";

revoke references on table "public"."chats" from "service_role";

revoke select on table "public"."chats" from "service_role";

revoke trigger on table "public"."chats" from "service_role";

revoke truncate on table "public"."chats" from "service_role";

revoke update on table "public"."chats" from "service_role";

revoke delete on table "public"."fulfillments" from "anon";

revoke insert on table "public"."fulfillments" from "anon";

revoke references on table "public"."fulfillments" from "anon";

revoke select on table "public"."fulfillments" from "anon";

revoke trigger on table "public"."fulfillments" from "anon";

revoke truncate on table "public"."fulfillments" from "anon";

revoke update on table "public"."fulfillments" from "anon";

revoke delete on table "public"."fulfillments" from "authenticated";

revoke insert on table "public"."fulfillments" from "authenticated";

revoke references on table "public"."fulfillments" from "authenticated";

revoke trigger on table "public"."fulfillments" from "authenticated";

revoke truncate on table "public"."fulfillments" from "authenticated";

revoke update on table "public"."fulfillments" from "authenticated";

revoke delete on table "public"."fulfillments" from "service_role";

revoke insert on table "public"."fulfillments" from "service_role";

revoke references on table "public"."fulfillments" from "service_role";

revoke select on table "public"."fulfillments" from "service_role";

revoke trigger on table "public"."fulfillments" from "service_role";

revoke truncate on table "public"."fulfillments" from "service_role";

revoke update on table "public"."fulfillments" from "service_role";

revoke delete on table "public"."messages" from "anon";

revoke insert on table "public"."messages" from "anon";

revoke references on table "public"."messages" from "anon";

revoke select on table "public"."messages" from "anon";

revoke trigger on table "public"."messages" from "anon";

revoke truncate on table "public"."messages" from "anon";

revoke update on table "public"."messages" from "anon";

revoke delete on table "public"."messages" from "authenticated";

revoke insert on table "public"."messages" from "authenticated";

revoke references on table "public"."messages" from "authenticated";

revoke trigger on table "public"."messages" from "authenticated";

revoke truncate on table "public"."messages" from "authenticated";

revoke update on table "public"."messages" from "authenticated";

revoke delete on table "public"."messages" from "service_role";

revoke insert on table "public"."messages" from "service_role";

revoke references on table "public"."messages" from "service_role";

revoke select on table "public"."messages" from "service_role";

revoke trigger on table "public"."messages" from "service_role";

revoke truncate on table "public"."messages" from "service_role";

revoke update on table "public"."messages" from "service_role";

revoke delete on table "public"."profiles" from "anon";

revoke insert on table "public"."profiles" from "anon";

revoke references on table "public"."profiles" from "anon";

revoke select on table "public"."profiles" from "anon";

revoke trigger on table "public"."profiles" from "anon";

revoke truncate on table "public"."profiles" from "anon";

revoke update on table "public"."profiles" from "anon";

revoke delete on table "public"."profiles" from "authenticated";

revoke insert on table "public"."profiles" from "authenticated";

revoke references on table "public"."profiles" from "authenticated";

revoke select on table "public"."profiles" from "authenticated";

revoke trigger on table "public"."profiles" from "authenticated";

revoke truncate on table "public"."profiles" from "authenticated";

revoke update on table "public"."profiles" from "authenticated";

revoke delete on table "public"."profiles" from "service_role";

revoke insert on table "public"."profiles" from "service_role";

revoke references on table "public"."profiles" from "service_role";

revoke select on table "public"."profiles" from "service_role";

revoke trigger on table "public"."profiles" from "service_role";

revoke truncate on table "public"."profiles" from "service_role";

revoke update on table "public"."profiles" from "service_role";

revoke delete on table "public"."requests" from "anon";

revoke insert on table "public"."requests" from "anon";

revoke references on table "public"."requests" from "anon";

revoke select on table "public"."requests" from "anon";

revoke trigger on table "public"."requests" from "anon";

revoke truncate on table "public"."requests" from "anon";

revoke update on table "public"."requests" from "anon";

revoke delete on table "public"."requests" from "authenticated";

revoke insert on table "public"."requests" from "authenticated";

revoke references on table "public"."requests" from "authenticated";

revoke trigger on table "public"."requests" from "authenticated";

revoke truncate on table "public"."requests" from "authenticated";

revoke update on table "public"."requests" from "authenticated";

revoke delete on table "public"."requests" from "service_role";

revoke insert on table "public"."requests" from "service_role";

revoke references on table "public"."requests" from "service_role";

revoke select on table "public"."requests" from "service_role";

revoke trigger on table "public"."requests" from "service_role";

revoke truncate on table "public"."requests" from "service_role";

revoke update on table "public"."requests" from "service_role";

revoke delete on table "public"."token_balances" from "anon";

revoke insert on table "public"."token_balances" from "anon";

revoke references on table "public"."token_balances" from "anon";

revoke select on table "public"."token_balances" from "anon";

revoke trigger on table "public"."token_balances" from "anon";

revoke truncate on table "public"."token_balances" from "anon";

revoke update on table "public"."token_balances" from "anon";

revoke delete on table "public"."token_balances" from "authenticated";

revoke insert on table "public"."token_balances" from "authenticated";

revoke references on table "public"."token_balances" from "authenticated";

revoke trigger on table "public"."token_balances" from "authenticated";

revoke truncate on table "public"."token_balances" from "authenticated";

revoke update on table "public"."token_balances" from "authenticated";

revoke delete on table "public"."token_balances" from "service_role";

revoke insert on table "public"."token_balances" from "service_role";

revoke references on table "public"."token_balances" from "service_role";

revoke select on table "public"."token_balances" from "service_role";

revoke trigger on table "public"."token_balances" from "service_role";

revoke truncate on table "public"."token_balances" from "service_role";

revoke update on table "public"."token_balances" from "service_role";

revoke delete on table "public"."token_transactions" from "anon";

revoke insert on table "public"."token_transactions" from "anon";

revoke references on table "public"."token_transactions" from "anon";

revoke select on table "public"."token_transactions" from "anon";

revoke trigger on table "public"."token_transactions" from "anon";

revoke truncate on table "public"."token_transactions" from "anon";

revoke update on table "public"."token_transactions" from "anon";

revoke delete on table "public"."token_transactions" from "authenticated";

revoke insert on table "public"."token_transactions" from "authenticated";

revoke references on table "public"."token_transactions" from "authenticated";

revoke select on table "public"."token_transactions" from "authenticated";

revoke trigger on table "public"."token_transactions" from "authenticated";

revoke truncate on table "public"."token_transactions" from "authenticated";

revoke update on table "public"."token_transactions" from "authenticated";

revoke delete on table "public"."token_transactions" from "service_role";

revoke insert on table "public"."token_transactions" from "service_role";

revoke references on table "public"."token_transactions" from "service_role";

revoke select on table "public"."token_transactions" from "service_role";

revoke trigger on table "public"."token_transactions" from "service_role";

revoke truncate on table "public"."token_transactions" from "service_role";

revoke update on table "public"."token_transactions" from "service_role";

revoke delete on table "public"."user_roles" from "anon";

revoke insert on table "public"."user_roles" from "anon";

revoke references on table "public"."user_roles" from "anon";

revoke select on table "public"."user_roles" from "anon";

revoke trigger on table "public"."user_roles" from "anon";

revoke truncate on table "public"."user_roles" from "anon";

revoke update on table "public"."user_roles" from "anon";

revoke delete on table "public"."user_roles" from "authenticated";

revoke insert on table "public"."user_roles" from "authenticated";

revoke references on table "public"."user_roles" from "authenticated";

revoke select on table "public"."user_roles" from "authenticated";

revoke trigger on table "public"."user_roles" from "authenticated";

revoke truncate on table "public"."user_roles" from "authenticated";

revoke update on table "public"."user_roles" from "authenticated";

revoke delete on table "public"."user_roles" from "service_role";

revoke insert on table "public"."user_roles" from "service_role";

revoke references on table "public"."user_roles" from "service_role";

revoke select on table "public"."user_roles" from "service_role";

revoke trigger on table "public"."user_roles" from "service_role";

revoke truncate on table "public"."user_roles" from "service_role";

revoke update on table "public"."user_roles" from "service_role";

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();



-- 1. Add features to chats
ALTER TABLE public.chats 
  ADD COLUMN IF NOT EXISTS original_request text DEFAULT '',
  ADD COLUMN IF NOT EXISTS tokens_spent bigint DEFAULT 0,
  ADD COLUMN IF NOT EXISTS rating int,
  ADD COLUMN IF NOT EXISTS resolved boolean;

-- 2. Add tokens to messages
ALTER TABLE public.messages
  ADD COLUMN IF NOT EXISTS tokens bigint DEFAULT 0;

-- 3. Create or replace the chat creation function
DROP FUNCTION IF EXISTS public.create_chat_with_initial_request(text, text, text, bigint);
CREATE OR REPLACE FUNCTION public.create_chat_with_initial_request(p_category text, p_request_text text, p_tokens_to_spend bigint)
RETURNS jsonb
LANGUAGE plpgsql
SET search_path TO public
AS $$
declare
  v_chat_id text;
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

  insert into public.chats (requester_id, category, original_request, tokens_spent, status, claim_state, title)
  values (
    v_uid,
    coalesce(nullif(trim(p_category), ''), 'general'),
    trim(p_request_text),
    p_tokens_to_spend,
    'open',
    'unclaimed',
    null
  )
  returning chat_id into v_chat_id;

  return jsonb_build_object(
    'ok', true,
    'chat_id', v_chat_id
  );
end;
$$;

-- 4. Clean up old tables
ALTER TABLE IF EXISTS public.token_transactions DROP COLUMN IF EXISTS request_id CASCADE;
DROP TABLE IF EXISTS public.fulfillments CASCADE;
DROP TABLE IF EXISTS public.requests CASCADE;
DROP FUNCTION IF EXISTS public.fulfill_chat_active_request CASCADE;

-- 5. Fix permissions for accounts table
GRANT ALL ON TABLE "public"."accounts" TO "postgres";
GRANT ALL ON TABLE "public"."accounts" TO "anon";
GRANT ALL ON TABLE "public"."accounts" TO "authenticated";
GRANT ALL ON TABLE "public"."accounts" TO "service_role";

-- 6. Fix permissions for other dependent tables
GRANT ALL ON TABLE "public"."token_balances" TO "postgres";
GRANT ALL ON TABLE "public"."token_balances" TO "anon";
GRANT ALL ON TABLE "public"."token_balances" TO "authenticated";
GRANT ALL ON TABLE "public"."token_balances" TO "service_role";

GRANT ALL ON TABLE "public"."token_transactions" TO "postgres";
GRANT ALL ON TABLE "public"."token_transactions" TO "anon";
GRANT ALL ON TABLE "public"."token_transactions" TO "authenticated";
GRANT ALL ON TABLE "public"."token_transactions" TO "service_role";

GRANT ALL ON TABLE "public"."chats" TO "postgres";
GRANT ALL ON TABLE "public"."chats" TO "anon";
GRANT ALL ON TABLE "public"."chats" TO "authenticated";
GRANT ALL ON TABLE "public"."chats" TO "service_role";

GRANT ALL ON TABLE "public"."messages" TO "postgres";
GRANT ALL ON TABLE "public"."messages" TO "anon";
GRANT ALL ON TABLE "public"."messages" TO "authenticated";
GRANT ALL ON TABLE "public"."messages" TO "service_role";

GRANT ALL ON TABLE "public"."profiles" TO "postgres";
GRANT ALL ON TABLE "public"."profiles" TO "anon";
GRANT ALL ON TABLE "public"."profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."profiles" TO "service_role";


-- Grand select on user_roles so has_role() policy checks work for authenticated users
GRANT ALL ON TABLE public.user_roles TO anon, authenticated, service_role;
