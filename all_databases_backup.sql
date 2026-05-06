--
-- PostgreSQL database cluster dump
--

\restrict 0RfSEExZxOYWhG94BgOJRstvoaXP1NtJ02xWLfxXZRYcTw06aRbAUMcAapVCePr

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE lms_user;
ALTER ROLE lms_user WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:V1oange3YIyqPs46SVUVYg==$wWsgqYOV8zltPCPiyoYTyC+eRLY3XjMZaKYJauXRgrw=:xG/Gp/4Tm+4YMqhCca97ujn8Q4limQ02sNjfdiL8oBo=';

--
-- User Configurations
--








\unrestrict 0RfSEExZxOYWhG94BgOJRstvoaXP1NtJ02xWLfxXZRYcTw06aRbAUMcAapVCePr

--
-- Databases
--

--
-- Database "template1" dump
--

\connect template1

--
-- PostgreSQL database dump
--

\restrict Im993w7qnhQBxcGSlmsjAkAdcShjg3ORwKrMsIElHBpe7j9ljDKscreiUzZqn4j

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

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

--
-- PostgreSQL database dump complete
--

\unrestrict Im993w7qnhQBxcGSlmsjAkAdcShjg3ORwKrMsIElHBpe7j9ljDKscreiUzZqn4j

--
-- Database "lms" dump
--

--
-- PostgreSQL database dump
--

\restrict 5r0Pekv2ZtxGE2ehfNq7VeqvHKlV7vU3CzYFtuinHdQvWBvtoAsorpChzqL3Fpf

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

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

--
-- Name: lms; Type: DATABASE; Schema: -; Owner: lms_user
--

CREATE DATABASE lms WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE lms OWNER TO lms_user;

\unrestrict 5r0Pekv2ZtxGE2ehfNq7VeqvHKlV7vU3CzYFtuinHdQvWBvtoAsorpChzqL3Fpf
\connect lms
\restrict 5r0Pekv2ZtxGE2ehfNq7VeqvHKlV7vU3CzYFtuinHdQvWBvtoAsorpChzqL3Fpf

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: academic_years; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.academic_years (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    is_active boolean NOT NULL,
    max_quarters integer NOT NULL
);


ALTER TABLE public.academic_years OWNER TO lms_user;

--
-- Name: assignment_files; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.assignment_files (
    id uuid NOT NULL,
    file_url character varying(1024) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_type character varying(100) NOT NULL,
    file_size integer NOT NULL,
    uploaded_at timestamp with time zone NOT NULL,
    assignment_id uuid NOT NULL,
    uploaded_by_id uuid NOT NULL
);


ALTER TABLE public.assignment_files OWNER TO lms_user;

--
-- Name: assignment_submissions; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.assignment_submissions (
    id uuid NOT NULL,
    file_url character varying(1024) NOT NULL,
    submitted_at timestamp with time zone NOT NULL,
    score double precision,
    feedback text NOT NULL,
    assignment_id uuid NOT NULL,
    graded_by_id uuid,
    student_module_id uuid NOT NULL
);


ALTER TABLE public.assignment_submissions OWNER TO lms_user;

--
-- Name: assignments; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.assignments (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    due_date timestamp with time zone NOT NULL,
    max_score integer NOT NULL,
    created_by_id uuid NOT NULL,
    module_id uuid NOT NULL,
    module_run_id uuid NOT NULL
);


ALTER TABLE public.assignments OWNER TO lms_user;

--
-- Name: attendance_records; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.attendance_records (
    id uuid NOT NULL,
    date date NOT NULL,
    status character varying(10) NOT NULL,
    module_session_id uuid NOT NULL,
    student_module_id uuid NOT NULL
);


ALTER TABLE public.attendance_records OWNER TO lms_user;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO lms_user;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO lms_user;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO lms_user;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: course_materials; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.course_materials (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    file_url character varying(1024) NOT NULL,
    material_type character varying(10) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    module_id uuid NOT NULL,
    uploaded_by_id uuid NOT NULL
);


ALTER TABLE public.course_materials OWNER TO lms_user;

--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id uuid NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO lms_user;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO lms_user;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO lms_user;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO lms_user;

--
-- Name: enrollments; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.enrollments (
    id uuid NOT NULL,
    track character varying(20) NOT NULL,
    start_date date NOT NULL,
    expected_completion_date date NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    student_id uuid NOT NULL,
    academic_year_id uuid
);


ALTER TABLE public.enrollments OWNER TO lms_user;

--
-- Name: module_runs; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.module_runs (
    id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    max_students integer NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    faculty_id uuid NOT NULL,
    module_id uuid NOT NULL,
    quarter_id uuid NOT NULL
);


ALTER TABLE public.module_runs OWNER TO lms_user;

--
-- Name: module_sessions; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.module_sessions (
    id uuid NOT NULL,
    session_number integer NOT NULL,
    session_date date NOT NULL,
    module_run_id uuid NOT NULL
);


ALTER TABLE public.module_sessions OWNER TO lms_user;

--
-- Name: modules; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.modules (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    order_number integer NOT NULL,
    session_count integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.modules OWNER TO lms_user;

--
-- Name: quarters; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.quarters (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    quarter_number integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    type character varying(10) NOT NULL,
    academic_year_id uuid
);


ALTER TABLE public.quarters OWNER TO lms_user;

--
-- Name: student_modules; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.student_modules (
    id uuid NOT NULL,
    status character varying(20) NOT NULL,
    attendance_percentage double precision,
    final_grade double precision,
    completed_at timestamp with time zone,
    enrollment_id uuid NOT NULL,
    module_run_id uuid NOT NULL
);


ALTER TABLE public.student_modules OWNER TO lms_user;

--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.user_profiles (
    id uuid NOT NULL,
    phone character varying(20) NOT NULL,
    address text NOT NULL,
    dob date,
    profile_image character varying(255) NOT NULL,
    user_id uuid NOT NULL
);


ALTER TABLE public.user_profiles OWNER TO lms_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.users (
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    id uuid NOT NULL,
    email character varying(254) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    role character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    is_staff boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.users OWNER TO lms_user;

--
-- Name: users_groups; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.users_groups (
    id bigint NOT NULL,
    user_id uuid NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.users_groups OWNER TO lms_user;

--
-- Name: users_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.users_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.users_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: users_user_permissions; Type: TABLE; Schema: public; Owner: lms_user
--

CREATE TABLE public.users_user_permissions (
    id bigint NOT NULL,
    user_id uuid NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.users_user_permissions OWNER TO lms_user;

--
-- Name: users_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: lms_user
--

ALTER TABLE public.users_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.users_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: academic_years; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.academic_years (id, name, start_date, end_date, is_active, max_quarters) FROM stdin;
d0b09682-e197-493b-b910-7fd0f6568a54	2026_Session	2026-06-01	2026-12-30	t	3
\.


--
-- Data for Name: assignment_files; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.assignment_files (id, file_url, file_name, file_type, file_size, uploaded_at, assignment_id, uploaded_by_id) FROM stdin;
0766019a-4c49-45be-bf43-37ccd3042851	/media/assignments/0b78d26b-d5a1-4c41-9996-55bf8b081865/33f0a699-8351-4fb8-bf62-aab011b15bc2/nexon-brochure.pdf	nexon-brochure.pdf	application/pdf	5480014	2026-05-06 15:47:06.510297+00	33f0a699-8351-4fb8-bf62-aab011b15bc2	dad18558-d1d4-4750-90a1-5c34f8a47676
\.


--
-- Data for Name: assignment_submissions; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.assignment_submissions (id, file_url, submitted_at, score, feedback, assignment_id, graded_by_id, student_module_id) FROM stdin;
167c62ac-b018-425d-9c48-c4636039632c	/media/assignment_submissions/33f0a699-8351-4fb8-bf62-aab011b15bc2/d316ebe8-c00c-44d8-a8ab-a6ff6c82760e/nexon-brochure.pdf	2026-05-06 16:03:50.837395+00	85		33f0a699-8351-4fb8-bf62-aab011b15bc2	20d1e8a5-cfe9-4ad4-aa80-cdd50408a0e6	d316ebe8-c00c-44d8-a8ab-a6ff6c82760e
\.


--
-- Data for Name: assignments; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.assignments (id, title, description, due_date, max_score, created_by_id, module_id, module_run_id) FROM stdin;
33f0a699-8351-4fb8-bf62-aab011b15bc2	Assignment 1	Assignment 1	2026-06-01 23:59:59+00	100	dad18558-d1d4-4750-90a1-5c34f8a47676	4e2203c2-2101-4bf1-b8ac-06c572b27857	0b78d26b-d5a1-4c41-9996-55bf8b081865
\.


--
-- Data for Name: attendance_records; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.attendance_records (id, date, status, module_session_id, student_module_id) FROM stdin;
777dc566-8e59-487b-af40-b1229cf2b8e7	2026-06-05	PRESENT	c9c50bbe-026c-4cd7-92f0-09995dbbe4cc	d316ebe8-c00c-44d8-a8ab-a6ff6c82760e
5ef5ff15-2e20-4740-a232-f7e792e322c9	2026-06-06	ABSENT	68c1daa8-5e38-4465-8c80-047dc610aaf0	d316ebe8-c00c-44d8-a8ab-a6ff6c82760e
46f35891-8713-46e3-bd2b-8ab53d71f9ae	2026-06-07	PRESENT	71a54e91-a359-4444-904c-a50908c3a16f	d316ebe8-c00c-44d8-a8ab-a6ff6c82760e
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add user	6	add_user
22	Can change user	6	change_user
23	Can delete user	6	delete_user
24	Can view user	6	view_user
25	Can add user profile	7	add_userprofile
26	Can change user profile	7	change_userprofile
27	Can delete user profile	7	delete_userprofile
28	Can view user profile	7	view_userprofile
29	Can add enrollment	8	add_enrollment
30	Can change enrollment	8	change_enrollment
31	Can delete enrollment	8	delete_enrollment
32	Can view enrollment	8	view_enrollment
33	Can add academic year	9	add_academicyear
34	Can change academic year	9	change_academicyear
35	Can delete academic year	9	delete_academicyear
36	Can view academic year	9	view_academicyear
37	Can add quarter	10	add_quarter
38	Can change quarter	10	change_quarter
39	Can delete quarter	10	delete_quarter
40	Can view quarter	10	view_quarter
41	Can add module	11	add_module
42	Can change module	11	change_module
43	Can delete module	11	delete_module
44	Can view module	11	view_module
45	Can add module run	12	add_modulerun
46	Can change module run	12	change_modulerun
47	Can delete module run	12	delete_modulerun
48	Can view module run	12	view_modulerun
49	Can add module session	13	add_modulesession
50	Can change module session	13	change_modulesession
51	Can delete module session	13	delete_modulesession
52	Can view module session	13	view_modulesession
53	Can add student module	14	add_studentmodule
54	Can change student module	14	change_studentmodule
55	Can delete student module	14	delete_studentmodule
56	Can view student module	14	view_studentmodule
57	Can add attendance record	15	add_attendancerecord
58	Can change attendance record	15	change_attendancerecord
59	Can delete attendance record	15	delete_attendancerecord
60	Can view attendance record	15	view_attendancerecord
61	Can add course material	16	add_coursematerial
62	Can change course material	16	change_coursematerial
63	Can delete course material	16	delete_coursematerial
64	Can view course material	16	view_coursematerial
65	Can add assignment	17	add_assignment
66	Can change assignment	17	change_assignment
67	Can delete assignment	17	delete_assignment
68	Can view assignment	17	view_assignment
69	Can add assignment file	18	add_assignmentfile
70	Can change assignment file	18	change_assignmentfile
71	Can delete assignment file	18	delete_assignmentfile
72	Can view assignment file	18	view_assignmentfile
73	Can add assignment submission	19	add_assignmentsubmission
74	Can change assignment submission	19	change_assignmentsubmission
75	Can delete assignment submission	19	delete_assignmentsubmission
76	Can view assignment submission	19	view_assignmentsubmission
\.


--
-- Data for Name: course_materials; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.course_materials (id, title, file_url, material_type, created_at, module_id, uploaded_by_id) FROM stdin;
a7506c5e-0bad-4834-a305-e8f40f10d2bf	Week 1 slide	/media/course_materials/4e2203c2-2101-4bf1-b8ac-06c572b27857/The-All-New-TATA-SIERRA-ESCAPE-MEDIOCRE_gewBElw.pdf	PDF	2026-05-02 16:17:24.812637+00	4e2203c2-2101-4bf1-b8ac-06c572b27857	dad18558-d1d4-4750-90a1-5c34f8a47676
02bd25f2-0ee7-447f-93d9-ad16c483e549	Awesome God song	https://www.youtube.com/watch?v=sT5whoRt4wA	LINK	2026-05-02 16:19:25.272778+00	0696b5cf-0f8d-44be-a469-1bf78c85fa2a	dad18558-d1d4-4750-90a1-5c34f8a47676
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	accounts	user
7	accounts	userprofile
8	academics	enrollment
9	academics	academicyear
10	academics	quarter
11	modules	module
12	modules	modulerun
13	modules	modulesession
14	modules	studentmodule
15	modules	attendancerecord
16	modules	coursematerial
17	modules	assignment
18	modules	assignmentfile
19	modules	assignmentsubmission
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2026-05-01 16:13:34.42863+00
2	contenttypes	0002_remove_content_type_name	2026-05-01 16:13:34.430238+00
3	auth	0001_initial	2026-05-01 16:13:34.444365+00
4	auth	0002_alter_permission_name_max_length	2026-05-01 16:13:34.445669+00
5	auth	0003_alter_user_email_max_length	2026-05-01 16:13:34.446938+00
6	auth	0004_alter_user_username_opts	2026-05-01 16:13:34.448805+00
7	auth	0005_alter_user_last_login_null	2026-05-01 16:13:34.450082+00
8	auth	0006_require_contenttypes_0002	2026-05-01 16:13:34.450499+00
9	auth	0007_alter_validators_add_error_messages	2026-05-01 16:13:34.451749+00
10	auth	0008_alter_user_username_max_length	2026-05-01 16:13:34.452975+00
11	auth	0009_alter_user_last_name_max_length	2026-05-01 16:13:34.454236+00
12	auth	0010_alter_group_name_max_length	2026-05-01 16:13:34.455675+00
13	auth	0011_update_proxy_permissions	2026-05-01 16:13:34.456875+00
14	auth	0012_alter_user_first_name_max_length	2026-05-01 16:13:34.458082+00
15	accounts	0001_initial	2026-05-01 16:13:34.477838+00
16	academics	0001_initial	2026-05-01 16:13:34.483605+00
17	academics	0002_academicyear_enrollment_academic_year_quarter	2026-05-01 16:13:34.499535+00
18	academics	0003_academicyear_max_quarters	2026-05-01 16:13:34.501056+00
19	admin	0001_initial	2026-05-01 16:13:34.525534+00
20	admin	0002_logentry_remove_auto_add	2026-05-01 16:13:34.52779+00
21	admin	0003_logentry_add_action_flag_choices	2026-05-01 16:13:34.529997+00
22	modules	0001_initial	2026-05-01 16:13:34.547448+00
23	modules	0002_studentmodule	2026-05-01 16:13:34.556659+00
24	sessions	0001_initial	2026-05-01 16:13:34.561383+00
25	modules	0003_attendancerecord	2026-05-02 13:12:37.256371+00
26	modules	0004_coursematerial	2026-05-02 16:09:20.597446+00
27	modules	0005_assignments	2026-05-06 15:27:24.572695+00
28	modules	0006_assignmentsubmission	2026-05-06 16:03:11.405831+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
dwrb2om833si18b6dyin20fk8276h6vz	.eJxVjrsOwjAMRf8lM4mSNLFTRna-oXLimvJQK_UxIf6dgDrAYl3J59j3qTra1qHbln7urqyOioldijFpdhx0wGh1a8npWJogiQICgjr8apnKvR-_7o3Gy2TKNK7zNZsPYvbtYs4T94_Tzv4dGGgZqo0efP3CwVGxjBEgA3tLQKnmILWXoASfS505M0rjWsviW4cCntXrDZJAQJM:1wJCub:Ff8D7gFm4A0vj0hFZpPecWI1_NIYHEW892bS5rjLS2s	2026-05-16 16:09:49.268103+00
258u6zntdi9syderbmt32wp5ir0f2v38	.eJxVjrsOwjAMRf8lM4mSNLFTRna-oXLimvJQK_UxIf6dgDrAYl3J59j3qTra1qHbln7urqyOioldijFpdhx0wGh1a8npWJogiQICgjr8apnKvR-_7o3Gy2TKNK7zNZsPYvbtYs4T94_Tzv4dGGgZqo0efP3CwVGxjBEgA3tLQKnmILWXoASfS505M0rjWsviW4cCntXrDZJAQJM:1wKf34:DAICJ8smTd_BlFR7tGI5z83pa1D7nVE-1v7Euezeq2I	2026-05-20 16:24:34.814291+00
\.


--
-- Data for Name: enrollments; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.enrollments (id, track, start_date, expected_completion_date, status, created_at, student_id, academic_year_id) FROM stdin;
d5039850-adf4-4a77-8f06-b24deadc878b	DIPLOMA	2026-06-01	2026-12-30	ACTIVE	2026-05-01 16:20:39.435848+00	be69581c-0a69-4d34-a7bf-d80de483d2aa	d0b09682-e197-493b-b910-7fd0f6568a54
bdd7732a-d655-4701-affb-ef3221f38294	DIPLOMA	2026-06-01	2026-12-30	ACTIVE	2026-05-01 16:21:24.552993+00	d0b1c754-de8c-497e-a55d-2afee2bf6d32	d0b09682-e197-493b-b910-7fd0f6568a54
\.


--
-- Data for Name: module_runs; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.module_runs (id, start_date, end_date, max_students, status, created_at, faculty_id, module_id, quarter_id) FROM stdin;
0b78d26b-d5a1-4c41-9996-55bf8b081865	2026-06-05	2026-06-07	10	SCHEDULED	2026-05-01 16:18:50.453563+00	20d1e8a5-cfe9-4ad4-aa80-cdd50408a0e6	4e2203c2-2101-4bf1-b8ac-06c572b27857	05319ce3-f1da-4623-a2be-23885395cbd6
79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9	2026-06-05	2026-06-08	10	SCHEDULED	2026-05-01 16:19:41.572104+00	ba30d303-51d8-46bb-9516-537c67eddc3e	0696b5cf-0f8d-44be-a469-1bf78c85fa2a	a78c7848-07cf-4448-b22f-9a3242561d64
\.


--
-- Data for Name: module_sessions; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.module_sessions (id, session_number, session_date, module_run_id) FROM stdin;
c9c50bbe-026c-4cd7-92f0-09995dbbe4cc	1	2026-06-05	0b78d26b-d5a1-4c41-9996-55bf8b081865
68c1daa8-5e38-4465-8c80-047dc610aaf0	2	2026-06-06	0b78d26b-d5a1-4c41-9996-55bf8b081865
71a54e91-a359-4444-904c-a50908c3a16f	3	2026-06-07	0b78d26b-d5a1-4c41-9996-55bf8b081865
2402f0db-61b6-4454-a230-d791dd607752	1	2026-06-05	79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9
4b12d2e2-013e-458b-9de0-101a36e39506	2	2026-06-06	79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9
1e0e0dc2-bef4-4514-a501-b1d95528c2b3	3	2026-06-07	79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9
f872fc23-756b-4a02-a77c-66ff1346a9f7	4	2026-06-08	79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9
\.


--
-- Data for Name: modules; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.modules (id, title, description, order_number, session_count, is_active, created_at) FROM stdin;
4e2203c2-2101-4bf1-b8ac-06c572b27857	Module 1	Module 1	1	3	t	2026-05-01 16:18:50.452478+00
0696b5cf-0f8d-44be-a469-1bf78c85fa2a	Module 2	Module 2	2	4	t	2026-05-01 16:19:41.571323+00
\.


--
-- Data for Name: quarters; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.quarters (id, name, quarter_number, start_date, end_date, type, academic_year_id) FROM stdin;
05319ce3-f1da-4623-a2be-23885395cbd6	Q1	1	2026-06-01	2026-06-30	MODULE	d0b09682-e197-493b-b910-7fd0f6568a54
a78c7848-07cf-4448-b22f-9a3242561d64	Q2	2	2026-07-01	2026-08-01	MODULE	d0b09682-e197-493b-b910-7fd0f6568a54
e61f80f0-da07-4862-b57f-4f8a36774027	Q3	3	2026-09-01	2026-12-30	QUIZ	d0b09682-e197-493b-b910-7fd0f6568a54
\.


--
-- Data for Name: student_modules; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.student_modules (id, status, attendance_percentage, final_grade, completed_at, enrollment_id, module_run_id) FROM stdin;
28fbc2a7-f828-4d40-a2dc-a44540f19afd	NOT_STARTED	0	\N	\N	bdd7732a-d655-4701-affb-ef3221f38294	79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9
52be1014-e51d-4850-b9b7-78d22431f322	NOT_STARTED	66.66666666666666	\N	\N	d5039850-adf4-4a77-8f06-b24deadc878b	79c0e8ee-44ce-4aac-86ca-6a5567ddbcd9
d316ebe8-c00c-44d8-a8ab-a6ff6c82760e	NOT_STARTED	66.66666666666666	\N	\N	d5039850-adf4-4a77-8f06-b24deadc878b	0b78d26b-d5a1-4c41-9996-55bf8b081865
\.


--
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.user_profiles (id, phone, address, dob, profile_image, user_id) FROM stdin;
7e71a193-1099-454a-aca9-2d56d2f16259	1234567890	Faculty 1 address	1988-10-01		20d1e8a5-cfe9-4ad4-aa80-cdd50408a0e6
cafecc8c-9854-4661-a272-986faa42bfe6	2345678901	Faculty 2 address	1982-08-05		ba30d303-51d8-46bb-9516-537c67eddc3e
1af3b7e6-6a23-4688-bc57-ec4b33aa531c	1234567890	Student1First Address	1992-06-01		be69581c-0a69-4d34-a7bf-d80de483d2aa
39517681-b323-4002-b3f2-4f06d4f0bdae	9876543210	Student2First Address	1996-08-01		d0b1c754-de8c-497e-a55d-2afee2bf6d32
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.users (password, last_login, is_superuser, id, email, first_name, last_name, role, is_active, is_staff, date_joined, created_at, updated_at) FROM stdin;
pbkdf2_sha256$720000$XKCnR062NgfZ25ij703qPy$cFwOCEwGrAyGEQ+bRS/LLsrEtMNdE52+n4Nrx3ZRHb8=	\N	f	20d1e8a5-cfe9-4ad4-aa80-cdd50408a0e6	Facultu1@faculty.com	Facultu1First	Facultu1Last	FACULTY	t	f	2026-05-01 16:17:21.303008+00	2026-05-01 16:17:21.404771+00	2026-05-01 16:17:21.404776+00
pbkdf2_sha256$720000$t7b358SCx4ErSnWYhLa1T5$MkdS2mnPwVtFruIqEwPRmdQgtii+xlJrYx7s78kxfgU=	\N	f	ba30d303-51d8-46bb-9516-537c67eddc3e	Facultu2@faculty.com	Faculty2First	Faculty2Last	FACULTY	t	f	2026-05-01 16:17:56.004422+00	2026-05-01 16:17:56.098373+00	2026-05-01 16:17:56.098376+00
pbkdf2_sha256$720000$zzGTXzBKKz79E92aQsydqW$scjf1gWp72mFGV6E77R9hWmUsMQmVhPiJQ9ojntWKOw=	\N	f	be69581c-0a69-4d34-a7bf-d80de483d2aa	Student1@student.com	Student1First	Student1Last	STUDENT	t	f	2026-05-01 16:20:39.338137+00	2026-05-01 16:20:39.432132+00	2026-05-01 16:20:39.432139+00
pbkdf2_sha256$720000$8ez9Gol1d4BnQ7v5j6fKwt$OqBaoAqOpPYsK3pJSX8snDv1W6cIC4Tk4SZKzz0nVdE=	\N	f	d0b1c754-de8c-497e-a55d-2afee2bf6d32	Student2@student.com	Student2First	Student2Last	STUDENT	t	f	2026-05-01 16:21:24.454186+00	2026-05-01 16:21:24.548659+00	2026-05-01 16:21:24.548661+00
pbkdf2_sha256$720000$bXBzq235ouVNEh2ZUtFFKz$brakVSMRXfN7GvS/lGSIkzFIII3rhwemrajUpR6aP4s=	2026-05-06 16:24:34.813442+00	t	dad18558-d1d4-4750-90a1-5c34f8a47676	admin@admin.com	admin	admin	ADMIN	t	t	2026-05-01 16:13:48.868626+00	2026-05-01 16:13:48.971228+00	2026-05-01 16:13:48.971233+00
\.


--
-- Data for Name: users_groups; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.users_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: users_user_permissions; Type: TABLE DATA; Schema: public; Owner: lms_user
--

COPY public.users_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 76, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 19, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 28, true);


--
-- Name: users_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.users_groups_id_seq', 1, false);


--
-- Name: users_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lms_user
--

SELECT pg_catalog.setval('public.users_user_permissions_id_seq', 1, false);


--
-- Name: academic_years academic_years_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.academic_years
    ADD CONSTRAINT academic_years_pkey PRIMARY KEY (id);


--
-- Name: assignment_files assignment_files_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_files
    ADD CONSTRAINT assignment_files_pkey PRIMARY KEY (id);


--
-- Name: assignment_submissions assignment_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissions_pkey PRIMARY KEY (id);


--
-- Name: assignments assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_pkey PRIMARY KEY (id);


--
-- Name: attendance_records attendance_records_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.attendance_records
    ADD CONSTRAINT attendance_records_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: course_materials course_materials_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.course_materials
    ADD CONSTRAINT course_materials_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: enrollments enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_pkey PRIMARY KEY (id);


--
-- Name: module_runs module_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.module_runs
    ADD CONSTRAINT module_runs_pkey PRIMARY KEY (id);


--
-- Name: module_sessions module_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.module_sessions
    ADD CONSTRAINT module_sessions_pkey PRIMARY KEY (id);


--
-- Name: modules modules_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.modules
    ADD CONSTRAINT modules_pkey PRIMARY KEY (id);


--
-- Name: quarters quarters_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.quarters
    ADD CONSTRAINT quarters_pkey PRIMARY KEY (id);


--
-- Name: student_modules student_modules_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.student_modules
    ADD CONSTRAINT student_modules_pkey PRIMARY KEY (id);


--
-- Name: assignment_submissions uniq_assignment_submission; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT uniq_assignment_submission UNIQUE (assignment_id, student_module_id);


--
-- Name: attendance_records uniq_attendance_session_student; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.attendance_records
    ADD CONSTRAINT uniq_attendance_session_student UNIQUE (module_session_id, student_module_id);


--
-- Name: student_modules uniq_student_module_enrollment_run; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.student_modules
    ADD CONSTRAINT uniq_student_module_enrollment_run UNIQUE (enrollment_id, module_run_id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users_groups users_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_groups
    ADD CONSTRAINT users_groups_pkey PRIMARY KEY (id);


--
-- Name: users_groups users_groups_user_id_group_id_fc7788e8_uniq; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_groups
    ADD CONSTRAINT users_groups_user_id_group_id_fc7788e8_uniq UNIQUE (user_id, group_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users_user_permissions users_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_user_permissions
    ADD CONSTRAINT users_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: users_user_permissions users_user_permissions_user_id_permission_id_3b86cbdf_uniq; Type: CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_user_permissions
    ADD CONSTRAINT users_user_permissions_user_id_permission_id_3b86cbdf_uniq UNIQUE (user_id, permission_id);


--
-- Name: assignment_files_assignment_id_97e01b1b; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignment_files_assignment_id_97e01b1b ON public.assignment_files USING btree (assignment_id);


--
-- Name: assignment_files_uploaded_by_id_dd59031d; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignment_files_uploaded_by_id_dd59031d ON public.assignment_files USING btree (uploaded_by_id);


--
-- Name: assignment_submissions_assignment_id_e9e4e86b; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignment_submissions_assignment_id_e9e4e86b ON public.assignment_submissions USING btree (assignment_id);


--
-- Name: assignment_submissions_graded_by_id_a935a876; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignment_submissions_graded_by_id_a935a876 ON public.assignment_submissions USING btree (graded_by_id);


--
-- Name: assignment_submissions_student_module_id_f210b7c4; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignment_submissions_student_module_id_f210b7c4 ON public.assignment_submissions USING btree (student_module_id);


--
-- Name: assignments_created_by_id_5d73a061; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignments_created_by_id_5d73a061 ON public.assignments USING btree (created_by_id);


--
-- Name: assignments_module_id_d063c9c7; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignments_module_id_d063c9c7 ON public.assignments USING btree (module_id);


--
-- Name: assignments_module_run_id_5b0dfb0f; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX assignments_module_run_id_5b0dfb0f ON public.assignments USING btree (module_run_id);


--
-- Name: attendance_records_module_session_id_46a8bdc2; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX attendance_records_module_session_id_46a8bdc2 ON public.attendance_records USING btree (module_session_id);


--
-- Name: attendance_records_student_module_id_df51f53d; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX attendance_records_student_module_id_df51f53d ON public.attendance_records USING btree (student_module_id);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: course_materials_module_id_2719679a; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX course_materials_module_id_2719679a ON public.course_materials USING btree (module_id);


--
-- Name: course_materials_uploaded_by_id_a8d85bb7; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX course_materials_uploaded_by_id_a8d85bb7 ON public.course_materials USING btree (uploaded_by_id);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: enrollments_academic_year_id_624e604e; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX enrollments_academic_year_id_624e604e ON public.enrollments USING btree (academic_year_id);


--
-- Name: enrollments_student_id_19c0bed4; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX enrollments_student_id_19c0bed4 ON public.enrollments USING btree (student_id);


--
-- Name: module_runs_faculty_id_7d4b13a8; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX module_runs_faculty_id_7d4b13a8 ON public.module_runs USING btree (faculty_id);


--
-- Name: module_runs_module_id_52355b08; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX module_runs_module_id_52355b08 ON public.module_runs USING btree (module_id);


--
-- Name: module_runs_quarter_id_e23beb1f; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX module_runs_quarter_id_e23beb1f ON public.module_runs USING btree (quarter_id);


--
-- Name: module_sessions_module_run_id_aafb8dcc; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX module_sessions_module_run_id_aafb8dcc ON public.module_sessions USING btree (module_run_id);


--
-- Name: quarters_academic_year_id_048c525d; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX quarters_academic_year_id_048c525d ON public.quarters USING btree (academic_year_id);


--
-- Name: student_modules_enrollment_id_df41e6b0; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX student_modules_enrollment_id_df41e6b0 ON public.student_modules USING btree (enrollment_id);


--
-- Name: student_modules_module_run_id_76a1a8f2; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX student_modules_module_run_id_76a1a8f2 ON public.student_modules USING btree (module_run_id);


--
-- Name: users_email_0ea73cca_like; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX users_email_0ea73cca_like ON public.users USING btree (email varchar_pattern_ops);


--
-- Name: users_groups_group_id_2f3517aa; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX users_groups_group_id_2f3517aa ON public.users_groups USING btree (group_id);


--
-- Name: users_groups_user_id_f500bee5; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX users_groups_user_id_f500bee5 ON public.users_groups USING btree (user_id);


--
-- Name: users_user_permissions_permission_id_6d08dcd2; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX users_user_permissions_permission_id_6d08dcd2 ON public.users_user_permissions USING btree (permission_id);


--
-- Name: users_user_permissions_user_id_92473840; Type: INDEX; Schema: public; Owner: lms_user
--

CREATE INDEX users_user_permissions_user_id_92473840 ON public.users_user_permissions USING btree (user_id);


--
-- Name: assignment_files assignment_files_assignment_id_97e01b1b_fk_assignments_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_files
    ADD CONSTRAINT assignment_files_assignment_id_97e01b1b_fk_assignments_id FOREIGN KEY (assignment_id) REFERENCES public.assignments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignment_files assignment_files_uploaded_by_id_dd59031d_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_files
    ADD CONSTRAINT assignment_files_uploaded_by_id_dd59031d_fk_users_id FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignment_submissions assignment_submissio_student_module_id_f210b7c4_fk_student_m; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissio_student_module_id_f210b7c4_fk_student_m FOREIGN KEY (student_module_id) REFERENCES public.student_modules(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignment_submissions assignment_submissions_assignment_id_e9e4e86b_fk_assignments_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissions_assignment_id_e9e4e86b_fk_assignments_id FOREIGN KEY (assignment_id) REFERENCES public.assignments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignment_submissions assignment_submissions_graded_by_id_a935a876_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignment_submissions
    ADD CONSTRAINT assignment_submissions_graded_by_id_a935a876_fk_users_id FOREIGN KEY (graded_by_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignments assignments_created_by_id_5d73a061_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_created_by_id_5d73a061_fk_users_id FOREIGN KEY (created_by_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignments assignments_module_id_d063c9c7_fk_modules_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_module_id_d063c9c7_fk_modules_id FOREIGN KEY (module_id) REFERENCES public.modules(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: assignments assignments_module_run_id_5b0dfb0f_fk_module_runs_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_module_run_id_5b0dfb0f_fk_module_runs_id FOREIGN KEY (module_run_id) REFERENCES public.module_runs(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: attendance_records attendance_records_module_session_id_46a8bdc2_fk_module_se; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.attendance_records
    ADD CONSTRAINT attendance_records_module_session_id_46a8bdc2_fk_module_se FOREIGN KEY (module_session_id) REFERENCES public.module_sessions(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: attendance_records attendance_records_student_module_id_df51f53d_fk_student_m; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.attendance_records
    ADD CONSTRAINT attendance_records_student_module_id_df51f53d_fk_student_m FOREIGN KEY (student_module_id) REFERENCES public.student_modules(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: course_materials course_materials_module_id_2719679a_fk_modules_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.course_materials
    ADD CONSTRAINT course_materials_module_id_2719679a_fk_modules_id FOREIGN KEY (module_id) REFERENCES public.modules(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: course_materials course_materials_uploaded_by_id_a8d85bb7_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.course_materials
    ADD CONSTRAINT course_materials_uploaded_by_id_a8d85bb7_fk_users_id FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: enrollments enrollments_academic_year_id_624e604e_fk_academic_years_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_academic_year_id_624e604e_fk_academic_years_id FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: enrollments enrollments_student_id_19c0bed4_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.enrollments
    ADD CONSTRAINT enrollments_student_id_19c0bed4_fk_users_id FOREIGN KEY (student_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: module_runs module_runs_faculty_id_7d4b13a8_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.module_runs
    ADD CONSTRAINT module_runs_faculty_id_7d4b13a8_fk_users_id FOREIGN KEY (faculty_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: module_runs module_runs_module_id_52355b08_fk_modules_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.module_runs
    ADD CONSTRAINT module_runs_module_id_52355b08_fk_modules_id FOREIGN KEY (module_id) REFERENCES public.modules(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: module_runs module_runs_quarter_id_e23beb1f_fk_quarters_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.module_runs
    ADD CONSTRAINT module_runs_quarter_id_e23beb1f_fk_quarters_id FOREIGN KEY (quarter_id) REFERENCES public.quarters(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: module_sessions module_sessions_module_run_id_aafb8dcc_fk_module_runs_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.module_sessions
    ADD CONSTRAINT module_sessions_module_run_id_aafb8dcc_fk_module_runs_id FOREIGN KEY (module_run_id) REFERENCES public.module_runs(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: quarters quarters_academic_year_id_048c525d_fk_academic_years_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.quarters
    ADD CONSTRAINT quarters_academic_year_id_048c525d_fk_academic_years_id FOREIGN KEY (academic_year_id) REFERENCES public.academic_years(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: student_modules student_modules_enrollment_id_df41e6b0_fk_enrollments_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.student_modules
    ADD CONSTRAINT student_modules_enrollment_id_df41e6b0_fk_enrollments_id FOREIGN KEY (enrollment_id) REFERENCES public.enrollments(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: student_modules student_modules_module_run_id_76a1a8f2_fk_module_runs_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.student_modules
    ADD CONSTRAINT student_modules_module_run_id_76a1a8f2_fk_module_runs_id FOREIGN KEY (module_run_id) REFERENCES public.module_runs(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_profiles user_profiles_user_id_8c5ab5fe_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_8c5ab5fe_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: users_groups users_groups_group_id_2f3517aa_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_groups
    ADD CONSTRAINT users_groups_group_id_2f3517aa_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: users_groups users_groups_user_id_f500bee5_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_groups
    ADD CONSTRAINT users_groups_user_id_f500bee5_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: users_user_permissions users_user_permissio_permission_id_6d08dcd2_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_user_permissions
    ADD CONSTRAINT users_user_permissio_permission_id_6d08dcd2_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: users_user_permissions users_user_permissions_user_id_92473840_fk_users_id; Type: FK CONSTRAINT; Schema: public; Owner: lms_user
--

ALTER TABLE ONLY public.users_user_permissions
    ADD CONSTRAINT users_user_permissions_user_id_92473840_fk_users_id FOREIGN KEY (user_id) REFERENCES public.users(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

\unrestrict 5r0Pekv2ZtxGE2ehfNq7VeqvHKlV7vU3CzYFtuinHdQvWBvtoAsorpChzqL3Fpf

--
-- Database "postgres" dump
--

\connect postgres

--
-- PostgreSQL database dump
--

\restrict dwaO56tQxrcgJYoMhkw7fOGCQSVukLSfbfowNmWbYcVgdqg93OSvbkLFWu6dXHc

-- Dumped from database version 15.17 (Debian 15.17-1.pgdg13+1)
-- Dumped by pg_dump version 15.17 (Debian 15.17-1.pgdg13+1)

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

--
-- PostgreSQL database dump complete
--

\unrestrict dwaO56tQxrcgJYoMhkw7fOGCQSVukLSfbfowNmWbYcVgdqg93OSvbkLFWu6dXHc

--
-- PostgreSQL database cluster dump complete
--

