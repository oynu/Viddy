import random
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.database.session import get_db
from backend.database import crud

class IdeaProposal(BaseModel):
    title: str
    category: str
    hook_angle: str
    keywords: List[str] = Field(default_factory=list)
    curiosity_score: float = 8.5
    visual_potential: float = 9.0
    scientific_reliability: float = 9.5
    visual_concept: str = ""

# Curated seed bank across the 8 science categories with diverse angles
SEED_CONCEPTS = [
    # Astrophysics & Space
    {
        "title": "What if Earth's Gravity Doubled?",
        "category": "physics",
        "hook_angle": "Your body instantly weighs 350 pounds and trees snap like twigs",
        "keywords": ["gravity", "weight", "density", "atmosphere", "physics"],
        "curiosity_score": 9.4,
        "visual_concept": "Low-poly human figure straining under heavy gravity as objects slam to the ground"
    },
    {
        "title": "What if the Moon Disappeared Tonight?",
        "category": "astronomy",
        "hook_angle": "Tides collapse by 70 percent and Earth's axis begins to wobble violently",
        "keywords": ["moon", "tides", "orbit", "astronomy", "earth"],
        "curiosity_score": 9.2,
        "visual_concept": "Low-poly Earth floating in deep space as the glowing Moon dissolves into dust"
    },
    {
        "title": "How Does a Supermassive Black Hole Warp Time?",
        "category": "astronomy",
        "hook_angle": "One hour near Sagittarius A star is seven years back on Earth",
        "keywords": ["black hole", "relativity", "event horizon", "time dilation"],
        "curiosity_score": 9.6,
        "visual_concept": "Low-poly accretion disk swirling around a dark singularity with glowing photon ring"
    },
    {
        "title": "What if the Sun Vanished for 24 Hours?",
        "category": "astronomy",
        "hook_angle": "Earth flies into the dark abyss at 67,000 miles per hour",
        "keywords": ["sun", "solar system", "gravity", "darkness", "freezing"],
        "curiosity_score": 9.5,
        "visual_concept": "Low-poly solar system where planetary orbits break into straight tangent lines"
    },
    # Quantum & Physics
    {
        "title": "How Does Quantum Tunneling Let Particles Pass Through Walls?",
        "category": "physics",
        "hook_angle": "At the atomic scale, matter behaves like waves that leak through solid barriers",
        "keywords": ["quantum", "tunneling", "particle", "wave function", "energy barrier"],
        "curiosity_score": 9.1,
        "visual_concept": "Glowing low-poly wave packet penetrating an impenetrable geometric energy wall"
    },
    {
        "title": "What if Every Atom Became Twice as Heavy?",
        "category": "physics",
        "hook_angle": "All chemical reactions freeze and celestial orbits collapse inward",
        "keywords": ["atoms", "mass", "chemistry", "protons", "universal constants"],
        "curiosity_score": 8.8,
        "visual_concept": "Low-poly atomic nucleus expanding with vibrating electron clouds"
    },
    # Biology & Neuroscience
    {
        "title": "How Does Your Brain Generate a Thought in Milliseconds?",
        "category": "biology",
        "hook_angle": "Eighty-six billion neurons firing electric pulses faster than a Formula 1 car",
        "keywords": ["neuroscience", "neurons", "action potential", "synapse", "brain"],
        "curiosity_score": 8.9,
        "visual_concept": "Pulsing low-poly neural network with glowing electrical impulses traveling across axons"
    },
    {
        "title": "What Happens Inside a Cell During Mitosis?",
        "category": "biology",
        "hook_angle": "Microscopic molecular machines pulling DNA strands apart with mechanical precision",
        "keywords": ["mitosis", "dna", "cell biology", "chromosomes", "microtubules"],
        "curiosity_score": 8.7,
        "visual_concept": "Low-poly cell membrane dividing into two distinct glowing daughter cells"
    },
    # Chemistry & Materials
    {
        "title": "Why Does Ice Float on Water Unlike Almost Every Other Liquid?",
        "category": "chemistry",
        "hook_angle": "The unique hexagonal crystal cage that saves all aquatic life on Earth",
        "keywords": ["water", "ice", "hydrogen bonds", "density", "chemistry"],
        "curiosity_score": 8.6,
        "visual_concept": "Low-poly water molecules snapping into open hexagonal crystal lattices"
    },
    {
        "title": "How Does Graphene Withstand Bullets Despite Being One Atom Thick?",
        "category": "chemistry",
        "hook_angle": "A hexagonal honeycomb of carbon 200 times stronger than structural steel",
        "keywords": ["graphene", "carbon", "materials science", "nanotech", "strength"],
        "curiosity_score": 9.0,
        "visual_concept": "Translucent low-poly 2D lattice deflecting an incoming high-speed geometric projectile"
    },
    # AI & Technology
    {
        "title": "How Does an Artificial Neural Network Actually Learn?",
        "category": "technology",
        "hook_angle": "Millions of mathematical weights shifting through high-dimensional gradient descent",
        "keywords": ["ai", "neural networks", "gradient descent", "machine learning"],
        "curiosity_score": 9.3,
        "visual_concept": "Geometric multi-layer perceptron lattice lighting up in cascading matrix passes"
    },
    {
        "title": "How Does Quantum Computing Calculate in Parallel Universes?",
        "category": "technology",
        "hook_angle": "Qubits existing in superposition until the moment of observation",
        "keywords": ["quantum computing", "qubit", "superposition", "algorithms"],
        "curiosity_score": 9.4,
        "visual_concept": "Bloch sphere with orbiting vector arrows illuminating multi-state low-poly geometries"
    },
    # Mathematics & Paradoxes
    {
        "title": "The Gabriel's Horn Paradox: Infinite Surface but Finite Paint?",
        "category": "mathematics",
        "hook_angle": "A 3D trumpet shape that you can fill with paint but never coat its surface",
        "keywords": ["calculus", "geometry", "paradox", "infinite", "mathematics"],
        "curiosity_score": 9.2,
        "visual_concept": "Flaring low-poly horn funneling endlessly into an infinitesimally narrow needle"
    },
    # Everyday Science
    {
        "title": "Why Does Boiling Water Make Bubbles from the Bottom Up?",
        "category": "everyday_science",
        "hook_angle": "Thermal convection plumes and nucleation sites creating miniature steam explosions",
        "keywords": ["thermodynamics", "nucleation", "boiling", "heat transfer"],
        "curiosity_score": 8.5,
        "visual_concept": "Low-poly liquid vessel with buoyant faceted steam bubbles accelerating upward"
    }
]

class IdeaDiscoveryAgent:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._counter = 0

    def discover_next_idea(self) -> IdeaProposal:
        """
        Discovers the next optimal video idea by cross-checking against past ideas
        in the persistent SQLite database to guarantee uniqueness.
        """
        # Load historical titles
        past_titles = set()
        if self.db_path:
            with get_db(self.db_path) as session:
                recent = crud.get_recent_ideas(session, limit=500)
                past_titles = {i.title.strip().lower() for i in recent}
        
        # Candidate pool
        candidates = []
        for seed in SEED_CONCEPTS:
            if seed["title"].strip().lower() not in past_titles:
                candidates.append(seed)
        
        # If all predefined seeds were used, generate algorithmic combinations
        if not candidates:
            candidates = self._generate_algorithmic_concepts(past_titles)
        
        # Select best candidate based on curiosity and freshness
        selected = random.choice(candidates)
        
        return IdeaProposal(
            title=selected["title"],
            category=selected["category"],
            hook_angle=selected["hook_angle"],
            keywords=selected["keywords"],
            curiosity_score=selected["curiosity_score"],
            visual_concept=selected.get("visual_concept", "Low-poly 3D educational scene")
        )

    def record_idea(self, idea: IdeaProposal) -> None:
        """Saves discovered idea into persistent history to avoid repeating it."""
        if self.db_path:
            with get_db(self.db_path) as session:
                crud.record_idea_history(
                    session=session,
                    title=idea.title,
                    category=idea.category,
                    hook_angle=idea.hook_angle,
                    keywords=",".join(idea.keywords),
                    score=idea.curiosity_score
                )

    def _generate_algorithmic_concepts(self, past_titles: set) -> List[dict]:
        """Generates novel permutations if seed library is fully consumed."""
        subjects = [
            ("Earth's magnetic field", "compasses spin wildly and cosmic radiation showers the atmosphere", "physics"),
            ("Speed of light halved", "car headlights illuminate yesterday and relativistic colors smear", "physics"),
            ("Ocean water turned to fresh water", "marine food webs collapse and global currents halt", "chemistry"),
            ("Atmospheric pressure dropped by 50%", "water boils at room temperature and weather turns violent", "physics"),
            ("DNA replication accuracy dropped to 90%", "mutations surge and cellular replication collapses", "biology"),
            ("Superconductivity at room temperature", "flying trains and lossless power grids transform civilization", "technology"),
            ("Jupiter ejected from the Solar System", "inner planets face a relentless asteroid bombardment", "astronomy")
        ]
        
        templates = [
            ("What if {subject} happened tomorrow?", "What if {subject}?"),
            ("How does {subject} actually work?", "How does {subject} work?")
        ]
        
        results = []
        for subj, consequence, category in subjects:
            for tmpl, _ in templates:
                title = tmpl.format(subject=subj)
                if title.strip().lower() not in past_titles:
                    results.append({
                        "title": title,
                        "category": category,
                        "hook_angle": consequence,
                        "keywords": [w.lower() for w in subj.split() if len(w) > 3],
                        "curiosity_score": 8.8,
                        "visual_concept": f"Low-poly visualization of {subj}"
                    })
        
        # Fallback if somehow even these match
        if not results:
            self._counter += 1
            results.append({
                "title": f"Cosmic Phenomenon #{self._counter}: What if Gravity Inverted?",
                "category": "physics",
                "hook_angle": "Objects fall upwards towards the stratosphere",
                "keywords": ["gravity", "inversion", "physics"],
                "curiosity_score": 8.5,
                "visual_concept": "Low-poly inverted physics simulation"
            })
            
        return results
