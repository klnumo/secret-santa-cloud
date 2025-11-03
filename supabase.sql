-- Включить UUID
create extension if not exists "uuid-ossp";

-- Таблицы
create table groups (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  creator_id uuid not null,
  created_at timestamp default now()
);

create table participants (
  id uuid primary key default uuid_generate_v4(),
  group_id uuid references groups(id) on delete cascade,
  name text not null,
  email text,
  target_id uuid,
  created_at timestamp default now()
);

-- RLS
alter table groups enable row level security;
alter table participants enable row level security;

create policy "owner_groups" on groups
  for all using (auth.uid() = creator_id) with check (auth.uid() = creator_id);

create policy "view_own_group" on participants
  for select using (
    exists (select 1 from groups g where g.id = group_id and g.creator_id = auth.uid())
  );

create policy "insert_participant" on participants
  for insert with check (
    exists (select 1 from groups g where g.id = group_id and g.creator_id = auth.uid())
  );