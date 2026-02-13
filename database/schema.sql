-- ============================================================================
-- FOAM Grant Alignment Engine - PostgreSQL Schema
-- Production-Quality Database Design for Grant Management System
-- ============================================================================
-- Purpose: Comprehensive schema for managing grant requirements, boilerplate
-- content, RFP parsing, requirement mapping, and grant plan generation
-- Created: 2024
-- ============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Text similarity search for content matching

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

-- RFP document status tracking
CREATE TYPE rfp_status AS ENUM ('uploaded', 'parsing', 'parsed', 'analyzed', 'archived');

-- Grant plan lifecycle status
CREATE TYPE grant_plan_status AS ENUM ('draft', 'review', 'approved', 'submitted', 'archived');

-- Alignment confidence levels
CREATE TYPE alignment_score AS ENUM ('strong', 'partial', 'weak', 'none');

-- Risk assessment levels
CREATE TYPE risk_level AS ENUM ('green', 'yellow', 'red');

-- User roles with granular permissions
CREATE TYPE user_role AS ENUM (
  'grant_writer',
  'executive_director',
  'program_director',
  'compliance_officer',
  'admin'
);

-- Tag categorization types
CREATE TYPE tag_type AS ENUM (
  'program',
  'funding_type',
  'evidence_type',
  'priority_area',
  'compliance_area',
  'outcome_area'
);

-- Compliance status tracking
CREATE TYPE compliance_status AS ENUM (
  'not_addressed',
  'partial',
  'complete',
  'exceeds_requirements'
);

-- ============================================================================
-- 1. BOILERPLATE_CATEGORIES
-- ============================================================================
-- Organizational structure for grouping reusable content sections
-- Higher-level categorization for content management and discovery

CREATE TABLE boilerplate_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category_name VARCHAR(255) NOT NULL UNIQUE,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_sort_order CHECK (sort_order >= 0)
);

CREATE INDEX idx_boilerplate_categories_active ON boilerplate_categories(is_active);
CREATE INDEX idx_boilerplate_categories_sort ON boilerplate_categories(sort_order);

-- ============================================================================
-- 2. BOILERPLATE_SECTIONS
-- ============================================================================
-- Core content repository for reusable grant language and organizational information
-- Each row represents a self-contained, reusable section of grant narrative
-- Purpose: Enable rapid grant assembly while maintaining quality and consistency

CREATE TABLE boilerplate_sections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category_id UUID NOT NULL REFERENCES boilerplate_categories(id) ON DELETE CASCADE,
  section_title VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  word_count INTEGER GENERATED ALWAYS AS (
    array_length(string_to_array(trim(content), ' '), 1)
  ) STORED,
  current_version INTEGER NOT NULL DEFAULT 1,

  -- Contextual metadata for intelligent matching and filtering
  tags TEXT[] DEFAULT '{}',  -- GIN indexed array of tags
  evidence_type VARCHAR(100),  -- 'Evidence-Based', 'Promising Practice', 'Research-Informed'
  program_area VARCHAR(255),  -- Specific program area this section addresses
  compliance_relevance VARCHAR(100),  -- e.g., 'Evaluation', 'Outcomes', 'Staffing'
  minimum_word_count INTEGER,  -- Guidance for minimum inclusion
  maximum_word_count INTEGER,  -- Guidance for maximum inclusion

  -- Audit and lifecycle management
  is_active BOOLEAN NOT NULL DEFAULT true,
  requires_customization BOOLEAN NOT NULL DEFAULT false,
  customization_guidance TEXT,  -- Instructions for adapting this section

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,

  CONSTRAINT valid_word_count_logic CHECK (
    (minimum_word_count IS NULL AND maximum_word_count IS NULL) OR
    (minimum_word_count IS NOT NULL AND maximum_word_count IS NOT NULL AND minimum_word_count <= maximum_word_count)
  )
);

-- Performance indexes for rapid content discovery
CREATE INDEX idx_boilerplate_sections_category ON boilerplate_sections(category_id);
CREATE INDEX idx_boilerplate_sections_active ON boilerplate_sections(is_active);
CREATE INDEX idx_boilerplate_sections_program ON boilerplate_sections(program_area);
CREATE INDEX idx_boilerplate_sections_evidence ON boilerplate_sections(evidence_type);
CREATE INDEX idx_boilerplate_sections_compliance ON boilerplate_sections(compliance_relevance);
CREATE INDEX idx_boilerplate_sections_tags_gin ON boilerplate_sections USING GIN(tags);
-- Full-text search optimization for content similarity matching
CREATE INDEX idx_boilerplate_sections_content_trgm ON boilerplate_sections USING GIN(content gin_trgm_ops);
CREATE INDEX idx_boilerplate_sections_title_trgm ON boilerplate_sections USING GIN(section_title gin_trgm_ops);
CREATE INDEX idx_boilerplate_sections_created ON boilerplate_sections(created_at DESC);

-- ============================================================================
-- 3. USERS
-- ============================================================================
-- User management for multi-user collaborative grant development

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  role user_role NOT NULL,

  -- Audit fields
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_email CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- ============================================================================
-- 4. BOILERPLATE_VERSIONS
-- ============================================================================
-- Complete version history for all boilerplate section changes
-- Enables rollback, audit trail, and collaborative content development

CREATE TABLE boilerplate_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  section_id UUID NOT NULL REFERENCES boilerplate_sections(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  content TEXT NOT NULL,
  word_count INTEGER GENERATED ALWAYS AS (
    array_length(string_to_array(trim(content), ' '), 1)
  ) STORED,

  -- Change tracking
  changed_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  change_notes TEXT,
  is_current BOOLEAN NOT NULL DEFAULT false,

  CONSTRAINT unique_version_per_section UNIQUE(section_id, version_number),
  CONSTRAINT valid_version_number CHECK (version_number > 0)
);

CREATE INDEX idx_boilerplate_versions_section ON boilerplate_versions(section_id);
CREATE INDEX idx_boilerplate_versions_current ON boilerplate_versions(section_id, is_current);
CREATE INDEX idx_boilerplate_versions_changed ON boilerplate_versions(changed_at DESC);

-- ============================================================================
-- 5. TAGS
-- ============================================================================
-- Flexible tagging system for content organization and filtering

CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL UNIQUE,
  tag_type tag_type NOT NULL,
  description TEXT,

  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_tag_name CHECK (length(trim(name)) > 0)
);

CREATE INDEX idx_tags_type ON tags(tag_type);
CREATE INDEX idx_tags_active ON tags(is_active);

-- ============================================================================
-- 6. BOILERPLATE_SECTION_TAGS (Junction Table)
-- ============================================================================
-- Many-to-many relationship between sections and tags

CREATE TABLE boilerplate_section_tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  section_id UUID NOT NULL REFERENCES boilerplate_sections(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT unique_section_tag UNIQUE(section_id, tag_id)
);

CREATE INDEX idx_boilerplate_section_tags_section ON boilerplate_section_tags(section_id);
CREATE INDEX idx_boilerplate_section_tags_tag ON boilerplate_section_tags(tag_id);

-- ============================================================================
-- 7. RFPS (Request For Proposals)
-- ============================================================================
-- Repository for uploaded RFP documents and parsed funding opportunities

CREATE TABLE rfps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Basic information
  title VARCHAR(500) NOT NULL,
  funder_name VARCHAR(500) NOT NULL,
  rfp_url VARCHAR(2000),

  -- Funding details
  funding_amount DECIMAL(15, 2),
  funding_type VARCHAR(100),  -- 'Federal', 'State', 'Foundation', 'Corporate', 'Municipal'
  eligibility_notes TEXT,

  -- File information
  file_path VARCHAR(2000),
  file_type VARCHAR(50),  -- 'pdf', 'docx', 'txt', etc.
  file_size_bytes INTEGER,
  upload_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Processing status and timeline
  status rfp_status NOT NULL DEFAULT 'uploaded',
  deadline DATE,
  parsing_started_at TIMESTAMP WITH TIME ZONE,
  parsed_at TIMESTAMP WITH TIME ZONE,
  raw_text TEXT,  -- Full extracted text from RFP document

  -- Content summary
  brief_description TEXT,
  key_objectives TEXT,
  target_population VARCHAR(500),
  geographic_scope VARCHAR(500),
  priority_areas TEXT[],

  -- Audit fields
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_funding_amount CHECK (funding_amount IS NULL OR funding_amount > 0),
  CONSTRAINT valid_file_size CHECK (file_size_bytes IS NULL OR file_size_bytes > 0)
);

CREATE INDEX idx_rfps_funder ON rfps(funder_name);
CREATE INDEX idx_rfps_status ON rfps(status);
CREATE INDEX idx_rfps_deadline ON rfps(deadline);
CREATE INDEX idx_rfps_created ON rfps(created_at DESC);
CREATE INDEX idx_rfps_funding_type ON rfps(funding_type);
CREATE INDEX idx_rfps_priority_areas ON rfps USING GIN(priority_areas);

-- ============================================================================
-- 8. RFP_REQUIREMENTS
-- ============================================================================
-- Parsed individual requirements extracted from each RFP document
-- Enables granular requirement tracking and section-by-section alignment

CREATE TABLE rfp_requirements (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rfp_id UUID NOT NULL REFERENCES rfps(id) ON DELETE CASCADE,

  -- Requirement content and structure
  section_name VARCHAR(500) NOT NULL,
  section_number VARCHAR(50),  -- e.g., '2.1.3' for hierarchical organization
  description TEXT NOT NULL,
  requirement_type VARCHAR(100),  -- e.g., 'Narrative', 'Attachment', 'Budget', 'Evaluation'

  -- Specifications and constraints
  word_limit INTEGER,
  minimum_word_count INTEGER,
  character_limit INTEGER,
  page_limit INTEGER,

  -- Scoring and priority
  scoring_weight DECIMAL(5, 2),  -- 0-100 point scale contribution
  is_mandatory BOOLEAN NOT NULL DEFAULT true,

  -- Formatting and content guidance
  formatting_notes TEXT,
  example_content TEXT,
  success_criteria TEXT,

  -- Compliance tracking
  required_attachments TEXT[],
  compliance_keywords TEXT[],  -- Words/phrases that must appear
  eligibility_flag BOOLEAN NOT NULL DEFAULT false,  -- Must-have requirement

  -- Organization
  section_order INTEGER NOT NULL,
  parent_section_id UUID REFERENCES rfp_requirements(id) ON DELETE CASCADE,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_word_limit CHECK (word_limit IS NULL OR word_limit > 0),
  CONSTRAINT valid_scoring CHECK (scoring_weight IS NULL OR (scoring_weight >= 0 AND scoring_weight <= 100))
);

CREATE INDEX idx_rfp_requirements_rfp ON rfp_requirements(rfp_id);
CREATE INDEX idx_rfp_requirements_parent ON rfp_requirements(parent_section_id);
CREATE INDEX idx_rfp_requirements_type ON rfp_requirements(requirement_type);
CREATE INDEX idx_rfp_requirements_mandatory ON rfp_requirements(is_mandatory);
CREATE INDEX idx_rfp_requirements_eligibility ON rfp_requirements(eligibility_flag);
CREATE INDEX idx_rfp_requirements_section_order ON rfp_requirements(rfp_id, section_order);
CREATE INDEX idx_rfp_requirements_keywords ON rfp_requirements USING GIN(compliance_keywords);

-- ============================================================================
-- 9. CROSSWALK_MAPS
-- ============================================================================
-- Core intelligence layer: mapping RFP requirements to boilerplate content
-- Drives the recommendation engine and gap identification

CREATE TABLE crosswalk_maps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rfp_requirement_id UUID NOT NULL REFERENCES rfp_requirements(id) ON DELETE CASCADE,
  boilerplate_section_id UUID NOT NULL REFERENCES boilerplate_sections(id) ON DELETE CASCADE,

  -- Alignment assessment
  alignment_score alignment_score NOT NULL DEFAULT 'weak',
  alignment_confidence DECIMAL(3, 2),  -- 0.0-1.0 confidence level from matching algorithm

  -- Risk and compliance assessment
  gap_flag BOOLEAN NOT NULL DEFAULT false,  -- True if requirement not fully met by boilerplate
  risk_level risk_level NOT NULL DEFAULT 'yellow',

  -- Customization guidance
  customization_needed TEXT,  -- Specific adjustments required
  customization_effort VARCHAR(50),  -- 'minimal', 'moderate', 'significant'

  -- Matching metadata
  auto_matched BOOLEAN NOT NULL DEFAULT false,  -- Auto-matched vs. manually assigned
  matching_keywords TEXT[],  -- Keywords that contributed to match

  -- Approval workflow
  reviewer_approved BOOLEAN NOT NULL DEFAULT false,
  reviewer_comments TEXT,
  approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
  approved_at TIMESTAMP WITH TIME ZONE,

  -- Notes and reasoning
  notes TEXT,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT unique_mapping UNIQUE(rfp_requirement_id, boilerplate_section_id),
  CONSTRAINT valid_confidence CHECK (alignment_confidence IS NULL OR (alignment_confidence >= 0 AND alignment_confidence <= 1))
);

CREATE INDEX idx_crosswalk_requirement ON crosswalk_maps(rfp_requirement_id);
CREATE INDEX idx_crosswalk_boilerplate ON crosswalk_maps(boilerplate_section_id);
CREATE INDEX idx_crosswalk_risk ON crosswalk_maps(risk_level);
CREATE INDEX idx_crosswalk_gap ON crosswalk_maps(gap_flag);
CREATE INDEX idx_crosswalk_alignment ON crosswalk_maps(alignment_score);
CREATE INDEX idx_crosswalk_approved ON crosswalk_maps(reviewer_approved);
CREATE INDEX idx_crosswalk_keywords ON crosswalk_maps USING GIN(matching_keywords);

-- ============================================================================
-- 10. GRANT_PLANS
-- ============================================================================
-- Structured grant applications generated from RFP + boilerplate matching

CREATE TABLE grant_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rfp_id UUID NOT NULL REFERENCES rfps(id) ON DELETE CASCADE,

  -- Identification
  title VARCHAR(500) NOT NULL,
  funder_name VARCHAR(500),

  -- Status and lifecycle
  status grant_plan_status NOT NULL DEFAULT 'draft',

  -- Plan data as structured JSON for flexibility and complex relationships
  plan_data JSONB NOT NULL,  -- Stores full plan structure: sections, matched content, customizations

  -- Compliance metrics
  overall_compliance_score DECIMAL(5, 2),  -- 0-100 score
  coverage_percentage DECIMAL(5, 2),  -- % of requirements addressed
  gap_count INTEGER DEFAULT 0,
  yellow_risk_count INTEGER DEFAULT 0,
  red_risk_count INTEGER DEFAULT 0,

  -- Metadata
  total_word_count INTEGER GENERATED ALWAYS AS (
    COALESCE((plan_data->>'total_word_count')::INTEGER, 0)
  ) STORED,
  last_recalculated_at TIMESTAMP WITH TIME ZONE,

  -- Submission tracking
  submitted_at TIMESTAMP WITH TIME ZONE,
  submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  feedback TEXT,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

  CONSTRAINT valid_compliance_score CHECK (overall_compliance_score IS NULL OR (overall_compliance_score >= 0 AND overall_compliance_score <= 100)),
  CONSTRAINT valid_coverage CHECK (coverage_percentage IS NULL OR (coverage_percentage >= 0 AND coverage_percentage <= 100))
);

CREATE INDEX idx_grant_plans_rfp ON grant_plans(rfp_id);
CREATE INDEX idx_grant_plans_status ON grant_plans(status);
CREATE INDEX idx_grant_plans_created ON grant_plans(created_at DESC);
CREATE INDEX idx_grant_plans_funder ON grant_plans(funder_name);
CREATE INDEX idx_grant_plans_created_by ON grant_plans(created_by);

-- ============================================================================
-- 11. GRANT_PLAN_SECTIONS
-- ============================================================================
-- Individual sections within a grant plan for detailed editing and tracking

CREATE TABLE grant_plan_sections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  plan_id UUID NOT NULL REFERENCES grant_plans(id) ON DELETE CASCADE,
  rfp_requirement_id UUID REFERENCES rfp_requirements(id) ON DELETE SET NULL,

  -- Content and structure
  section_title VARCHAR(500) NOT NULL,
  section_order INTEGER NOT NULL,
  section_number VARCHAR(50),  -- e.g., '2.1'

  -- Content management
  suggested_content TEXT,  -- Initial suggested content from boilerplate
  final_content TEXT,  -- Editor's final version
  word_limit INTEGER,
  word_count_target INTEGER,
  current_word_count INTEGER,

  -- Customization tracking
  customization_notes TEXT,  -- What was changed from suggestion
  customized_by UUID REFERENCES users(id) ON DELETE SET NULL,
  customized_at TIMESTAMP WITH TIME ZONE,

  -- Compliance and quality
  compliance_status compliance_status NOT NULL DEFAULT 'partial',
  risk_level risk_level NOT NULL DEFAULT 'yellow',
  quality_score DECIMAL(3, 2),  -- 0-100

  -- Content sources
  source_boilerplate_sections UUID[],  -- Array of boilerplate IDs used

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_section_order CHECK (section_order >= 0),
  CONSTRAINT valid_quality_score CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100))
);

CREATE INDEX idx_grant_plan_sections_plan ON grant_plan_sections(plan_id);
CREATE INDEX idx_grant_plan_sections_rfp_req ON grant_plan_sections(rfp_requirement_id);
CREATE INDEX idx_grant_plan_sections_compliance ON grant_plan_sections(compliance_status);
CREATE INDEX idx_grant_plan_sections_risk ON grant_plan_sections(risk_level);
CREATE INDEX idx_grant_plan_sections_section_order ON grant_plan_sections(plan_id, section_order);

-- ============================================================================
-- 12. GAP_ANALYSES
-- ============================================================================
-- Gap analysis results identifying misalignments and improvement opportunities

CREATE TABLE gap_analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rfp_id UUID NOT NULL REFERENCES rfps(id) ON DELETE CASCADE,
  grant_plan_id UUID REFERENCES grant_plans(id) ON DELETE SET NULL,

  -- Analysis metadata
  analysis_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  analyzed_by UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Overall assessment
  overall_risk_level risk_level NOT NULL,
  overall_gap_score DECIMAL(5, 2),  -- 0-100, higher = more gaps

  -- Gap data as structured JSON for complex analysis results
  gap_data JSONB NOT NULL,  -- Detailed breakdown by category

  -- Key findings
  missing_metrics TEXT[],  -- Required metrics/evidence not in boilerplate
  weak_alignments TEXT[],  -- Requirements with weak boilerplate matches
  outdated_data TEXT[],  -- Statistics/data that need updating
  missing_partnerships TEXT[],  -- Partnership gaps
  evaluation_weaknesses TEXT[],  -- Evaluation/outcome tracking gaps

  -- Recommendations as structured JSON
  recommendations JSONB NOT NULL,  -- Prioritized action items

  -- Status
  is_current BOOLEAN NOT NULL DEFAULT true,

  -- Audit
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_gap_score CHECK (overall_gap_score >= 0 AND overall_gap_score <= 100)
);

CREATE INDEX idx_gap_analyses_rfp ON gap_analyses(rfp_id);
CREATE INDEX idx_gap_analyses_plan ON gap_analyses(grant_plan_id);
CREATE INDEX idx_gap_analyses_date ON gap_analyses(analysis_date DESC);
CREATE INDEX idx_gap_analyses_current ON gap_analyses(is_current);
CREATE INDEX idx_gap_analyses_risk ON gap_analyses(overall_risk_level);

-- ============================================================================
-- 13. AUDIT_LOG
-- ============================================================================
-- Complete audit trail for compliance and change tracking

CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Action details
  action VARCHAR(255) NOT NULL,  -- 'create', 'update', 'delete', 'approve', 'submit'
  entity_type VARCHAR(100) NOT NULL,  -- 'boilerplate_section', 'rfp', 'grant_plan', etc.
  entity_id UUID,

  -- Change tracking
  old_value JSONB,  -- Previous value
  new_value JSONB,  -- New value
  change_description TEXT,

  -- IP and session info
  ip_address INET,
  user_agent TEXT,

  -- Audit
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT valid_action CHECK (action IN ('create', 'update', 'delete', 'approve', 'submit', 'review', 'archive', 'restore'))
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);

-- ============================================================================
-- FOREIGN KEY CONSTRAINT FOR users.id REFERENCE (defined late)
-- ============================================================================
-- Add the constraint for created_by in boilerplate_sections after users table exists

ALTER TABLE boilerplate_sections
ADD CONSTRAINT fk_boilerplate_sections_created_by
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active boilerplate sections with category information
CREATE OR REPLACE VIEW v_active_boilerplate_with_category AS
SELECT
  bs.id,
  bs.section_title,
  bs.content,
  bs.word_count,
  bs.program_area,
  bs.evidence_type,
  bs.compliance_relevance,
  bs.tags,
  bc.category_name,
  bs.created_at,
  bs.updated_at
FROM boilerplate_sections bs
JOIN boilerplate_categories bc ON bs.category_id = bc.id
WHERE bs.is_active = true
ORDER BY bc.sort_order, bs.section_title;

-- RFP requirements with parent section information
CREATE OR REPLACE VIEW v_rfp_requirements_hierarchy AS
SELECT
  rr.id,
  rr.rfp_id,
  rr.section_name,
  rr.section_number,
  rr.description,
  rr.word_limit,
  rr.scoring_weight,
  rr.is_mandatory,
  rr.section_order,
  parent.section_number AS parent_section_number,
  parent.section_name AS parent_section_name
FROM rfp_requirements rr
LEFT JOIN rfp_requirements parent ON rr.parent_section_id = parent.id
ORDER BY rr.section_order;

-- Crosswalk summary with statistics
CREATE OR REPLACE VIEW v_crosswalk_summary AS
SELECT
  cm.rfp_requirement_id,
  cm.boilerplate_section_id,
  rr.section_name,
  bs.section_title,
  cm.alignment_score,
  cm.risk_level,
  cm.gap_flag,
  cm.reviewer_approved,
  cm.customization_needed
FROM crosswalk_maps cm
JOIN rfp_requirements rr ON cm.rfp_requirement_id = rr.id
JOIN boilerplate_sections bs ON cm.boilerplate_section_id = bs.id
WHERE rr.id IS NOT NULL AND bs.is_active = true;

-- Grant plan status summary
CREATE OR REPLACE VIEW v_grant_plan_summary AS
SELECT
  gp.id,
  gp.title,
  gp.funder_name,
  gp.status,
  gp.overall_compliance_score,
  gp.coverage_percentage,
  gp.gap_count,
  gp.yellow_risk_count,
  gp.red_risk_count,
  COUNT(gps.id) AS section_count,
  gp.created_at,
  u.name AS created_by_name
FROM grant_plans gp
LEFT JOIN grant_plan_sections gps ON gp.id = gps.plan_id
LEFT JOIN users u ON gp.created_by = u.id
GROUP BY gp.id, u.id;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
