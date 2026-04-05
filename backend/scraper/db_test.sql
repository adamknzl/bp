-------------------------------------------------
-- ROLE
-------------------------------------------------
CREATE TABLE role (
    role_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(50) NOT NULL,
    description TEXT
);

-------------------------------------------------
-- SIZE CATEGORY
-------------------------------------------------
CREATE TABLE size_category (
    cat_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label       VARCHAR(50) NOT NULL,
    min_emp     INTEGER NOT NULL,
    max_emp     INTEGER
);

-------------------------------------------------
-- USER
-------------------------------------------------
CREATE TABLE "user" (
    user_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id       UUID REFERENCES role(role_id),
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP
);

-------------------------------------------------
-- DATA_SOURCE
-------------------------------------------------
CREATE TABLE data_source (
    source_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(100),
    url           TEXT,
    last_scraped  TIMESTAMP
);

-------------------------------------------------
-- ORGANIZATION
-------------------------------------------------
CREATE TABLE organization (
    organization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID REFERENCES data_source(source_id),

    name            VARCHAR(200) NOT NULL,
    ico             VARCHAR(20) NOT NULL UNIQUE,
    legal_form      VARCHAR(100),
    web_url         TEXT,
    created_at      TIMESTAMP,
    hq_address      TEXT,
    size_category   VARCHAR(50),
    hq_email        VARCHAR(120),
    hq_tel_number   VARCHAR(30),
    description      TEXT
);

-------------------------------------------------
-- BRANCH
-------------------------------------------------
CREATE TABLE branch (
    branch_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organization(organization_id),

    city           VARCHAR(100),
    street         VARCHAR(150),
    email          VARCHAR(120),
    tel_num        VARCHAR(30)
);

-------------------------------------------------
-- CATEGORY
-------------------------------------------------
CREATE TABLE category (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100)
);

-------------------------------------------------
-- ORGANIZATION_CATEGORY (M:N)
-------------------------------------------------
CREATE TABLE organization_category (
    organization_id UUID NOT NULL REFERENCES organization(organization_id) ON DELETE CASCADE,
    category_id     UUID NOT NULL REFERENCES category(category_id) ON DELETE CASCADE,
    PRIMARY KEY (organization_id, category_id)
);

-------------------------------------------------
-- NPO_MANAGER (User ↔ Organization M:N)
-------------------------------------------------
CREATE TABLE npo_manager (
    user_id         UUID NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organization(organization_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, organization_id)
);
