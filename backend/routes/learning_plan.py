import json
import sqlalchemy as sa
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from urllib.parse import urlparse, quote_plus

from extensions import db
from models import SkillScore, SkillTaxonomy, AssessmentResponse, AssessmentScoreDetail
from ai_service import analyze_gaps, generate_enhanced_learning_plan

learning_bp = Blueprint('learning', __name__)

TRUSTED_RESOURCE_DOMAINS = {
    'youtube.com',
    'youtu.be',
    'docs.python.org',
    'realpython.com',
    'react.dev',
    'developer.mozilla.org',
    'nodejs.org',
    'docs.docker.com',
    'kubernetes.io',
    'flask.palletsprojects.com',
    'fastapi.tiangolo.com',
    'sqlalchemy.org',
    'postgresql.org',
    'aws.amazon.com',
    'learn.microsoft.com',
    'cloud.google.com',
    'coursera.org',
    'edx.org',
    'freecodecamp.org',
    'leetcode.com',
    'geeksforgeeks.org',
}


def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace('www.', '')
    except Exception:
        return ''


def _is_trusted_resource(url: str) -> bool:
    domain = _domain_from_url(url)
    if not domain:
        return False
    return any(domain == trusted or domain.endswith(f'.{trusted}') for trusted in TRUSTED_RESOURCE_DOMAINS)


def _is_relevant_resource(skill_name: str, title: str, url: str) -> bool:
    normalized_skill = skill_name.lower().strip()
    tokens = [t for t in normalized_skill.replace('-', ' ').split() if len(t) > 2]
    haystack = f"{title} {url}".lower()
    if not tokens:
        return True
    return any(token in haystack for token in tokens)


def _fallback_verified_resources(skill_name: str):
    query = quote_plus(f"{skill_name} tutorial")
    docs_query = quote_plus(f"{skill_name} official documentation")
    practice_query = quote_plus(f"{skill_name} practice")
    return {
        'youtube': [
            {
                'title': f'{skill_name} tutorial videos',
                'url': f'https://www.youtube.com/results?search_query={query}',
                'duration_minutes': 45,
            }
        ],
        'websites': [
            {
                'title': f'{skill_name} official docs and guides',
                'url': f'https://www.coursera.org/search?query={docs_query}',
                'category': 'documentation',
                'estimated_hours': 2,
            },
            {
                'title': f'{skill_name} guided practice resources',
                'url': f'https://www.geeksforgeeks.org/?s={practice_query}',
                'category': 'practice',
                'estimated_hours': 3,
            },
        ],
    }


def _sanitize_plan_resources(skill_name: str, plan_data: dict) -> dict:
    sanitized = _coerce_json(plan_data)
    phases = sanitized.get('phases', []) if isinstance(sanitized.get('phases', []), list) else []
    fallback = _fallback_verified_resources(skill_name)

    for phase in phases:
        youtube = phase.get('youtube_resources', []) if isinstance(phase.get('youtube_resources', []), list) else []
        websites = phase.get('website_resources', []) if isinstance(phase.get('website_resources', []), list) else []

        valid_youtube = [
            {
                'title': str(resource.get('title', '')).strip(),
                'url': str(resource.get('url', '')).strip(),
                'duration_minutes': int(resource.get('duration_minutes', 30) or 30),
            }
            for resource in youtube
            if isinstance(resource, dict)
            and _is_trusted_resource(str(resource.get('url', '')))
            and _is_relevant_resource(skill_name, str(resource.get('title', '')), str(resource.get('url', '')))
        ]

        valid_websites = [
            {
                'title': str(resource.get('title', '')).strip(),
                'url': str(resource.get('url', '')).strip(),
                'category': str(resource.get('category', 'tutorial')).strip() or 'tutorial',
                'estimated_hours': int(resource.get('estimated_hours', 1) or 1),
            }
            for resource in websites
            if isinstance(resource, dict)
            and _is_trusted_resource(str(resource.get('url', '')))
            and _is_relevant_resource(skill_name, str(resource.get('title', '')), str(resource.get('url', '')))
        ]

        if not valid_youtube:
            valid_youtube = fallback['youtube']
        if not valid_websites:
            valid_websites = fallback['websites']

        phase['youtube_resources'] = valid_youtube
        phase['website_resources'] = valid_websites

    sanitized['phases'] = phases
    return sanitized


def _learning_plan_table() -> sa.Table:
    metadata = sa.MetaData()
    return sa.Table('learning_plans', metadata, autoload_with=db.engine)


def _is_enhanced_schema(lp_table: sa.Table) -> bool:
    return 'skill_gap_id' in lp_table.c


def _is_json_like_column(column: sa.Column) -> bool:
    return "json" in type(column.type).__name__.lower()


def _recommendations_for_insert(lp_table: sa.Table, plan_data: dict):
    rec_col = lp_table.c.get('recommendations')
    if rec_col is None:
        return plan_data
    if _is_json_like_column(rec_col):
        return plan_data
    return json.dumps(plan_data)


def _coerce_json(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _extract_resources_from_plan(plan_data: dict):
    youtube = []
    websites = []
    for phase in plan_data.get('phases', []):
        for resource in phase.get('youtube_resources', []):
            youtube.append({
                "title": resource.get("title", ""),
                "url": resource.get("url", ""),
                "duration_minutes": resource.get("duration_minutes", 0),
            })
        for resource in phase.get('website_resources', []):
            websites.append({
                "title": resource.get("title", ""),
                "url": resource.get("url", ""),
                "category": resource.get("category", ""),
                "estimated_hours": resource.get("estimated_hours", 0),
            })
    return youtube, websites


@learning_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """
    POST /learning-plan/generate
    Body: { skill_score_id }

    Generates a personalized learning plan with YouTube and website resources
    for a specific identified skill gap.
    """
    current_user_id = str(get_jwt_identity())
    data = request.get_json() or {}
    skill_score_id = data.get('skill_score_id')

    if not skill_score_id:
        return jsonify({"error": "skill_score_id is required"}), 400

    skill_score = db.session.get(SkillScore, skill_score_id)
    if not skill_score:
        return jsonify({"error": "Skill score not found"}), 404
    if current_user_id != str(skill_score.student_id):
        return jsonify({"error": "Unauthorized"}), 403
    if not skill_score.gap_identified:
        return jsonify({"error": "No gap identified for this skill — learning plan not needed"}), 400

    taxonomy = db.session.get(SkillTaxonomy, skill_score.skill_id)

    lp_table = _learning_plan_table()
    enhanced_schema = _is_enhanced_schema(lp_table)

    # Check if plan already exists and is reusable.
    if enhanced_schema:
        existing_stmt = (
            sa.select(lp_table)
            .where(lp_table.c.skill_gap_id == skill_score_id)
            .order_by(lp_table.c.id.desc())
            .limit(1)
        )
    else:
        existing_stmt = (
            sa.select(lp_table)
            .where(
                lp_table.c.student_id == str(skill_score.student_id),
                lp_table.c.skill_id == skill_score.skill_id,
            )
            .order_by(lp_table.c.id.desc())
            .limit(1)
        )

    existing = db.session.execute(existing_stmt).mappings().first()
    if existing:
        existing_plan = _coerce_json(existing.get('recommendations'))
        existing_youtube, existing_websites = _extract_resources_from_plan(existing_plan)
        return jsonify({
            "status": "exists",
            "learning_plan_id": existing.get('id'),
            "plan": existing_plan,
            "youtube_resources": existing.get('youtube_resources') or existing_youtube,
            "website_resources": existing.get('website_resources') or existing_websites,
            "timeline_weeks": existing.get('timeline_weeks') or existing.get('duration_weeks') or existing_plan.get('total_weeks'),
        }), 200

    # ── Extract Gap Information from Assessment ────────────────────────────────
    response_record = AssessmentResponse.query.filter_by(
        assessment_id=skill_score.assessment_id
    ).first()
    AssessmentScoreDetail.query.filter_by(
        assessment_id=skill_score.assessment_id
    ).first()
    
    # Extract identified gaps from the response
    identified_gaps = []
    improvement_potential = 5
    
    if response_record and response_record.ai_feedback:
        feedback = response_record.ai_feedback
        if 'identified_gaps' in feedback:
            identified_gaps = feedback['identified_gaps']
        
        # Calculate improvement potential based on score
        if skill_score.score < 3:
            improvement_potential = 9  # High potential if very low score
        elif skill_score.score < 6:
            improvement_potential = 7
        else:
            improvement_potential = 5

    # ── Enhanced Learning Plan Generation ──────────────────────────────────────
    try:
        plan_result = generate_enhanced_learning_plan(
            skill_name=taxonomy.skill_name,
            score=skill_score.score,
            identified_gaps=identified_gaps,
            improvement_potential=improvement_potential,
        )
    except Exception as e:
        return jsonify({"error": "Learning plan generation failed", "details": str(e)}), 502

    # Save plan to DB with schema compatibility.
    plan_data = _sanitize_plan_resources(taxonomy.skill_name, plan_result.model_dump())
    youtube_resources, website_resources = _extract_resources_from_plan(plan_data)

    insert_values = {
        'student_id': str(skill_score.student_id),
        'recommendations': _recommendations_for_insert(lp_table, plan_data),
    }

    columns = set(lp_table.c.keys())
    if enhanced_schema:
        insert_values['skill_gap_id'] = skill_score_id
        if 'estimated_hours' in columns:
            insert_values['estimated_hours'] = plan_result.total_weeks * 5
        if 'priority' in columns:
            insert_values['priority'] = 1
        if 'youtube_resources' in columns:
            insert_values['youtube_resources'] = youtube_resources
        if 'website_resources' in columns:
            insert_values['website_resources'] = website_resources
        if 'timeline_weeks' in columns:
            insert_values['timeline_weeks'] = plan_result.total_weeks
        if 'is_reusable' in columns:
            insert_values['is_reusable'] = True
    else:
        insert_values['skill_id'] = skill_score.skill_id
        if 'duration_weeks' in columns:
            insert_values['duration_weeks'] = plan_result.total_weeks
        if 'progress' in columns:
            insert_values['progress'] = 0
        if 'status' in columns:
            insert_values['status'] = 'active'

    insert_result = db.session.execute(lp_table.insert().values(**insert_values))
    db.session.commit()

    learning_plan_id = insert_result.inserted_primary_key[0] if insert_result.inserted_primary_key else None

    return jsonify({
        "status": "success",
        "learning_plan_id": learning_plan_id,
        "skill_name": taxonomy.skill_name,
        "total_weeks": plan_data.get('total_weeks', plan_result.total_weeks),
        "summary": plan_data.get('summary', plan_result.summary),
        "plan": plan_data,
        "youtube_resources": youtube_resources,
        "website_resources": website_resources,
        "reassessment": {
            "cooldown_days": 7,
            "rule": "Reassessment allowed after cooldown or after study completion",
        },
    }), 201


@learning_bp.route('/student/<string:student_id>', methods=['GET'])
@jwt_required()
def list_plans(student_id: str):
    """GET /learning-plan/student/{id} — All learning plans for a student."""
    current_user_id = str(get_jwt_identity())
    if current_user_id != str(student_id):
        return jsonify({"error": "Unauthorized"}), 403

    lp_table = _learning_plan_table()
    enhanced_schema = _is_enhanced_schema(lp_table)

    plans = db.session.execute(
        sa.select(lp_table)
        .where(lp_table.c.student_id == str(student_id))
        .order_by(lp_table.c.id.desc())
    ).mappings().all()

    result = []
    for lp in plans:
        recommendations = _coerce_json(lp.get('recommendations'))
        if enhanced_schema:
            score_row = db.session.get(SkillScore, lp.get('skill_gap_id'))
            skill_id = score_row.skill_id if score_row else None
            score = score_row.score if score_row else None
            estimated_hours = lp.get('estimated_hours')
            priority = lp.get('priority')
        else:
            skill_id = lp.get('skill_id')
            score = None
            estimated_hours = (lp.get('duration_weeks') or recommendations.get('total_weeks') or 0) * 5
            priority = 3

        taxonomy = db.session.get(SkillTaxonomy, skill_id) if skill_id else None
        created_at = lp.get('created_at')

        result.append({
            "learning_plan_id": lp.get('id'),
            "skill_name": taxonomy.skill_name if taxonomy else "Unknown",
            "score": score,
            "estimated_hours": estimated_hours,
            "priority": priority,
            "summary": recommendations.get('summary', ''),
            "phases_count": len(recommendations.get('phases', [])),
            "created_at": created_at.isoformat() if created_at else None,
        })

    return jsonify({"learning_plans": result}), 200


@learning_bp.route('/<int:plan_id>', methods=['GET'])
@jwt_required()
def get_plan(plan_id: int):
    """GET /learning-plan/{id} — Full plan detail with resources."""
    current_user_id = str(get_jwt_identity())
    lp_table = _learning_plan_table()

    plan = db.session.execute(
        sa.select(lp_table).where(lp_table.c.id == plan_id)
    ).mappings().first()
    if not plan:
        return jsonify({"error": "Learning plan not found"}), 404
    if current_user_id != str(plan.get('student_id')):
        return jsonify({"error": "Unauthorized"}), 403

    recommendations = _coerce_json(plan.get('recommendations'))
    youtube_resources, website_resources = _extract_resources_from_plan(recommendations)

    return jsonify({
        "learning_plan_id": plan.get('id'),
        "recommendations": recommendations,
        "estimated_hours": plan.get('estimated_hours') or (plan.get('duration_weeks') or recommendations.get('total_weeks') or 0) * 5,
        "timeline_weeks": plan.get('timeline_weeks') or plan.get('duration_weeks') or recommendations.get('total_weeks'),
        "youtube_resources": plan.get('youtube_resources') or youtube_resources,
        "website_resources": plan.get('website_resources') or website_resources,
        "is_reusable": plan.get('is_reusable', True),
        "created_at": plan.get('created_at').isoformat() if plan.get('created_at') else None,
    }), 200


@learning_bp.route('/skill/<int:skill_id>/reusable', methods=['GET'])
@jwt_required()
def get_reusable_plans(skill_id: int):
    """GET /learning-plan/skill/{id}/reusable — Get existing reusable plans for a skill."""
    current_user_id = str(get_jwt_identity())

    lp_table = _learning_plan_table()
    enhanced_schema = _is_enhanced_schema(lp_table)

    stmt = sa.select(lp_table).where(lp_table.c.student_id == current_user_id)
    if enhanced_schema and 'is_reusable' in lp_table.c:
        stmt = stmt.where(lp_table.c.is_reusable == True)
    elif not enhanced_schema:
        stmt = stmt.where(lp_table.c.skill_id == skill_id)

    plans = db.session.execute(stmt.order_by(lp_table.c.id.desc())).mappings().all()

    result = []
    for lp in plans:
        recommendations = _coerce_json(lp.get('recommendations'))

        if enhanced_schema:
            score_row = db.session.get(SkillScore, lp.get('skill_gap_id'))
            if not score_row or score_row.skill_id != skill_id:
                continue
            skill_score_value = score_row.score
            timeline_weeks = lp.get('timeline_weeks') or recommendations.get('total_weeks')
        else:
            skill_score_value = None
            timeline_weeks = lp.get('duration_weeks') or recommendations.get('total_weeks')

        taxonomy = db.session.get(SkillTaxonomy, skill_id)
        youtube_resources, website_resources = _extract_resources_from_plan(recommendations)
        created_at = lp.get('created_at')

        result.append({
            "learning_plan_id": lp.get('id'),
            "skill_name": taxonomy.skill_name if taxonomy else "Unknown",
            "score": skill_score_value,
            "estimated_hours": lp.get('estimated_hours') or (timeline_weeks or 0) * 5,
            "timeline_weeks": timeline_weeks,
            "summary": recommendations.get('summary', ''),
            "phases_count": len(recommendations.get('phases', [])),
            "youtube_resources_count": len(lp.get('youtube_resources') or youtube_resources),
            "website_resources_count": len(lp.get('website_resources') or website_resources),
            "created_at": created_at.isoformat() if created_at else None,
        })

    return jsonify({"reusable_plans": result}), 200
