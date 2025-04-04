/*
Defines the schema for the database. Execute this script to set up the database.
*/

/* Create the echo user */
CREATE
    USER echo WITH ENCRYPTED PASSWORD 'echo';

/* Create the echo database */
CREATE
    DATABASE echo WITH OWNER echo;

/* Connect to the echo database */
\c echo;

/* Enable UUID extension */
CREATE
    EXTENSION IF NOT EXISTS "uuid-ossp";

/* Create the schema, Note that public is automatically created */
CREATE SCHEMA secured;

CREATE TABLE public.users
(
    id          UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email       TEXT      NOT NULL UNIQUE,
    username    TEXT      NOT NULL,
    tag         INT       NOT NULL DEFAULT 0,
    icon        uuid,
    bio         TEXT,
    status      jsonb     NOT NULL DEFAULT '{
      "type": 0,
      "text": ""
    }', /* Json Object. See docs/database.md#status */
    last_online TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_online   BOOLEAN   NOT NULL DEFAULT FALSE,
    is_banned   BOOLEAN   NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN   NOT NULL DEFAULT FALSE
);

CREATE TABLE public.files
(
    id         UUID PRIMARY KEY   DEFAULT uuid_generate_v4(), /* Id is also the filename */
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID      NOT NULL
);

CREATE TABLE public.guilds
(
    id         UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner_id   UUID      NOT NULL,
    name       TEXT      NOT NULL,
    icon       UUID
);

CREATE TABLE public.channels
(
    id         UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    guild_id   UUID      NOT NULL,
    name       TEXT      NOT NULL,
    type       INT       NOT NULL,
    parent     UUID
);

CREATE TABLE public.messages
(
    id         UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id    UUID      NOT NULL,
    channel_id UUID      NOT NULL,
    body       TEXT      NOT NULL,
    embeds     jsonb     NOT NULL DEFAULT '{}' /* See https://www.postgresql.org/docs/current/datatype-json.html for justification for using jsonb instead of json */
);

CREATE TABLE public.message_attachments
(
    id         UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_id UUID      NOT NULL,
    file_id    UUID      NOT NULL
);

CREATE TABLE public.roles
(
    id               UUID PRIMARY KEY    DEFAULT uuid_generate_v4(),
    created_at       TIMESTAMP  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    guild_id         UUID       NOT NULL,
    name             TEXT       NOT NULL,
    colour           VARCHAR(6) NOT NULL DEFAULT '000000',
    separate_display BOOLEAN    NOT NULL DEFAULT FALSE,
    permissions      INT        NOT NULL DEFAULT 0
);

CREATE TABLE public.user_roles
(
    id         UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id    UUID      NOT NULL,
    role_id    UUID      NOT NULL
);

CREATE TABLE public.guild_members
(
    user_id         UUID      NOT NULL,
    guild_id        UUID      NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nickname        TEXT,
    profile_picture uuid,
    bio             TEXT
);

CREATE TABLE public.channel_members
(
    id          UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id     UUID      NOT NULL,
    channel_id  UUID      NOT NULL,
    permissions INT       NOT NULL DEFAULT 0
);

CREATE TABLE public.invites
(
    id          UUID PRIMARY KEY   DEFAULT uuid_generate_v4(),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    guild_id    UUID      NOT NULL,
    channel_id  UUID      NOT NULL,
    created_by  UUID      NOT NULL,
    uses        REAL      NOT NULL DEFAULT -1,
    expires_at  TIMESTAMP,
    target_user uuid,
    code        TEXT
);

CREATE TABLE public.config
(
    key  TEXT  NOT NULL,
    data JSONB NOT NULL DEFAULT '{}'
);

/* Secured Data */
CREATE TABLE secured.config
(
    id                UUID PRIMARY KEY   DEFAULT public.uuid_generate_v4(),
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id           UUID      NOT NULL,
    two_factor_method INT       NOT NULL DEFAULT 0 /* 0=email, 1=code-generator */
);

CREATE TABLE secured.tokens
(
    id         UUID PRIMARY KEY   DEFAULT public.uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id    UUID      NOT NULL,
    last_used  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type       INT       NOT NULL DEFAULT 0
);

CREATE TABLE secured.passwords
(
    id           UUID PRIMARY KEY      DEFAULT public.uuid_generate_v4(),
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id      UUID         NOT NULL UNIQUE,
    hash         VARCHAR(130) NOT NULL,
    last_updated TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE secured.two_factor
(
    id           UUID PRIMARY KEY       DEFAULT public.uuid_generate_v4(),
    created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id      UUID          NOT NULL UNIQUE,
    secret       TEXT          NOT NULL,
    backup_codes VARCHAR(8)[8] NOT NULL
);

CREATE TABLE secured.verification_codes
(
    id         UUID PRIMARY KEY   DEFAULT public.uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id    UUID      NOT NULL UNIQUE,
    code       TEXT      NOT NULL,
    expires    TIMESTAMP NOT NULL
);

/* Create checks */
ALTER TABLE public.channels
    ADD CONSTRAINT channel_type_check CHECK (type >= 0 AND type <= 2);

/* Create functions */
CREATE
    OR REPLACE FUNCTION set_default_profile_picture()
    RETURNS TRIGGER AS
$$
BEGIN
    new.profile_picture
        = (SELECT icon FROM public.users WHERE id = new.user_id);
    RETURN new;
END;
$$
    LANGUAGE plpgsql;

CREATE
    OR REPLACE FUNCTION hash_bigint(text) RETURNS bigint AS
$$
SELECT ('x' || SUBSTR(MD5($1), 1, 16)) ::BIT(64)::BIGINT;
$$
    LANGUAGE sql;


/* Create triggers */
CREATE TRIGGER set_default_profile_picture
    BEFORE INSERT
    ON public.guild_members
EXECUTE FUNCTION set_default_profile_picture();

/* Create Rules */
CREATE
    OR REPLACE RULE update_last_updated AS
    ON
        UPDATE TO secured.passwords
    DO INSTEAD
    UPDATE secured.passwords
    SET last_updated = CURRENT_TIMESTAMP
    WHERE user_id = new.user_id;

/* Create relations */
ALTER TABLE public.files
    ADD CONSTRAINT files_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users (id) ON DELETE CASCADE;

ALTER TABLE public.guilds
    ADD CONSTRAINT guilds_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users (id);
ALTER TABLE public.guilds
    ADD CONSTRAINT guilds_icon_fkey FOREIGN KEY (icon) REFERENCES public.files (id) ON DELETE SET NULL;

ALTER TABLE public.channels
    ADD CONSTRAINT channels_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES public.guilds (id) ON DELETE CASCADE;
ALTER TABLE public.channels
    ADD CONSTRAINT channels_parent_fkey FOREIGN KEY (parent) REFERENCES public.channels (id) ON DELETE CASCADE;

ALTER TABLE public.messages
    ADD CONSTRAINT messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;
ALTER TABLE public.messages
    ADD CONSTRAINT messages_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels (id) ON DELETE CASCADE;

ALTER TABLE public.message_attachments
    ADD CONSTRAINT message_attachments_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages (id) ON DELETE CASCADE;
ALTER TABLE public.message_attachments
    ADD CONSTRAINT message_attachments_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files (id) ON DELETE SET NULL;

ALTER TABLE public.roles
    ADD CONSTRAINT roles_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES public.guilds (id) ON DELETE CASCADE;

ALTER TABLE public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;
ALTER TABLE public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles (id) ON DELETE CASCADE;

ALTER TABLE public.guild_members
    ADD CONSTRAINT guild_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;
ALTER TABLE public.guild_members
    ADD CONSTRAINT guild_members_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES public.guilds (id) ON DELETE CASCADE;
ALTER TABLE public.guild_members
    ADD CONSTRAINT guild_members_profile_picture_fkey FOREIGN KEY (profile_picture) REFERENCES public.files (id) ON DELETE SET NULL;

ALTER TABLE public.channel_members
    ADD CONSTRAINT channel_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;
ALTER TABLE public.channel_members
    ADD CONSTRAINT channel_members_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels (id) ON DELETE CASCADE;

ALTER TABLE public.invites
    ADD CONSTRAINT invites_guild_id_fkey FOREIGN KEY (guild_id) REFERENCES public.guilds (id) ON DELETE CASCADE;
ALTER TABLE public.invites
    ADD CONSTRAINT invites_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.channels (id) ON DELETE CASCADE;
ALTER TABLE public.invites
    ADD CONSTRAINT invites_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users (id) ON DELETE CASCADE;
ALTER TABLE public.invites
    ADD CONSTRAINT invites_target_user_fkey FOREIGN KEY (target_user) REFERENCES public.users (id) ON DELETE CASCADE;

ALTER TABLE secured.config
    ADD CONSTRAINT config_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;

ALTER TABLE secured.tokens
    ADD CONSTRAINT tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;

ALTER TABLE secured.passwords
    ADD CONSTRAINT passwords_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;

ALTER TABLE secured.two_factor
    ADD CONSTRAINT two_factor_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;

ALTER TABLE secured.verification_codes
    ADD CONSTRAINT verification_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users (id) ON DELETE CASCADE;

/* Apply permissions */
REVOKE ALL ON ALL TABLES IN SCHEMA secured FROM PUBLIC;

GRANT
    SELECT,
    INSERT
    ,
    UPDATE,
    DELETE
    ON ALL TABLES IN SCHEMA secured TO echo;
GRANT
    USAGE
    ON
    SCHEMA
    secured TO echo;

GRANT
    SELECT,
    INSERT
    ,
    UPDATE,
    DELETE
    ON ALL TABLES IN SCHEMA public TO echo;
GRANT
    USAGE
    ON
    SCHEMA
    public TO echo;

GRANT
    SELECT,
    INSERT
    ,
    UPDATE,
    DELETE
    ON ALL TABLES IN SCHEMA public TO PUBLIC;
GRANT
    USAGE
    ON
    SCHEMA
    public TO PUBLIC;
