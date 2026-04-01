from typing import Annotated

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from ..models import Tag
from ..forms import DreamEntryForm
from ..utils import DbSesDep, ResearcherDep, UserDep, flash
from ..jinja import templates

router = APIRouter()

@router.get("/")
def record_dream_form(request: Request, dbSes: DbSesDep, user: UserDep):
    # Attempt to retrieve stored form data from the session
    storedEntryJson = request.session.get("storedEntry")
    if storedEntryJson:
        storedEntry = DreamEntryForm.model_validate_json(storedEntryJson)
    else:
        storedEntry = None
    
    # Various useful data for the template renderer
    context = {
        "entry": storedEntry,
        "senses": ['sight', 'sound', 'touch', 'smell', 'taste', 'pain', 'other'],
        "contentTags": map(lambda row: row[0], dbSes.execute(select(Tag.value).where(Tag.category == "dream_content")).all()),
        "typeTags": map(lambda row: row[0], dbSes.execute(select(Tag.value).where(Tag.category == "dream_type")).all()),
        "contextTags": map(lambda row: row[0], dbSes.execute(select(Tag.value).where(Tag.category == "irl_context")).all()),
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
        # Create and save a new DreamEntry based on form data, and link any necessary tags
        newEntry = formDataModel.createDreamEntry()
        if newEntry.public and not user.public_enabled:
            newEntry.public = False
            flash(request, "Entry marked as non-public to match your account settings", "info")
        user.dream_entries.append(newEntry)
        badTags = []
        for tagName in formDataModel.all_tags:
            tagObj = dbSes.get(Tag, tagName)
            if tagObj is None: badTags.append(tagName)
            else: newEntry.tags.append(tagObj)
        if badTags:
            for tag in badTags: flash(request, f"'{tag}' is not a valid tag!", "warn")
            return RedirectResponse("/", status_code=303)
        dbSes.add(newEntry)
        dbSes.commit()

        # Now that the entry is saved, clear it out of the session if it's there
        request.session.pop("storedEntry", None)

        # Return to homepage with success message
        flash(request, "Dream entry saved", "success")
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

        # Redirect to the signup page with 'please sign up first' message
        flash(request, "Dream entry temporarily stored - create an account to save it!", "info")
        return RedirectResponse("/signup", status_code=303)