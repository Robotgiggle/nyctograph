from typing import Annotated, List, Tuple

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import User, Tag
from ..forms import DreamEntryForm
from ..utils import DbSesDep, ResearcherDep, UserDep, flash
from ..jinja import templates

router = APIRouter()

# Attempts to save the provided form data into the database
# Returns a bool for whether it succeeded, and a list of messages to flash
def save_dream_entry(dbSes: Session, user: User, formDataModel: DreamEntryForm) -> Tuple[bool, List[str]]:
    flashes = []

    # Create the DreamEntry itself
    newEntry = formDataModel.createDreamEntry()
    for entry in user.dream_entries:
        if entry.title == newEntry.title:
            flashes.append((f"You already have an entry with that title!", "warn"))
            return (False, flashes)
    if newEntry.public and not user.public_enabled:
        newEntry.public = False
        flashes.append(("Entry marked as non-public to match your account settings.", "info"))
    user.dream_entries.append(newEntry)

    # Link the appropriate tags, fail if a nonexistent tag is listed
    badTags = []
    for tagName in formDataModel.all_tags:
        tagObj = dbSes.get(Tag, tagName)
        if tagObj is None: badTags.append(tagName)
        else: newEntry.tags.append(tagObj)
    if badTags:
        for tag in badTags: flashes.append((f"'{tag}' is not a valid tag!", "warn"))
        return (False, flashes)
    
    # Compare entry location to user's default location
    if formDataModel.country != user.country or formDataModel.state != user.state or formDataModel.city != user.city:
        nsLocTag = dbSes.get(Tag, "Atypical Location")
        if nsLocTag: newEntry.tags.append(nsLocTag)

    # Save the entry
    dbSes.add(newEntry)
    dbSes.commit()
    return (True, flashes)

@router.get("/")
def record_dream_form(request: Request, dbSes: DbSesDep, user: UserDep):
    # Attempt to retrieve stored form data from the session, save and clear storage if logged in
    storedEntryJson = request.session.get("storedEntry")
    if storedEntryJson:
        storedEntry = DreamEntryForm.model_validate_json(storedEntryJson)
        if user and request.session.get("saveOnLogin"):
            success, flashes = save_dream_entry(dbSes, user, storedEntry)
            for item in flashes: flash(request, item[0], item[1])
            if success: 
                flash(request, "Stored dream entry saved.", "success")
                request.session.pop("storedEntry", None)
                request.session.pop("saveOnLogin", None)
                storedEntry = None
    else:
        storedEntry = None
    
    # Various useful data for the template renderer
    context = {
        "entry": storedEntry,
        "senses": ['sight', 'sound', 'touch', 'smell', 'taste', 'pain', 'other'],
        "contentTags": dbSes.execute(select(Tag.value).where(Tag.category == "dream_content")).scalars().all(),
        "typeTags": dbSes.execute(select(Tag.value).where(Tag.category == "dream_type")).scalars().all(),
        "contextTags": dbSes.execute(select(Tag.value).where(Tag.category == "irl_context")).scalars().all(),
        "defaultLocation": (
            storedEntry.country if storedEntry else (user.country or '' if user else ''), 
            storedEntry.state if storedEntry else (user.state or '' if user else ''), 
            storedEntry.city if storedEntry else (user.city or '' if user else '')
        ),
        "publicDisabled": not user.public_enabled if user else False
    }

    # Display the dream entry creation form
    return templates.TemplateResponse(request, "record-dream.html", context)

@router.post("/")
def record_dream_action(request: Request, dbSes: DbSesDep, user: UserDep, researcher: ResearcherDep, formDataModel: Annotated[DreamEntryForm, Form()]):#, title: Annotated[str, Form()], description: Annotated[str, Form()]):
    if user:
        success, flashes = save_dream_entry(dbSes, user, formDataModel)
        for item in flashes: flash(request, item[0], item[1])
        if not success: 
            request.session["storedEntry"] = formDataModel.model_dump_json()
            return RedirectResponse("/", status_code=303)

        # Now that the entry is saved, clear it out of the session if it's there
        request.session.pop("storedEntry", None)
        request.session.pop("saveOnLogin", None)

        # Return to homepage with success message
        flash(request, "Dream entry saved.", "success")
        return RedirectResponse("/", status_code=303)
    else:
        if researcher:
            flash(
                request,
                "Research institution accounts cannot save dream entries. Log in with a standard user account to record dreams.",
                "warn",
            )
            return RedirectResponse("/", status_code=303)
        
        # Store a representation of the form data into the session for later use
        request.session["storedEntry"] = formDataModel.model_dump_json()
        request.session["saveOnLogin"] = True

        # Redirect to the signup page with 'please sign up first' message
        flash(request, "Dream entry temporarily stored - log in or create an account to save it!", "info")
        return RedirectResponse("/signup", status_code=303)