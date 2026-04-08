from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from collections import Counter
from typing import List

from ..models import DreamEntry, User
from ..utils import *
from ..jinja import templates

router = APIRouter()

# Calculate personal statistics
def calculate_personal_stats(user: User, time_slice: str = 'all'):
    """Calculate user's dream statistics"""
    
    # Filter entries by time slice
    now = datetime.now()
    if time_slice == 'day':
        cutoff = now - timedelta(days=1)
    elif time_slice == 'week':
        cutoff = now - timedelta(weeks=1)
    elif time_slice == 'month':
        cutoff = now - timedelta(days=30)
    else:  # 'all'
        cutoff = None
    
    # Filter entries
    if cutoff:
        entries = [e for e in user.dream_entries if e.created_at >= cutoff]
    else:
        entries = user.dream_entries
    
    total_entries = len(entries)
    
    if total_entries == 0:
        return {
            'time_slice': time_slice,
            'total_entries': 0,
            'top_content_tag': None,
            'second_content_tag': None,
            'top_context_tag': None,
            'second_context_tag': None,
            'top_type_tag': None,
            'second_type_tag': None,
            'sight_rate': 0,
            'sound_rate': 0,
            'touch_rate': 0,
            'smell_rate': 0,
            'taste_rate': 0,
            'pain_rate': 0,
            'avg_sleep_duration': 0,
            'public_ratio': 0,
            'reflection_ratio': 0,
        }
    
    # Count tags
    content_tags = Counter()
    context_tags = Counter()
    type_tags = Counter()
    
    for entry in entries:
        for tag in entry.tags:
            if tag.category == 'dream_content':
                content_tags[tag.value] += 1
            elif tag.category == 'irl_context':
                context_tags[tag.value] += 1
            elif tag.category == 'dream_type':
                type_tags[tag.value] += 1
    
    # Get top two tags
    def get_top_two(counter):
        most_common = counter.most_common(2)
        top = most_common[0][0] if len(most_common) > 0 else None
        second = most_common[1][0] if len(most_common) > 1 else None
        return top, second
    
    top_content, second_content = get_top_two(content_tags)
    top_context, second_context = get_top_two(context_tags)
    top_type, second_type = get_top_two(type_tags)
    
    # Calculate sensory rates
    sense_counts = {
        'sight': sum(1 for e in entries if e.sense_sight),
        'sound': sum(1 for e in entries if e.sense_sound),
        'touch': sum(1 for e in entries if e.sense_touch),
        'smell': sum(1 for e in entries if e.sense_smell),
        'taste': sum(1 for e in entries if e.sense_taste),
        'pain': sum(1 for e in entries if e.sense_pain),
    }
    
    sense_rates = {k: v / total_entries for k, v in sense_counts.items()}
    
    # Calculate average sleep duration
    sleep_durations = []
    for entry in entries:
        if entry.bed_time and entry.wake_time:
            # Calculate sleep duration (hours)
            bed_minutes = entry.bed_time.hour * 60 + entry.bed_time.minute
            wake_minutes = entry.wake_time.hour * 60 + entry.wake_time.minute
            
            # Handle overnight sleep
            if wake_minutes < bed_minutes:
                wake_minutes += 24 * 60
            
            duration = (wake_minutes - bed_minutes) / 60.0
            sleep_durations.append(duration)
    
    avg_sleep = sum(sleep_durations) / len(sleep_durations) if sleep_durations else 0
    
    # Calculate public and reflection ratios
    public_count = sum(1 for e in entries if e.public)
    reflection_count = sum(1 for e in entries if e.reflection)
    
    return {
        'time_slice': time_slice,
        'total_entries': total_entries,
        'top_content_tag': top_content,
        'second_content_tag': second_content,
        'top_context_tag': top_context,
        'second_context_tag': second_context,
        'top_type_tag': top_type,
        'second_type_tag': second_type,
        'sight_rate': sense_rates['sight'],
        'sound_rate': sense_rates['sound'],
        'touch_rate': sense_rates['touch'],
        'smell_rate': sense_rates['smell'],
        'taste_rate': sense_rates['taste'],
        'pain_rate': sense_rates['pain'],
        'avg_sleep_duration': avg_sleep,
        'public_ratio': public_count / total_entries,
        'reflection_ratio': reflection_count / total_entries,
    }

# Page listing stored dream entries and local stats
@router.get("/my-dreams")
def list_dream_entries(request: Request, dbSes: DbSesDep, user: UserDep):
    if not user:
        flash(request, "This page or method requires an account!", "warn")
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "my-dreams.html", {"entries": user.dream_entries})

# Page to display the full details of a specific dream entry
@router.get("/my-dreams/{entry_id}")
def dream_entry_detail(request: Request, entry_id: int, dbSes: DbSesDep, user: UserDep, res: ResearcherDep):
    if not (user or res):
        flash(request, "This page or method requires an account!", "warn")
        return RedirectResponse("/login", status_code=303)
    
    # Get the dream entry from database
    entry = dbSes.get(DreamEntry, entry_id)
    
    # Handle entry not found
    if not entry:
        flash(request, "Dream entry not found!", "warn")
        return RedirectResponse("/my-dreams" if user else "/", status_code=303)
    
    # You cannot view an entry if:
    # - you're a user and the entry isn't yours
    # - you're a researcher and the entry doesn't match your filters
    if (user and entry.user_id != user.id) or (res and not res.allowed_to_view(entry)):
        flash(request, "You don't have permission to view this dream entry!", "warn")
        return RedirectResponse("/my-dreams" if user else "/login", status_code=303)
    
    # Render the detail page
    return templates.TemplateResponse(
        request,
        "dream-detail.html",
        {"entry": entry, "is_owner": bool(user and entry.user_id == user.id)},
    )

# Update the follow-up reflection on the current entry
@router.post("/my-dreams/{entry_id}/reflection")
def update_reflection(request: Request,
    entry_id: int,
    dbSes: DbSesDep,
    user: UserDep,
    rfln: Annotated[str, Form()] = "",
):
    if not user:
        flash(request, "You must be logged in to add a follow-up reflection.", "warn")
        return RedirectResponse("/login", status_code=303)

    entry = dbSes.get(DreamEntry, entry_id)
    if not entry or entry.user_id != user.id:
        flash(request, "You don't have permission to modify this entry.", "warn")
        return RedirectResponse("/my-dreams", status_code=303)

    entry.reflection = rfln
    entry.rfln_timestamp = datetime.now()
    dbSes.add(entry)
    dbSes.commit()

    flash(request, "Follow-up reflection saved.", "success")
    return RedirectResponse(f"/my-dreams/{entry_id}", status_code=303)

# Page to display personal statistics
@router.get("/personal-stats")
def view_personal_stats(request: Request, dbSes: DbSesDep, user: UserDep):
    if not user:
        flash(request, "This page or method requires an account!", "warn")
        return RedirectResponse("/login", status_code=303)
    
    # Calculate stats for all time slices
    stats = {
        'all': calculate_personal_stats(user, 'all'),
        'month': calculate_personal_stats(user, 'month'),
        'week': calculate_personal_stats(user, 'week'),
    }
    
    return templates.TemplateResponse(request, "my-dreams-stats.html", {"stats": stats})