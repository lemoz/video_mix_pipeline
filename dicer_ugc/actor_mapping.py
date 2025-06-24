"""Actor scene ID mappings and voice configurations."""

from typing import Dict, Optional
from .models import Actor


# Scene IDs from production system
ACTOR_SCENE_MAPPING = {
    # Primary actors
    "janet": "5513cdb5-c6c7-483e-8b94-67f6a42f1747",
    "violet": "7b4c0d82-2e4c-4e83-b7a2-4ac11ac53e54",
    "nora": "2841226b-85f0-4f5a-929c-ff752ed3d1ad",
    "grace": "05cf6a24-1305-45cc-bf07-8aee2c21b30a",
    "lauren": "96f59715-0c73-4395-8dde-e73937c6b8a0",
    "lily": "c0b2afd0-a026-11ee-8c90-0242ac120002",
    "donna": "63cf7c90-abd3-4443-87ff-c5a066d62cf3",
    "zoe": "5d3d66ee-e168-492b-9185-340425abcd0b",
    "susan": "53c0d132-2f56-4b2f-8373-e7d5efb3b2ec",
    "ernest": "6fb4c27f-cf6a-41af-a292-9439b0628187",
    "cooper": "8f3e31fd-3904-4b6c-a6ab-bf7a2b15f670",
    "damian": "7b48c323-3441-4130-ab75-0dab00a0c838",
    "danielle": "c08004ce-d522-40a9-959c-98275e85942a",
    "erin": "2699eebf-f304-4237-bdcf-de2e866ac5d4",
    "henry": "23d32324-b39b-4404-bf1d-d763524f5186",
    "raymond": "93463280-b873-40f2-a594-5a4859896914",
    "robert": "49eba1cf-60ae-4ea9-9459-2e62ca911177",
    "olivia": "9bd1e9ed-5747-4052-96fe-1b6862e6dada",
    "thomas": "170692b6-d269-4370-83ea-0fe69add708f",
    "timothy": "1b8edf0c-6301-44f0-9794-c5a375fb3416",
    "walter": "6ae0395a-e409-4827-b8c7-9a5ea091ee6f",
    
    # Additional actors
    "audrey": "82896cba-128a-4ef0-96ea-a76a669625ad",
    "gloria": "4077478a-bf36-48fc-ae83-d55673c6cada",
    "jasmine": "69a98718-8f80-4254-8ab0-79444d1144b6",
    "roger": "de17674a-ad6a-4cd9-b09f-4cee8c101ec1",
    "vincent": "63328872-43e1-4f88-b513-d7eeeca09827",
    "albert": "2078e5db-9e78-4f6f-a0c0-35eec8ae0f6b",
    "daniel": "3624caae-f548-4cf9-93cb-72bd18c5de76",
    
    # Pet scenario actors
    "victoria_pet": "200bd758-d76f-4fdb-b85b-2a9b9505ee08",
    "vincent_pet": "b62640a7-f1b2-4cf7-877c-63b78aed2ad1",
    "leah_pet": "355238b5-0588-45bd-9e3f-95ecd2b3408a",
    "allison_pet": "060a1cfa-8500-4edf-99f7-00195ead26a5",
    "hailey_pet": "8d6bdce4-4327-4bcf-b79a-4f160d500902",
    "austin_pet": "520bbf1a-3ee3-44b0-8ffc-741ce2a32e1d",
    "emmy_pet": "6b7f35ab-dbaa-46b7-a1e7-51c86ef0cb51",
    "janet_pet": "2624b4ce-ee7c-48dd-86ab-986d1db779dd",
}


# Example ElevenLabs voice ID mappings (customize as needed)
ACTOR_VOICE_MAPPING = {
    # Female voices
    "janet": "21m00Tcm4TlvDq8ikWAM",      # Rachel
    "violet": "AZnzlk1XvdvUeBnXmlld",     # Domi
    "nora": "EXAVITQu4vr4xnSDxMaL",        # Bella
    "grace": "MF3mGyEYCl7XYWbV9V6O",       # Elli
    "lauren": "XrExE9yKIg1WjnnlVkGX",      # Lily
    "lily": "pNInz6obpgDQGcFmaJgB",        # Glinda
    "donna": "ThT5KcBeYPX3keUQqHPh",       # Dorothy
    "olivia": "jBpfuIE2acCO8z3wKNLl",      # Gigi
    "susan": "jsCqWAovK2LkecY7zXl4",       # Freya
    
    # Male voices
    "ernest": "VR6AewLTigWG4xSOukaG",      # Arnold
    "cooper": "pqHfZKP75CvOlQylNhV4",      # Bill
    "damian": "nPczCjzI2devNBz1zQrb",      # Brian
    "henry": "ODq5zmih8GrVes37Dizd",       # Patrick
    "robert": "yoZ06aMxZJJ28mfd3POQ",      # Sam
    "thomas": "GBv7mTt0atIp3Br8iCZE",      # Thomas
    "walter": "flq6f7yk4E4fJM5XTYuZ",      # Michael
    
    # Default for unmapped actors
    "_default": "21m00Tcm4TlvDq8ikWAM",     # Rachel
}


def get_actor(name: str, voice_id: Optional[str] = None) -> Actor:
    """
    Get an Actor object with scene ID and voice mapping.
    
    Args:
        name: Actor name
        voice_id: Optional override for voice ID
        
    Returns:
        Actor object with scene_id and voice_id populated
    """
    scene_id = ACTOR_SCENE_MAPPING.get(name, "")
    
    if not scene_id:
        raise ValueError(f"Unknown actor: {name}. Available actors: {', '.join(ACTOR_SCENE_MAPPING.keys())}")
    
    # Get voice ID from mapping or use provided override
    if voice_id is None:
        voice_id = ACTOR_VOICE_MAPPING.get(name, ACTOR_VOICE_MAPPING["_default"])
    
    return Actor(
        name=name,
        scene_id=scene_id,
        voice_id=voice_id
    )


def list_available_actors() -> Dict[str, str]:
    """List all available actors and their scene IDs."""
    return ACTOR_SCENE_MAPPING.copy()


def list_pet_actors() -> Dict[str, str]:
    """List actors with pet scenarios."""
    return {k: v for k, v in ACTOR_SCENE_MAPPING.items() if k.endswith("_pet")}


def list_regular_actors() -> Dict[str, str]:
    """List actors without pet scenarios."""
    return {k: v for k, v in ACTOR_SCENE_MAPPING.items() if not k.endswith("_pet")}